"""Tests for tag and wiki commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestTagCommands:
    """Test tag commands."""
    
    def test_tag_set_help(self, runner):
        """Test tag set help."""
        result = runner.invoke(cli, ["tag", "set", "--help"])
        assert result.exit_code == 0
        assert "Set tags on a catalog object" in result.output
    
    def test_tag_get_help(self, runner):
        """Test tag get help."""
        result = runner.invoke(cli, ["tag", "get", "--help"])
        assert result.exit_code == 0
        assert "Get tags from a catalog object" in result.output
    
    def test_tag_delete_help(self, runner):
        """Test tag delete help."""
        result = runner.invoke(cli, ["tag", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete all tags" in result.output


class TestWikiCommands:
    """Test wiki commands."""
    
    def test_wiki_set_help(self, runner):
        """Test wiki set help."""
        result = runner.invoke(cli, ["wiki", "set", "--help"])
        assert result.exit_code == 0
        assert "Set wiki documentation" in result.output
    
    def test_wiki_get_help(self, runner):
        """Test wiki get help."""
        result = runner.invoke(cli, ["wiki", "get", "--help"])
        assert result.exit_code == 0
        assert "Get wiki documentation" in result.output
    
    def test_wiki_delete_help(self, runner):
        """Test wiki delete help."""
        result = runner.invoke(cli, ["wiki", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete wiki documentation" in result.output
