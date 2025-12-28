"""Tests for source commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestSourceCommands:
    """Test source commands."""
    
    def test_source_list_help(self, runner):
        """Test source list help."""
        result = runner.invoke(cli, ["source", "list", "--help"])
        assert result.exit_code == 0
        assert "List all sources" in result.output
    
    def test_source_get_help(self, runner):
        """Test source get help."""
        result = runner.invoke(cli, ["source", "get", "--help"])
        assert result.exit_code == 0
        assert "Get source by ID" in result.output
    
    def test_source_create_help(self, runner):
        """Test source create help."""
        result = runner.invoke(cli, ["source", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new source" in result.output
    
    def test_source_update_help(self, runner):
        """Test source update help."""
        result = runner.invoke(cli, ["source", "update", "--help"])
        assert result.exit_code == 0
        assert "Update an existing source" in result.output
    
    def test_source_refresh_help(self, runner):
        """Test source refresh help."""
        result = runner.invoke(cli, ["source", "refresh", "--help"])
        assert result.exit_code == 0
        assert "Refresh source metadata" in result.output
    
    def test_source_delete_help(self, runner):
        """Test source delete help."""
        result = runner.invoke(cli, ["source", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a source" in result.output
    
    def test_source_test_connection_help(self, runner):
        """Test source test-connection help."""
        result = runner.invoke(cli, ["source", "test-connection", "--help"])
        assert result.exit_code == 0
        assert "Test source connection" in result.output
