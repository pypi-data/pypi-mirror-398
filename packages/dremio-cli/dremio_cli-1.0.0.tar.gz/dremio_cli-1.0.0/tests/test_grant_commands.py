"""Tests for grant commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestGrantCommands:
    """Test grant commands."""
    
    def test_grant_list_help(self, runner):
        """Test grant list help."""
        result = runner.invoke(cli, ["grant", "list", "--help"])
        assert result.exit_code == 0
        assert "List grants for a catalog object" in result.output
    
    def test_grant_add_help(self, runner):
        """Test grant add help."""
        result = runner.invoke(cli, ["grant", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a grant to a catalog object" in result.output
    
    def test_grant_remove_help(self, runner):
        """Test grant remove help."""
        result = runner.invoke(cli, ["grant", "remove", "--help"])
        assert result.exit_code == 0
        assert "Remove a grant from a catalog object" in result.output
    
    def test_grant_set_help(self, runner):
        """Test grant set help."""
        result = runner.invoke(cli, ["grant", "set", "--help"])
        assert result.exit_code == 0
        assert "Set all grants for a catalog object" in result.output
