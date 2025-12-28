"""Client factory for creating appropriate Dremio clients."""

from typing import Dict, Any, Union

from dremio_cli.client.cloud import CloudClient
from dremio_cli.client.software import SoftwareClient
from dremio_cli.client.auth import authenticate_with_username_password
from dremio_cli.utils.exceptions import ConfigurationError, AuthenticationError


def create_client(profile: Dict[str, Any]) -> Union[CloudClient, SoftwareClient]:
    """Create appropriate Dremio client from profile.
    
    Args:
        profile: Profile configuration dictionary
        
    Returns:
        CloudClient or SoftwareClient instance
        
    Raises:
        ConfigurationError: If profile is invalid
        AuthenticationError: If authentication fails
    """
    profile_type = profile.get("type")
    
    if not profile_type:
        raise ConfigurationError("Profile missing 'type' field")
    
    if profile_type not in ["cloud", "software"]:
        raise ConfigurationError(f"Invalid profile type: {profile_type}")
    
    base_url = profile.get("base_url")
    if not base_url:
        raise ConfigurationError("Profile missing 'base_url' field")
    
    auth = profile.get("auth", {})
    auth_type = auth.get("type")
    
    if not auth_type:
        raise ConfigurationError("Profile missing 'auth.type' field")
    
    # Get or generate token
    token = _get_token(profile, auth, base_url)
    
    # Create appropriate client
    if profile_type == "cloud":
        project_id = profile.get("project_id")
        if not project_id:
            raise ConfigurationError("Cloud profile missing 'project_id' field")
        
        return CloudClient(
            base_url=base_url,
            project_id=project_id,
            token=token,
        )
    else:  # software
        return SoftwareClient(
            base_url=base_url,
            token=token,
        )


def _get_token(profile: Dict[str, Any], auth: Dict[str, Any], base_url: str) -> str:
    """Get authentication token from profile or generate it.
    
    Args:
        profile: Profile configuration
        auth: Auth configuration
        base_url: Base URL for API
        
    Returns:
        Authentication token
        
    Raises:
        AuthenticationError: If authentication fails
        ConfigurationError: If auth configuration is invalid
    """
    auth_type = auth.get("type")
    
    if auth_type == "pat":
        token = auth.get("token")
        if not token:
            raise ConfigurationError("PAT auth requires 'token' field")
        return token
    
    elif auth_type == "oauth":
        token = auth.get("token")
        if not token:
            raise ConfigurationError("OAuth auth requires 'token' field")
        # TODO: Check if token is expired and refresh if needed
        return token
    
    elif auth_type == "username_password":
        # Check if we have a cached token
        cached_token = auth.get("token")
        if cached_token:
            # TODO: Check if token is expired
            return cached_token
        
        # Generate new token
        username = auth.get("username")
        password = auth.get("password")
        
        if not username or not password:
            raise ConfigurationError(
                "Username/password auth requires 'username' and 'password' fields"
            )
        
        # Only supported for Software
        if profile.get("type") != "software":
            raise ConfigurationError(
                "Username/password auth only supported for Dremio Software"
            )
        
        token = authenticate_with_username_password(base_url, username, password)
        
        # TODO: Cache token in profile for future use
        
        return token
    
    else:
        raise ConfigurationError(f"Unsupported auth type: {auth_type}")
