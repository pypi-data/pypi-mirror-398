"""Helper utility functions."""

from datetime import datetime
from typing import Any, Dict, Optional


def format_timestamp(timestamp: Optional[str]) -> str:
    """Format ISO timestamp to human-readable format.
    
    Args:
        timestamp: ISO 8601 timestamp string
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return timestamp


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate a string to maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string with ellipsis if needed
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.
    
    Args:
        data: Dictionary to query
        *keys: Nested keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at nested key or default
    """
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"
