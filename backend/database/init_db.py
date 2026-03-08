#!/usr/bin/env python3
"""
Database Initialization

This module initializes the browser database with proper
tables and indexes for optimal performance.
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.models import DatabaseManager


def initialize_database(db_path: str = "browser_data.db"):
    """Initialize the browser database."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Initializing database: {db_path}")
        
        # Create database manager
        db_manager = DatabaseManager(db_path)
        
        # Test database connection
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # Verify tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('bookmarks', 'history', 'preferences', 'cache', 'sessions')
        """)
        
        tables = cursor.fetchall()
        logger.info(f"Created/verified {len(tables)} tables")
        
        # Insert default preferences if they don't exist
        default_preferences = {
            'browser.theme': 'dark',
            'browser.enable_javascript': True,
            'browser.enable_cookies': True,
            'browser.default_homepage': 'https://www.google.com',
            'security.enable_ad_blocker': True,
            'security.enforce_https': True,
            'security.block_trackers': True,
            'ui.window_width': 1200,
            'ui.window_height': 800,
            'ui.show_bookmarks_bar': True,
            'ui.show_status_bar': True
        }
        
        for key, value in default_preferences.items():
            cursor.execute("SELECT COUNT(*) as count FROM preferences WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result['count'] == 0:
                cursor.execute("""
                    INSERT INTO preferences (key, value, category, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (key, str(value), 'default', datetime.now()))
        
        conn.commit()
        
        # Test basic operations
        logger.info("Testing database operations...")
        
        # Test bookmark insertion
        cursor.execute("""
            INSERT OR IGNORE INTO bookmarks (title, url, folder, created_at)
            VALUES (?, ?, ?, ?)
        """, ("Google", "https://www.google.com", "Search Engines", datetime.now()))
        
        # Test history insertion
        cursor.execute("""
            INSERT OR IGNORE INTO history (url, title, visit_count, last_visited)
            VALUES (?, ?, ?, ?)
        """, ("https://www.google.com", "Google", 1, datetime.now()))
        
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT COUNT(*) as bookmarks FROM bookmarks")
        bookmark_count = cursor.fetchone()['bookmarks']
        
        cursor.execute("SELECT COUNT(*) as history FROM history")
        history_count = cursor.fetchone()['history']
        
        logger.info(f"Database initialized successfully:")
        logger.info(f"  - Bookmarks: {bookmark_count}")
        logger.info(f"  - History entries: {history_count}")
        logger.info(f"  - Preferences: {len(default_preferences)}")
        
        # Close connection
        db_manager.close()
        
        logger.info("Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def create_sample_data(db_path: str = "browser_data.db"):
    """Create sample data for testing."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        db_manager = DatabaseManager(db_path)
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # Sample bookmarks
        sample_bookmarks = [
            ("GitHub", "https://github.com", "Development"),
            ("Stack Overflow", "https://stackoverflow.com", "Development"),
            ("Python.org", "https://python.org", "Development"),
            ("Wikipedia", "https://wikipedia.org", "Reference"),
            ("YouTube", "https://youtube.com", "Entertainment"),
            ("Reddit", "https://reddit.com", "Social")
        ]
        
        for title, url, folder in sample_bookmarks:
            cursor.execute("""
                INSERT OR IGNORE INTO bookmarks (title, url, folder, created_at)
                VALUES (?, ?, ?, ?)
            """, (title, url, folder, datetime.now()))
        
        # Sample history
        sample_history = [
            ("https://www.google.com", "Google", 5),
            ("https://github.com", "GitHub", 3),
            ("https://stackoverflow.com", "Stack Overflow", 2),
            ("https://python.org", "Python.org", 1),
            ("https://wikipedia.org", "Wikipedia", 1)
        ]
        
        for url, title, visits in sample_history:
            cursor.execute("""
                INSERT OR IGNORE INTO history (url, title, visit_count, last_visited)
                VALUES (?, ?, ?, ?)
            """, (url, title, visits, datetime.now()))
        
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT COUNT(*) as count FROM bookmarks")
        bookmark_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM history")
        history_count = cursor.fetchone()['count']
        
        logger.info(f"Sample data created:")
        logger.info(f"  - Bookmarks: {bookmark_count}")
        logger.info(f"  - History entries: {history_count}")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return False


def backup_database(db_path: str = "browser_data.db", backup_path: str = None):
    """Create a backup of the database."""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"browser_data_backup_{timestamp}.db"
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        return False


def vacuum_database(db_path: str = "browser_data.db"):
    """Vacuum the database to optimize performance."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database vacuumed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error vacuuming database: {e}")
        return False


def get_database_info(db_path: str = "browser_data.db"):
    """Get information about the database."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        info = {
            'database_path': db_path,
            'tables': {},
            'total_size': os.path.getsize(db_path) if os.path.exists(db_path) else 0
        }
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            info['tables'][table] = count
        
        conn.close()
        
        # Print info
        logger.info("Database Information:")
        logger.info(f"  Path: {info['database_path']}")
        logger.info(f"  Size: {info['total_size']} bytes")
        logger.info("  Tables:")
        for table, count in info['tables'].items():
            logger.info(f"    - {table}: {count} rows")
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Browser Database Utility")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--sample", action="store_true", help="Create sample data")
    parser.add_argument("--backup", help="Backup database to specified path")
    parser.add_argument("--vacuum", action="store_true", help="Vacuum database")
    parser.add_argument("--info", action="store_true", help="Show database information")
    parser.add_argument("--db", default="browser_data.db", help="Database file path")
    
    args = parser.parse_args()
    
    if args.init:
        initialize_database(args.db)
    elif args.sample:
        create_sample_data(args.db)
    elif args.backup:
        backup_database(args.db, args.backup)
    elif args.vacuum:
        vacuum_database(args.db)
    elif args.info:
        get_database_info(args.db)
    else:
        print("Use --help to see available options")
        print("Common usage:")
        print("  python -m backend.database.init_db --init")
        print("  python -m backend.database.init_db --sample")
        print("  python -m backend.database.init_db --info")
