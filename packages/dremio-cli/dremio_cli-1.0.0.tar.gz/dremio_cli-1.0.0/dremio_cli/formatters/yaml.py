"""YAML output formatter."""

from typing import Any

import yaml


def format_as_yaml(data: Any) -> str:
    """Format data as YAML.
    
    Args:
        data: Data to format
        
    Returns:
        YAML string
    """
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
