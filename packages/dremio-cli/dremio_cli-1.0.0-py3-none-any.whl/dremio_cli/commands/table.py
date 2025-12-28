"""Table operations commands."""

import json
import click
from rich.console import Console
from pathlib import Path

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def table() -> None:
    """Table operations."""
    pass


@table.command("promote")
@click.argument("dataset_id")
@click.pass_context
def promote_table(ctx, dataset_id: str) -> None:
    """Promote a dataset to a physical dataset (table).
    
    Examples:
        dremio table promote abc-123-def-456
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Promote to table
        with console.status(f"[bold green]Promoting dataset {dataset_id}..."):
            result = client.promote_dataset(dataset_id)
        
        console.print(f"[green]✓[/green] Dataset promoted successfully")
        console.print(f"  ID: {dataset_id}")
        
        if ctx.obj.verbose:
            output_format = ctx.obj.output_format
            if output_format == "json":
                console.print(format_as_json(result))
            elif output_format == "yaml":
                console.print(format_as_yaml(result))
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@table.command("format")
@click.argument("dataset_id")
@click.option("--type", "format_type", required=True, help="Format type (e.g., CSV, JSON, Parquet)")
@click.option("--from-file", "format_file", type=click.Path(exists=True), help="Load format config from JSON file")
@click.pass_context
def format_table(ctx, dataset_id: str, format_type: str, format_file: str) -> None:
    """Configure format for a physical dataset.
    
    Examples:
        dremio table format abc-123 --type CSV --from-file csv_format.json
        dremio table format abc-123 --type JSON
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Build format config
        if format_file:
            with open(format_file, 'r') as f:
                format_config = json.load(f)
        else:
            format_config = {
                "type": format_type
            }
        
        # Set format
        with console.status(f"[bold green]Setting format for {dataset_id}..."):
            result = client.set_dataset_format(dataset_id, format_config)
        
        console.print(f"[green]✓[/green] Format configured successfully")
        console.print(f"  Type: {format_type}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@table.command("update")
@click.argument("dataset_id")
@click.option("--from-file", "table_file", type=click.Path(exists=True), required=True, help="Updated table JSON file")
@click.pass_context
def update_table(ctx, dataset_id: str, table_file: str) -> None:
    """Update table metadata.
    
    Examples:
        dremio table update abc-123 --from-file updated_table.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Load table data
        with open(table_file, 'r') as f:
            table_data = json.load(f)
        
        # Update table
        with console.status(f"[bold green]Updating table {dataset_id}..."):
            result = client.update_dataset(dataset_id, table_data)
        
        console.print(f"[green]✓[/green] Table updated successfully")
        console.print(f"  ID: {dataset_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
