"""Tests for view management commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestViewCommands:
    """Test view management commands."""
    
    def test_view_create_help(self, runner):
        """Test view create help."""
        result = runner.invoke(cli, ["view", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new view" in result.output
    
    def test_view_get_help(self, runner):
        """Test view get help."""
        result = runner.invoke(cli, ["view", "get", "--help"])
        assert result.exit_code == 0
        assert "Get view by ID" in result.output
    
    def test_view_get_by_path_help(self, runner):
        """Test view get-by-path help."""
        result = runner.invoke(cli, ["view", "get-by-path", "--help"])
        assert result.exit_code == 0
        assert "Get view by path" in result.output
    
    def test_view_update_help(self, runner):
        """Test view update help."""
        result = runner.invoke(cli, ["view", "update", "--help"])
        assert result.exit_code == 0
        assert "Update an existing view" in result.output
    
    def test_view_delete_help(self, runner):
        """Test view delete help."""
        result = runner.invoke(cli, ["view", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a view" in result.output
    
    def test_view_list_help(self, runner):
        """Test view list help."""
        result = runner.invoke(cli, ["view", "list", "--help"])
        assert result.exit_code == 0
        assert "List all views" in result.output
    
    def test_view_create_requires_sql_or_file(self, runner):
        """Test view create requires SQL or file."""
        result = runner.invoke(cli, ["view", "create", "--path", "test.view"])
        assert result.exit_code != 0
