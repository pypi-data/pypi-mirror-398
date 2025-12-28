"""History management commands."""

import click
from rich.console import Console
from rich.table import Table

from dremio_cli.history import HistoryManager
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def history() -> None:
    """Query history management."""
    pass


@history.command("list")
@click.option("--limit", default=50, help="Maximum number of entries")
@click.pass_context
def list_history(ctx, limit: int) -> None:
    """List recent query history.
    
    Examples:
        dremio history list
        dremio history list --limit 10
    """
    try:
        manager = HistoryManager()
        entries = manager.get_history(limit=limit)
        
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(entries))
        elif output_format == "yaml":
            console.print(format_as_yaml(entries))
        else:
            if entries:
                table = Table(title=f"Query History (last {len(entries)})")
                table.add_column("ID", style="cyan")
                table.add_column("Command", style="green")
                table.add_column("Query", style="yellow", max_width=50)
                table.add_column("Profile", style="magenta")
                table.add_column("Time", style="blue")
                
                for entry in entries:
                    table.add_row(
                        str(entry["id"]),
                        entry["command"],
                        entry["query"][:47] + "..." if entry["query"] and len(entry["query"]) > 50 else (entry["query"] or ""),
                        entry["profile"] or "",
                        entry["timestamp"][:19]
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No history found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@history.command("run")
@click.argument("history_id", type=int)
@click.pass_context
def run_history(ctx, history_id: int) -> None:
    """Re-run a command from history.
    
    Examples:
        dremio history run 5
    """
    try:
        manager = HistoryManager()
        entry = manager.get_history_item(history_id)
        
        if not entry:
            console.print(f"[red]History entry {history_id} not found[/red]")
            raise click.Abort()
        
        console.print(f"[cyan]Re-running:[/cyan] {entry['command']}")
        if entry['query']:
            console.print(f"[yellow]Query:[/yellow] {entry['query']}")
        
        # Re-execute the command
        # Note: This is a simplified version - full implementation would parse and execute
        console.print("[yellow]Note: Re-execution not yet implemented - use the command shown above[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@history.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear all history?")
@click.pass_context
def clear_history(ctx) -> None:
    """Clear all query history.
    
    Examples:
        dremio history clear
    """
    try:
        manager = HistoryManager()
        manager.clear_history()
        console.print("[green]✓[/green] History cleared")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
