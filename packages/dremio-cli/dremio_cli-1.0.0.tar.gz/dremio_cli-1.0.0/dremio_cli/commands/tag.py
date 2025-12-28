"""Tag management commands."""

import click
from rich.console import Console

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def tag() -> None:
    """Tag management operations."""
    pass


@tag.command("set")
@click.argument("catalog_id")
@click.option("--tags", required=True, help="Comma-separated list of tags")
@click.pass_context
def set_tags(ctx, catalog_id: str, tags: str) -> None:
    """Set tags on a catalog object.
    
    Examples:
        dremio tag set abc-123 --tags analytics,production
        dremio tag set abc-123 --tags "sensitive data,pii,gdpr"
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
        
        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")]
        
        # Set tags
        with console.status(f"[bold green]Setting tags on {catalog_id}..."):
            client.set_tags(catalog_id, tag_list)
        
        console.print(f"[green]✓[/green] Tags set successfully")
        console.print(f"  Tags: {', '.join(tag_list)}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@tag.command("get")
@click.argument("catalog_id")
@click.pass_context
def get_tags(ctx, catalog_id: str) -> None:
    """Get tags from a catalog object.
    
    Examples:
        dremio tag get abc-123
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
        
        # Get tags
        with console.status(f"[bold green]Fetching tags for {catalog_id}..."):
            data = client.get_tags(catalog_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            tags = data.get("tags", [])
            if tags:
                console.print(f"[bold]Tags:[/bold] {', '.join(tags)}")
            else:
                console.print("[yellow]No tags found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@tag.command("delete")
@click.argument("catalog_id")
@click.confirmation_option(prompt="Are you sure you want to delete all tags?")
@click.pass_context
def delete_tags(ctx, catalog_id: str) -> None:
    """Delete all tags from a catalog object.
    
    Examples:
        dremio tag delete abc-123
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
        
        # Delete tags
        with console.status(f"[bold yellow]Deleting tags from {catalog_id}..."):
            client.delete_tags(catalog_id)
        
        console.print(f"[green]✓[/green] Tags deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
