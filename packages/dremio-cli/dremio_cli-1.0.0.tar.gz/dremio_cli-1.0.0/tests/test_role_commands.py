"""Tests for role commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestRoleCommands:
    """Test role commands."""
    
    def test_role_list_help(self, runner):
        """Test role list help."""
        result = runner.invoke(cli, ["role", "list", "--help"])
        assert result.exit_code == 0
        assert "List all roles" in result.output
    
    def test_role_get_help(self, runner):
        """Test role get help."""
        result = runner.invoke(cli, ["role", "get", "--help"])
        assert result.exit_code == 0
        assert "Get role by ID" in result.output
    
    def test_role_create_help(self, runner):
        """Test role create help."""
        result = runner.invoke(cli, ["role", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new role" in result.output
    
    def test_role_update_help(self, runner):
        """Test role update help."""
        result = runner.invoke(cli, ["role", "update", "--help"])
        assert result.exit_code == 0
        assert "Update an existing role" in result.output
    
    def test_role_delete_help(self, runner):
        """Test role delete help."""
        result = runner.invoke(cli, ["role", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a role" in result.output
    
    def test_role_add_member_help(self, runner):
        """Test role add-member help."""
        result = runner.invoke(cli, ["role", "add-member", "--help"])
        assert result.exit_code == 0
        assert "Add a user to a role" in result.output
    
    def test_role_remove_member_help(self, runner):
        """Test role remove-member help."""
        result = runner.invoke(cli, ["role", "remove-member", "--help"])
        assert result.exit_code == 0
        assert "Remove a user from a role" in result.output
