"""Tests for space and folder management commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestSpaceCommands:
    """Test space management commands."""
    
    def test_space_create_help(self, runner):
        """Test space create help."""
        result = runner.invoke(cli, ["space", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new space" in result.output
    
    def test_space_list_help(self, runner):
        """Test space list help."""
        result = runner.invoke(cli, ["space", "list", "--help"])
        assert result.exit_code == 0
        assert "List all spaces" in result.output
    
    def test_space_get_help(self, runner):
        """Test space get help."""
        result = runner.invoke(cli, ["space", "get", "--help"])
        assert result.exit_code == 0
        assert "Get space by ID" in result.output
    
    def test_space_delete_help(self, runner):
        """Test space delete help."""
        result = runner.invoke(cli, ["space", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a space" in result.output


class TestFolderCommands:
    """Test folder management commands."""
    
    def test_folder_create_help(self, runner):
        """Test folder create help."""
        result = runner.invoke(cli, ["folder", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new folder" in result.output
    
    def test_folder_list_help(self, runner):
        """Test folder list help."""
        result = runner.invoke(cli, ["folder", "list", "--help"])
        assert result.exit_code == 0
        assert "List folders" in result.output
    
    def test_folder_get_help(self, runner):
        """Test folder get help."""
        result = runner.invoke(cli, ["folder", "get", "--help"])
        assert result.exit_code == 0
        assert "Get folder by ID" in result.output
    
    def test_folder_get_by_path_help(self, runner):
        """Test folder get-by-path help."""
        result = runner.invoke(cli, ["folder", "get-by-path", "--help"])
        assert result.exit_code == 0
        assert "Get folder by path" in result.output
    
    def test_folder_delete_help(self, runner):
        """Test folder delete help."""
        result = runner.invoke(cli, ["folder", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a folder" in result.output
