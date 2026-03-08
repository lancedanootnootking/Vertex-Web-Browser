"""
Bookmark Service

This module manages bookmark operations, including adding, organizing,
and searching bookmarks.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from ..models import DatabaseManager, Bookmark


class BookmarkService:
    """Service for managing bookmarks."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def add_bookmark(self, bookmark: Bookmark) -> int:
        """Add a new bookmark."""
        try:
            bookmark_id = self.db_manager.add_bookmark(bookmark)
            self.logger.info(f"Added bookmark: {bookmark.url}")
            return bookmark_id
        except Exception as e:
            self.logger.error(f"Error adding bookmark: {e}")
            raise
    
    def get_bookmarks(self, folder: str = None, tags: List[str] = None) -> List[Bookmark]:
        """Get bookmarks, optionally filtered by folder and/or tags."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            query = "SELECT * FROM bookmarks"
            params = []
            
            if folder or tags:
                conditions = []
                if folder:
                    conditions.append("folder = ?")
                    params.append(folder)
                
                if tags:
                    # This is a simplified tag search - in practice you'd want better tag handling
                    for tag in tags:
                        conditions.append("tags LIKE ?")
                        params.append(f'%"{tag}"%')
                
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY title"
            
            cursor.execute(query, params)
            
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
            
        except Exception as e:
            self.logger.error(f"Error getting bookmarks: {e}")
            return []
    
    def get_bookmark(self, bookmark_id: int) -> Optional[Bookmark]:
        """Get a specific bookmark."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
            row = cursor.fetchone()
            
            if row:
                return Bookmark(
                    id=row['id'],
                    title=row['title'],
                    url=row['url'],
                    folder=row['folder'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    favicon=row['favicon'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_visited=datetime.fromisoformat(row['last_visited']) if row['last_visited'] else None
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting bookmark {bookmark_id}: {e}")
            return None
    
    def update_bookmark(self, bookmark_id: int, updates: Dict[str, Any]) -> bool:
        """Update a bookmark."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ['title', 'url', 'folder', 'favicon']:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
                elif field == 'tags':
                    set_clauses.append("tags = ?")
                    params.append(json.dumps(value))
                elif field == 'last_visited':
                    set_clauses.append("last_visited = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            params.append(bookmark_id)
            
            query = f"UPDATE bookmarks SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"Updated bookmark {bookmark_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating bookmark {bookmark_id}: {e}")
            return False
    
    def delete_bookmark(self, bookmark_id: int) -> bool:
        """Delete a bookmark."""
        try:
            success = self.db_manager.delete_bookmark(bookmark_id)
            if success:
                self.logger.info(f"Deleted bookmark {bookmark_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error deleting bookmark {bookmark_id}: {e}")
            return False
    
    def search_bookmarks(self, query: str) -> List[Bookmark]:
        """Search bookmarks by title, URL, or tags."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM bookmarks 
                WHERE title LIKE ? OR url LIKE ? OR tags LIKE ?
                ORDER BY title
            ''', (search_term, search_term, search_term))
            
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
            
        except Exception as e:
            self.logger.error(f"Error searching bookmarks: {e}")
            return []
    
    def get_folders(self) -> List[str]:
        """Get all bookmark folders."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT folder FROM bookmarks ORDER BY folder')
            folders = [row['folder'] for row in cursor.fetchall()]
            return folders
            
        except Exception as e:
            self.logger.error(f"Error getting folders: {e}")
            return []
    
    def get_tags(self) -> List[str]:
        """Get all bookmark tags."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('SELECT tags FROM bookmarks WHERE tags IS NOT NULL')
            
            all_tags = set()
            for row in cursor.fetchall():
                tags = json.loads(row['tags']) if row['tags'] else []
                all_tags.update(tags)
            
            return sorted(list(all_tags))
            
        except Exception as e:
            self.logger.error(f"Error getting tags: {e}")
            return []
    
    def move_bookmark(self, bookmark_id: int, new_folder: str) -> bool:
        """Move a bookmark to a different folder."""
        return self.update_bookmark(bookmark_id, {'folder': new_folder})
    
    def add_tag(self, bookmark_id: int, tag: str) -> bool:
        """Add a tag to a bookmark."""
        try:
            bookmark = self.get_bookmark(bookmark_id)
            if not bookmark:
                return False
            
            if tag not in bookmark.tags:
                bookmark.tags.append(tag)
                return self.update_bookmark(bookmark_id, {'tags': bookmark.tags})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding tag to bookmark {bookmark_id}: {e}")
            return False
    
    def remove_tag(self, bookmark_id: int, tag: str) -> bool:
        """Remove a tag from a bookmark."""
        try:
            bookmark = self.get_bookmark(bookmark_id)
            if not bookmark:
                return False
            
            if tag in bookmark.tags:
                bookmark.tags.remove(tag)
                return self.update_bookmark(bookmark_id, {'tags': bookmark.tags})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing tag from bookmark {bookmark_id}: {e}")
            return False
    
    def get_recent_bookmarks(self, limit: int = 10) -> List[Bookmark]:
        """Get recently added bookmarks."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM bookmarks 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
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
            
        except Exception as e:
            self.logger.error(f"Error getting recent bookmarks: {e}")
            return []
    
    def get_most_visited_bookmarks(self, limit: int = 10) -> List[Bookmark]:
        """Get most visited bookmarks (based on last_visited frequency)."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM bookmarks 
                WHERE last_visited IS NOT NULL
                ORDER BY last_visited DESC 
                LIMIT ?
            ''', (limit,))
            
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
            
        except Exception as e:
            self.logger.error(f"Error getting most visited bookmarks: {e}")
            return []
    
    def export_bookmarks(self, file_path: str, format: str = 'json') -> bool:
        """Export bookmarks to a file."""
        try:
            bookmarks = self.get_bookmarks()
            
            if format.lower() == 'json':
                export_data = {
                    'exported_at': datetime.now().isoformat(),
                    'bookmarks': [
                        {
                            'title': b.title,
                            'url': b.url,
                            'folder': b.folder,
                            'tags': b.tags,
                            'favicon': b.favicon,
                            'created_at': b.created_at.isoformat() if b.created_at else None,
                            'last_visited': b.last_visited.isoformat() if b.last_visited else None
                        }
                        for b in bookmarks
                    ]
                }
                
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            elif format.lower() == 'html':
                # Export as HTML bookmarks file
                html_content = self._generate_html_bookmarks(bookmarks)
                with open(file_path, 'w') as f:
                    f.write(html_content)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Exported {len(bookmarks)} bookmarks to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting bookmarks: {e}")
            return False
    
    def import_bookmarks(self, file_path: str, format: str = 'json') -> int:
        """Import bookmarks from a file."""
        try:
            imported_count = 0
            
            if format.lower() == 'json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                bookmarks_data = data.get('bookmarks', [])
                for bookmark_data in bookmarks_data:
                    bookmark = Bookmark(
                        title=bookmark_data.get('title', ''),
                        url=bookmark_data.get('url', ''),
                        folder=bookmark_data.get('folder', 'Imported'),
                        tags=bookmark_data.get('tags', []),
                        favicon=bookmark_data.get('favicon', '')
                    )
                    self.add_bookmark(bookmark)
                    imported_count += 1
            
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            self.logger.info(f"Imported {imported_count} bookmarks from {file_path}")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"Error importing bookmarks: {e}")
            return 0
    
    def get_bookmark_stats(self) -> Dict[str, Any]:
        """Get bookmark statistics."""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()
            
            # Total bookmarks
            cursor.execute('SELECT COUNT(*) as total FROM bookmarks')
            total_bookmarks = cursor.fetchone()['total']
            
            # Bookmarks by folder
            cursor.execute('''
                SELECT folder, COUNT(*) as count 
                FROM bookmarks 
                GROUP BY folder 
                ORDER BY count DESC
            ''')
            folders = {row['folder']: row['count'] for row in cursor.fetchall()}
            
            # Bookmarks with tags
            cursor.execute('''
                SELECT COUNT(*) as with_tags 
                FROM bookmarks 
                WHERE tags IS NOT NULL AND tags != '[]'
            ''')
            with_tags = cursor.fetchone()['with_tags']
            
            return {
                'total_bookmarks': total_bookmarks,
                'folders': folders,
                'bookmarks_with_tags': with_tags,
                'bookmarks_without_tags': total_bookmarks - with_tags,
                'total_folders': len(folders)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting bookmark stats: {e}")
            return {'error': str(e)}
    
    def _generate_html_bookmarks(self, bookmarks: List[Bookmark]) -> str:
        """Generate HTML bookmarks file content."""
        html = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
'''
        
        # Group by folder
        folders = {}
        for bookmark in bookmarks:
            if bookmark.folder not in folders:
                folders[bookmark.folder] = []
            folders[bookmark.folder].append(bookmark)
        
        for folder, folder_bookmarks in folders.items():
            html += f'    <DT><H3>{folder}</H3>\n    <DL><p>\n'
            
            for bookmark in folder_bookmarks:
                add_date = int(bookmark.created_at.timestamp()) if bookmark.created_at else 0
                html += f'        <DT><A HREF="{bookmark.url}" ADD_DATE="{add_date}">{bookmark.title}</A>\n'
            
            html += '    </DL><p>\n'
        
        html += '</DL><p>\n'
        return html
