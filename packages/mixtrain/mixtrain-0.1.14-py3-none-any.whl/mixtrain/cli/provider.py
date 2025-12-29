import typer
from rich import print as rprint
from rich.table import Table

from mixtrain.client import MixClient

app = typer.Typer(help="Manage dataset and model providers", invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def get_provider_config_by_id(provider_id: int):
    client = MixClient()
    # Check dataset providers first
    dataset_data = client.list_dataset_providers()
    dataset_onboarded = dataset_data.get("onboarded_providers", [])
    for provider in dataset_onboarded:
        if provider.get("id") == provider_id:
            provider["provider_category"] = "dataset"
            return provider, client

    # Check model providers
    model_data = client.list_model_providers()
    model_onboarded = model_data.get("onboarded_providers", [])
    for provider in model_onboarded:
        if provider.get("id") == provider_id:
            provider["provider_category"] = "model"
            return provider, client

    rprint(f"[red]Error:[/red] Provider with ID {provider_id} not found.")
    raise typer.Exit(1)


def get_provider_config(provider_type: str):
    client = MixClient()
    # Check dataset providers first
    dataset_data = client.list_dataset_providers()
    dataset_available = dataset_data.get("available_providers", [])

    for provider in dataset_available:
        if provider.get("provider_type") == provider_type:
            provider["provider_category"] = "dataset"
            return provider, client

    # Check model providers
    model_data = client.list_model_providers()
    model_available = model_data.get("available_providers", [])

    for provider in model_available:
        if provider.get("provider_type") == provider_type:
            provider["provider_category"] = "model"
            return provider, client

    # Provider not found - show available options
    rprint(f"[red]Error:[/red] Provider type '{provider_type}' not found.")
    rprint("Available dataset providers:")
    for provider in dataset_available:
        rprint(
            f"  - {provider.get('provider_type')}: {provider.get('display_name')}"
        )
    rprint("Available model providers:")
    for provider in model_available:
        rprint(
            f"  - {provider.get('provider_type')}: {provider.get('display_name')}"
        )
    raise typer.Exit(1)


@app.command(name="status")
def status():
    """List available and configured dataset and model providers."""
    try:
        client = MixClient()
        # Get dataset providers
        dataset_data = client.list_dataset_providers()

        # Get model providers
        model_data = client.list_model_providers()

        # Show available dataset providers
        dataset_available = dataset_data.get("available_providers", [])
        if dataset_available:
            rprint("[bold]Available Dataset Providers:[/bold]")
            table = Table("Provider Type", "Display Name", "Description", "Status")
            for provider in dataset_available:
                table.add_row(
                    provider.get("provider_type", ""),
                    provider.get("display_name", ""),
                    provider.get("description", "")[:50] + "..."
                    if len(provider.get("description", "")) > 50
                    else provider.get("description", ""),
                    provider.get("status", ""),
                )
            rprint(table)
            rprint()

        # Show available model providers
        model_available = model_data.get("available_providers", [])
        if model_available:
            rprint("[bold]Available Model Providers:[/bold]")
            table = Table("Provider Type", "Display Name", "Description", "Status")
            for provider in model_available:
                table.add_row(
                    provider.get("provider_type", ""),
                    provider.get("display_name", ""),
                    provider.get("description", "")[:50] + "..."
                    if len(provider.get("description", "")) > 50
                    else provider.get("description", ""),
                    provider.get("status", ""),
                )
            rprint(table)
            rprint()

        # Show onboarded dataset providers
        dataset_onboarded = dataset_data.get("onboarded_providers", [])
        if dataset_onboarded:
            rprint("[bold]Configured Dataset Providers:[/bold]")
            table = Table("ID", "Provider Type", "Display Name", "Created At")
            for provider in dataset_onboarded:
                table.add_row(
                    str(provider.get("id", "")),
                    provider.get("provider_type", ""),
                    provider.get("display_name", ""),
                    provider.get("created_at", ""),
                )
            rprint(table)
            rprint()

        # Show onboarded model providers
        model_onboarded = model_data.get("onboarded_providers", [])
        if model_onboarded:
            rprint("[bold]Configured Model Providers:[/bold]")
            table = Table("ID", "Provider Type", "Display Name", "Created At")
            for provider in model_onboarded:
                table.add_row(
                    str(provider.get("id", "")),
                    provider.get("provider_type", ""),
                    provider.get("display_name", ""),
                    provider.get("created_at", ""),
                )
            rprint(table)
            rprint()

        if not dataset_onboarded and not model_onboarded:
            rprint("[yellow]No providers configured yet.[/yellow]")
            rprint("Use 'mixtrain provider add <type>' to add one.")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="add")
def add_provider(provider_type: str):
    """Add a new dataset or model provider to workspace."""
    try:
        provider_config, client = get_provider_config(provider_type)
        provider_category = provider_config.get("provider_category")

        # Show provider info
        rprint(f"[bold]Adding {provider_config.get('display_name')} ({provider_category} provider)[/bold]")
        rprint(f"Description: {provider_config.get('description', '')}")
        if provider_config.get("onboarding_instructions"):
            rprint(f"Instructions: {provider_config.get('onboarding_instructions')}")
        rprint()

        # Collect secrets
        secrets = {}
        secret_requirements = provider_config.get("secret_requirements", [])

        for req in secret_requirements:
            prompt_text = f"{req.get('display_name')} ({req.get('description')})"
            if req.get("is_required"):
                prompt_text += " [required]"
            else:
                prompt_text += " [optional]"

            # Use hidden input for sensitive data
            if any(
                keyword in req.get("name", "").lower()
                for keyword in ["key", "secret", "password", "token"]
            ):
                value = typer.prompt(prompt_text, hide_input=True)
            else:
                value = typer.prompt(
                    prompt_text, default="" if not req.get("is_required") else None
                )

            if value:
                secrets[req.get("name")] = value

        if not secrets:
            rprint("[yellow]No secrets provided. Cancelling setup.[/yellow]")
            raise typer.Exit(1)

        # Create the provider based on category
        if provider_category == "dataset":
            result = client.create_dataset_provider(provider_type, secrets)
        elif provider_category == "model":
            result = client.create_model_provider(provider_type, secrets)
        else:
            raise Exception(f"Unknown provider category: {provider_category}")

        rprint(f"[green]✓[/green] Successfully added {result.get('display_name')}!")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="update")
def update_provider_cmd(provider_id: int):
    """Update secrets for an existing dataset or model provider."""
    try:
        provider, client = get_provider_config_by_id(provider_id)
        provider_category = provider.get("provider_category")

        rprint(f"[bold]Updating {provider.get('display_name')} ({provider_category} provider)[/bold]")
        rprint()

        # Collect updated secrets
        secrets = {}
        secret_requirements = provider.get("secret_requirements", [])

        for req in secret_requirements:
            prompt_text = f"{req.get('display_name')} ({req.get('description')}) [leave empty to keep current]"

            # Use hidden input for sensitive data
            if any(
                keyword in req.get("name", "").lower()
                for keyword in ["key", "secret", "password", "token"]
            ):
                value = typer.prompt(prompt_text, default="", hide_input=True)
            else:
                value = typer.prompt(prompt_text, default="")

            # Only include non-empty values
            if value:
                secrets[req.get("name")] = value

        if not secrets:
            rprint("[yellow]No secrets updated.[/yellow]")
            return

        # Update provider based on category
        if provider_category == "dataset":
            result = client.update_dataset_provider(provider_id, secrets)
        elif provider_category == "model":
            result = client.update_model_provider(provider_id, secrets)
        else:
            raise Exception(f"Unknown provider category: {provider_category}")

        rprint(f"[green]✓[/green] Successfully updated {result.get('display_name')}!")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="remove")
def remove_provider(provider_id: int):
    """Remove a dataset or model provider from workspace."""
    try:
        provider, client = get_provider_config_by_id(provider_id)
        provider_category = provider.get("provider_category")
        provider_name = provider.get("display_name")

        confirm = typer.confirm(
            f"Remove {provider_name} ({provider_category} provider)? This will delete all associated secrets."
        )
        if not confirm:
            rprint("Removal cancelled.")
            return

        # Remove provider based on category
        if provider_category == "dataset":
            client.delete_dataset_provider(provider_id)
        elif provider_category == "model":
            client.delete_model_provider(provider_id)
        else:
            raise Exception(f"Unknown provider category: {provider_category}")

        rprint(f"[green]✓[/green] Successfully removed {provider_name}!")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="info")
def info_provider(provider_type: str):
    """Show detailed information about a dataset or model provider."""
    try:
        client = MixClient()
        # Check dataset providers first
        dataset_data = client.list_dataset_providers()
        provider_config = None
        provider_category = None

        # Look in available dataset providers
        for provider in dataset_data.get("available_providers", []):
            if provider.get("provider_type") == provider_type:
                provider_config = provider
                provider_category = "dataset"
                break

        # Look in onboarded dataset providers
        if not provider_config:
            for provider in dataset_data.get("onboarded_providers", []):
                if provider.get("provider_type") == provider_type:
                    provider_config = provider
                    provider_category = "dataset"
                    break

        # Check model providers if not found in dataset providers
        if not provider_config:
            model_data = client.list_model_providers()

            # Look in available model providers
            for provider in model_data.get("available_providers", []):
                if provider.get("provider_type") == provider_type:
                    provider_config = provider
                    provider_category = "model"
                    break

            # Look in onboarded model providers
            if not provider_config:
                for provider in model_data.get("onboarded_providers", []):
                    if provider.get("provider_type") == provider_type:
                        provider_config = provider
                        provider_category = "model"
                        break

        if not provider_config:
            rprint(f"[red]Error:[/red] Provider type '{provider_type}' not found.")
            raise typer.Exit(1)

        # Display provider information
        rprint(f"[bold]{provider_config.get('display_name')} ({provider_category} provider)[/bold]")
        rprint(f"Type: {provider_config.get('provider_type')}")
        rprint(f"Status: {provider_config.get('status', 'available')}")
        rprint(f"Description: {provider_config.get('description', '')}")
        if provider_config.get("website_url"):
            rprint(f"Website: {provider_config.get('website_url')}")
        rprint()

        # Show secret requirements
        secret_requirements = provider_config.get("secret_requirements", [])
        if secret_requirements:
            rprint("[bold]Required Configuration:[/bold]")
            table = Table("Setting", "Description", "Required")
            for req in secret_requirements:
                table.add_row(
                    req.get("display_name", ""),
                    req.get("description", ""),
                    "Yes" if req.get("is_required") else "No",
                )
            rprint(table)

        # Show onboarding instructions
        if provider_config.get("onboarding_instructions"):
            rprint("\n[bold]Setup Instructions:[/bold]")
            rprint(provider_config.get("onboarding_instructions"))

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="models")
def list_available_models():
    """List all available models from configured model providers."""
    try:
        client = MixClient()
        models = client.list_models()

        if not models:
            rprint("[yellow]No models available.[/yellow]")
            rprint("Configure a model provider first using 'mixtrain provider add <type>'.")
            return

        rprint("[bold]Available Models:[/bold]")
        table = Table("Name", "Provider", "URL")
        for model in models:
            table.add_row(
                model.get("name", ""),
                model.get("provider_name", ""),
                model.get("url", ""),
            )
        rprint(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
