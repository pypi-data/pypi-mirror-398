"""Favorite query management commands."""

import click
from rich.console import Console
from rich.table import Table

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.history import HistoryManager
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def favorite() -> None:
    """Favorite query management."""
    pass


@favorite.command("add")
@click.argument("name")
@click.option("--sql", required=True, help="SQL query")
@click.option("--description", help="Optional description")
@click.pass_context
def add_favorite(ctx, name: str, sql: str, description: str) -> None:
    """Add a favorite query.
    
    Examples:
        dremio favorite add daily_report --sql "SELECT * FROM sales WHERE date = CURRENT_DATE"
        dremio favorite add summary --sql "SELECT COUNT(*) FROM customers" --description "Customer count"
    """
    try:
        manager = HistoryManager()
        manager.add_favorite(name, sql, description)
        
        console.print(f"[green]✓[/green] Favorite '{name}' saved")
        console.print(f"  SQL: {sql[:100]}{'...' if len(sql) > 100 else ''}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@favorite.command("list")
@click.pass_context
def list_favorites(ctx) -> None:
    """List all favorite queries.
    
    Examples:
        dremio favorite list
    """
    try:
        manager = HistoryManager()
        favorites = manager.get_favorites()
        
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(favorites))
        elif output_format == "yaml":
            console.print(format_as_yaml(favorites))
        else:
            if favorites:
                table = Table(title="Favorite Queries")
                table.add_column("Name", style="cyan")
                table.add_column("Query", style="yellow", max_width=60)
                table.add_column("Description", style="green", max_width=30)
                
                for fav in favorites:
                    query = fav["query"]
                    table.add_row(
                        fav["name"],
                        query[:57] + "..." if len(query) > 60 else query,
                        fav["description"] or ""
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No favorites found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@favorite.command("run")
@click.argument("name")
@click.pass_context
def run_favorite(ctx, name: str) -> None:
    """Execute a favorite query.
    
    Examples:
        dremio favorite run daily_report
    """
    try:
        manager = HistoryManager()
        favorite = manager.get_favorite(name)
        
        if not favorite:
            console.print(f"[red]Favorite '{name}' not found[/red]")
            raise click.Abort()
        
        # Get profile
        profile_manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = profile_manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        console.print(f"[cyan]Running favorite:[/cyan] {name}")
        console.print(f"[yellow]SQL:[/yellow] {favorite['query']}")
        
        # Execute query
        with console.status(f"[bold green]Executing query..."):
            result = client.execute_sql(favorite['query'])
        
        job_id = result.get("id")
        console.print(f"[green]✓[/green] Query executed")
        console.print(f"  Job ID: {job_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@favorite.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this favorite?")
@click.pass_context
def delete_favorite(ctx, name: str) -> None:
    """Delete a favorite query.
    
    Examples:
        dremio favorite delete daily_report
    """
    try:
        manager = HistoryManager()
        manager.delete_favorite(name)
        console.print(f"[green]✓[/green] Favorite '{name}' deleted")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
