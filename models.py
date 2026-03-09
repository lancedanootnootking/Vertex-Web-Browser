"""
Database Models

This module defines all database models used by the browser backend,
including bookmarks, history, sessions, and user preferences.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class Bookmark:
    """Represents a bookmark entry."""
    id: Optional[int] = None
    title: str = ""
    url: str = ""
    folder: str = "Default"
    tags: List[str] = None
    favicon: str = ""
    created_at: Optional[datetime] = None
    last_visited: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class HistoryEntry:
    """Represents a browsing history entry."""
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    visit_count: int = 1
    last_visited: Optional[datetime] = None
    favicon: str = ""
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.last_visited is None:
            self.last_visited = datetime.now()


@dataclass
class UserPreference:
    """Represents a user preference setting."""
    key: str
    value: Any
    category: str = "general"
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class CacheEntry:
    """Represents a cached web resource."""
    url: str
    content: bytes
    content_type: str
    expires_at: datetime
    etag: str = ""
    size: int = 0
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.size = len(self.content)


@dataclass
class Session:
    """Represents a browsing session."""
    session_id: str
    name: str
    tabs: List[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tabs is None:
            self.tabs = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()


class DatabaseManager:
    """Manages all database operations for the browser."""
    
    def __init__(self, db_path: str = "browser_data.db"):
        self.db_path = db_path
        self.connection = None
        self._initialize_database()
    
    def connect(self):
        """Establish database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def _initialize_database(self):
        """Initialize database tables."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Bookmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                folder TEXT DEFAULT 'Default',
                tags TEXT,  -- JSON array
                favicon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visited TIMESTAMP
            )
        ''')
        
        # History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                visit_count INTEGER DEFAULT 1,
                last_visited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                favicon TEXT,
                session_id TEXT
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT DEFAULT 'general',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                url TEXT PRIMARY KEY,
                content BLOB,
                content_type TEXT,
                expires_at TIMESTAMP,
                etag TEXT,
                size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                tabs TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_url ON history(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_last_visited ON history(last_visited)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_url ON bookmarks(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at)')
        
        conn.commit()
    
    # Bookmark operations
    def add_bookmark(self, bookmark: Bookmark) -> int:
        """Add a new bookmark."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bookmarks (title, url, folder, tags, favicon, created_at, last_visited)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bookmark.title,
            bookmark.url,
            bookmark.folder,
            json.dumps(bookmark.tags),
            bookmark.favicon,
            bookmark.created_at,
            bookmark.last_visited
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_bookmarks(self, folder: str = None) -> List[Bookmark]:
        """Get all bookmarks, optionally filtered by folder."""
        conn = self.connect()
        cursor = conn.cursor()
        
        if folder:
            cursor.execute('SELECT * FROM bookmarks WHERE folder = ? ORDER BY title', (folder,))
        else:
            cursor.execute('SELECT * FROM bookmarks ORDER BY title')
        
        bookmarks = []
        for row in cursor.fetchall():
            bookmark = Bookmark(
                id=row['id'],
                title=row['title'],
                url=row['url'],
                folder=row['folder'],
                tags=json.loads(row['tags']) if row['tags'] else [],
                favicon=row['favicon'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                last_visited=datetime.fromisoformat(row['last_visited']) if row['last_visited'] else None
            )
            bookmarks.append(bookmark)
        
        return bookmarks
    
    def delete_bookmark(self, bookmark_id: int) -> bool:
        """Delete a bookmark."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    # History operations
    def add_history_entry(self, entry: HistoryEntry) -> int:
        """Add or update a history entry."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Check if URL already exists
        cursor.execute('SELECT id, visit_count FROM history WHERE url = ?', (entry.url,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing entry
            cursor.execute('''
                UPDATE history 
                SET title = ?, visit_count = ?, last_visited = ?, favicon = ?, session_id = ?
                WHERE id = ?
            ''', (
                entry.title,
                existing['visit_count'] + 1,
                entry.last_visited,
                entry.favicon,
                entry.session_id,
                existing['id']
            ))
            conn.commit()
            return existing['id']
        else:
            # Insert new entry
            cursor.execute('''
                INSERT INTO history (url, title, visit_count, last_visited, favicon, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                entry.url,
                entry.title,
                entry.visit_count,
                entry.last_visited,
                entry.favicon,
                entry.session_id
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_history(self, limit: int = 100) -> List[HistoryEntry]:
        """Get browsing history."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM history 
            ORDER BY last_visited DESC 
            LIMIT ?
        ''', (limit,))
        
        history = []
        for row in cursor.fetchall():
            entry = HistoryEntry(
                id=row['id'],
                url=row['url'],
                title=row['title'],
                visit_count=row['visit_count'],
                last_visited=datetime.fromisoformat(row['last_visited']) if row['last_visited'] else None,
                favicon=row['favicon'],
                session_id=row['session_id']
            )
            history.append(entry)
        
        return history
    
    def clear_history(self) -> bool:
        """Clear all browsing history."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history')
        conn.commit()
        return True
    
    # Preference operations
    def set_preference(self, preference: UserPreference) -> bool:
        """Set a user preference."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO preferences (key, value, category, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (
            preference.key,
            json.dumps(preference.value) if not isinstance(preference.value, str) else preference.value,
            preference.category,
            preference.updated_at
        ))
        
        conn.commit()
        return True
    
    def get_preference(self, key: str) -> Optional[UserPreference]:
        """Get a user preference."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM preferences WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            try:
                value = json.loads(row['value'])
            except json.JSONDecodeError:
                value = row['value']
            
            return UserPreference(
                key=row['key'],
                value=value,
                category=row['category'],
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        
        return None
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM preferences')
        preferences = {}
        
        for row in cursor.fetchall():
            try:
                value = json.loads(row['value'])
            except json.JSONDecodeError:
                value = row['value']
            preferences[row['key']] = value
        
        return preferences
