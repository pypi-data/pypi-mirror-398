"""Input validators for CLI commands."""

import re
from typing import Any, List, Optional
from urllib.parse import urlparse

from dremio_cli.utils.exceptions import ValidationError


def validate_url(url: str) -> str:
    """Validate a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        The validated URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError(f"Invalid URL: {url}")
        return url
    except Exception as e:
        raise ValidationError(f"Invalid URL: {url} - {e}")


def validate_uuid(uuid_str: str) -> str:
    """Validate a UUID string.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        The validated UUID string
        
    Raises:
        ValidationError: If UUID is invalid
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    if not uuid_pattern.match(uuid_str):
        raise ValidationError(f"Invalid UUID: {uuid_str}")
    
    return uuid_str


def validate_profile_type(profile_type: str) -> str:
    """Validate profile type.
    
    Args:
        profile_type: Profile type to validate
        
    Returns:
        The validated profile type
        
    Raises:
        ValidationError: If profile type is invalid
    """
    valid_types = ["cloud", "software"]
    
    if profile_type not in valid_types:
        raise ValidationError(
            f"Invalid profile type: {profile_type}. Must be one of: {', '.join(valid_types)}"
        )
    
    return profile_type


def validate_auth_type(auth_type: str) -> str:
    """Validate authentication type.
    
    Args:
        auth_type: Authentication type to validate
        
    Returns:
        The validated authentication type
        
    Raises:
        ValidationError: If authentication type is invalid
    """
    valid_types = ["pat", "oauth", "username_password"]
    
    if auth_type not in valid_types:
        raise ValidationError(
            f"Invalid auth type: {auth_type}. Must be one of: {', '.join(valid_types)}"
        )
    
    return auth_type


def validate_output_format(output_format: str) -> str:
    """Validate output format.
    
    Args:
        output_format: Output format to validate
        
    Returns:
        The validated output format
        
    Raises:
        ValidationError: If output format is invalid
    """
    valid_formats = ["table", "json", "yaml", "csv"]
    
    if output_format not in valid_formats:
        raise ValidationError(
            f"Invalid output format: {output_format}. Must be one of: {', '.join(valid_formats)}"
        )
    
    return output_format


def validate_path(path: Any) -> List[str]:
    """Validate and parse a Dremio path.
    
    Args:
        path: Path as string or list
        
    Returns:
        Path as list of strings
        
    Raises:
        ValidationError: If path is invalid
    """
    if isinstance(path, str):
        # Try to parse as JSON array
        import json
        try:
            path = json.loads(path)
        except json.JSONDecodeError:
            # Treat as dot-separated path
            path = path.split(".")
    
    if not isinstance(path, list):
        raise ValidationError(f"Invalid path format: {path}")
    
    if not all(isinstance(p, str) for p in path):
        raise ValidationError("Path must contain only strings")
    
    return path
