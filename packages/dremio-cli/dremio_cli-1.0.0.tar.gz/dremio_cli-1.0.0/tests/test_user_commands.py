"""Tests for user commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestUserCommands:
    """Test user commands."""
    
    def test_user_list_help(self, runner):
        """Test user list help."""
        result = runner.invoke(cli, ["user", "list", "--help"])
        assert result.exit_code == 0
        assert "List all users" in result.output
    
    def test_user_get_help(self, runner):
        """Test user get help."""
        result = runner.invoke(cli, ["user", "get", "--help"])
        assert result.exit_code == 0
        assert "Get user by ID" in result.output
    
    def test_user_create_help(self, runner):
        """Test user create help."""
        result = runner.invoke(cli, ["user", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new user" in result.output
    
    def test_user_update_help(self, runner):
        """Test user update help."""
        result = runner.invoke(cli, ["user", "update", "--help"])
        assert result.exit_code == 0
        assert "Update an existing user" in result.output
    
    def test_user_delete_help(self, runner):
        """Test user delete help."""
        result = runner.invoke(cli, ["user", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a user" in result.output
