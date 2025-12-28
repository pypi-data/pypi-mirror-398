"""Tests for history and favorite commands."""

import pytest
import tempfile
import os
from click.testing import CliRunner

from dremio_cli.cli import cli
from dremio_cli.history import HistoryManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestHistoryManager:
    """Test history manager."""
    
    def test_add_and_get_history(self, temp_db):
        """Test adding and retrieving history."""
        manager = HistoryManager(temp_db)
        
        manager.add_history("sql execute", "SELECT * FROM table", "default")
        history = manager.get_history(limit=10)
        
        assert len(history) == 1
        assert history[0]["command"] == "sql execute"
        assert history[0]["query"] == "SELECT * FROM table"
    
    def test_clear_history(self, temp_db):
        """Test clearing history."""
        manager = HistoryManager(temp_db)
        
        manager.add_history("sql execute", "SELECT 1")
        manager.clear_history()
        history = manager.get_history()
        
        assert len(history) == 0
    
    def test_add_and_get_favorite(self, temp_db):
        """Test adding and retrieving favorites."""
        manager = HistoryManager(temp_db)
        
        manager.add_favorite("daily", "SELECT * FROM sales", "Daily report")
        favorite = manager.get_favorite("daily")
        
        assert favorite["name"] == "daily"
        assert favorite["query"] == "SELECT * FROM sales"
        assert favorite["description"] == "Daily report"
    
    def test_delete_favorite(self, temp_db):
        """Test deleting favorite."""
        manager = HistoryManager(temp_db)
        
        manager.add_favorite("test", "SELECT 1")
        manager.delete_favorite("test")
        favorite = manager.get_favorite("test")
        
        assert favorite is None


class TestHistoryCommands:
    """Test history commands."""
    
    def test_history_list_help(self, runner):
        """Test history list help."""
        result = runner.invoke(cli, ["history", "list", "--help"])
        assert result.exit_code == 0
        assert "List recent query history" in result.output
    
    def test_history_clear_help(self, runner):
        """Test history clear help."""
        result = runner.invoke(cli, ["history", "clear", "--help"])
        assert result.exit_code == 0
        assert "Clear all query history" in result.output


class TestFavoriteCommands:
    """Test favorite commands."""
    
    def test_favorite_add_help(self, runner):
        """Test favorite add help."""
        result = runner.invoke(cli, ["favorite", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a favorite query" in result.output
    
    def test_favorite_list_help(self, runner):
        """Test favorite list help."""
        result = runner.invoke(cli, ["favorite", "list", "--help"])
        assert result.exit_code == 0
        assert "List all favorite queries" in result.output
    
    def test_favorite_delete_help(self, runner):
        """Test favorite delete help."""
        result = runner.invoke(cli, ["favorite", "delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a favorite query" in result.output
