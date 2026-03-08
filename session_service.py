"""
Session Service

This module manages browsing sessions, including saving and restoring
tab states and session data.
"""

import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from ..models import DatabaseManager, Session


class SessionService:
    """Service for managing browsing sessions."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_session(self, name: str = None, tabs: List[Dict[str, Any]] = None) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        
        if name is None:
            name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if tabs is None:
            tabs = []
        
        session = Session(
            session_id=session_id,
            name=name,
            tabs=tabs
        )
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (session_id, name, tabs, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.name,
                json.dumps(session.tabs),
                session.created_at,
                session.last_accessed
            ))
            
            conn.commit()
            self.logger.info(f"Created session: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            raise
    
    def save_session(self, name: str, tabs: List[Dict[str, Any]], session_id: str = None) -> str:
        """Save a session with current tabs."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = Session(
            session_id=session_id,
            name=name,
            tabs=tabs
        )
        
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (session_id, name, tabs, last_accessed)
                VALUES (?, ?, ?, ?)
            ''', (
                session.session_id,
                session.name,
                json.dumps(session.tabs),
                session.last_accessed
            ))
            
            conn.commit()
            self.logger.info(f"Saved session: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                return Session(
                    session_id=row['session_id'],
                    name=row['name'],
                    tabs=json.loads(row['tabs']) if row['tabs'] else [],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def get_sessions(self) -> List[Session]:
        """Get all sessions."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions 
                ORDER BY last_accessed DESC
            ''')
            
            sessions = []
            for row in cursor.fetchall():
                session = Session(
                    session_id=row['session_id'],
                    name=row['name'],
                    tabs=json.loads(row['tabs']) if row['tabs'] else [],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None
                )
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error getting sessions: {e}")
            return []
    
    def update_session_access(self, session_id: str) -> bool:
        """Update the last accessed time for a session."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions 
                SET last_accessed = ?
                WHERE session_id = ?
            ''', (datetime.now(), session_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error updating session access: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"Deleted session: {session_id}")
            else:
                self.logger.warning(f"Session not found for deletion: {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def get_recent_sessions(self, limit: int = 10) -> List[Session]:
        """Get recently accessed sessions."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions 
                ORDER BY last_accessed DESC 
                LIMIT ?
            ''', (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                session = Session(
                    session_id=row['session_id'],
                    name=row['name'],
                    tabs=json.loads(row['tabs']) if row['tabs'] else [],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None
                )
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error getting recent sessions: {e}")
            return []
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old sessions."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            cursor.execute('''
                DELETE FROM sessions 
                WHERE last_accessed < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            self.logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0
    
    def export_session(self, session_id: str, file_path: str) -> bool:
        """Export a session to a file."""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            session_data = {
                'session_id': session.session_id,
                'name': session.name,
                'tabs': session.tabs,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'last_accessed': session.last_accessed.isoformat() if session.last_accessed else None,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.info(f"Exported session {session_id} to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting session {session_id}: {e}")
            return False
    
    def import_session(self, file_path: str) -> Optional[str]:
        """Import a session from a file."""
        try:
            with open(file_path, 'r') as f:
                session_data = json.load(f)
            
            # Create new session with imported data
            session_id = self.save_session(
                name=session_data.get('name', 'Imported Session'),
                tabs=session_data.get('tabs', [])
            )
            
            self.logger.info(f"Imported session from {file_path}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error importing session from {file_path}: {e}")
            return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute('SELECT COUNT(*) as total FROM sessions')
            total_sessions = cursor.fetchone()['total']
            
            # Sessions with tabs
            cursor.execute('''
                SELECT COUNT(*) as with_tabs 
                FROM sessions 
                WHERE json_array_length(tabs) > 0
            ''')
            sessions_with_tabs = cursor.fetchone()['with_tabs']
            
            # Average tabs per session
            cursor.execute('''
                SELECT AVG(json_array_length(tabs)) as avg_tabs
                FROM sessions
                WHERE json_array_length(tabs) > 0
            ''')
            avg_tabs_result = cursor.fetchone()
            avg_tabs = avg_tabs_result['avg_tabs'] if avg_tabs_result['avg_tabs'] else 0
            
            return {
                'total_sessions': total_sessions,
                'sessions_with_tabs': sessions_with_tabs,
                'average_tabs_per_session': round(avg_tabs, 2),
                'empty_sessions': total_sessions - sessions_with_tabs
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session stats: {e}")
            return {'error': str(e)}
