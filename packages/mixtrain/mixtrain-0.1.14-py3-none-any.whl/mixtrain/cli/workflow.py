"""Mixtrain Workflow CLI Commands"""

import json
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from mixtrain import MixClient

app = typer.Typer(help="Manage workflows.", invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(name="list")
def list_workflows():
    """List all workflows in the current workspace."""
    try:
        response = MixClient().list_workflows()
        workflows = response.get("data", [])

        if not workflows:
            rprint("[yellow]No workflows found.[/yellow]")
            rprint("Use 'mixtrain workflow create' to create one.")
            return

        # Show workflows
        rprint("[bold]Workflows:[/bold]")
        table = Table("Name", "Description", "Created At")
        for workflow in workflows:
            table.add_row(
                workflow.get("name", ""),
                workflow.get("description", "")[:50] + "..."
                if len(workflow.get("description", "")) > 50
                else workflow.get("description", ""),
                workflow.get("created_at", ""),
            )
        rprint(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="create")
def create_workflow(
    workflow_file: str = typer.Argument(..., help="Path to workflow Python file"),
    name: str = typer.Option(None, "--name", "-n", help="Workflow name (defaults to filename)"),
    description: str = typer.Option("", "--description", "-d", help="Workflow description"),
    src_files: Optional[list[str]] = typer.Option(None, "--src", "-s", help="Additional source files to include (can be specified multiple times)"),
):
    """Create a new workflow from a Python file.

    The workflow file should be a Python script that defines your workflow logic.
    You can optionally include additional source files that the workflow depends on.

    Examples:
      mixtrain workflow create train.py --name my-training-workflow
      mixtrain workflow create workflow.py --src utils.py --src config.json
      mixtrain workflow create main.py --name inference --description "Run inference"
    """
    try:
        import os

        # Validate workflow file exists
        if not os.path.exists(workflow_file):
            rprint(f"[red]Error:[/red] Workflow file not found: {workflow_file}")
            raise typer.Exit(1)

        # Default name to filename without extension if not provided
        if not name:
            name = os.path.splitext(os.path.basename(workflow_file))[0]

        # Validate source files exist
        if src_files:
            for src_file in src_files:
                if not os.path.exists(src_file):
                    rprint(f"[red]Error:[/red] Source file not found: {src_file}")
                    raise typer.Exit(1)

        # Create workflow with files
        result = MixClient().create_workflow_with_files(
            name=name,
            description=description,
            workflow_file=workflow_file,
            src_files=src_files or [],
        )
        workflow_data = result.get("data", {})
        rprint(
            f"[green]✓[/green] Successfully created workflow '{workflow_data.get('name')}'"
        )
        rprint(f"  Uploaded workflow file: {workflow_file}")
        if src_files:
            rprint(f"  Uploaded {len(src_files)} additional source file(s)")

    except FileNotFoundError as e:
        rprint(f"[red]Error:[/red] File not found: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="get")
def get_workflow(workflow_name: str = typer.Argument(..., help="Workflow name")):
    """Get details of a specific workflow."""
    try:
        result = MixClient().get_workflow(workflow_name)
        workflow = result.get("data", {})

        rprint(f"[bold]Workflow: {workflow.get('name')}[/bold]")
        rprint(f"Description: {workflow.get('description')}")
        rprint(f"Created: {workflow.get('created_at')}")
        rprint(f"Updated: {workflow.get('updated_at')}")

        # Show runs
        runs = workflow.get('runs', [])
        if runs:
            rprint(f"\n[bold]Recent Runs ({len(runs)}):[/bold]")
            table = Table("Run #", "Status", "Started", "Triggered By")
            for run in runs[:10]:  # Show last 10 runs
                # Display user name, email, or ID as fallback
                triggered_by = run.get("triggered_by_name") or run.get("triggered_by_email") or f"User {run.get('triggered_by', 'Unknown')}"
                table.add_row(
                    str(run.get("run_number", "")),
                    run.get("status", ""),
                    run.get("started_at", "N/A"),
                    triggered_by,
                )
            rprint(table)
        else:
            rprint("\n[yellow]No runs yet.[/yellow]")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="update")
def update_workflow(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    workflow_file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to new workflow Python file"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New workflow name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New workflow description"),
    src_files: Optional[list[str]] = typer.Option(None, "--src", "-s", help="Additional source files to include (can be specified multiple times)"),
):
    """Update a workflow.

    You can update the workflow's metadata (name, description) and/or its files.
    If files are provided, they will overwrite existing files with the same name.
    """
    try:
        import os

        # Validate workflow file exists if provided
        if workflow_file and not os.path.exists(workflow_file):
            rprint(f"[red]Error:[/red] Workflow file not found: {workflow_file}")
            raise typer.Exit(1)

        # Validate source files exist if provided
        if src_files:
            for src_file in src_files:
                if not os.path.exists(src_file):
                    rprint(f"[red]Error:[/red] Source file not found: {src_file}")
                    raise typer.Exit(1)

        # Update workflow
        result = MixClient().update_workflow(
            workflow_name=workflow_name,
            name=name,
            description=description,
            workflow_file=workflow_file,
            src_files=src_files,
        )

        workflow_data = result.get("data", {})
        rprint(
            f"[green]✓[/green] Successfully updated workflow '{workflow_data.get('name')}'"
        )

        if workflow_file:
            rprint(f"  Uploaded new workflow file: {workflow_file}")
        if src_files:
            rprint(f"  Uploaded {len(src_files)} additional source file(s)")

    except FileNotFoundError as e:
        rprint(f"[red]Error:[/red] File not found: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="delete")
def delete_workflow(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a workflow."""
    try:
        if not yes:
            confirm = typer.confirm(
                f"Delete workflow '{workflow_name}'? This will permanently delete all workflow runs."
            )
            if not confirm:
                rprint("Deletion cancelled.")
                return

        MixClient().delete_workflow(workflow_name)
        rprint(f"[green]✓[/green] Successfully deleted workflow '{workflow_name}'")

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="run")
def run_workflow(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="JSON configuration or path to JSON file"),
):
    """Start a new workflow run."""
    try:
        json_config = {}
        if config:
            import json
            import os

            # Check if config is a file path
            if os.path.exists(config):
                try:
                    with open(config, 'r') as f:
                        json_config = json.load(f)
                except json.JSONDecodeError:
                    rprint(f"[red]Error:[/red] Invalid JSON in config file: {config}")
                    raise typer.Exit(1)
                except Exception as e:
                    rprint(f"[red]Error:[/red] Could not read config file: {str(e)}")
                    raise typer.Exit(1)
            else:
                # Try to parse as JSON string
                try:
                    json_config = json.loads(config)
                except json.JSONDecodeError:
                    rprint(f"[red]Error:[/red] Config must be a valid JSON string or an existing file path.")
                    raise typer.Exit(1)

        result = MixClient().start_workflow_run(workflow_name, json_config=json_config)
        run_data = result.get("data", {})
        rprint(
            f"[green]✓[/green] Started workflow run (Run #{run_data.get('run_number')}, Status: {run_data.get('status')})"
        )

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="cancel")
def cancel_run(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    run_number: int = typer.Argument(..., help="Run number"),
):
    """Cancel a running workflow."""
    try:
        result = MixClient().cancel_workflow_run(workflow_name, run_number)
        run_data = result.get("data", {})
        rprint(
            f"[green]✓[/green] Cancelled workflow run #{run_number} (Status: {run_data.get('status')})"
        )

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="runs")
def list_runs(workflow_name: str = typer.Argument(..., help="Workflow name")):
    """List all runs for a workflow."""
    try:
        response = MixClient().list_workflow_runs(workflow_name)
        runs = response.get("data", [])

        if not runs:
            rprint("[yellow]No runs found for this workflow.[/yellow]")
            return

        rprint(f"[bold]Workflow Runs (Total: {len(runs)}):[/bold]")
        table = Table("Run #", "Status", "Started", "Completed", "Triggered By")
        for run in runs:
            # Display user name, email, or ID as fallback
            triggered_by = run.get("triggered_by_name") or run.get("triggered_by_email") or f"User {run.get('triggered_by', 'Unknown')}"
            table.add_row(
                str(run.get("run_number", "")),
                run.get("status", ""),
                run.get("started_at", "N/A"),
                run.get("completed_at", "N/A"),
                triggered_by,
            )
        rprint(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
