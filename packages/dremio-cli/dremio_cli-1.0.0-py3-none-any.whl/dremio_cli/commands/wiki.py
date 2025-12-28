"""Wiki management commands."""

import click
from rich.console import Console
from pathlib import Path

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def wiki() -> None:
    """Wiki management operations."""
    pass


@wiki.command("set")
@click.argument("catalog_id")
@click.option("--text", help="Wiki text content")
@click.option("--file", "wiki_file", type=click.Path(exists=True), help="Load wiki from file")
@click.pass_context
def set_wiki(ctx, catalog_id: str, text: str, wiki_file: str) -> None:
    """Set wiki documentation on a catalog object.
    
    Examples:
        dremio wiki set abc-123 --text "# My Dataset\\n\\nThis is documentation"
        dremio wiki set abc-123 --file README.md
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get wiki content
        if wiki_file:
            with open(wiki_file, 'r') as f:
                wiki_content = f.read()
        elif text:
            wiki_content = text
        else:
            console.print("[red]Error: Either --text or --file is required[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Set wiki
        with console.status(f"[bold green]Setting wiki on {catalog_id}..."):
            client.set_wiki(catalog_id, wiki_content)
        
        console.print(f"[green]✓[/green] Wiki set successfully")
        console.print(f"  Length: {len(wiki_content)} characters")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@wiki.command("get")
@click.argument("catalog_id")
@click.option("--output-file", type=click.Path(), help="Save wiki to file")
@click.pass_context
def get_wiki(ctx, catalog_id: str, output_file: str) -> None:
    """Get wiki documentation from a catalog object.
    
    Examples:
        dremio wiki get abc-123
        dremio wiki get abc-123 --output-file README.md
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
        
        # Get wiki
        with console.status(f"[bold green]Fetching wiki for {catalog_id}..."):
            data = client.get_wiki(catalog_id)
        
        wiki_text = data.get("text", "")
        
        if output_file:
            # Save to file
            Path(output_file).write_text(wiki_text)
            console.print(f"[green]✓[/green] Wiki saved to {output_file}")
            console.print(f"  Length: {len(wiki_text)} characters")
        else:
            # Display wiki
            output_format = ctx.obj.output_format
            
            if output_format == "json":
                console.print(format_as_json(data))
            elif output_format == "yaml":
                console.print(format_as_yaml(data))
            else:
                if wiki_text:
                    console.print("\n[bold]Wiki Content:[/bold]\n")
                    console.print(wiki_text)
                else:
                    console.print("[yellow]No wiki content found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@wiki.command("delete")
@click.argument("catalog_id")
@click.confirmation_option(prompt="Are you sure you want to delete the wiki?")
@click.pass_context
def delete_wiki(ctx, catalog_id: str) -> None:
    """Delete wiki documentation from a catalog object.
    
    Examples:
        dremio wiki delete abc-123
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
        
        # Delete wiki
        with console.status(f"[bold yellow]Deleting wiki from {catalog_id}..."):
            client.delete_wiki(catalog_id)
        
        console.print(f"[green]✓[/green] Wiki deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
