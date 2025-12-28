"""Tests for job management commands."""

import pytest
from click.testing import CliRunner

from dremio_cli.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestJobCommands:
    """Test job management commands."""
    
    def test_job_list_help(self, runner):
        """Test job list help."""
        result = runner.invoke(cli, ["job", "list", "--help"])
        assert result.exit_code == 0
        assert "List jobs" in result.output
    
    def test_job_get_help(self, runner):
        """Test job get help."""
        result = runner.invoke(cli, ["job", "get", "--help"])
        assert result.exit_code == 0
        assert "Get job details by ID" in result.output
    
    def test_job_results_help(self, runner):
        """Test job results help."""
        result = runner.invoke(cli, ["job", "results", "--help"])
        assert result.exit_code == 0
        assert "Get job results" in result.output
    
    def test_job_cancel_help(self, runner):
        """Test job cancel help."""
        result = runner.invoke(cli, ["job", "cancel", "--help"])
        assert result.exit_code == 0
        assert "Cancel a running job" in result.output
    
    def test_job_profile_help(self, runner):
        """Test job profile help."""
        result = runner.invoke(cli, ["job", "profile", "--help"])
        assert result.exit_code == 0
        assert "Get job profile" in result.output
    
    def test_job_reflections_help(self, runner):
        """Test job reflections help."""
        result = runner.invoke(cli, ["job", "reflections", "--help"])
        assert result.exit_code == 0
        assert "Get reflection information" in result.output
