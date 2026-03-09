#!/usr/bin/env python3.12
"""
Advanced History and Bookmarks System for Vertex Browser

Comprehensive history and bookmarks management with search, tags,
import/export, synchronization, and advanced features.
"""

import json
import sqlite3
import threading
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import weakref
import asyncio
from urllib.parse import urlparse

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit,
                             QFrame, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                             QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
                             QFormLayout, QScrollArea, QSplitter, QMenu, QToolBar,
                             QToolButton, QFileDialog, QStatusBar, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QSlider, QDoubleSpinBox, QDateTimeEdit, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QObject, pyqtSlot, QSortFilterProxyModel
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QPainter, QColor

from frontend.themes.modern_theme import theme, style_manager, ui_components


class BookmarkType(Enum):
    """Bookmark types."""
    BOOKMARK = "bookmark"
    FOLDER = "folder"
    SEPARATOR = "separator"


class BookmarkSortOrder(Enum):
    """Bookmark sort orders."""
    NAME = "name"
    DATE = "date"
    URL = "url"
    VISITS = "visits"
    MANUAL = "manual"


@dataclass
class BookmarkItem:
    """Bookmark item data structure."""
    id: str
    title: str
    url: str = ""
    parent_id: Optional[str] = None
    type: BookmarkType = BookmarkType.BOOKMARK
    position: int = 0
    favicon: str = ""
    tags: Set[str] = None
    notes: str = ""
    created_at: datetime = None
    modified_at: datetime = None
    last_visited: Optional[datetime] = None
    visit_count: int = 0
    is_favorite: bool = False
    is_read_later: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = set()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_folder(self) -> bool:
        """Check if bookmark is a folder."""
        return self.type == BookmarkType.FOLDER
    
    @property
    def is_separator(self) -> bool:
        """Check if bookmark is a separator."""
        return self.type == BookmarkType.SEPARATOR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'parent_id': self.parent_id,
            'type': self.type.value,
            'position': self.position,
            'favicon': self.favicon,
            'tags': list(self.tags),
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'last_visited': self.last_visited.isoformat() if self.last_visited else None,
            'visit_count': self.visit_count,
            'is_favorite': self.is_favorite,
            'is_read_later': self.is_read_later,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookmarkItem':
        """Create from dictionary."""
        item = cls(
            id=data['id'],
            title=data['title'],
            url=data['url'],
            parent_id=data['parent_id'],
            type=BookmarkType(data['type']),
            position=data['position'],
            favicon=data['favicon'],
            tags=set(data['tags']),
            notes=data['notes'],
            visit_count=data['visit_count'],
            is_favorite=data['is_favorite'],
            is_read_later=data['is_read_later'],
            metadata=data['metadata']
        )
        
        if data['created_at']:
            item.created_at = datetime.fromisoformat(data['created_at'])
        if data['modified_at']:
            item.modified_at = datetime.fromisoformat(data['modified_at'])
        if data['last_visited']:
            item.last_visited = datetime.fromisoformat(data['last_visited'])
        
        return item


@dataclass
class HistoryItem:
    """History item data structure."""
    id: str
    url: str
    title: str
    visit_time: datetime
    visit_count: int = 1
    last_visit_time: datetime = None
    favicon: str = ""
    tags: Set[str] = None
    notes: str = ""
    is_favorite: bool = False
    transition_type: str = "link"  # link, typed, auto_bookmark, auto_subframe, manual_subframe, generated, start_page, form_submit, reload, keyword, keyword_generated
    from_url: str = ""
    session_id: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = set()
        if self.last_visit_time is None:
            self.last_visit_time = self.visit_time
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'visit_time': self.visit_time.isoformat(),
            'visit_count': self.visit_count,
            'last_visit_time': self.last_visit_time.isoformat(),
            'favicon': self.favicon,
            'tags': list(self.tags),
            'notes': self.notes,
            'is_favorite': self.is_favorite,
            'transition_type': self.transition_type,
            'from_url': self.from_url,
            'session_id': self.session_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryItem':
        """Create from dictionary."""
        item = cls(
            id=data['id'],
            url=data['url'],
            title=data['title'],
            visit_time=datetime.fromisoformat(data['visit_time']),
            visit_count=data['visit_count'],
            favicon=data['favicon'],
            tags=set(data['tags']),
            notes=data['notes'],
            is_favorite=data['is_favorite'],
            transition_type=data['transition_type'],
            from_url=data['from_url'],
            session_id=data['session_id'],
            metadata=data['metadata']
        )
        
        if data['last_visit_time']:
            item.last_visit_time = datetime.fromisoformat(data['last_visit_time'])
        
        return item


class BookmarkDatabase:
    """Database for bookmarks storage."""
    
    def __init__(self):
        self.db_path = Path.home() / '.vertex_bookmarks.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Bookmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                parent_id TEXT,
                type TEXT,
                position INTEGER,
                favicon TEXT,
                tags TEXT,
                notes TEXT,
                created_at TEXT,
                modified_at TEXT,
                last_visited TEXT,
                visit_count INTEGER,
                is_favorite INTEGER,
                is_read_later INTEGER,
                metadata TEXT
            )
        ''')
        
        # Bookmark tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmark_tags (
                bookmark_id TEXT,
                tag TEXT,
                PRIMARY KEY (bookmark_id, tag),
                FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_bookmark(self, bookmark: BookmarkItem):
        """Save bookmark to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bookmarks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bookmark.id,
            bookmark.title,
            bookmark.url,
            bookmark.parent_id,
            bookmark.type.value,
            bookmark.position,
            bookmark.favicon,
            json.dumps(list(bookmark.tags)),
            bookmark.notes,
            bookmark.created_at.isoformat(),
            bookmark.modified_at.isoformat(),
            bookmark.last_visited.isoformat() if bookmark.last_visited else None,
            bookmark.visit_count,
            int(bookmark.is_favorite),
            int(bookmark.is_read_later),
            json.dumps(bookmark.metadata)
        ))
        
        # Update tags table
        cursor.execute('DELETE FROM bookmark_tags WHERE bookmark_id = ?', (bookmark.id,))
        for tag in bookmark.tags:
            cursor.execute('INSERT INTO bookmark_tags VALUES (?, ?)', (bookmark.id, tag))
        
        conn.commit()
        conn.close()
    
    def load_bookmarks(self) -> List[BookmarkItem]:
        """Load bookmarks from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bookmarks ORDER BY parent_id, position')
        rows = cursor.fetchall()
        
        bookmarks = []
        for row in rows:
            # Convert row to dictionary
            columns = [
                'id', 'title', 'url', 'parent_id', 'type', 'position', 'favicon',
                'tags', 'notes', 'created_at', 'modified_at', 'last_visited',
                'visit_count', 'is_favorite', 'is_read_later', 'metadata'
            ]
            
            data = dict(zip(columns, row))
            data['tags'] = json.loads(data['tags'])
            data['is_favorite'] = bool(data['is_favorite'])
            data['is_read_later'] = bool(data['is_read_later'])
            data['metadata'] = json.loads(data['metadata'])
            
            bookmark = BookmarkItem.from_dict(data)
            bookmarks.append(bookmark)
        
        conn.close()
        return bookmarks
    
    def delete_bookmark(self, bookmark_id: str):
        """Delete bookmark from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        
        conn.commit()
        conn.close()
    
    def get_tags(self) -> List[str]:
        """Get all tags."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT tag FROM bookmark_tags ORDER BY tag')
        tags = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tags
    
    def search_bookmarks(self, query: str, tags: List[str] = None) -> List[BookmarkItem]:
        """Search bookmarks."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        sql = '''
            SELECT b.* FROM bookmarks b
            LEFT JOIN bookmark_tags bt ON b.id = bt.bookmark_id
            WHERE 1=1
        '''
        params = []
        
        if query:
            sql += ' AND (b.title LIKE ? OR b.url LIKE ? OR b.notes LIKE ?)'
            params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
        if tags:
            placeholders = ','.join(['?'] * len(tags))
            sql += f' AND bt.tag IN ({placeholders})'
            params.extend(tags)
        
        sql += ' GROUP BY b.id ORDER BY b.title'
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        bookmarks = []
        for row in rows:
            columns = [
                'id', 'title', 'url', 'parent_id', 'type', 'position', 'favicon',
                'tags', 'notes', 'created_at', 'modified_at', 'last_visited',
                'visit_count', 'is_favorite', 'is_read_later', 'metadata'
            ]
            
            data = dict(zip(columns, row))
            data['tags'] = json.loads(data['tags'])
            data['is_favorite'] = bool(data['is_favorite'])
            data['is_read_later'] = bool(data['is_read_later'])
            data['metadata'] = json.loads(data['metadata'])
            
            bookmark = BookmarkItem.from_dict(data)
            bookmarks.append(bookmark)
        
        conn.close()
        return bookmarks


class HistoryDatabase:
    """Database for history storage."""
    
    def __init__(self):
        self.db_path = Path.home() / '.vertex_history.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                visit_time TEXT,
                visit_count INTEGER,
                last_visit_time TEXT,
                favicon TEXT,
                tags TEXT,
                notes TEXT,
                is_favorite INTEGER,
                transition_type TEXT,
                from_url TEXT,
                session_id TEXT,
                metadata TEXT
            )
        ''')
        
        # History tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_tags (
                history_id TEXT,
                tag TEXT,
                PRIMARY KEY (history_id, tag),
                FOREIGN KEY (history_id) REFERENCES history(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_url ON history(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_visit_time ON history(visit_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_title ON history(title)')
        
        conn.commit()
        conn.close()
    
    def save_history_item(self, item: HistoryItem):
        """Save history item to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.id,
            item.url,
            item.title,
            item.visit_time.isoformat(),
            item.visit_count,
            item.last_visit_time.isoformat(),
            item.favicon,
            json.dumps(list(item.tags)),
            item.notes,
            int(item.is_favorite),
            item.transition_type,
            item.from_url,
            item.session_id,
            json.dumps(item.metadata)
        ))
        
        # Update tags table
        cursor.execute('DELETE FROM history_tags WHERE history_id = ?', (item.id,))
        for tag in item.tags:
            cursor.execute('INSERT INTO history_tags VALUES (?, ?)', (item.id, tag))
        
        conn.commit()
        conn.close()
    
    def load_history(self, limit: int = None, days: int = None) -> List[HistoryItem]:
        """Load history from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        sql = 'SELECT * FROM history'
        params = []
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            sql += ' WHERE visit_time >= ?'
            params.append(cutoff_date.isoformat())
        
        sql += ' ORDER BY visit_time DESC'
        
        if limit:
            sql += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        history_items = []
        for row in rows:
            columns = [
                'id', 'url', 'title', 'visit_time', 'visit_count', 'last_visit_time',
                'favicon', 'tags', 'notes', 'is_favorite', 'transition_type',
                'from_url', 'session_id', 'metadata'
            ]
            
            data = dict(zip(columns, row))
            data['tags'] = json.loads(data['tags'])
            data['is_favorite'] = bool(data['is_favorite'])
            data['metadata'] = json.loads(data['metadata'])
            
            item = HistoryItem.from_dict(data)
            history_items.append(item)
        
        conn.close()
        return history_items
    
    def delete_history_item(self, item_id: str):
        """Delete history item from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history WHERE id = ?', (item_id,))
        
        conn.commit()
        conn.close()
    
    def clear_history(self, older_than_days: int = None, all_history: bool = False):
        """Clear history."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if all_history:
            cursor.execute('DELETE FROM history')
        elif older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            cursor.execute('DELETE FROM history WHERE visit_time < ?', (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_tags(self) -> List[str]:
        """Get all tags."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT tag FROM history_tags ORDER BY tag')
        tags = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tags
    
    def search_history(self, query: str, tags: List[str] = None, days: int = None) -> List[HistoryItem]:
        """Search history."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        sql = '''
            SELECT h.* FROM history h
            LEFT JOIN history_tags ht ON h.id = ht.history_id
            WHERE 1=1
        '''
        params = []
        
        if query:
            sql += ' AND (h.title LIKE ? OR h.url LIKE ? OR h.notes LIKE ?)'
            params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
        if tags:
            placeholders = ','.join(['?'] * len(tags))
            sql += f' AND ht.tag IN ({placeholders})'
            params.extend(tags)
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            sql += ' AND h.visit_time >= ?'
            params.append(cutoff_date.isoformat())
        
        sql += ' GROUP BY h.id ORDER BY h.visit_time DESC'
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        history_items = []
        for row in rows:
            columns = [
                'id', 'url', 'title', 'visit_time', 'visit_count', 'last_visit_time',
                'favicon', 'tags', 'notes', 'is_favorite', 'transition_type',
                'from_url', 'session_id', 'metadata'
            ]
            
            data = dict(zip(columns, row))
            data['tags'] = json.loads(data['tags'])
            data['is_favorite'] = bool(data['is_favorite'])
            data['metadata'] = json.loads(data['metadata'])
            
            item = HistoryItem.from_dict(data)
            history_items.append(item)
        
        conn.close()
        return history_items
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total visits
        cursor.execute('SELECT COUNT(*) FROM history')
        total_visits = cursor.fetchone()[0]
        
        # Unique URLs
        cursor.execute('SELECT COUNT(DISTINCT url) FROM history')
        unique_urls = cursor.fetchone()[0]
        
        # Most visited domains
        cursor.execute('''
            SELECT SUBSTR(url, 1, INSTR(SUBSTR(url, 9), '/') + 8) as domain, COUNT(*) as visits
            FROM history 
            WHERE url LIKE 'http%'
            GROUP BY domain
            ORDER BY visits DESC
            LIMIT 10
        ''')
        top_domains = cursor.fetchall()
        
        # Most visited pages
        cursor.execute('''
            SELECT url, title, COUNT(*) as visits
            FROM history
            GROUP BY url
            ORDER BY visits DESC
            LIMIT 10
        ''')
        top_pages = cursor.fetchall()
        
        # Visits by day
        cursor.execute('''
            SELECT DATE(visit_time) as date, COUNT(*) as visits
            FROM history
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        ''')
        visits_by_day = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_visits': total_visits,
            'unique_urls': unique_urls,
            'top_domains': top_domains,
            'top_pages': top_pages,
            'visits_by_day': visits_by_day
        }


class BookmarkManager:
    """Main bookmark manager."""
    
    bookmark_added = pyqtSignal(object)  # BookmarkItem
    bookmark_updated = pyqtSignal(object)  # BookmarkItem
    bookmark_deleted = pyqtSignal(str)  # bookmark_id
    bookmark_moved = pyqtSignal(str, str, int)  # bookmark_id, new_parent_id, new_position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database = BookmarkDatabase()
        self.bookmarks = []
        self.folders = {}
        self.root_folder_id = "root"
        self.bookmarks_bar_id = "bookmarks_bar"
        self.other_bookmarks_id = "other_bookmarks"
        self.counter = 0
        
        # Load bookmarks
        self.load_bookmarks()
        
        # Create default folders if needed
        self.create_default_folders()
    
    def load_bookmarks(self):
        """Load bookmarks from database."""
        self.bookmarks = self.database.load_bookmarks()
        
        # Build folder hierarchy
        self.folders = {}
        for bookmark in self.bookmarks:
            if bookmark.is_folder:
                self.folders[bookmark.id] = bookmark
    
    def create_default_folders(self):
        """Create default folders."""
        if self.root_folder_id not in self.folders:
            root_folder = BookmarkItem(
                id=self.root_folder_id,
                title="Bookmarks",
                type=BookmarkType.FOLDER
            )
            self.add_bookmark(root_folder)
        
        if self.bookmarks_bar_id not in self.folders:
            bar_folder = BookmarkItem(
                id=self.bookmarks_bar_id,
                title="Bookmarks Bar",
                parent_id=self.root_folder_id,
                type=BookmarkType.FOLDER
            )
            self.add_bookmark(bar_folder)
        
        if self.other_bookmarks_id not in self.folders:
            other_folder = BookmarkItem(
                id=self.other_bookmarks_id,
                title="Other Bookmarks",
                parent_id=self.root_folder_id,
                type=BookmarkType.FOLDER
            )
            self.add_bookmark(other_folder)
    
    def add_bookmark(self, bookmark: BookmarkItem) -> str:
        """Add bookmark."""
        if not bookmark.id:
            self.counter += 1
            bookmark.id = f"bookmark_{self.counter}_{int(time.time())}"
        
        self.bookmarks.append(bookmark)
        self.database.save_bookmark(bookmark)
        
        if bookmark.is_folder:
            self.folders[bookmark.id] = bookmark
        
        self.bookmark_added.emit(bookmark)
        return bookmark.id
    
    def update_bookmark(self, bookmark: BookmarkItem):
        """Update bookmark."""
        bookmark.modified_at = datetime.now()
        
        # Update in list
        for i, existing in enumerate(self.bookmarks):
            if existing.id == bookmark.id:
                self.bookmarks[i] = bookmark
                break
        
        self.database.save_bookmark(bookmark)
        self.bookmark_updated.emit(bookmark)
    
    def delete_bookmark(self, bookmark_id: str):
        """Delete bookmark and its children."""
        # Find and delete bookmark
        bookmark_to_delete = None
        for i, bookmark in enumerate(self.bookmarks):
            if bookmark.id == bookmark_id:
                bookmark_to_delete = bookmark
                del self.bookmarks[i]
                break
        
        if bookmark_to_delete:
            # Delete children if it's a folder
            if bookmark_to_delete.is_folder:
                children = self.get_children(bookmark_id)
                for child in children:
                    self.delete_bookmark(child.id)
            
            # Remove from folders
            if bookmark_id in self.folders:
                del self.folders[bookmark_id]
            
            self.database.delete_bookmark(bookmark_id)
            self.bookmark_deleted.emit(bookmark_id)
    
    def move_bookmark(self, bookmark_id: str, new_parent_id: str, new_position: int):
        """Move bookmark to new position."""
        bookmark = self.get_bookmark(bookmark_id)
        if bookmark:
            bookmark.parent_id = new_parent_id
            bookmark.position = new_position
            bookmark.modified_at = datetime.now()
            
            self.database.save_bookmark(bookmark)
            self.bookmark_moved.emit(bookmark_id, new_parent_id, new_position)
    
    def get_bookmark(self, bookmark_id: str) -> Optional[BookmarkItem]:
        """Get bookmark by ID."""
        for bookmark in self.bookmarks:
            if bookmark.id == bookmark_id:
                return bookmark
        return None
    
    def get_children(self, parent_id: str) -> List[BookmarkItem]:
        """Get children of a folder."""
        return [b for b in self.bookmarks if b.parent_id == parent_id]
    
    def get_root_bookmarks(self) -> List[BookmarkItem]:
        """Get root level bookmarks."""
        return self.get_children(self.root_folder_id)
    
    def get_bookmarks_bar(self) -> List[BookmarkItem]:
        """Get bookmarks bar items."""
        return self.get_children(self.bookmarks_bar_id)
    
    def get_other_bookmarks(self) -> List[BookmarkItem]:
        """Get other bookmarks."""
        return self.get_children(self.other_bookmarks_id)
    
    def search_bookmarks(self, query: str, tags: List[str] = None) -> List[BookmarkItem]:
        """Search bookmarks."""
        return self.database.search_bookmarks(query, tags)
    
    def get_tags(self) -> List[str]:
        """Get all tags."""
        return self.database.get_tags()
    
    def get_favorites(self) -> List[BookmarkItem]:
        """Get favorite bookmarks."""
        return [b for b in self.bookmarks if b.is_favorite and not b.is_folder]
    
    def get_read_later(self) -> List[BookmarkItem]:
        """Get read later bookmarks."""
        return [b for b in self.bookmarks if b.is_read_later and not b.is_folder]
    
    def add_to_favorites(self, bookmark_id: str):
        """Add bookmark to favorites."""
        bookmark = self.get_bookmark(bookmark_id)
        if bookmark:
            bookmark.is_favorite = True
            self.update_bookmark(bookmark)
    
    def remove_from_favorites(self, bookmark_id: str):
        """Remove bookmark from favorites."""
        bookmark = self.get_bookmark(bookmark_id)
        if bookmark:
            bookmark.is_favorite = False
            self.update_bookmark(bookmark)
    
    def add_to_read_later(self, bookmark_id: str):
        """Add bookmark to read later."""
        bookmark = self.get_bookmark(bookmark_id)
        if bookmark:
            bookmark.is_read_later = True
            self.update_bookmark(bookmark)
    
    def remove_from_read_later(self, bookmark_id: str):
        """Remove bookmark from read later."""
        bookmark = self.get_bookmark(bookmark_id)
        if bookmark:
            bookmark.is_read_later = False
            self.update_bookmark(bookmark)
    
    def import_bookmarks(self, file_path: str, format: str = "json"):
        """Import bookmarks from file."""
        if format == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import bookmarks recursively
            self._import_bookmarks_recursive(data, self.other_bookmarks_id)
        
        elif format == "html":
            # Parse HTML bookmarks file
            self._import_html_bookmarks(file_path)
        
        self.load_bookmarks()
    
    def _import_bookmarks_recursive(self, data: List[Dict], parent_id: str):
        """Import bookmarks recursively from JSON data."""
        for item_data in data:
            if item_data.get('type') == 'folder':
                # Create folder
                folder = BookmarkItem(
                    id=item_data.get('id', ''),
                    title=item_data.get('title', ''),
                    parent_id=parent_id,
                    type=BookmarkType.FOLDER
                )
                folder_id = self.add_bookmark(folder)
                
                # Import children
                children = item_data.get('children', [])
                self._import_bookmarks_recursive(children, folder_id)
            
            else:
                # Create bookmark
                bookmark = BookmarkItem(
                    id=item_data.get('id', ''),
                    title=item_data.get('title', ''),
                    url=item_data.get('url', ''),
                    parent_id=parent_id,
                    tags=set(item_data.get('tags', [])),
                    notes=item_data.get('notes', '')
                )
                self.add_bookmark(bookmark)
    
    def _import_html_bookmarks(self, file_path: str):
        """Import bookmarks from HTML file."""
        # This would parse Netscape bookmark format
        # Implementation would be more complex
        pass
    
    def export_bookmarks(self, file_path: str, format: str = "json"):
        """Export bookmarks to file."""
        if format == "json":
            # Build tree structure
            root_data = []
            for bookmark in self.get_root_bookmarks():
                item_data = self._bookmark_to_dict(bookmark)
                root_data.append(item_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(root_data, f, indent=2, default=str)
        
        elif format == "html":
            # Export as HTML bookmarks
            self._export_html_bookmarks(file_path)
    
    def _bookmark_to_dict(self, bookmark: BookmarkItem) -> Dict[str, Any]:
        """Convert bookmark to dictionary for export."""
        data = bookmark.to_dict()
        
        if bookmark.is_folder:
            # Add children
            children = self.get_children(bookmark.id)
            data['children'] = [self._bookmark_to_dict(child) for child in children]
        
        return data
    
    def _export_html_bookmarks(self, file_path: str):
        """Export bookmarks as HTML."""
        # This would generate Netscape bookmark format
        # Implementation would be more complex
        pass


class HistoryManager:
    """Main history manager."""
    
    history_added = pyqtSignal(object)  # HistoryItem
    history_updated = pyqtSignal(object)  # HistoryItem
    history_deleted = pyqtSignal(str)  # item_id
    history_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database = HistoryDatabase()
        self.history = []
        self.counter = 0
        self.session_id = f"session_{int(time.time())}"
        
        # Load recent history
        self.load_history()
    
    def load_history(self, limit: int = 1000):
        """Load recent history."""
        self.history = self.database.load_history(limit=limit)
    
    def add_page_visit(self, url: str, title: str, transition_type: str = "link", 
                      from_url: str = "") -> str:
        """Add page visit to history."""
        # Check if URL already exists in recent history
        existing_item = None
        for item in self.history[:100]:  # Check last 100 items
            if item.url == url:
                existing_item = item
                break
        
        if existing_item:
            # Update existing item
            existing_item.visit_count += 1
            existing_item.last_visit_time = datetime.now()
            existing_item.transition_type = transition_type
            existing_item.from_url = from_url
            
            self.database.save_history_item(existing_item)
            self.history_updated.emit(existing_item)
            return existing_item.id
        else:
            # Create new history item
            self.counter += 1
            item = HistoryItem(
                id=f"history_{self.counter}_{int(time.time())}",
                url=url,
                title=title,
                visit_time=datetime.now(),
                transition_type=transition_type,
                from_url=from_url,
                session_id=self.session_id
            )
            
            self.history.insert(0, item)
            self.database.save_history_item(item)
            self.history_added.emit(item)
            
            # Limit history size
            if len(self.history) > 1000:
                old_item = self.history.pop()
                self.database.delete_history_item(old_item.id)
            
            return item.id
    
    def update_history_item(self, item: HistoryItem):
        """Update history item."""
        self.database.save_history_item(item)
        
        # Update in list
        for i, existing in enumerate(self.history):
            if existing.id == item.id:
                self.history[i] = item
                break
        
        self.history_updated.emit(item)
    
    def delete_history_item(self, item_id: str):
        """Delete history item."""
        # Remove from list
        self.history = [h for h in self.history if h.id != item_id]
        
        # Remove from database
        self.database.delete_history_item(item_id)
        self.history_deleted.emit(item_id)
    
    def clear_history(self, older_than_days: int = None, all_history: bool = False):
        """Clear history."""
        if all_history:
            self.history.clear()
            self.database.clear_history(all_history=True)
        elif older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            self.history = [h for h in self.history if h.visit_time >= cutoff_date]
            self.database.clear_history(older_than_days=older_than_days)
        
        self.history_cleared.emit()
    
    def search_history(self, query: str, tags: List[str] = None, days: int = None) -> List[HistoryItem]:
        """Search history."""
        return self.database.search_history(query, tags, days)
    
    def get_tags(self) -> List[str]:
        """Get all tags."""
        return self.database.get_tags()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics."""
        return self.database.get_statistics()
    
    def get_recent_history(self, limit: int = 50) -> List[HistoryItem]:
        """Get recent history."""
        return self.history[:limit]
    
    def get_history_by_domain(self, domain: str, limit: int = 100) -> List[HistoryItem]:
        """Get history for specific domain."""
        domain_items = []
        for item in self.history:
            if domain in item.url:
                domain_items.append(item)
                if len(domain_items) >= limit:
                    break
        
        return domain_items
    
    def get_frequent_pages(self, limit: int = 20) -> List[HistoryItem]:
        """Get most frequently visited pages."""
        # Sort by visit count
        sorted_items = sorted(self.history, key=lambda x: x.visit_count, reverse=True)
        return sorted_items[:limit]
    
    def get_history_by_date(self, date: datetime) -> List[HistoryItem]:
        """Get history for specific date."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        date_items = []
        for item in self.history:
            if start_of_day <= item.visit_time < end_of_day:
                date_items.append(item)
        
        return date_items


def show_bookmarks_manager(parent=None):
    """Show bookmarks manager dialog."""
    from .bookmarks_ui import BookmarksManagerDialog
    dialog = BookmarksManagerDialog(parent)
    dialog.show()
    return dialog


def show_history_manager(parent=None):
    """Show history manager dialog."""
    from .history_ui import HistoryManagerDialog
    dialog = HistoryManagerDialog(parent)
    dialog.show()
    return dialog
