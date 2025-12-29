"""CLI commands for routing engine."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from mixtrain.client import MixClient
from mixtrain.routing import (
    ConfigBuilder,
    RoutingConfig,
    RoutingEngineFactory,
    RoutingStrategy,
)

app = typer.Typer(
    help="Routing engine commands",
    invoke_without_command=True,
)
console = Console()


@app.callback()
def routing_main(ctx: typer.Context):
    """Router commands for configuration management and testing.

    Use 'mixtrain router list' to see available routers.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(name="list")
def list_routers():
    """List all routers in the workspace.

    Each router can be independently deployed with its own inference URL.
    Routers with 'Deployed' status have an active deployment.
    """
    try:
        client = MixClient()
        routers = client.list_routers()

        if not routers:
            rprint("[yellow]No routers found.[/yellow]")
            rprint("Use 'mixtrain router create <name>' to create one.")
            return

        # Show routers
        table = Table("Name", "Description", "Version", "Created", "Updated")
        for router in routers:
            table.add_row(
                router.get("name", ""),
                (router.get("description", "") or "")[:40]
                + ("..." if len(router.get("description", "") or "") > 40 else ""),
                str(router.get("version", "")),
                format_date(router.get("created_at", "")),
                format_date(router.get("updated_at", "")),
            )
        console.print(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def format_date(date_str: str) -> str:
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()  # converts to system local timezone
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


@app.command()
def create(
    name: str = typer.Argument(help="Router name"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output file path"
    ),
    interactive: bool = typer.Option(
        False, "-i", "--interactive", help="Interactive router builder"
    ),
    from_json: Optional[str] = typer.Option(
        None, "--from-json", help="Create router from JSON file"
    ),
):
    """Create a new router.

    Can create from JSON file (--from-json), interactively (-i), or with basic prompts.
    """
    try:
        if from_json:
            # Load configuration from JSON file
            try:
                with open(from_json) as f:
                    json_data = json.load(f)

                # Use the name and description from the JSON file, but allow name override from CLI
                config_name = name if name else json_data.get("name", "imported-router")
                config_description = json_data.get("description", "")
                rules = json_data.get("rules", [])

                if not rules:
                    rprint("[red]Error:[/red] JSON file must contain 'rules' array")
                    raise typer.Exit(1)

                # Create RoutingConfig object from JSON data
                config = RoutingConfig(
                    name=config_name, description=config_description, rules=rules
                )

            except FileNotFoundError:
                rprint(f"[red]Error:[/red] JSON file '{from_json}' not found")
                raise typer.Exit(1)
            except json.JSONDecodeError as e:
                rprint(f"[red]Error:[/red] Invalid JSON in file '{from_json}': {e}")
                raise typer.Exit(1)
        elif interactive:
            config = _interactive_config_builder(name)
        else:
            # Create a simple default configuration
            endpoint = typer.prompt("Default endpoint URL")
            config = (
                ConfigBuilder(name, "Default routing configuration")
                .add_rule(
                    "default", description="Route all requests to default endpoint"
                )
                .add_target("custom", "default", endpoint)
                .build()
            )

        config_json = config.to_json()

        if output:
            # Save to local file
            with open(output, "w") as f:
                json.dump(config_json, f, indent=2)
            rprint(f"[green]✓[/green] Configuration saved to {output}")
        else:
            # Create in backend via API
            client = MixClient()
            response = client.create_routing_config(
                config.name,
                config.description or "",
                [rule.dict() for rule in config.rules],
            )

            if response:
                router_name = response.get("name", config.name)
                rprint(f"[green]✓[/green] Router '{router_name}' created successfully")
                rprint(f"Use 'mixtrain router view {router_name}' to view details")
            else:
                rprint("[red]Error:[/red] Failed to create router in backend")
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="add-rule")
def add_rule(
    router_name: str = typer.Argument(help="Router name to add rule to"),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="Rule name"),
):
    """Add a new rule to a router.

    A new version is created with the added rule.
    """
    try:
        client = MixClient()
        config_data = client.get_routing_config(router_name)

        # Build new rule interactively
        rprint(
            f"[bold]Adding new rule to router: {config_data.get('name', 'Unnamed')}[/bold]"
        )
        if not name:
            name = typer.prompt("Rule name")

        priority = typer.prompt("Rule priority", default=0, type=int)
        description = typer.prompt("Rule description", default="")

        # Create rule data
        rule_data = {
            "name": name,
            "priority": priority,
            "description": description,
            "is_enabled": True,
            "conditions": [],
            "targets": [],
            "strategy": "single",
        }

        # Add conditions
        rprint(
            "\n[bold]Add conditions (press Enter with empty field to finish):[/bold]"
        )
        while True:
            field = typer.prompt("Condition field", default="")
            if not field.strip():
                break
            operator = typer.prompt(
                "Operator (equals, in, greater_than, etc.)", default="equals"
            )
            value = typer.prompt("Value (or JSON for arrays)")
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            rule_data["conditions"].append(
                {"field": field, "operator": operator, "value": parsed_value}
            )

        # Add targets
        rprint("\n[bold]Add targets (at least one required):[/bold]")
        while True:
            target_data = _interactive_target_builder()
            rule_data["targets"].append(target_data)

            if not typer.confirm("Add another target?"):
                break

        # Set strategy based on number of targets
        if len(rule_data["targets"]) > 1:
            strategy = typer.prompt("Strategy", default="split")
            rule_data["strategy"] = strategy

        # Add rule to config
        rules = config_data.get("rules", [])
        rules.append(rule_data)

        # Update backend config - creates a new version
        client.update_routing_config(router_name, rules=rules)
        rprint(f"Rule '{name}' added to router '{router_name}'")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def test(
    router_name: str = typer.Argument(help="Router name to test"),
    request_file: Optional[str] = typer.Option(
        None, "-r", "--request", help="JSON file containing request data"
    ),
    request_data: Optional[str] = typer.Option(
        None, "-d", "--data", help="JSON string with request data"
    ),
    expected_rule: Optional[str] = typer.Option(
        None, "-e", "--expected", help="Expected rule name"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show detailed results"
    ),
):
    """Test routing against sample request data."""
    try:
        client = MixClient()
        config_data = client.get_routing_config(router_name)
        engine = RoutingEngineFactory.from_json(config_data)

        # Get request data
        if request_file:
            with open(request_file) as f:
                request_data_dict = json.load(f)
        elif request_data:
            request_data_dict = json.loads(request_data)
        else:
            # Interactive input
            request_data_dict = _interactive_request_builder()

        # Route the request
        result = engine.test_request(request_data_dict, expected_rule)

        # Display results
        _display_routing_result(result, verbose)

        # Exit with error code if test failed expectation
        if expected_rule and result.metadata.get("matched_expected") is False:
            raise typer.Exit(1)

    except json.JSONDecodeError as e:
        rprint(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def view(
    router_name: str = typer.Argument(help="Router name to view"),
    json_output: bool = typer.Option(False, "--json", help="Output json format"),
):
    """View detailed router rules and configuration."""
    try:
        client = MixClient()
        config_data = client.get_routing_config(router_name)

        config = RoutingConfig.from_json(config_data)

        if json_output:
            rprint(json.dumps(config.to_json(), indent=2))
        else:
            _display_detailed_config_view(config)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def _interactive_config_builder(name: str) -> "RoutingConfig":
    """Interactive router builder."""
    description = typer.prompt("Router description", default="")
    builder = ConfigBuilder(name, description)

    while True:
        rule_name = typer.prompt("\nRule name")
        rule_priority = typer.prompt("Rule priority", default=0, type=int)
        rule_description = typer.prompt("Rule description", default="")

        rule_builder = builder.add_rule(rule_name, rule_priority, rule_description)

        # Add conditions
        rprint(
            "\n[bold]Add conditions (press Enter with empty field to finish):[/bold]"
        )
        while True:
            field = typer.prompt("Condition field", default="")
            if not field.strip():
                break

            operator = typer.prompt(
                "Operator (equals, in, greater_than, etc.)", default="equals"
            )
            value = typer.prompt("Value (or JSON for arrays)")

            try:
                # Try to parse as JSON first
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                # Use as string if not valid JSON
                parsed_value = value

            rule_builder = rule_builder.with_condition(field, operator, parsed_value)

        # Set strategy
        strategy = typer.prompt(
            "Strategy", default=RoutingStrategy.SINGLE, type=RoutingStrategy
        )

        if strategy == RoutingStrategy.SPLIT:
            rule_builder = rule_builder.use_split_strategy()
        elif strategy == RoutingStrategy.SHADOW:
            rule_builder = rule_builder.use_shadow_strategy()
        elif strategy == RoutingStrategy.FALLBACK:
            rule_builder = rule_builder.use_fallback_strategy()

        # Add targets
        rprint("\n[bold]Add targets:[/bold]")
        while True:
            provider = typer.prompt("Target provider", default="")
            if not provider.strip():
                break

            target_data = _interactive_target_builder_from_provider(provider)

            # Use the builder pattern with the target data
            rule_builder = rule_builder.add_target(
                target_data["provider"],
                target_data["model_name"],
                target_data["endpoint"],
                target_data["weight"],
                function_name=target_data.get("function_name"),
                request_class=target_data.get("request_class"),
            )

        # Ask if user wants to add another rule
        add_another = typer.confirm("\nAdd another rule?")
        if add_another:
            rule_builder = rule_builder.and_rule("", 0, "")
        else:
            break

    return rule_builder.build()


def _interactive_target_builder() -> Dict[str, Any]:
    """Interactive target builder that handles provider-specific fields."""
    provider = typer.prompt("Target provider")
    model_name = typer.prompt("Model name")
    weight = typer.prompt("Weight", default=1.0, type=float)

    target_data = {"provider": provider, "model_name": model_name, "weight": weight}

    if provider.lower() == "modal":
        # Modal provider uses function_name and request_class, endpoint is auto-generated
        function_name = typer.prompt("Function name", default="main")
        request_class = typer.prompt("Request class", default="")
        # Generate placeholder Modal endpoint from model name
        endpoint = f"https://{model_name}--modal.modal.run"
        target_data.update(
            {
                "endpoint": endpoint,
                "function_name": function_name,
                "request_class": request_class or None,
            }
        )
    else:
        # Other providers use endpoint
        endpoint = typer.prompt("Endpoint URL")
        target_data.update(
            {"endpoint": endpoint, "function_name": None, "request_class": None}
        )

    return target_data


def _interactive_target_builder_from_provider(provider: str) -> Dict[str, Any]:
    """Interactive target builder when provider is already known."""
    model_name = typer.prompt("Model name")
    weight = typer.prompt("Weight", default=1.0, type=float)

    target_data = {"provider": provider, "model_name": model_name, "weight": weight}

    if provider.lower() == "modal":
        # Modal provider uses function_name and request_class, endpoint is auto-generated
        function_name = typer.prompt("Function name", default="main")
        request_class = typer.prompt("Request class", default="")
        # Generate placeholder Modal endpoint from model name
        endpoint = f"https://{model_name}--modal.modal.run"
        target_data.update(
            {
                "endpoint": endpoint,
                "function_name": function_name,
                "request_class": request_class or None,
            }
        )
    else:
        # Other providers use endpoint
        endpoint = typer.prompt("Endpoint URL")
        target_data.update(
            {"endpoint": endpoint, "function_name": None, "request_class": None}
        )

    return target_data


def _interactive_request_builder() -> Dict[str, Any]:
    """Interactive request data builder."""
    rprint("[bold]Enter request data (JSON format):[/bold]")
    rprint('Example: {"user": {"tier": "premium"}, "request": {"type": "image"}}')

    while True:
        request_input = typer.prompt("Request data")
        try:
            return json.loads(request_input)
        except json.JSONDecodeError as e:
            rprint(f"[red]Invalid JSON:[/red] {e}")
            rprint("Please enter valid JSON data.")


def _display_routing_result(result, verbose: bool = False):
    """Display routing test results."""
    if result.matched_rule:
        rprint(f"[green]✓ Matched Rule:[/green] {result.matched_rule.name}")
        rprint(f"[blue]Strategy:[/blue] {result.matched_rule.strategy}")
        rprint(f"[blue]Selected Targets:[/blue] {len(result.selected_targets)}")

        if verbose:
            # Show matched rule details
            table = Table(title="Matched Rule Details")
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            table.add_row("Name", result.matched_rule.name)
            table.add_row("Description", result.matched_rule.description or "")
            table.add_row("Priority", str(result.matched_rule.priority))
            table.add_row("Strategy", result.matched_rule.strategy)
            table.add_row("Conditions", str(len(result.matched_rule.conditions)))

            console.print(table)

            # Show selected targets
            if result.selected_targets:
                targets_table = Table(title="Selected Targets")
                targets_table.add_column("Provider")
                targets_table.add_column("Model")
                targets_table.add_column("Endpoint")
                targets_table.add_column("Weight")
                targets_table.add_column("Shadow")

                for target in result.selected_targets:
                    targets_table.add_row(
                        target.provider,
                        target.model_name,
                        target.endpoint,
                        str(target.weight),
                        "Yes" if target.is_shadow else "No",
                    )

                console.print(targets_table)

    else:
        rprint("[red]✗ No rules matched[/red]")

    rprint(f"\n[dim]Explanation:[/dim] {result.explanation}")

    if result.execution_time_ms:
        rprint(f"[dim]Execution time:[/dim] {result.execution_time_ms:.2f}ms")


def _display_detailed_config_view(config):
    """Display configuration details in a compact, table-based format."""
    # Header with basic info
    if config.description:
        rprint(f"[dim]{config.description}[/dim]")

    rprint(
        f"Rules: {sum(1 for r in config.rules if r.is_enabled)}/{len(config.rules)} active"
    )

    if not config.rules:
        rprint("\n[yellow]No routing rules found in this configuration.[/yellow]")
        return

    # Main rules table
    table = Table(show_header=True, header_style="bold cyan", title=config.name)
    table.add_column("Rule Name", style="bold")
    table.add_column("Priority", style="dim")
    table.add_column("Conditions")
    table.add_column("Strategy")
    table.add_column("Targets")

    # Sort rules by priority (highest first)
    sorted_rules = sorted(config.rules, key=lambda r: r.priority, reverse=True)

    for rule in sorted_rules:
        # Conditions summary
        if rule.conditions:
            conditions_summary = []
            for condition in rule.conditions:
                operator_symbol = {
                    "equals": "==",
                    "not_equals": "!=",
                    "in": "∈",
                    "not_in": "∉",
                    "contains": "⊃",
                    "greater_than": ">",
                    "less_than": "<",
                    "greater_than_or_equal": "≥",
                    "less_than_or_equal": "≤",
                    "regex": "~",
                    "exists": "∃",
                    "not_exists": "∄",
                }.get(condition.operator, condition.operator)

                value_str = str(condition.value)
                # if len(value_str) > 10:
                #     value_str = value_str[:8] + ".."

                conditions_summary.append(
                    f"{condition.field}{operator_symbol}{value_str}"
                )

            conditions_text = "\n".join(conditions_summary)
            # if len(rule.conditions) > 2:
            #     conditions_text += f"\n+{len(rule.conditions)-2} more"
        else:
            conditions_text = "[dim]none[/dim]"

        # Targets summary
        if rule.targets:
            targets_summary = []
            for target in rule.targets[:2]:  # Show first 2 targets
                target_text = f"{target.provider}/{target.model_name}"
                if target.weight != 1.0:
                    target_text += f" ({target.weight})"
                if target.is_shadow:
                    target_text += " [dim](shadow)[/dim]"
                targets_summary.append(target_text)

            targets_text = "\n".join(targets_summary)
            if len(rule.targets) > 2:
                targets_text += f"\n+{len(rule.targets) - 2} more"
        else:
            targets_text = "[red]none![/red]"

        if rule.is_enabled:
            table.add_row(
                rule.name,
                str(rule.priority),
                conditions_text,
                rule.strategy,
                targets_text,
            )
        else:
            table.add_row(
                f"[dim]{rule.name}[/dim]",
                f"[dim]{str(rule.priority)}[/dim]",
                f"[dim]{conditions_text}[/dim]",
                f"[dim]{rule.strategy}[/dim]",
                f"[dim]{targets_text}[/dim]",
            )
        table.add_section()

    console.print(table)
