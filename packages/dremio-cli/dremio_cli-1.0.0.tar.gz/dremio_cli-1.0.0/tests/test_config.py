"""Tests for profile management."""

import pytest
from pathlib import Path
import tempfile
import shutil

from dremio_cli.config import ProfileManager


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def profile_manager(temp_config_dir):
    """Create profile manager with temp directory."""
    return ProfileManager(config_dir=temp_config_dir)


def test_create_profile(profile_manager):
    """Test creating a profile."""
    profile_manager.create_profile(
        name="test",
        profile_type="cloud",
        base_url="https://api.dremio.cloud/v0",
        auth_type="pat",
        project_id="test-project",
        token="test-token",
    )
    
    profile = profile_manager.get_profile("test")
    assert profile is not None
    assert profile["type"] == "cloud"
    assert profile["base_url"] == "https://api.dremio.cloud/v0"
    assert profile["project_id"] == "test-project"
    assert profile["auth"]["type"] == "pat"
    assert profile["auth"]["token"] == "test-token"


def test_list_profiles(profile_manager):
    """Test listing profiles."""
    profile_manager.create_profile(
        name="test1",
        profile_type="cloud",
        base_url="https://api.dremio.cloud/v0",
        auth_type="pat",
        project_id="test-project",
        token="test-token",
    )
    
    profile_manager.create_profile(
        name="test2",
        profile_type="software",
        base_url="http://localhost:9047/api/v3",
        auth_type="pat",
        token="test-token",
    )
    
    profiles = profile_manager.list_profiles()
    assert len(profiles) == 2
    assert "test1" in profiles
    assert "test2" in profiles


def test_delete_profile(profile_manager):
    """Test deleting a profile."""
    profile_manager.create_profile(
        name="test",
        profile_type="cloud",
        base_url="https://api.dremio.cloud/v0",
        auth_type="pat",
        project_id="test-project",
        token="test-token",
    )
    
    profile_manager.delete_profile("test")
    
    profiles = profile_manager.list_profiles()
    assert "test" not in profiles


def test_set_default_profile(profile_manager):
    """Test setting default profile."""
    profile_manager.create_profile(
        name="test1",
        profile_type="cloud",
        base_url="https://api.dremio.cloud/v0",
        auth_type="pat",
        project_id="test-project",
        token="test-token",
    )
    
    profile_manager.create_profile(
        name="test2",
        profile_type="software",
        base_url="http://localhost:9047/api/v3",
        auth_type="pat",
        token="test-token",
    )
    
    # First profile should be default
    assert profile_manager.get_default_profile() == "test1"
    
    # Change default
    profile_manager.set_default_profile("test2")
    assert profile_manager.get_default_profile() == "test2"
