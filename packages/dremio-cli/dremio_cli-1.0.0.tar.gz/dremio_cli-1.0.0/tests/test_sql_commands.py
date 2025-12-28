"""Tests for SQL commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestSQLCommands:
    """Test SQL commands."""
    
    def test_sql_execute_help(self, runner):
        """Test SQL execute help."""
        result = runner.invoke(cli, ["sql", "execute", "--help"])
        assert result.exit_code == 0
        assert "Execute a SQL query" in result.output
    
    def test_sql_explain_help(self, runner):
        """Test SQL explain help."""
        result = runner.invoke(cli, ["sql", "explain", "--help"])
        assert result.exit_code == 0
        assert "Explain a SQL query" in result.output
    
    def test_sql_validate_help(self, runner):
        """Test SQL validate help."""
        result = runner.invoke(cli, ["sql", "validate", "--help"])
        assert result.exit_code == 0
        assert "Validate SQL query syntax" in result.output
    
    def test_sql_execute_requires_query(self, runner):
        """Test SQL execute requires query or file."""
        result = runner.invoke(cli, ["sql", "execute"])
        assert result.exit_code != 0
