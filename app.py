"""
Backend Flask Application

This module provides the Flask-based REST API for browser backend services,
including endpoints for bookmarks, history, preferences, and caching.
"""

import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from typing import Dict, Any

from .models import DatabaseManager, Bookmark, HistoryEntry, UserPreference, CacheEntry
from .services.cache_service import CacheService
from .services.session_service import SessionService
from .services.bookmark_service import BookmarkService
from .services.history_service import HistoryService
from .services.security_service import SecurityService


class BackendApp:
    """Main backend application class."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.app = None
        self.server_thread = None
        self.running = False
        
        # Initialize database
        db_config = config.get('database', {})
        self.db_path = db_config.get('path', 'browser_data.db')
        self.db_manager = DatabaseManager(self.db_path)
        
        # Initialize services
        self.cache_service = CacheService(self.db_manager, config.get('cache', {}))
        self.session_service = SessionService(self.db_manager)
        self.bookmark_service = BookmarkService(self.db_manager)
        self.history_service = HistoryService(self.db_manager)
        self.security_service = SecurityService(config.get('security', {}))
        
        self._setup_flask_app()
    
    def _setup_flask_app(self):
        """Setup Flask application and routes."""
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config['JSON_SORT_KEYS'] = False
        
        # Register routes
        self._register_bookmark_routes()
        self._register_history_routes()
        self._register_preference_routes()
        self._register_cache_routes()
        self._register_session_routes()
        self._register_security_routes()
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal server error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def _register_bookmark_routes(self):
        """Register bookmark-related routes."""
        
        @self.app.route('/api/bookmarks', methods=['GET'])
        def get_bookmarks():
            """Get all bookmarks."""
            try:
                folder = request.args.get('folder')
                bookmarks = self.bookmark_service.get_bookmarks(folder)
                return jsonify([{
                    'id': b.id,
                    'title': b.title,
                    'url': b.url,
                    'folder': b.folder,
                    'tags': b.tags,
                    'favicon': b.favicon,
                    'created_at': b.created_at.isoformat() if b.created_at else None,
                    'last_visited': b.last_visited.isoformat() if b.last_visited else None
                } for b in bookmarks])
            except Exception as e:
                self.logger.error(f"Error getting bookmarks: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/bookmarks', methods=['POST'])
        def add_bookmark():
            """Add a new bookmark."""
            try:
                data = request.get_json()
                bookmark = Bookmark(
                    title=data.get('title', ''),
                    url=data.get('url', ''),
                    folder=data.get('folder', 'Default'),
                    tags=data.get('tags', []),
                    favicon=data.get('favicon', '')
                )
                bookmark_id = self.bookmark_service.add_bookmark(bookmark)
                return jsonify({'id': bookmark_id, 'message': 'Bookmark added successfully'})
            except Exception as e:
                self.logger.error(f"Error adding bookmark: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
        def delete_bookmark(bookmark_id):
            """Delete a bookmark."""
            try:
                success = self.bookmark_service.delete_bookmark(bookmark_id)
                if success:
                    return jsonify({'message': 'Bookmark deleted successfully'})
                else:
                    return jsonify({'error': 'Bookmark not found'}), 404
            except Exception as e:
                self.logger.error(f"Error deleting bookmark: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _register_history_routes(self):
        """Register history-related routes."""
        
        @self.app.route('/api/history', methods=['GET'])
        def get_history():
            """Get browsing history."""
            try:
                limit = request.args.get('limit', 100, type=int)
                history = self.history_service.get_history(limit)
                return jsonify([{
                    'id': h.id,
                    'url': h.url,
                    'title': h.title,
                    'visit_count': h.visit_count,
                    'last_visited': h.last_visited.isoformat() if h.last_visited else None,
                    'favicon': h.favicon,
                    'session_id': h.session_id
                } for h in history])
            except Exception as e:
                self.logger.error(f"Error getting history: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/history', methods=['POST'])
        def add_history_entry():
            """Add a history entry."""
            try:
                data = request.get_json()
                entry = HistoryEntry(
                    url=data.get('url', ''),
                    title=data.get('title', ''),
                    favicon=data.get('favicon', ''),
                    session_id=data.get('session_id')
                )
                entry_id = self.history_service.add_history_entry(entry)
                return jsonify({'id': entry_id, 'message': 'History entry added successfully'})
            except Exception as e:
                self.logger.error(f"Error adding history entry: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/history', methods=['DELETE'])
        def clear_history():
            """Clear browsing history."""
            try:
                success = self.history_service.clear_history()
                return jsonify({'message': 'History cleared successfully'})
            except Exception as e:
                self.logger.error(f"Error clearing history: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _register_preference_routes(self):
        """Register preference-related routes."""
        
        @self.app.route('/api/preferences', methods=['GET'])
        def get_preferences():
            """Get all user preferences."""
            try:
                preferences = self.db_manager.get_all_preferences()
                return jsonify(preferences)
            except Exception as e:
                self.logger.error(f"Error getting preferences: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/preferences/<key>', methods=['GET'])
        def get_preference(key):
            """Get a specific preference."""
            try:
                preference = self.db_manager.get_preference(key)
                if preference:
                    return jsonify({
                        'key': preference.key,
                        'value': preference.value,
                        'category': preference.category,
                        'updated_at': preference.updated_at.isoformat() if preference.updated_at else None
                    })
                else:
                    return jsonify({'error': 'Preference not found'}), 404
            except Exception as e:
                self.logger.error(f"Error getting preference: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/preferences/<key>', methods=['PUT'])
        def set_preference(key):
            """Set a preference."""
            try:
                data = request.get_json()
                preference = UserPreference(
                    key=key,
                    value=data.get('value'),
                    category=data.get('category', 'general')
                )
                success = self.db_manager.set_preference(preference)
                if success:
                    return jsonify({'message': 'Preference set successfully'})
                else:
                    return jsonify({'error': 'Failed to set preference'}), 500
            except Exception as e:
                self.logger.error(f"Error setting preference: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _register_cache_routes(self):
        """Register cache-related routes."""
        
        @self.app.route('/api/cache/<path:url>', methods=['GET'])
        def get_cached_content(url):
            """Get cached content for a URL."""
            try:
                content = self.cache_service.get_cached_content(url)
                if content:
                    return content
                else:
                    return jsonify({'error': 'Content not found in cache'}), 404
            except Exception as e:
                self.logger.error(f"Error getting cached content: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/cache/<path:url>', methods=['PUT'])
        def cache_content(url):
            """Cache content for a URL."""
            try:
                data = request.get_json()
                entry = CacheEntry(
                    url=url,
                    content=data.get('content', b''),
                    content_type=data.get('content_type', 'text/html'),
                    expires_at=data.get('expires_at')
                )
                success = self.cache_service.cache_content(entry)
                if success:
                    return jsonify({'message': 'Content cached successfully'})
                else:
                    return jsonify({'error': 'Failed to cache content'}), 500
            except Exception as e:
                self.logger.error(f"Error caching content: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/cache/cleanup', methods=['POST'])
        def cleanup_cache():
            """Clean up expired cache entries."""
            try:
                cleaned = self.cache_service.cleanup_expired()
                return jsonify({'message': f'Cleaned {cleaned} expired cache entries'})
            except Exception as e:
                self.logger.error(f"Error cleaning up cache: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _register_session_routes(self):
        """Register session-related routes."""
        
        @self.app.route('/api/sessions', methods=['GET'])
        def get_sessions():
            """Get all sessions."""
            try:
                sessions = self.session_service.get_sessions()
                return jsonify([{
                    'session_id': s.session_id,
                    'name': s.name,
                    'tabs': s.tabs,
                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    'last_accessed': s.last_accessed.isoformat() if s.last_accessed else None
                } for s in sessions])
            except Exception as e:
                self.logger.error(f"Error getting sessions: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/sessions', methods=['POST'])
        def save_session():
            """Save a session."""
            try:
                data = request.get_json()
                session_id = self.session_service.save_session(
                    name=data.get('name', ''),
                    tabs=data.get('tabs', [])
                )
                return jsonify({'session_id': session_id, 'message': 'Session saved successfully'})
            except Exception as e:
                self.logger.error(f"Error saving session: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/sessions/<session_id>', methods=['DELETE'])
        def delete_session(session_id):
            """Delete a session."""
            try:
                success = self.session_service.delete_session(session_id)
                if success:
                    return jsonify({'message': 'Session deleted successfully'})
                else:
                    return jsonify({'error': 'Session not found'}), 404
            except Exception as e:
                self.logger.error(f"Error deleting session: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _register_security_routes(self):
        """Register security-related routes."""
        
        @self.app.route('/api/security/check-url', methods=['POST'])
        def check_url_security():
            """Check if a URL is safe."""
            try:
                data = request.get_json()
                url = data.get('url', '')
                is_safe = self.security_service.is_url_safe(url)
                return jsonify({'safe': is_safe})
            except Exception as e:
                self.logger.error(f"Error checking URL security: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/security/blocklist', methods=['GET'])
        def get_blocklist():
            """Get the current blocklist."""
            try:
                blocklist = self.security_service.get_blocklist()
                return jsonify({'blocklist': blocklist})
            except Exception as e:
                self.logger.error(f"Error getting blocklist: {e}")
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """Start the backend server."""
        if not self.running:
            self.running = True
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            self.logger.info("Backend server started")
    
    def _run_server(self):
        """Run the Flask server."""
        self.app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False
        )
    
    def stop(self):
        """Stop the backend server."""
        if self.running:
            self.running = False
            if self.server_thread:
                self.server_thread.join(timeout=5)
            self.db_manager.close()
            self.logger.info("Backend server stopped")
