"""
Backend Tests

This module contains tests for the backend services,
including API endpoints, database operations, and services.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import DatabaseManager, Bookmark, HistoryEntry, UserPreference
from backend.services.cache_service import CacheService
from backend.services.session_service import SessionService
from backend.services.bookmark_service import BookmarkService
from backend.services.history_service import HistoryService
from backend.services.security_service import SecurityService


class TestDatabaseManager(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_add_bookmark(self):
        """Test adding a bookmark."""
        bookmark = Bookmark(
            title="Test Bookmark",
            url="https://example.com",
            folder="Test"
        )
        
        bookmark_id = self.db_manager.add_bookmark(bookmark)
        self.assertIsInstance(bookmark_id, int)
        self.assertGreater(bookmark_id, 0)
    
    def test_get_bookmarks(self):
        """Test retrieving bookmarks."""
        # Add test bookmark
        bookmark = Bookmark(
            title="Test Bookmark",
            url="https://example.com",
            folder="Test"
        )
        self.db_manager.add_bookmark(bookmark)
        
        # Retrieve bookmarks
        bookmarks = self.db_manager.get_bookmarks()
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].title, "Test Bookmark")
    
    def test_add_history_entry(self):
        """Test adding a history entry."""
        entry = HistoryEntry(
            url="https://example.com",
            title="Example Site"
        )
        
        entry_id = self.db_manager.add_history_entry(entry)
        self.assertIsInstance(entry_id, int)
        self.assertGreater(entry_id, 0)
    
    def test_get_history(self):
        """Test retrieving history."""
        # Add test entry
        entry = HistoryEntry(
            url="https://example.com",
            title="Example Site"
        )
        self.db_manager.add_history_entry(entry)
        
        # Retrieve history
        history = self.db_manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].url, "https://example.com")
    
    def test_set_preference(self):
        """Test setting a preference."""
        preference = UserPreference(
            key="test.key",
            value="test_value",
            category="test"
        )
        
        success = self.db_manager.set_preference(preference)
        self.assertTrue(success)
    
    def test_get_preference(self):
        """Test retrieving a preference."""
        # Set preference
        preference = UserPreference(
            key="test.key",
            value="test_value",
            category="test"
        )
        self.db_manager.set_preference(preference)
        
        # Retrieve preference
        retrieved = self.db_manager.get_preference("test.key")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.value, "test_value")


class TestCacheService(unittest.TestCase):
    """Test cache service."""
    
    def setUp(self):
        """Set up test cache service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        
        config = {
            'enabled': True,
            'max_size_mb': 100,
            'cache_duration_hours': 24,
            'compress_cache': True
        }
        self.cache_service = CacheService(self.db_manager, config)
    
    def tearDown(self):
        """Clean up test cache service."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_cache_content(self):
        """Test caching content."""
        from datetime import datetime, timedelta
        
        entry = {
            'url': 'https://example.com',
            'content': b'<html>Test content</html>',
            'content_type': 'text/html',
            'expires_at': datetime.now() + timedelta(hours=1)
        }
        
        # Cache content
        success = self.cache_service.cache_content(entry)
        self.assertTrue(success)
        
        # Retrieve cached content
        cached_content = self.cache_service.get_cached_content('https://example.com')
        self.assertIsNotNone(cached_content)
        self.assertEqual(cached_content, b'<html>Test content</html>')
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        from datetime import datetime, timedelta
        
        # Cache expired content
        entry = {
            'url': 'https://example.com',
            'content': b'<html>Expired content</html>',
            'content_type': 'text/html',
            'expires_at': datetime.now() - timedelta(hours=1)
        }
        
        self.cache_service.cache_content(entry)
        
        # Try to retrieve expired content
        cached_content = self.cache_service.get_cached_content('https://example.com')
        self.assertIsNone(cached_content)
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        from datetime import datetime, timedelta
        
        # Add expired entry
        expired_entry = {
            'url': 'https://expired.com',
            'content': b'<html>Expired</html>',
            'content_type': 'text/html',
            'expires_at': datetime.now() - timedelta(hours=1)
        }
        
        # Add valid entry
        valid_entry = {
            'url': 'https://valid.com',
            'content': b'<html>Valid</html>',
            'content_type': 'text/html',
            'expires_at': datetime.now() + timedelta(hours=1)
        }
        
        self.cache_service.cache_content(expired_entry)
        self.cache_service.cache_content(valid_entry)
        
        # Cleanup expired entries
        cleaned = self.cache_service.cleanup_expired()
        self.assertGreater(cleaned, 0)
        
        # Verify expired entry is gone, valid entry remains
        expired_content = self.cache_service.get_cached_content('https://expired.com')
        valid_content = self.cache_service.get_cached_content('https://valid.com')
        
        self.assertIsNone(expired_content)
        self.assertIsNotNone(valid_content)


class TestSessionService(unittest.TestCase):
    """Test session service."""
    
    def setUp(self):
        """Set up test session service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.session_service = SessionService(self.db_manager)
    
    def tearDown(self):
        """Clean up test session service."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_create_session(self):
        """Test creating a session."""
        session_id = self.session_service.create_session("Test Session")
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, str)
    
    def test_save_session(self):
        """Test saving a session."""
        tabs = [
            {'url': 'https://example.com', 'title': 'Example'},
            {'url': 'https://test.com', 'title': 'Test'}
        ]
        
        session_id = self.session_service.save_session("Test Session", tabs)
        self.assertIsNotNone(session_id)
        
        # Retrieve session
        session = self.session_service.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.name, "Test Session")
        self.assertEqual(len(session.tabs), 2)
    
    def test_get_sessions(self):
        """Test retrieving all sessions."""
        # Create test sessions
        self.session_service.create_session("Session 1")
        self.session_service.create_session("Session 2")
        
        # Retrieve sessions
        sessions = self.session_service.get_sessions()
        self.assertEqual(len(sessions), 2)
    
    def test_delete_session(self):
        """Test deleting a session."""
        session_id = self.session_service.create_session("Test Session")
        
        # Delete session
        success = self.session_service.delete_session(session_id)
        self.assertTrue(success)
        
        # Verify session is deleted
        session = self.session_service.get_session(session_id)
        self.assertIsNone(session)


class TestBookmarkService(unittest.TestCase):
    """Test bookmark service."""
    
    def setUp(self):
        """Set up test bookmark service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.bookmark_service = BookmarkService(self.db_manager)
    
    def tearDown(self):
        """Clean up test bookmark service."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_add_bookmark(self):
        """Test adding a bookmark."""
        bookmark_data = {
            'title': 'Test Bookmark',
            'url': 'https://example.com',
            'folder': 'Test'
        }
        
        bookmark_id = self.bookmark_service.add_bookmark(Bookmark(**bookmark_data))
        self.assertIsInstance(bookmark_id, int)
        self.assertGreater(bookmark_id, 0)
    
    def test_search_bookmarks(self):
        """Test searching bookmarks."""
        # Add test bookmarks
        self.bookmark_service.add_bookmark(Bookmark(
            title='Python Tutorial',
            url='https://python.org',
            folder='Programming'
        ))
        
        self.bookmark_service.add_bookmark(Bookmark(
            title='JavaScript Guide',
            url='https://javascript.info',
            folder='Programming'
        ))
        
        # Search for 'Python'
        results = self.bookmark_service.search_bookmarks('Python')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Python Tutorial')
    
    def test_get_folders(self):
        """Test getting bookmark folders."""
        # Add bookmarks in different folders
        self.bookmark_service.add_bookmark(Bookmark(
            title='Site 1',
            url='https://site1.com',
            folder='Folder A'
        ))
        
        self.bookmark_service.add_bookmark(Bookmark(
            title='Site 2',
            url='https://site2.com',
            folder='Folder B'
        ))
        
        # Get folders
        folders = self.bookmark_service.get_folders()
        self.assertEqual(len(folders), 2)
        self.assertIn('Folder A', folders)
        self.assertIn('Folder B', folders)


class TestHistoryService(unittest.TestCase):
    """Test history service."""
    
    def setUp(self):
        """Set up test history service."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.history_service = HistoryService(self.db_manager)
    
    def tearDown(self):
        """Clean up test history service."""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_add_history_entry(self):
        """Test adding a history entry."""
        entry = HistoryEntry(
            url='https://example.com',
            title='Example Site'
        )
        
        entry_id = self.history_service.add_history_entry(entry)
        self.assertIsInstance(entry_id, int)
        self.assertGreater(entry_id, 0)
    
    def test_search_history(self):
        """Test searching history."""
        # Add test entries
        self.history_service.add_history_entry(HistoryEntry(
            url='https://python.org',
            title='Python Documentation'
        ))
        
        self.history_service.add_history_entry(HistoryEntry(
            url='https://javascript.info',
            title='JavaScript Tutorial'
        ))
        
        # Search for 'Python'
        results = self.history_service.search_history('Python')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Python Documentation')
    
    def test_get_most_visited_sites(self):
        """Test getting most visited sites."""
        # Add entries with different visit counts
        entry1 = HistoryEntry(
            url='https://popular.com',
            title='Popular Site',
            visit_count=10
        )
        
        entry2 = HistoryEntry(
            url='https://unpopular.com',
            title='Unpopular Site',
            visit_count=2
        )
        
        self.history_service.add_history_entry(entry1)
        self.history_service.add_history_entry(entry2)
        
        # Get most visited
        most_visited = self.history_service.get_most_visited_sites(5)
        self.assertEqual(len(most_visited), 2)
        self.assertEqual(most_visited[0].url, 'https://popular.com')
        self.assertEqual(most_visited[0].visit_count, 10)


class TestSecurityService(unittest.TestCase):
    """Test security service."""
    
    def setUp(self):
        """Set up test security service."""
        config = {
            'enable_ad_blocker': True,
            'enforce_https': True,
            'block_trackers': True,
            'block_malicious_domains': True
        }
        self.security_service = SecurityService(config)
    
    def test_url_validation(self):
        """Test URL validation."""
        # Test valid URLs
        self.assertTrue(self.security_service.is_url_safe('https://example.com'))
        self.assertTrue(self.security_service.is_url_safe('https://google.com'))
        
        # Test HTTP URLs (should be blocked if HTTPS enforcement is enabled)
        self.assertFalse(self.security_service.is_url_safe('http://example.com'))
        
        # Test localhost (should be allowed)
        self.assertTrue(self.security_service.is_url_safe('http://localhost:8000'))
    
    def test_request_blocking(self):
        """Test request blocking."""
        # Test ad blocking
        blocked = self.security_service.should_block_request(
            'https://doubleclick.net/ad',
            'script'
        )
        self.assertTrue(blocked)
        
        # Test tracker blocking
        blocked = self.security_service.should_block_request(
            'https://google-analytics.com/collect',
            'script'
        )
        self.assertTrue(blocked)
        
        # Test safe request
        blocked = self.security_service.should_block_request(
            'https://example.com/page',
            'document'
        )
        self.assertFalse(blocked)
    
    def test_url_sanitization(self):
        """Test URL sanitization."""
        # Test HTTPS upgrade
        sanitized = self.security_service.sanitize_url('http://example.com')
        self.assertEqual(sanitized, 'https://example.com')
        
        # Test tracking parameter removal
        sanitized = self.security_service.sanitize_url(
            'https://example.com/page?utm_source=google&utm_medium=cpc'
        )
        self.assertNotIn('utm_source', sanitized)
        self.assertNotIn('utm_medium', sanitized)
    
    def test_security_report(self):
        """Test security report generation."""
        report = self.security_service.get_security_report('https://example.com')
        
        self.assertIn('url', report)
        self.assertIn('safe', report)
        self.assertIn('warnings', report)
        self.assertIn('recommendations', report)


if __name__ == '__main__':
    unittest.main()
