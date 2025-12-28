"""Environment variable configuration loader.

Supports loading profiles from environment variables using the pattern:
DREMIO_{PROFILE}_{KEY}={VALUE}

Example:
    DREMIO_CLOUD_TOKEN=xxx
    DREMIO_CLOUD_PROJECTID=yyy
    DREMIO_CLOUD_TYPE=cloud
    DREMIO_SOFTWARE_TOKEN=zzz
    DREMIO_SOFTWARE_BASE_URL=https://v26.dremio.org
    DREMIO_SOFTWARE_TYPE=software
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path


def load_dotenv(dotenv_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file.
    
    Args:
        dotenv_path: Path to .env file. If None, looks in current directory.
    """
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
    
    if not dotenv_path.exists():
        return
    
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


def get_profile_names_from_env() -> List[str]:
    """Get list of profile names defined in environment variables.
    
    Returns:
        List of profile names found in environment variables
    """
    profiles = set()
    prefix = "DREMIO_"
    
    for key in os.environ.keys():
        if key.startswith(prefix):
            parts = key.split("_")
            if len(parts) >= 3:  # DREMIO_PROFILENAME_KEY
                profile_name = parts[1].lower()
                profiles.add(profile_name)
    
    return sorted(list(profiles))


def get_profile_from_env(profile_name: str) -> Optional[Dict[str, Any]]:
    """Load a profile from environment variables.
    
    Args:
        profile_name: Name of the profile to load
        
    Returns:
        Profile dictionary or None if not found
    """
    profile_name_upper = profile_name.upper()
    prefix = f"DREMIO_{profile_name_upper}_"
    
    profile_data: Dict[str, Any] = {}
    auth_data: Dict[str, Any] = {}
    
    # Collect all environment variables for this profile
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Extract the key name after the profile prefix
            config_key = key[len(prefix):].lower()
            
            # Map environment variable names to profile structure
            if config_key == "type":
                profile_data["type"] = value
            elif config_key == "base_url":
                profile_data["base_url"] = value
            elif config_key == "projectid":
                profile_data["project_id"] = value
            elif config_key == "token":
                auth_data["token"] = value
            elif config_key == "username":
                auth_data["username"] = value
            elif config_key == "password":
                auth_data["password"] = value
            elif config_key == "auth_type":
                auth_data["type"] = value
            elif config_key == "testing_folder":
                # Store testing folder for test utilities
                profile_data["testing_folder"] = value
            else:
                # Store any other keys as-is
                profile_data[config_key] = value
    
    if not profile_data:
        return None
    
    # Set default base URLs if not specified
    if "base_url" not in profile_data:
        if profile_data.get("type") == "cloud":
            profile_data["base_url"] = "https://api.dremio.cloud/v0"
        elif profile_data.get("type") == "software":
            # No default for software, must be specified
            pass
    
    # Determine auth type if not specified
    if "type" not in auth_data:
        if "token" in auth_data:
            auth_data["type"] = "pat"
        elif "username" in auth_data and "password" in auth_data:
            auth_data["type"] = "username_password"
    
    if auth_data:
        profile_data["auth"] = auth_data
    
    return profile_data


def get_env_override(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable override.
    
    Supports both DREMIO_KEY and KEY formats.
    
    Args:
        key: Environment variable key (without DREMIO_ prefix)
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    # Try with DREMIO_ prefix first
    value = os.environ.get(f"DREMIO_{key.upper()}")
    if value is not None:
        return value
    
    # Try without prefix
    value = os.environ.get(key.upper())
    if value is not None:
        return value
    
    return default


def merge_env_profiles(yaml_profiles: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Merge environment variable profiles with YAML profiles.
    
    Environment variables take precedence over YAML.
    
    Args:
        yaml_profiles: Profiles loaded from YAML file
        
    Returns:
        Merged profiles dictionary
    """
    merged = yaml_profiles.copy()
    
    # Load all profiles from environment
    env_profile_names = get_profile_names_from_env()
    
    for profile_name in env_profile_names:
        env_profile = get_profile_from_env(profile_name)
        if env_profile:
            merged[profile_name] = env_profile
    
    return merged
