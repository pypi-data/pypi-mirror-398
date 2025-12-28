"""Table output formatter."""

from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table


def format_as_table(data: Any, title: str = None) -> None:
    """Format data as a table.
    
    Args:
        data: Data to format (dict, list of dicts, or simple value)
        title: Optional table title
    """
    console = Console()
    
    if isinstance(data, list) and data and isinstance(data[0], dict):
        # List of dictionaries - create table
        table = Table(title=title)
        
        # Add columns from first item
        for key in data[0].keys():
            table.add_column(str(key).replace("_", " ").title(), style="cyan")
        
        # Add rows
        for item in data:
            table.add_row(*[str(v) for v in item.values()])
        
        console.print(table)
        
    elif isinstance(data, dict):
        # Single dictionary - create key-value table
        table = Table(title=title, show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key).replace("_", " ").title(), str(value))
        
        console.print(table)
        
    else:
        # Simple value
        console.print(data)
