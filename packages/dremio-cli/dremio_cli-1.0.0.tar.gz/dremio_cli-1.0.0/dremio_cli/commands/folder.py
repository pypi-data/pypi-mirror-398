"""Folder management commands."""

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
def folder() -> None:
    """Folder management operations."""
    pass


@folder.command("create")
@click.option("--path", required=True, help="Folder path as JSON array or slash-separated")
@click.option("--description", help="Folder description")
@click.pass_context
def create_folder(ctx, path: str, description: str) -> None:
    """Create a new folder.
    
    Examples:
        dremio folder create --path "Analytics/Reports"
        dremio folder create --path '["Analytics", "Reports", "2024"]'
        dremio folder create --path "namespace/data" --description "Data folder"
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
        
        # Parse path
        folder_path = validate_path(path)
        
        # Create folder data
        folder_data = {
            "path": folder_path,
        }
        
        if description:
            folder_data["description"] = description
        
        with console.status(f"[bold green]Creating folder '{'/'.join(folder_path)}'..."):
            result = client.create_folder(folder_data)
        
        folder_id = result.get("id")
        result_path = result.get("path", [])
        
        console.print(f"[green]✓[/green] Folder created successfully")
        console.print(f"  ID: {folder_id}")
        console.print(f"  Path: {'.'.join(result_path)}")
        
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


@folder.command("list")
@click.option("--parent", help="Parent folder/space ID or path")
@click.pass_context
def list_folders(ctx, parent: str) -> None:
    """List folders.
    
    Examples:
        dremio folder list
        dremio folder list --parent "Analytics"
        dremio folder list --parent abc-123-def-456
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
        with console.status(f"[bold green]Fetching folders..."):
            data = client.get_catalog()
        
        items = data.get("data", [])
        
        # Filter for folders
        folders = [
            item for item in items
            if item.get("containerType") == "FOLDER"
        ]
        
        # Filter by parent if specified
        if parent:
            # Try to resolve parent to a path
            try:
                parent_item = client.get_catalog_item(parent)
                parent_path = parent_item.get("path", [])
            except:
                # Assume it's a path
                parent_path = validate_path(parent)
            
            # Filter folders that are children of parent
            folders = [
                folder for folder in folders
                if folder.get("path", [])[:len(parent_path)] == parent_path and
                   len(folder.get("path", [])) == len(parent_path) + 1
            ]
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(folders))
        elif output_format == "yaml":
            console.print(format_as_yaml(folders))
        else:
            if folders:
                title = f"Folders in {parent}" if parent else "All Folders"
                format_as_table(folders, title=title)
            else:
                console.print("[yellow]No folders found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@folder.command("get")
@click.argument("folder_id")
@click.pass_context
def get_folder(ctx, folder_id: str) -> None:
    """Get folder by ID.
    
    Examples:
        dremio folder get abc-123-def-456
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
        
        # Get folder
        with console.status(f"[bold green]Fetching folder {folder_id}..."):
            data = client.get_catalog_item(folder_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Folder: {folder_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@folder.command("get-by-path")
@click.argument("path")
@click.pass_context
def get_folder_by_path(ctx, path: str) -> None:
    """Get folder by path.
    
    Examples:
        dremio folder get-by-path "Analytics/Reports"
        dremio folder get-by-path '["Analytics", "Reports", "2024"]'
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
        
        # Get folder by path
        with console.status(f"[bold green]Fetching folder {path}..."):
            data = client.get_catalog_item_by_path(path)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Folder: {path}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@folder.command("delete")
@click.argument("folder_id")
@click.option("--tag", help="Version tag for optimistic concurrency control")
@click.confirmation_option(prompt="Are you sure you want to delete this folder?")
@click.pass_context
def delete_folder(ctx, folder_id: str, tag: str) -> None:
    """Delete a folder.
    
    Examples:
        dremio folder delete abc-123-def-456
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
            folder = client.get_catalog_item(folder_id)
            tag = folder.get("tag")
        
        # Delete folder
        with console.status(f"[bold yellow]Deleting folder {folder_id}..."):
            client.delete_folder(folder_id, tag)
        
        console.print(f"[green]✓[/green] Folder deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
