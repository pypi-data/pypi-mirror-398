"""Catalog commands implementation."""

import click
from rich.console import Console

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def catalog() -> None:
    """Catalog operations."""
    pass


@catalog.command("list")
@click.option("--include", help="Include additional fields (permissions, datasetCount)")
@click.pass_context
def list_catalog(ctx, include: str) -> None:
    """List catalog contents."""
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
        
        # Make API call
        if hasattr(client, 'get_catalog'):
            data = client.get_catalog(include=include)
        else:
            console.print("[red]Client does not support catalog operations[/red]")
            raise click.Abort()
        
        # Format output
        output_format = ctx.obj.output_format
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            # Display as table
            items = data.get("data", [])
            if items:
                format_as_table(items, title=f"Catalog ({profile_name})")
            else:
                console.print("[yellow]No catalog items found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@catalog.command("get")
@click.argument("item_id")
@click.option("--include", help="Include additional fields")
@click.pass_context
def get_catalog_item(ctx, item_id: str, include: str) -> None:
    """Get catalog item by ID."""
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
        
        # Make API call
        data = client.get_catalog_item(item_id, include=include)
        
        # Format output
        output_format = ctx.obj.output_format
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Catalog Item: {item_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@catalog.command("get-by-path")
@click.argument("path")
@click.option("--include", help="Include additional fields")
@click.pass_context
def get_catalog_item_by_path(ctx, path: str, include: str) -> None:
    """Get catalog item by path."""
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
        
        # Make API call
        data = client.get_catalog_item_by_path(path, include=include)
        
        # Format output
        output_format = ctx.obj.output_format
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Catalog Item: {path}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
