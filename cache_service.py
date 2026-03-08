"""
Cache Service

This module handles caching of web resources to improve performance
and reduce network requests.
"""

import hashlib
import gzip
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from ..models import DatabaseManager, CacheEntry


class CacheService:
    """Service for managing web resource caching."""
    
    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        self.db_manager = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache configuration
        self.enabled = config.get('enabled', True)
        self.max_size_mb = config.get('max_size_mb', 500)
        self.cache_duration_hours = config.get('cache_duration_hours', 24)
        self.compress_cache = config.get('compress_cache', True)
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, bytes] = {}
        self.memory_cache_limit = 100  # Number of items to keep in memory
    
    def get_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_cached_content(self, url: str) -> Optional[bytes]:
        """Get cached content for a URL."""
        if not self.enabled:
            return None
        
        try:
            # Check memory cache first
            cache_key = self.get_cache_key(url)
            if cache_key in self.memory_cache:
                self.logger.debug(f"Memory cache hit for: {url}")
                return self.memory_cache[cache_key]
            
            # Check database cache
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content, content_type, expires_at, etag 
                FROM cache 
                WHERE url = ? AND expires_at > ?
            ''', (url, datetime.now()))
            
            row = cursor.fetchone()
            
            if row:
                content = row['content']
                
                # Decompress if needed
                if self.compress_cache and isinstance(content, bytes):
                    try:
                        content = gzip.decompress(content)
                    except:
                        pass  # Content might not be compressed
                
                # Update memory cache
                if len(self.memory_cache) < self.memory_cache_limit:
                    self.memory_cache[cache_key] = content
                
                self.logger.debug(f"Database cache hit for: {url}")
                return content
            
            self.logger.debug(f"Cache miss for: {url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached content for {url}: {e}")
            return None
    
    def cache_content(self, entry: CacheEntry) -> bool:
        """Cache content for a URL."""
        if not self.enabled:
            return False
        
        try:
            # Check cache size limit
            if self._is_cache_full():
                self._cleanup_old_entries()
            
            # Compress content if enabled
            content = entry.content
            if self.compress_cache and isinstance(content, bytes):
                content = gzip.compress(content)
            
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache 
                (url, content, content_type, expires_at, etag, size, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.url,
                content,
                entry.content_type,
                entry.expires_at,
                entry.etag,
                len(content),
                entry.created_at
            ))
            
            conn.commit()
            
            # Update memory cache
            cache_key = self.get_cache_key(entry.url)
            if len(self.memory_cache) < self.memory_cache_limit:
                self.memory_cache[cache_key] = entry.content
            
            self.logger.debug(f"Cached content for: {entry.url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching content for {entry.url}: {e}")
            return False
    
    def is_cached(self, url: str) -> bool:
        """Check if content is cached and not expired."""
        if not self.enabled:
            return False
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM cache 
                WHERE url = ? AND expires_at > ?
            ''', (url, datetime.now()))
            
            row = cursor.fetchone()
            return row['count'] > 0
            
        except Exception as e:
            self.logger.error(f"Error checking if URL is cached: {e}")
            return False
    
    def get_cache_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cache information for a URL."""
        if not self.enabled:
            return None
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT url, content_type, expires_at, etag, size, created_at
                FROM cache 
                WHERE url = ?
            ''', (url,))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'url': row['url'],
                    'content_type': row['content_type'],
                    'expires_at': row['expires_at'],
                    'etag': row['etag'],
                    'size': row['size'],
                    'created_at': row['created_at']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cache info for {url}: {e}")
            return None
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        if not self.enabled:
            return 0
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM cache 
                WHERE expires_at <= ?
            ''', (datetime.now(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            # Clear memory cache of expired items
            expired_keys = []
            for key in self.memory_cache:
                # This is a simplified check - in practice we'd need to track URLs
                pass
            
            self.logger.info(f"Cleaned up {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired cache entries: {e}")
            return 0
    
    def clear_cache(self) -> bool:
        """Clear all cache entries."""
        if not self.enabled:
            return False
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache')
            conn.commit()
            
            # Clear memory cache
            self.memory_cache.clear()
            
            self.logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            # Get total size and count
            cursor.execute('''
                SELECT COUNT(*) as count, COALESCE(SUM(size), 0) as total_size
                FROM cache
            ''')
            
            stats_row = cursor.fetchone()
            
            # Get expired count
            cursor.execute('''
                SELECT COUNT(*) as expired_count
                FROM cache
                WHERE expires_at <= ?
            ''', (datetime.now(),))
            
            expired_row = cursor.fetchone()
            
            return {
                'enabled': True,
                'total_entries': stats_row['count'],
                'total_size_bytes': stats_row['total_size'],
                'total_size_mb': round(stats_row['total_size'] / (1024 * 1024), 2),
                'expired_entries': expired_row['expired_count'],
                'memory_cache_entries': len(self.memory_cache),
                'max_size_mb': self.max_size_mb,
                'usage_percentage': round((stats_row['total_size'] / (1024 * 1024)) / self.max_size_mb * 100, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def _is_cache_full(self) -> bool:
        """Check if cache is over size limit."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COALESCE(SUM(size), 0) as total_size FROM cache')
            row = cursor.fetchone()
            
            total_size_mb = row['total_size'] / (1024 * 1024)
            return total_size_mb >= self.max_size_mb
            
        except Exception as e:
            self.logger.error(f"Error checking cache size: {e}")
            return False
    
    def _cleanup_old_entries(self, target_size_mb: float = None) -> int:
        """Clean up old entries to free space."""
        if target_size_mb is None:
            target_size_mb = self.max_size_mb * 0.8  # Clean up to 80% of max size
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            # Delete oldest entries until under target size
            while True:
                cursor.execute('''
                    SELECT COALESCE(SUM(size), 0) as total_size
                    FROM cache
                ''')
                
                row = cursor.fetchone()
                current_size_mb = row['total_size'] / (1024 * 1024)
                
                if current_size_mb <= target_size_mb:
                    break
                
                # Delete oldest entry
                cursor.execute('''
                    DELETE FROM cache
                    WHERE created_at = (
                        SELECT MIN(created_at) FROM cache
                    )
                    LIMIT 1
                ''')
                
                if cursor.rowcount == 0:
                    break
            
            conn.commit()
            deleted_count = cursor.rowcount
            
            self.logger.info(f"Cleaned up {deleted_count} old cache entries")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old cache entries: {e}")
            return 0
