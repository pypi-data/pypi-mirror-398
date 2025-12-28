"""Integration tests for Phase 1 commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from dremio_cli.cli import cli
from dremio_cli.config import ProfileManager


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_profile(temp_config_dir, monkeypatch):
    """Create a mock profile for testing."""
    # Set up environment variables for testing
    monkeypatch.setenv("DREMIO_MOCKTEST_TYPE", "software")
    monkeypatch.setenv("DREMIO_MOCKTEST_BASE_URL", "http://localhost:9047/api/v3")
    monkeypatch.setenv("DREMIO_MOCKTEST_TOKEN", "test_token_123")
    
    # Create profile manager with temp directory
    manager = ProfileManager(config_dir=temp_config_dir)
    
    # Create a test profile with unique name
    manager.create_profile(
        name="mocktest",
        profile_type="software",
        base_url="http://localhost:9047/api/v3",
        auth_type="pat",
        token="test_token_123",
    )
    
    return "mocktest"


class TestProfileCommands:
    """Test profile management commands."""
    
    def test_profile_list(self, runner, mock_profile):
        """Test profile list command."""
        result = runner.invoke(cli, ["profile", "list"])
        assert result.exit_code == 0
        assert "test" in result.output or "Profiles" in result.output
    
    def test_profile_current(self, runner, mock_profile):
        """Test profile current command."""
        result = runner.invoke(cli, ["profile", "current"])
        assert result.exit_code == 0


class TestCatalogCommands:
    """Test catalog commands."""
    
    def test_catalog_list_help(self, runner):
        """Test catalog list help."""
        result = runner.invoke(cli, ["catalog", "list", "--help"])
        assert result.exit_code == 0
        assert "List catalog contents" in result.output
    
    def test_catalog_get_help(self, runner):
        """Test catalog get help."""
        result = runner.invoke(cli, ["catalog", "get", "--help"])
        assert result.exit_code == 0
        assert "Get catalog item by ID" in result.output


class TestSQLCommands:
    """Test SQL commands."""
    
    def test_sql_execute_help(self, runner):
        """Test SQL execute help."""
        result = runner.invoke(cli, ["sql", "execute", "--help"])
        assert result.exit_code == 0
        assert "Execute SQL query" in result.output
    
    def test_sql_execute_no_query(self, runner, mock_profile):
        """Test SQL execute without query."""
        result = runner.invoke(cli, ["--profile", "mocktest", "sql", "execute"])
        assert result.exit_code != 0


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


class TestTableCommands:
    """Test table commands."""
    
    def test_table_get_help(self, runner):
        """Test table get help."""
        result = runner.invoke(cli, ["table", "get", "--help"])
        assert result.exit_code == 0
        assert "Get table by ID" in result.output
    
    def test_table_get_by_path_help(self, runner):
        """Test table get-by-path help."""
        result = runner.invoke(cli, ["table", "get-by-path", "--help"])
        assert result.exit_code == 0
        assert "Get table by path" in result.output


class TestOutputFormats:
    """Test output format options."""
    
    def test_json_output_format(self, runner):
        """Test JSON output format option."""
        result = runner.invoke(cli, ["--output", "json", "profile", "list"])
        assert result.exit_code == 0
    
    def test_yaml_output_format(self, runner):
        """Test YAML output format option."""
        result = runner.invoke(cli, ["--output", "yaml", "profile", "list"])
        assert result.exit_code == 0
    
    def test_table_output_format(self, runner):
        """Test table output format option."""
        result = runner.invoke(cli, ["--output", "table", "profile", "list"])
        assert result.exit_code == 0
