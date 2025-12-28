"""Tests for table commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestTableCommands:
    """Test table commands."""
    
    def test_table_promote_help(self, runner):
        """Test table promote help."""
        result = runner.invoke(cli, ["table", "promote", "--help"])
        assert result.exit_code == 0
        assert "Promote a dataset" in result.output
    
    def test_table_format_help(self, runner):
        """Test table format help."""
        result = runner.invoke(cli, ["table", "format", "--help"])
        assert result.exit_code == 0
        assert "Configure format" in result.output
    
    def test_table_update_help(self, runner):
        """Test table update help."""
        result = runner.invoke(cli, ["table", "update", "--help"])
        assert result.exit_code == 0
        assert "Update table metadata" in result.output
