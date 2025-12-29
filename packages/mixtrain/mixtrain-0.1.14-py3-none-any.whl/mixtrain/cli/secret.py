import typer
from rich import print as rprint
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt, Confirm
from typing import Optional

from mixtrain.client import MixClient

console = Console()
app = typer.Typer(help="Manage workspace secrets.", invoke_without_command=True)

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

@app.command()
def list():
    """List all secrets in the current workspace."""
    try:
        client = MixClient()
        secrets = client.get_all_secrets()

        if not secrets:
            rprint("[yellow]No secrets found in this workspace.[/yellow]")
            rprint("\nUse [bold]mixtrain secret set <name> <value>[/bold] to create your first secret.")
            return


        # Create table
        table = Table()
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Created", style="dim")
        table.add_column("Created By", style="dim")

        for secret in secrets:
            created_date = secret.get('created_at', '')
            if created_date:
                # Format date nicely
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    created_date = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, AttributeError):
                    pass

            table.add_row(
                secret.get('name', ''),
                secret.get('description', '') or '[dim]No description[/dim]',
                created_date,
                secret.get('created_by', '')
            )

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error listing secrets:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def get(
    name: str = typer.Argument(..., help="Name of the secret to retrieve"),
    show_value: bool = typer.Option(False, "--show", "-s", help="Display the secret value (use with caution)")
):
    """Get a specific secret by name."""
    try:
        client = MixClient()
        secret_data = client._make_request("GET", f"/workspaces/{client.workspace_name}/secrets/{name}").json()

        rprint(f"[bold]Secret '[cyan]{name}[/cyan]':[/bold]\n")

        # Create info table
        table = Table.grid(padding=(0, 2))
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Name:", secret_data.get('name', ''))
        table.add_row("Description:", secret_data.get('description', '') or '[dim]No description[/dim]')

        # Format dates
        created_at = secret_data.get('created_at', '')
        updated_at = secret_data.get('updated_at', '')

        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except (ValueError, AttributeError):
                pass

        if updated_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                updated_at = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except (ValueError, AttributeError):
                pass

        table.add_row("Created:", created_at)
        table.add_row("Updated:", updated_at)
        table.add_row("Created by:", secret_data.get('created_by', ''))

        if show_value:
            value = secret_data.get('value', '')
            display_value = value
            table.add_row("Value:", f"[yellow]{display_value}[/yellow]")
        else:
            table.add_row("Value:", "[dim]Hidden (use --show to display)[/dim]")

        console.print(table)

        if not show_value:
            rprint("\n[dim]💡 Use --show to display the secret value[/dim]")

    except Exception as e:
        if "404" in str(e):
            rprint(f"[red]Secret '[bold]{name}[/bold]' not found[/red]")
        else:
            rprint(f"[red]Error retrieving secret:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def set(
    name: str = typer.Argument(..., help="Name of the secret"),
    value: Optional[str] = typer.Argument(None, help="Value of the secret (will prompt if not provided)"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description of the secret"),
    update: bool = typer.Option(False, "--update", "-u", help="Update existing secret if it exists")
):
    """Create or update a secret."""
    try:
        client = MixClient()
        workspace_name = client.workspace_name

        # Get value if not provided
        if value is None:
            rprint(f"Creating secret '[cyan]{name}[/cyan]' in workspace '[bold]{workspace_name}[/bold]'")
            value = Prompt.ask("\nEnter secret value", password=True)
            if not value.strip():
                rprint("[red]Error:[/red] Secret value cannot be empty")
                raise typer.Exit(1)

        # Get description if not provided
        if description is None:
            description = Prompt.ask("Enter description (optional)", default="")

        # Check if secret already exists
        existing_secret = None
        try:
            existing_secret = client._make_request("GET", f"/workspaces/{workspace_name}/secrets/{name}").json()
        except Exception:
            pass  # Secret doesn't exist, which is fine for creation

        if existing_secret and not update:
            rprint(f"[red]Error:[/red] Secret '[bold]{name}[/bold]' already exists.")
            rprint("Use [bold]--update[/bold] flag to update existing secret, or choose a different name.")
            raise typer.Exit(1)

        # Create or update secret
        data = {
            "name": name,
            "value": value,
            "description": description
        }

        if existing_secret:
            # Update existing secret
            update_data = {
                "value": value,
                "description": description
            }
            client._make_request("PUT", f"/workspaces/{workspace_name}/secrets/{name}", json=update_data)
            rprint(f"[green]✓[/green] Secret '[bold]{name}[/bold]' updated successfully!")
        else:
            # Create new secret
            client._make_request("POST", f"/workspaces/{workspace_name}/secrets/", json=data)
            rprint(f"[green]✓[/green] Secret '[bold]{name}[/bold]' created successfully!")

    except Exception as e:
        if "already exists" in str(e):
            rprint(f"[red]Error:[/red] Secret '[bold]{name}[/bold]' already exists.")
            rprint("Use [bold]--update[/bold] flag to update the existing secret.")
        else:
            rprint(f"[red]Error creating/updating secret:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def delete(
    name: str = typer.Argument(..., help="Name of the secret to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Delete a secret."""
    try:
        client = MixClient()
        workspace_name = client.workspace_name

        # Confirm deletion unless --force is used
        if not force:
            confirmed = Confirm.ask(f"Delete secret '[bold]{name}[/bold]' from workspace '[bold]{workspace_name}[/bold]'?", default=False)
            if not confirmed:
                rprint("Deletion cancelled.")
                return

        client._make_request("DELETE", f"/workspaces/{workspace_name}/secrets/{name}")
        rprint(f"[green]✓[/green] Secret '[bold]{name}[/bold]' deleted successfully!")

    except Exception as e:
        if "404" in str(e):
            rprint(f"[red]Error:[/red] Secret '[bold]{name}[/bold]' not found")
        else:
            rprint(f"[red]Error deleting secret:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def copy(
    source_name: str = typer.Argument(..., help="Name of the source secret"),
    target_name: str = typer.Argument(..., help="Name for the new secret"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description for the new secret")
):
    """Copy a secret to a new name."""
    try:
        client = MixClient()
        workspace_name = client.workspace_name

        # Get source secret
        source_secret = client._make_request("GET", f"/workspaces/{workspace_name}/secrets/{source_name}").json()

        # Use source description if no new description provided
        if description is None:
            description = source_secret.get('description', '')

        # Create new secret with source value
        data = {
            "name": target_name,
            "value": source_secret.get('value', ''),
            "description": description
        }

        client._make_request("POST", f"/workspaces/{workspace_name}/secrets/", json=data)
        rprint(f"[green]✓[/green] Secret '[bold]{source_name}[/bold]' copied to '[bold]{target_name}[/bold]' successfully!")

    except Exception as e:
        if "404" in str(e) and source_name in str(e):
            rprint(f"[red]Error:[/red] Source secret '[bold]{source_name}[/bold]' not found")
        elif "already exists" in str(e):
            rprint(f"[red]Error:[/red] Target secret '[bold]{target_name}[/bold]' already exists")
        else:
            rprint(f"[red]Error copying secret:[/red] {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
