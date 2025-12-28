"""Profile and configuration management."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console

from dremio_cli.env import load_dotenv, merge_env_profiles

console = Console()


class ProfileManager:
    """Manages Dremio CLI profiles."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize profile manager.
        
        Args:
            config_dir: Configuration directory path. Defaults to ~/.dremio
        """
        self.config_dir = config_dir or Path.home() / ".dremio"
        self.config_file = self.config_dir / "profiles.yaml"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and merge with environment variables.
        
        Environment variables take precedence over YAML configuration.
        """
        # Load .env file if it exists
        load_dotenv()
        
        # Load YAML config
        if not self.config_file.exists():
            yaml_config = {"default_profile": None, "profiles": {}}
        else:
            with open(self.config_file, "r") as f:
                yaml_config = yaml.safe_load(f) or {"default_profile": None, "profiles": {}}
        
        # Merge environment variable profiles
        yaml_profiles = yaml_config.get("profiles", {})
        merged_profiles = merge_env_profiles(yaml_profiles)
        
        yaml_config["profiles"] = merged_profiles
        
        # Set default profile from environment if specified
        env_default = os.environ.get("DREMIO_PROFILE")
        if env_default and env_default in merged_profiles:
            yaml_config["default_profile"] = env_default
        
        return yaml_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """List all profiles."""
        config = self._load_config()
        return config.get("profiles", {})

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific profile by name."""
        profiles = self.list_profiles()
        return profiles.get(name)

    def get_default_profile(self) -> Optional[str]:
        """Get the default profile name."""
        config = self._load_config()
        return config.get("default_profile")

    def create_profile(
        self,
        name: str,
        profile_type: str,
        base_url: str,
        auth_type: str,
        project_id: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """Create a new profile.
        
        Args:
            name: Profile name
            profile_type: 'cloud' or 'software'
            base_url: Base URL for Dremio API
            auth_type: Authentication type ('pat', 'oauth', 'username_password')
            project_id: Project ID (required for cloud)
            token: Authentication token
            username: Username (for username_password auth)
            password: Password (for username_password auth)
        """
        config = self._load_config()
        
        if name in config["profiles"]:
            raise ValueError(f"Profile '{name}' already exists")
        
        profile: Dict[str, Any] = {
            "type": profile_type,
            "base_url": base_url,
            "auth": {"type": auth_type},
        }
        
        if project_id:
            profile["project_id"] = project_id
        
        if token:
            profile["auth"]["token"] = token
        
        if username:
            profile["auth"]["username"] = username
        
        if password:
            profile["auth"]["password"] = password
        
        config["profiles"][name] = profile
        
        # Set as default if it's the first profile
        if not config["default_profile"]:
            config["default_profile"] = name
        
        self._save_config(config)

    def update_profile(self, name: str, updates: Dict[str, Any]) -> None:
        """Update an existing profile.
        
        Args:
            name: Profile name
            updates: Dictionary of updates to apply
        """
        config = self._load_config()
        
        if name not in config["profiles"]:
            raise ValueError(f"Profile '{name}' does not exist")
        
        profile = config["profiles"][name]
        
        # Update top-level fields
        for key in ["type", "base_url", "project_id"]:
            if key in updates:
                profile[key] = updates[key]
        
        # Update auth fields
        if "auth" in updates:
            if "auth" not in profile:
                profile["auth"] = {}
            profile["auth"].update(updates["auth"])
        
        self._save_config(config)

    def delete_profile(self, name: str) -> None:
        """Delete a profile.
        
        Args:
            name: Profile name
        """
        config = self._load_config()
        
        if name not in config["profiles"]:
            raise ValueError(f"Profile '{name}' does not exist")
        
        del config["profiles"][name]
        
        # Update default if we deleted it
        if config["default_profile"] == name:
            remaining = list(config["profiles"].keys())
            config["default_profile"] = remaining[0] if remaining else None
        
        self._save_config(config)

    def set_default_profile(self, name: str) -> None:
        """Set the default profile.
        
        Args:
            name: Profile name
        """
        config = self._load_config()
        
        if name not in config["profiles"]:
            raise ValueError(f"Profile '{name}' does not exist")
        
        config["default_profile"] = name
        self._save_config(config)
