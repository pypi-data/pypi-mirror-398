"""Authentication handlers for Dremio API."""

from typing import Dict, Any, Optional
import requests

from dremio_cli.utils.exceptions import AuthenticationError


def authenticate_with_username_password(
    base_url: str,
    username: str,
    password: str,
) -> str:
    """Authenticate with username and password (Dremio Software only).
    
    Args:
        base_url: Base URL for Dremio
        username: Username
        password: Password
        
    Returns:
        Authentication token
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # Use v2 API for login
    login_url = base_url.replace("/api/v3", "/apiv2/login")
    
    try:
        response = requests.post(
            login_url,
            json={"userName": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if not response.ok:
            raise AuthenticationError(f"Authentication failed: {response.text}")
        
        data = response.json()
        token = data.get("token")
        
        if not token:
            raise AuthenticationError("No token in authentication response")
        
        # Return self-contained token
        return f"_dremio{token}"
        
    except requests.RequestException as e:
        raise AuthenticationError(f"Authentication request failed: {e}")


def refresh_oauth_token(
    base_url: str,
    refresh_token: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """Refresh OAuth token.
    
    Args:
        base_url: Base URL for Dremio
        refresh_token: Refresh token
        client_id: OAuth client ID
        client_secret: OAuth client secret
        
    Returns:
        Dictionary with new access_token and refresh_token
        
    Raises:
        AuthenticationError: If refresh fails
    """
    oauth_url = f"{base_url}/oauth/token"
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    
    if client_id:
        data["client_id"] = client_id
    if client_secret:
        data["client_secret"] = client_secret
    
    try:
        response = requests.post(
            oauth_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if not response.ok:
            raise AuthenticationError(f"Token refresh failed: {response.text}")
        
        return response.json()
        
    except requests.RequestException as e:
        raise AuthenticationError(f"Token refresh request failed: {e}")
