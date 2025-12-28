"""View management commands."""

import json
import click
from rich.console import Console
from pathlib import Path

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml
from dremio_cli.utils.validators import validate_path

console = Console()


@click.group()
def view() -> None:
    """View management operations."""
    pass


@view.command("create")
@click.option("--path", required=True, help="View path as JSON array or dot-separated (e.g., '[\"space\", \"view\"]' or 'space.view')")
@click.option("--sql", help="SQL query for the view")
@click.option("--from-file", type=click.Path(exists=True), help="Load view definition from JSON file")
@click.pass_context
def create_view(ctx, path: str, sql: str, from_file: str) -> None:
    """Create a new view.
    
    Examples:
        dremio view create --path '["MySpace", "MyView"]' --sql "SELECT * FROM table"
        dremio view create --path "MySpace.MyView" --sql "SELECT 1 as col"
        dremio view create --from-file view-definition.json
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
        
        # Load view definition
        if from_file:
            with open(from_file, 'r') as f:
                view_data = json.load(f)
        else:
            if not sql:
                console.print("[red]Error: Either --sql or --from-file is required[/red]")
                raise click.Abort()
            
            # Parse path
            view_path = validate_path(path)
            
            # Create view definition
            view_data = {
                "entityType": "dataset",
                "type": "VIRTUAL_DATASET",
                "path": view_path,
                "sql": sql,
            }
        
        # Create view
        with console.status(f"[bold green]Creating view..."):
            result = client.create_view(view_data)
        
        view_id = result.get("id")
        view_path = result.get("path", [])
        
        console.print(f"[green]✓[/green] View created successfully")
        console.print(f"  ID: {view_id}")
        console.print(f"  Path: {'.'.join(view_path)}")
        
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


@view.command("get")
@click.argument("view_id")
@click.option("--include", help="Include additional fields")
@click.pass_context
def get_view(ctx, view_id: str, include: str) -> None:
    """Get view by ID.
    
    Examples:
        dremio view get abc-123-def-456
        dremio view get abc-123-def-456 --include sql
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
        
        # Get view
        with console.status(f"[bold green]Fetching view {view_id}..."):
            data = client.get_catalog_item(view_id, include=include)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"View: {view_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@view.command("get-by-path")
@click.argument("path")
@click.option("--include", help="Include additional fields")
@click.pass_context
def get_view_by_path(ctx, path: str, include: str) -> None:
    """Get view by path.
    
    Examples:
        dremio view get-by-path "MySpace.MyView"
        dremio view get-by-path '["MySpace", "MyView"]'
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
        
        # Get view by path
        with console.status(f"[bold green]Fetching view {path}..."):
            data = client.get_catalog_item_by_path(path, include=include)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"View: {path}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@view.command("update")
@click.argument("view_id")
@click.option("--sql", help="New SQL query for the view")
@click.option("--from-file", type=click.Path(exists=True), help="Load view definition from JSON file")
@click.pass_context
def update_view(ctx, view_id: str, sql: str, from_file: str) -> None:
    """Update an existing view.
    
    Examples:
        dremio view update abc-123 --sql "SELECT * FROM table WHERE id > 100"
        dremio view update abc-123 --from-file updated-view.json
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
        
        # Get current view to get tag
        current_view = client.get_catalog_item(view_id)
        
        # Load update data
        if from_file:
            with open(from_file, 'r') as f:
                update_data = json.load(f)
        else:
            if not sql:
                console.print("[red]Error: Either --sql or --from-file is required[/red]")
                raise click.Abort()
            
            # Create update with new SQL
            update_data = {
                "entityType": "dataset",
                "type": "VIRTUAL_DATASET",
                "id": view_id,
                "path": current_view.get("path"),
                "tag": current_view.get("tag"),
                "sql": sql,
            }
        
        # Ensure tag is present for optimistic concurrency
        if "tag" not in update_data:
            update_data["tag"] = current_view.get("tag")
        
        # Update view
        with console.status(f"[bold green]Updating view {view_id}..."):
            result = client.update_view(view_id, update_data)
        
        console.print(f"[green]✓[/green] View updated successfully")
        console.print(f"  ID: {result.get('id')}")
        console.print(f"  Path: {'.'.join(result.get('path', []))}")
        
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


@view.command("delete")
@click.argument("view_id")
@click.option("--tag", help="Version tag for optimistic concurrency control")
@click.confirmation_option(prompt="Are you sure you want to delete this view?")
@click.pass_context
def delete_view(ctx, view_id: str, tag: str) -> None:
    """Delete a view.
    
    Examples:
        dremio view delete abc-123-def-456
        dremio view delete abc-123-def-456 --tag "version-tag"
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
            view = client.get_catalog_item(view_id)
            tag = view.get("tag")
        
        # Delete view
        with console.status(f"[bold yellow]Deleting view {view_id}..."):
            client.delete_view(view_id, tag)
        
        console.print(f"[green]✓[/green] View deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@view.command("list")
@click.option("--space", help="Filter views by space name")
@click.pass_context
def list_views(ctx, space: str) -> None:
    """List all views.
    
    Examples:
        dremio view list
        dremio view list --space MySpace
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
        with console.status(f"[bold green]Fetching views..."):
            data = client.get_catalog()
        
        items = data.get("data", [])
        
        # Filter for views
        views = [
            item for item in items
            if item.get("type") == "VIRTUAL_DATASET" or item.get("datasetType") == "VIRTUAL_DATASET"
        ]
        
        # Filter by space if specified
        if space:
            views = [
                view for view in views
                if view.get("path", [])[0] == space
            ]
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(views))
        elif output_format == "yaml":
            console.print(format_as_yaml(views))
        else:
            if views:
                title = f"Views in {space}" if space else "All Views"
                format_as_table(views, title=title)
            else:
                console.print("[yellow]No views found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
