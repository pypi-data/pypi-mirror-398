"""Mixtrain Dataset CLI Commands"""

import os
from logging import getLogger
from typing import Optional

import rich
import typer
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Input

from mixtrain import MixClient

logger = getLogger(__name__)

app = typer.Typer(help="Manage datasets.", invoke_without_command=True)


class DatasetBrowser(App):
    """A textual app for browsing dataset contents."""

    def __init__(self, data, schema, dataset_name):
        super().__init__()
        self.data = data
        self.schema = schema
        self.dataset_name = dataset_name

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Input(placeholder="Search... (Ctrl+F to focus)", id="search")
        yield DataTable()
        yield Footer()

    CSS = """
    #search {
        height: 3;
        margin: 1;
    }
    """

    def on_mount(self) -> None:
        """Set up the data table when the app starts."""
        self.table = self.query_one(DataTable)
        self.search_input = self.query_one("#search", Input)

        # Build normalized list of column names and add columns to table
        self.column_names: list[str] = []
        for col in self.schema:
            column_name = (
                col[0] if isinstance(col, (list, tuple)) else col
            )  # support [name, type] style or simple string names
            self.column_names.append(column_name)
            # Use full column name as key to avoid DuplicateKey errors when first characters repeat
            self.table.add_column(column_name, key=column_name)

        # Helper to convert a raw row (list / tuple / dict) into a list of cell strings
        def normalize_row(raw_row):
            if isinstance(raw_row, dict):
                # Preserve the ordering of self.column_names
                return [str(raw_row.get(col, "")) for col in self.column_names]
            else:
                # Assume it's already an ordered sequence of cell values
                return [str(cell) for cell in raw_row]

        # Convert and add rows
        self.data = [normalize_row(r) for r in self.data]
        for row in self.data:
            self.table.add_row(*row)

        # Set title and focus on table by default
        self.title = f"Dataset Browser {self.dataset_name} - {len(self.data)} rows"
        self.table.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        search_term = event.value.lower()

        # Clear current rows (but keep columns)
        self.table.clear(columns=False)

        # Filter and add matching rows
        for row in self.data:
            # Check if any cell contains the search term
            if any(search_term in str(cell).lower() for cell in row):
                self.table.add_row(*row)

    def on_key(self, event):
        """Handle key events."""
        if event.key == "q":
            self.exit()
        elif event.key == "ctrl+f":
            # Focus search input
            self.search_input.focus()
        elif event.key == "escape":
            # Clear search and return focus to table
            self.search_input.value = ""
            self.on_input_changed(Input.Changed(self.search_input, "", ""))
            self.table.focus()


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def validate_file(file_path: str):
    """
    Create a temporary file from an uploaded file and return the path.
    """
    logger.info(f"Creating temporary file from upload: {file_path}")
    # Validate file exists and is a supported format
    if not (
        file_path.endswith(".parquet")
        or file_path.endswith(".csv")
        or file_path.endswith(".tsv")
    ):
        typer.echo("Error: Only parquet, CSV, or TSV files are supported", err=True)
        raise typer.Exit(1)

    # Create dataset with file upload
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")

    if not (
        file_path.endswith(".parquet")
        or file_path.endswith(".csv")
        or file_path.endswith(".tsv")
    ):
        raise ValueError("Only parquet, CSV, or TSV files are supported")

    return file_path


@app.command()
def create(
    dataset_name: str,
    file_path: str = typer.Argument(..., help="File path to upload (CSV or Parquet)"),
    description: Optional[str] = typer.Option(None, help="Description for the dataset"),
):
    """
    Create a dataset table from a file.
    """
    try:
        validate_file(file_path)
        MixClient().create_dataset_from_file(dataset_name, file_path, description)
        typer.echo(f"Dataset '{dataset_name}' created successfully from {file_path}!")
        typer.echo(f"Browse with: mixtrain dataset browse {dataset_name}")

    except FileNotFoundError:
        typer.echo(f"Error: File {file_path} not found", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_datasets():
    """
    List datasets in the current workspace.
    """
    try:
        data = MixClient().list_datasets()
        if data and "tables" in data:
            table = rich.table.Table("dataset_name", "namespace", "description")
            for table_info in data["tables"]:
                table.add_row(
                    table_info["name"],
                    table_info["namespace"],
                    table_info["description"],
                )
            rich.print(table)
        else:
            typer.echo("No datasets found or no dataset providers configured.")
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command(name="delete")
def delete(dataset_name: str):
    """
    Delete a dataset.
    """
    try:
        MixClient().delete_dataset(dataset_name)
        typer.echo(f"Table {dataset_name} deleted successfully")
    except Exception as e:
        typer.echo(f"{str(e)}", err=True)
        raise typer.Exit(1)


@app.command(name="query")
def query(
    dataset_name: str,
    sql: str = typer.Argument(
        "",
        help="SQL query to execute. Defaults to SELECT * FROM <dataset_name> LIMIT 100",
    ),
):
    """
    Execute a SQL query on a dataset and display the results in TUI.
    """
    if not sql:
        sql = f"SELECT * FROM {dataset_name} LIMIT 100"

    try:
        arrow_table = (
            MixClient()
            .get_dataset(dataset_name)
            .scan()
            .to_duckdb(dataset_name)
            .execute(sql)
            .fetch_arrow_table()
        )
        browser_app = DatasetBrowser(
            arrow_table.to_pylist(), arrow_table.schema.names, dataset_name
        )
        browser_app.run()

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command(name="metadata")
def metadata(dataset_name: str):
    """
    Get detailed metadata for a dataset.
    """
    try:
        data = MixClient().get_dataset_metadata(dataset_name)

        if data:
            typer.echo(f"Format Version: {data.format_version}")
            typer.echo(f"Dataset UUID: {data.table_uuid}")
            typer.echo(f"Location: {data.location}")

            # Schema info
            schema = data.schema()
            typer.echo(f"schema: {schema}")
        else:
            typer.echo("No metadata returned")

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)
