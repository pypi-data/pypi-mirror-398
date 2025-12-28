"""Space management commands."""

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
def space() -> None:
    """Space management operations.
    
    Note: In Cloud, this creates top-level folders in the project catalog.
    In Software, this creates traditional spaces.
    """
    pass


@space.command("create")
@click.option("--name", required=True, help="Space name")
@click.option("--description", help="Space description")
@click.pass_context
def create_space(ctx, name: str, description: str) -> None:
    """Create a new space.
    
    Examples:
        dremio space create --name "Analytics"
        dremio space create --name "Sales" --description "Sales data and reports"
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
        
        # Create space (backend handles Cloud vs Software)
        space_data = {
            "name": name,
        }
        
        if description:
            space_data["description"] = description
        
        with console.status(f"[bold green]Creating space '{name}'..."):
            result = client.create_space(space_data)
        
        space_id = result.get("id")
        space_path = result.get("path", [])
        
        console.print(f"[green]✓[/green] Space created successfully")
        console.print(f"  ID: {space_id}")
        console.print(f"  Name: {name}")
        if space_path:
            console.print(f"  Path: {'.'.join(space_path)}")
        
        # Display full result if verbose
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


@space.command("list")
@click.pass_context
def list_spaces(ctx) -> None:
    """List all spaces.
    
    Examples:
        dremio space list
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
        
        # Get catalog
        with console.status(f"[bold green]Fetching spaces..."):
            data = client.get_catalog()
        
        items = data.get("data", [])
        
        # Filter for spaces
        spaces = [
            item for item in items
            if item.get("containerType") == "SPACE" or 
               (item.get("containerType") == "FOLDER" and len(item.get("path", [])) == 1)
        ]
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(spaces))
        elif output_format == "yaml":
            console.print(format_as_yaml(spaces))
        else:
            if spaces:
                format_as_table(spaces, title=f"Spaces ({profile_name})")
            else:
                console.print("[yellow]No spaces found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@space.command("get")
@click.argument("space_id")
@click.pass_context
def get_space(ctx, space_id: str) -> None:
    """Get space by ID.
    
    Examples:
        dremio space get abc-123-def-456
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
        
        # Get space
        with console.status(f"[bold green]Fetching space {space_id}..."):
            data = client.get_catalog_item(space_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Space: {space_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@space.command("delete")
@click.argument("space_id")
@click.option("--tag", help="Version tag for optimistic concurrency control")
@click.confirmation_option(prompt="Are you sure you want to delete this space?")
@click.pass_context
def delete_space(ctx, space_id: str, tag: str) -> None:
    """Delete a space.
    
    Examples:
        dremio space delete abc-123-def-456
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
        
        # Get tag if not provided
        if not tag:
            space = client.get_catalog_item(space_id)
            tag = space.get("tag")
        
        # Delete space
        with console.status(f"[bold yellow]Deleting space {space_id}..."):
            client.delete_space(space_id, tag)
        
        console.print(f"[green]✓[/green] Space deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
