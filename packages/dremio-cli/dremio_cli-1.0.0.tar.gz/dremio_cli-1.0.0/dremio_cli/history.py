"""Query history and favorites management."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class HistoryManager:
    """Manage query history and favorites."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize history manager.
        
        Args:
            db_path: Path to SQLite database (default: ~/.dremio/history.db)
        """
        if db_path is None:
            dremio_dir = Path.home() / ".dremio"
            dremio_dir.mkdir(exist_ok=True)
            db_path = str(dremio_dir / "history.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                query TEXT,
                profile TEXT,
                timestamp TEXT NOT NULL,
                success INTEGER DEFAULT 1
            )
        """)
        
        # Favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                name TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_history(self, command: str, query: Optional[str] = None, 
                   profile: Optional[str] = None, success: bool = True):
        """Add command to history.
        
        Args:
            command: Command executed
            query: SQL query if applicable
            profile: Profile name used
            success: Whether command succeeded
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO history (command, query, profile, timestamp, success)
            VALUES (?, ?, ?, ?, ?)
        """, (command, query, profile, datetime.now().isoformat(), 1 if success else 0))
        
        conn.commit()
        conn.close()
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent history.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_history_item(self, history_id: int) -> Optional[Dict[str, Any]]:
        """Get specific history item.
        
        Args:
            history_id: History entry ID
            
        Returns:
            History entry or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM history WHERE id = ?", (history_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def clear_history(self):
        """Clear all history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        conn.close()
    
    def add_favorite(self, name: str, query: str, description: Optional[str] = None):
        """Add or update favorite.
        
        Args:
            name: Favorite name
            query: SQL query
            description: Optional description
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO favorites (name, query, description, created_at, updated_at)
            VALUES (?, ?, ?, 
                COALESCE((SELECT created_at FROM favorites WHERE name = ?), ?),
                ?)
        """, (name, query, description, name, now, now))
        
        conn.commit()
        conn.close()
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorites.
        
        Returns:
            List of favorites
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM favorites ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_favorite(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific favorite.
        
        Args:
            name: Favorite name
            
        Returns:
            Favorite or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM favorites WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def delete_favorite(self, name: str):
        """Delete favorite.
        
        Args:
            name: Favorite name
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE name = ?", (name,))
        conn.commit()
        conn.close()
