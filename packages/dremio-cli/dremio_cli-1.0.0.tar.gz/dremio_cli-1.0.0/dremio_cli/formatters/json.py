"""JSON output formatter."""

import json
from typing import Any


def format_as_json(data: Any, pretty: bool = True) -> str:
    """Format data as JSON.
    
    Args:
        data: Data to format
        pretty: Whether to pretty-print
        
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, sort_keys=False)
    return json.dumps(data)
