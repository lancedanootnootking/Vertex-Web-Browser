"""
History Service

This module manages browsing history, including adding entries,
searching, and maintaining history data.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from ..models import DatabaseManager, HistoryEntry


class HistoryService:
    """Service for managing browsing history."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def add_history_entry(self, entry: HistoryEntry) -> int:
        """Add or update a history entry."""
        try:
            entry_id = self.db_manager.add_history_entry(entry)
            self.logger.debug(f"Added history entry: {entry.url}")
            return entry_id
        except Exception as e:
            self.logger.error(f"Error adding history entry: {e}")
            raise
    
    def get_history(self, limit: int = 100, offset: int = 0) -> List[HistoryEntry]:
        """Get browsing history with pagination."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM history 
                ORDER BY last_visited DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
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
            
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return []
    
    def search_history(self, query: str, limit: int = 50) -> List[HistoryEntry]:
        """Search history by title or URL."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM history 
                WHERE title LIKE ? OR url LIKE ?
                ORDER BY last_visited DESC 
                LIMIT ?
            ''', (search_term, search_term, limit))
            
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
            
        except Exception as e:
            self.logger.error(f"Error searching history: {e}")
            return []
    
    def get_history_by_date_range(self, start_date: datetime, end_date: datetime) -> List[HistoryEntry]:
        """Get history entries within a date range."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM history 
                WHERE last_visited >= ? AND last_visited <= ?
                ORDER BY last_visited DESC
            ''', (start_date, end_date))
            
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
            
        except Exception as e:
            self.logger.error(f"Error getting history by date range: {e}")
            return []
    
    def get_most_visited_sites(self, limit: int = 20) -> List[HistoryEntry]:
        """Get most visited sites."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM history 
                ORDER BY visit_count DESC, last_visited DESC 
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
            
        except Exception as e:
            self.logger.error(f"Error getting most visited sites: {e}")
            return []
    
    def get_recent_history(self, hours: int = 24) -> List[HistoryEntry]:
        """Get history from the last N hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return self.get_history_by_date_range(cutoff_time, datetime.now())
        except Exception as e:
            self.logger.error(f"Error getting recent history: {e}")
            return []
    
    def get_history_for_domain(self, domain: str) -> List[HistoryEntry]:
        """Get history entries for a specific domain."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            domain_pattern = f"%{domain}%"
            cursor.execute('''
                SELECT * FROM history 
                WHERE url LIKE ?
                ORDER BY last_visited DESC
            ''', (domain_pattern,))
            
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
            
        except Exception as e:
            self.logger.error(f"Error getting history for domain {domain}: {e}")
            return []
    
    def delete_history_entry(self, entry_id: int) -> bool:
        """Delete a specific history entry."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM history WHERE id = ?', (entry_id,))
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"Deleted history entry {entry_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting history entry {entry_id}: {e}")
            return False
    
    def delete_history_for_url(self, url: str) -> bool:
        """Delete all history entries for a specific URL."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM history WHERE url = ?', (url,))
            conn.commit()
            
            deleted_count = cursor.rowcount
            self.logger.info(f"Deleted {deleted_count} history entries for {url}")
            return deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting history for URL {url}: {e}")
            return False
    
    def delete_history_for_domain(self, domain: str) -> bool:
        """Delete all history entries for a specific domain."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            domain_pattern = f"%{domain}%"
            cursor.execute('DELETE FROM history WHERE url LIKE ?', (domain_pattern,))
            conn.commit()
            
            deleted_count = cursor.rowcount
            self.logger.info(f"Deleted {deleted_count} history entries for domain {domain}")
            return deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting history for domain {domain}: {e}")
            return False
    
    def delete_history_by_date_range(self, start_date: datetime, end_date: datetime) -> int:
        """Delete history entries within a date range."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM history 
                WHERE last_visited >= ? AND last_visited <= ?
            ''', (start_date, end_date))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            self.logger.info(f"Deleted {deleted_count} history entries from date range")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting history by date range: {e}")
            return 0
    
    def clear_history(self) -> bool:
        """Clear all browsing history."""
        try:
            success = self.db_manager.clear_history()
            if success:
                self.logger.info("Cleared all browsing history")
            return success
        except Exception as e:
            self.logger.error(f"Error clearing history: {e}")
            return False
    
    def get_history_stats(self) -> Dict[str, Any]:
        """Get history statistics."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute('SELECT COUNT(*) as total FROM history')
            total_entries = cursor.fetchone()['total']
            
            # Entries in last 24 hours
            yesterday = datetime.now() - timedelta(hours=24)
            cursor.execute('SELECT COUNT(*) as recent FROM history WHERE last_visited >= ?', (yesterday,))
            recent_entries = cursor.fetchone()['recent']
            
            # Most visited domains
            cursor.execute('''
                SELECT 
                    SUBSTR(url, 1, 
                        CASE 
                            WHEN url LIKE 'https://%' THEN INSTR(SUBSTR(url, 9), '/') + 8
                            WHEN url LIKE 'http://%' THEN INSTR(SUBSTR(url, 8), '/') + 7
                            ELSE LENGTH(url)
                        END
                    ) as domain,
                    COUNT(*) as visits,
                    SUM(visit_count) as total_visits
                FROM history 
                GROUP BY domain
                ORDER BY total_visits DESC
                LIMIT 10
            ''')
            
            top_domains = []
            for row in cursor.fetchall():
                top_domains.append({
                    'domain': row['domain'],
                    'unique_visits': row['visits'],
                    'total_visits': row['total_visits']
                })
            
            return {
                'total_entries': total_entries,
                'recent_entries_24h': recent_entries,
                'top_domains': top_domains,
                'average_visits_per_site': total_entries / len(top_domains) if top_domains else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting history stats: {e}")
            return {'error': str(e)}
    
    def export_history(self, file_path: str, format: str = 'json') -> bool:
        """Export history to a file."""
        try:
            history = self.get_history(limit=10000)  # Export up to 10k entries
            
            if format.lower() == 'json':
                export_data = {
                    'exported_at': datetime.now().isoformat(),
                    'history': [
                        {
                            'url': h.url,
                            'title': h.title,
                            'visit_count': h.visit_count,
                            'last_visited': h.last_visited.isoformat() if h.last_visited else None,
                            'favicon': h.favicon,
                            'session_id': h.session_id
                        }
                        for h in history
                    ]
                }
                
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            elif format.lower() == 'csv':
                import csv
                
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['URL', 'Title', 'Visit Count', 'Last Visited', 'Favicon', 'Session ID'])
                    
                    for h in history:
                        writer.writerow([
                            h.url,
                            h.title,
                            h.visit_count,
                            h.last_visited.isoformat() if h.last_visited else '',
                            h.favicon,
                            h.session_id or ''
                        ])
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Exported {len(history)} history entries to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting history: {e}")
            return False
    
    def get_suggestions_from_history(self, query: str, limit: int = 10) -> List[str]:
        """Get URL suggestions from history based on query."""
        try:
            if not query:
                # Return most visited sites if no query
                most_visited = self.get_most_visited_sites(limit)
                return [h.url for h in most_visited]
            
            # Search for matching URLs
            matching_history = self.search_history(query, limit)
            return [h.url for h in matching_history]
            
        except Exception as e:
            self.logger.error(f"Error getting suggestions from history: {e}")
            return []
    
    def cleanup_old_history(self, days_old: int = 90) -> int:
        """Clean up old history entries."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = self.delete_history_by_date_range(
                datetime.min, cutoff_date
            )
            
            self.logger.info(f"Cleaned up {deleted_count} old history entries")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old history: {e}")
            return 0
