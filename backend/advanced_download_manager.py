#!/usr/bin/env python3.12
"""
Advanced Download Manager for Vertex Browser

Comprehensive download management with queue control, resume support,
download history, speed limiting, and advanced features.
"""

import os
import re
import json
import threading
import time
import hashlib
import urllib.request
import urllib.parse
import queue
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import sqlite3
import shutil
import mimetypes
import tempfile
import weakref
import asyncio
from urllib.parse import urlparse
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit,
                             QFrame, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                             QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
                             QFormLayout, QScrollArea, QSplitter, QMenu, QToolBar,
                             QToolButton, QFileDialog, QStatusBar, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QSlider, QDoubleSpinBox, QDateTimeEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QObject, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette

from frontend.themes.modern_theme import theme, style_manager, ui_components


class DownloadState(Enum):
    """Download states."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RESUMING = "resuming"


class DownloadPriority(Enum):
    """Download priorities."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class DownloadItem:
    """Download item data structure."""
    id: str
    url: str
    filename: str
    full_path: Path
    file_size: int = 0
    downloaded_bytes: int = 0
    state: DownloadState = DownloadState.PENDING
    priority: DownloadPriority = DownloadPriority.NORMAL
    speed: float = 0.0  # bytes per second
    eta: int = 0  # estimated time remaining in seconds
    mime_type: str = ""
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""
    resume_pos: int = 0
    chunk_size: int = 8192
    max_retries: int = 3
    retry_count: int = 0
    speed_limit: Optional[int] = None  # bytes per second
    concurrent_chunks: int = 1
    checksum: Optional[str] = None
    checksum_algorithm: str = "md5"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def progress(self) -> float:
        """Get download progress as percentage."""
        if self.file_size == 0:
            return 0.0
        return (self.downloaded_bytes / self.file_size) * 100
    
    @property
    def remaining_bytes(self) -> int:
        """Get remaining bytes to download."""
        return self.file_size - self.downloaded_bytes
    
    @property
    def is_active(self) -> bool:
        """Check if download is active."""
        return self.state in [DownloadState.DOWNLOADING, DownloadState.RESUMING]
    
    @property
    def is_finished(self) -> bool:
        """Check if download is finished."""
        return self.state in [DownloadState.COMPLETED, DownloadState.FAILED, DownloadState.CANCELLED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'url': self.url,
            'filename': self.filename,
            'full_path': str(self.full_path),
            'file_size': self.file_size,
            'downloaded_bytes': self.downloaded_bytes,
            'state': self.state.value,
            'priority': self.priority.value,
            'speed': self.speed,
            'eta': self.eta,
            'mime_type': self.mime_type,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'resume_pos': self.resume_pos,
            'chunk_size': self.chunk_size,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'speed_limit': self.speed_limit,
            'concurrent_chunks': self.concurrent_chunks,
            'checksum': self.checksum,
            'checksum_algorithm': self.checksum_algorithm,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadItem':
        """Create from dictionary."""
        item = cls(
            id=data['id'],
            url=data['url'],
            filename=data['filename'],
            full_path=Path(data['full_path']),
            file_size=data['file_size'],
            downloaded_bytes=data['downloaded_bytes'],
            state=DownloadState(data['state']),
            priority=DownloadPriority(data['priority']),
            speed=data['speed'],
            eta=data['eta'],
            mime_type=data['mime_type'],
            error_message=data['error_message'],
            resume_pos=data['resume_pos'],
            chunk_size=data['chunk_size'],
            max_retries=data['max_retries'],
            retry_count=data['retry_count'],
            speed_limit=data['speed_limit'],
            concurrent_chunks=data['concurrent_chunks'],
            checksum=data['checksum'],
            checksum_algorithm=data['checksum_algorithm'],
            metadata=data['metadata']
        )
        
        if data['created_at']:
            item.created_at = datetime.fromisoformat(data['created_at'])
        if data['started_at']:
            item.started_at = datetime.fromisoformat(data['started_at'])
        if data['completed_at']:
            item.completed_at = datetime.fromisoformat(data['completed_at'])
        
        return item


class DownloadWorker(QThread):
    """Worker thread for downloading files."""
    
    progress_updated = pyqtSignal(str, int, int)  # download_id, downloaded, total
    speed_updated = pyqtSignal(str, float)  # download_id, speed
    state_changed = pyqtSignal(str, str)  # download_id, state
    completed = pyqtSignal(str)  # download_id
    failed = pyqtSignal(str, str)  # download_id, error
    checksum_verified = pyqtSignal(str, bool)  # download_id, valid
    
    def __init__(self, download_item: DownloadItem):
        super().__init__()
        self.download_item = download_item
        self.should_pause = False
        self.should_cancel = False
        self.speed_limiter = None
        self.last_progress_time = time.time()
        self.last_bytes = 0
    
    def run(self):
        """Run download."""
        try:
            self.download_item.state = DownloadState.DOWNLOADING
            self.state_changed.emit(self.download_item.id, DownloadState.DOWNLOADING.value)
            self.download_item.started_at = datetime.now()
            
            # Create directory if needed
            self.download_item.full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Setup speed limiter
            if self.download_item.speed_limit:
                self.speed_limiter = SpeedLimiter(self.download_item.speed_limit)
            
            # Open connection
            req = urllib.request.Request(self.download_item.url)
            if self.download_item.resume_pos > 0:
                req.add_header('Range', f'bytes={self.download_item.resume_pos}-')
            
            response = urllib.request.urlopen(req, timeout=30)
            
            # Get file info
            content_length = response.headers.get('Content-Length')
            if content_length and not self.download_item.resume_pos:
                self.download_item.file_size = int(content_length)
            
            # Get MIME type
            content_type = response.headers.get('Content-Type', '')
            if content_type:
                self.download_item.mime_type = content_type.split(';')[0]
            
            # Open file for writing
            mode = 'ab' if self.download_item.resume_pos > 0 else 'wb'
            with open(self.download_item.full_path, mode) as f:
                # Download loop
                while not self.should_cancel and not self.should_pause:
                    chunk = response.read(self.download_item.chunk_size)
                    if not chunk:
                        break
                    
                    # Apply speed limiting
                    if self.speed_limiter:
                        self.speed_limiter.wait(len(chunk))
                    
                    # Write chunk
                    f.write(chunk)
                    self.download_item.downloaded_bytes += len(chunk)
                    
                    # Update progress
                    current_time = time.time()
                    time_diff = current_time - self.last_progress_time
                    
                    if time_diff >= 0.5:  # Update every 0.5 seconds
                        # Calculate speed
                        bytes_diff = self.download_item.downloaded_bytes - self.last_bytes
                        self.download_item.speed = bytes_diff / time_diff
                        
                        # Calculate ETA
                        if self.download_item.speed > 0:
                            remaining = self.download_item.remaining_bytes
                            self.download_item.eta = int(remaining / self.download_item.speed)
                        
                        # Emit signals
                        self.progress_updated.emit(
                            self.download_item.id,
                            self.download_item.downloaded_bytes,
                            self.download_item.file_size
                        )
                        self.speed_updated.emit(self.download_item.id, self.download_item.speed)
                        
                        self.last_progress_time = current_time
                        self.last_bytes = self.download_item.downloaded_bytes
            
            # Handle pause
            if self.should_pause:
                self.download_item.state = DownloadState.PAUSED
                self.download_item.resume_pos = self.download_item.downloaded_bytes
                self.state_changed.emit(self.download_item.id, DownloadState.PAUSED.value)
                return
            
            # Handle cancel
            if self.should_cancel:
                self.download_item.state = DownloadState.CANCELLED
                self.state_changed.emit(self.download_item.id, DownloadState.CANCELLED.value)
                # Delete partial file
                if self.download_item.full_path.exists():
                    self.download_item.full_path.unlink()
                return
            
            # Download completed
            self.download_item.state = DownloadState.COMPLETED
            self.download_item.completed_at = datetime.now()
            self.state_changed.emit(self.download_item.id, DownloadState.COMPLETED.value)
            self.completed.emit(self.download_item.id)
            
            # Verify checksum if provided
            if self.download_item.checksum:
                valid = self._verify_checksum()
                self.checksum_verified.emit(self.download_item.id, valid)
            
        except Exception as e:
            self.download_item.state = DownloadState.FAILED
            self.download_item.error_message = str(e)
            self.download_item.retry_count += 1
            self.state_changed.emit(self.download_item.id, DownloadState.FAILED.value)
            self.failed.emit(self.download_item.id, str(e))
    
    def pause(self):
        """Pause download."""
        self.should_pause = True
    
    def cancel(self):
        """Cancel download."""
        self.should_cancel = True
    
    def resume(self):
        """Resume download."""
        self.should_pause = False
        self.start()
    
    def _verify_checksum(self) -> bool:
        """Verify file checksum."""
        if not self.download_item.checksum or not self.download_item.full_path.exists():
            return True
        
        try:
            hash_func = getattr(hashlib, self.download_item.checksum_algorithm.lower())
            with open(self.download_item.full_path, 'rb') as f:
                file_hash = hash_func()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
            
            return file_hash.hexdigest().lower() == self.download_item.checksum.lower()
        except Exception:
            return False


class SpeedLimiter:
    """Speed limiter for downloads."""
    
    def __init__(self, max_bytes_per_second: int):
        self.max_bytes_per_second = max_bytes_per_second
        self.last_time = time.time()
        self.bytes_transferred = 0
    
    def wait(self, bytes_count: int):
        """Wait if speed limit exceeded."""
        self.bytes_transferred += bytes_count
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        if elapsed >= 1.0:
            # Reset counter every second
            self.bytes_transferred = 0
            self.last_time = current_time
        elif self.bytes_transferred >= self.max_bytes_per_second:
            # Wait until next second
            sleep_time = 1.0 - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.bytes_transferred = 0
                self.last_time = time.time()


class DownloadQueue:
    """Download queue management."""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.queue = queue.PriorityQueue()
        self.active_downloads = {}
        self.download_items = {}
        self.workers = {}
        self.lock = threading.Lock()
        self.running = False
        self.start_thread = None
    
    def start(self):
        """Start queue processing."""
        if not self.running:
            self.running = True
            self.start_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.start_thread.start()
    
    def stop(self):
        """Stop queue processing."""
        self.running = False
        if self.start_thread:
            self.start_thread.join()
    
    def add_download(self, download_item: DownloadItem):
        """Add download to queue."""
        with self.lock:
            self.download_items[download_item.id] = download_item
            # Priority queue uses negative priority for max-heap behavior
            priority = -download_item.priority.value
            self.queue.put((priority, download_item.id))
    
    def remove_download(self, download_id: str):
        """Remove download from queue."""
        with self.lock:
            if download_id in self.download_items:
                del self.download_items[download_id]
            
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
            
            if download_id in self.workers:
                worker = self.workers[download_id]
                worker.cancel()
                del self.workers[download_id]
    
    def pause_download(self, download_id: str):
        """Pause download."""
        with self.lock:
            if download_id in self.workers:
                self.workers[download_id].pause()
                if download_id in self.active_downloads:
                    del self.active_downloads[download_id]
    
    def resume_download(self, download_id: str):
        """Resume download."""
        with self.lock:
            download_item = self.download_items.get(download_id)
            if download_item and download_item.state == DownloadState.PAUSED:
                # Re-add to queue
                priority = -download_item.priority.value
                self.queue.put((priority, download_id))
    
    def cancel_download(self, download_id: str):
        """Cancel download."""
        with self.lock:
            if download_id in self.workers:
                self.workers[download_id].cancel()
            
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
            
            if download_id in self.download_items:
                self.download_items[download_id].state = DownloadState.CANCELLED
    
    def _process_queue(self):
        """Process download queue."""
        while self.running:
            try:
                # Check if we can start new downloads
                if len(self.active_downloads) < self.max_concurrent:
                    try:
                        priority, download_id = self.queue.get(timeout=1.0)
                        
                        with self.lock:
                            download_item = self.download_items.get(download_id)
                            if download_item and download_item.state == DownloadState.PENDING:
                                # Start download
                                worker = DownloadWorker(download_item)
                                worker.completed.connect(self._on_download_completed)
                                worker.failed.connect(self._on_download_failed)
                                worker.state_changed.connect(self._on_state_changed)
                                
                                self.workers[download_id] = worker
                                self.active_downloads[download_id] = download_item
                                worker.start()
                    
                    except queue.Empty:
                        continue
                
                time.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Queue processing error: {e}")
    
    def _on_download_completed(self, download_id: str):
        """Handle download completion."""
        with self.lock:
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
            if download_id in self.workers:
                del self.workers[download_id]
    
    def _on_download_failed(self, download_id: str, error: str):
        """Handle download failure."""
        with self.lock:
            download_item = self.download_items.get(download_id)
            if download_item:
                if download_item.retry_count < download_item.max_retries:
                    # Retry download
                    download_item.state = DownloadState.PENDING
                    priority = -download_item.priority.value
                    self.queue.put((priority, download_id))
                else:
                    # Mark as failed
                    download_item.state = DownloadState.FAILED
            
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
            if download_id in self.workers:
                del self.workers[download_id]
    
    def _on_state_changed(self, download_id: str, state: str):
        """Handle state change."""
        with self.lock:
            download_item = self.download_items.get(download_id)
            if download_item:
                download_item.state = DownloadState(state)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status."""
        with self.lock:
            return {
                'total_downloads': len(self.download_items),
                'active_downloads': len(self.active_downloads),
                'queued_downloads': self.queue.qsize(),
                'max_concurrent': self.max_concurrent,
                'running': self.running
            }


class DownloadHistory:
    """Download history management."""
    
    def __init__(self):
        self.db_path = Path.home() / '.vertex_downloads.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                url TEXT,
                filename TEXT,
                full_path TEXT,
                file_size INTEGER,
                downloaded_bytes INTEGER,
                state TEXT,
                priority INTEGER,
                speed REAL,
                eta INTEGER,
                mime_type TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                resume_pos INTEGER,
                chunk_size INTEGER,
                max_retries INTEGER,
                retry_count INTEGER,
                speed_limit INTEGER,
                concurrent_chunks INTEGER,
                checksum TEXT,
                checksum_algorithm TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_download(self, download_item: DownloadItem):
        """Save download to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO downloads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            download_item.id,
            download_item.url,
            download_item.filename,
            str(download_item.full_path),
            download_item.file_size,
            download_item.downloaded_bytes,
            download_item.state.value,
            download_item.priority.value,
            download_item.speed,
            download_item.eta,
            download_item.mime_type,
            download_item.created_at.isoformat(),
            download_item.started_at.isoformat() if download_item.started_at else None,
            download_item.completed_at.isoformat() if download_item.completed_at else None,
            download_item.error_message,
            download_item.resume_pos,
            download_item.chunk_size,
            download_item.max_retries,
            download_item.retry_count,
            download_item.speed_limit,
            download_item.concurrent_chunks,
            download_item.checksum,
            download_item.checksum_algorithm,
            json.dumps(download_item.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def load_downloads(self) -> List[DownloadItem]:
        """Load downloads from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM downloads')
        rows = cursor.fetchall()
        
        downloads = []
        for row in rows:
            # Convert row to dictionary
            columns = [
                'id', 'url', 'filename', 'full_path', 'file_size', 'downloaded_bytes',
                'state', 'priority', 'speed', 'eta', 'mime_type', 'created_at',
                'started_at', 'completed_at', 'error_message', 'resume_pos',
                'chunk_size', 'max_retries', 'retry_count', 'speed_limit',
                'concurrent_chunks', 'checksum', 'checksum_algorithm', 'metadata'
            ]
            
            data = dict(zip(columns, row))
            data['full_path'] = Path(data['full_path'])
            data['metadata'] = json.loads(data['metadata'])
            
            download = DownloadItem.from_dict(data)
            downloads.append(download)
        
        conn.close()
        return downloads
    
    def delete_download(self, download_id: str):
        """Delete download from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM downloads WHERE id = ?', (download_id,))
        
        conn.commit()
        conn.close()
    
    def clear_history(self, older_than_days: int = 30):
        """Clear download history."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cursor.execute('DELETE FROM downloads WHERE created_at < ?', (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total downloads
        cursor.execute('SELECT COUNT(*) FROM downloads')
        total_downloads = cursor.fetchone()[0]
        
        # Completed downloads
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE state = ?', ('completed',))
        completed_downloads = cursor.fetchone()[0]
        
        # Total bytes downloaded
        cursor.execute('SELECT SUM(downloaded_bytes) FROM downloads WHERE state = ?', ('completed',))
        total_bytes = cursor.fetchone()[0] or 0
        
        # Average speed
        cursor.execute('SELECT AVG(speed) FROM downloads WHERE state = ? AND speed > 0', ('completed',))
        avg_speed = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_downloads': total_downloads,
            'completed_downloads': completed_downloads,
            'failed_downloads': total_downloads - completed_downloads,
            'total_bytes': total_bytes,
            'average_speed': avg_speed,
            'success_rate': (completed_downloads / total_downloads * 100) if total_downloads > 0 else 0
        }


class DownloadManager(QObject):
    """Main download manager."""
    
    download_added = pyqtSignal(object)  # DownloadItem
    download_updated = pyqtSignal(object)  # DownloadItem
    download_completed = pyqtSignal(object)  # DownloadItem
    download_failed = pyqtSignal(object, str)  # DownloadItem, error
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_queue = DownloadQueue(max_concurrent=3)
        self.download_history = DownloadHistory()
        self.downloads = {}
        self.default_download_dir = Path.home() / "Downloads"
        self.download_counter = 0
        self.speed_limits = {
            'default': None,
            'wifi': None,
            'mobile': None
        }
        
        # Load existing downloads
        self.load_downloads()
        
        # Start queue
        self.download_queue.start()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_downloads)
        self.update_timer.start(1000)  # Update every second
    
    def load_downloads(self):
        """Load downloads from history."""
        downloads = self.download_history.load_downloads()
        for download in downloads:
            self.downloads[download.id] = download
            
            # Re-add pending downloads to queue
            if download.state == DownloadState.PENDING:
                self.download_queue.add_download(download)
    
    def create_download(self, url: str, filename: str = None, download_dir: Path = None) -> str:
        """Create new download."""
        # Generate download ID
        self.download_counter += 1
        download_id = f"download_{self.download_counter}_{int(time.time())}"
        
        # Determine filename
        if not filename:
            filename = self._extract_filename_from_url(url)
        
        # Determine download directory
        if not download_dir:
            download_dir = self.default_download_dir
        
        # Create download item
        full_path = download_dir / filename
        download_item = DownloadItem(
            id=download_id,
            url=url,
            filename=filename,
            full_path=full_path
        )
        
        # Add to downloads
        self.downloads[download_id] = download_item
        self.download_history.save_download(download_item)
        
        # Add to queue
        self.download_queue.add_download(download_item)
        
        # Emit signal
        self.download_added.emit(download_item)
        
        return download_id
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        if not filename:
            # Generate filename from URL
            filename = f"download_{int(time.time())}"
        
        # Clean filename
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Ensure unique filename
        counter = 1
        base_filename = filename
        while (self.default_download_dir / filename).exists():
            name, ext = os.path.splitext(base_filename)
            filename = f"{name}_{counter}{ext}"
            counter += 1
        
        return filename
    
    def pause_download(self, download_id: str):
        """Pause download."""
        self.download_queue.pause_download(download_id)
    
    def resume_download(self, download_id: str):
        """Resume download."""
        self.download_queue.resume_download(download_id)
    
    def cancel_download(self, download_id: str):
        """Cancel download."""
        self.download_queue.cancel_download(download_id)
        self.download_history.delete_download(download_id)
        if download_id in self.downloads:
            del self.downloads[download_id]
    
    def remove_download(self, download_item: DownloadItem):
        """Remove download from list."""
        if download_item.id in self.downloads:
            del self.downloads[download_item]
        
        # Delete file if completed
        if download_item.state == DownloadState.COMPLETED and download_item.full_path.exists():
            download_item.full_path.unlink()
        
        # Remove from history
        self.download_history.delete_download(download_item.id)
    
    def retry_download(self, download_id: str):
        """Retry failed download."""
        download_item = self.downloads.get(download_id)
        if download_item and download_item.state == DownloadState.FAILED:
            # Reset download state
            download_item.state = DownloadState.PENDING
            download_item.retry_count = 0
            download_item.error_message = ""
            
            # Re-add to queue
            self.download_queue.add_download(download_item)
            self.download_history.save_download(download_item)
    
    def set_speed_limit(self, limit: int, connection_type: str = 'default'):
        """Set speed limit for downloads."""
        self.speed_limits[connection_type] = limit
    
    def get_speed_limit(self, connection_type: str = 'default') -> Optional[int]:
        """Get speed limit for downloads."""
        return self.speed_limits.get(connection_type)
    
    def set_max_concurrent(self, max_concurrent: int):
        """Set maximum concurrent downloads."""
        self.download_queue.max_concurrent = max_concurrent
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status."""
        return self.download_queue.get_queue_status()
    
    def get_downloads(self, state: DownloadState = None) -> List[DownloadItem]:
        """Get downloads by state."""
        if state is None:
            return list(self.downloads.values())
        
        return [d for d in self.downloads.values() if d.state == state]
    
    def update_downloads(self):
        """Update download statistics."""
        for download in self.downloads.values():
            if download.is_active:
                # Update ETA
                if download.speed > 0:
                    download.eta = int(download.remaining_bytes / download.speed)
                
                # Emit update signal
                self.download_updated.emit(download)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics."""
        return self.download_history.get_statistics()
    
    def clear_history(self, older_than_days: int = 30):
        """Clear download history."""
        self.download_history.clear_history(older_than_days)
        self.load_downloads()
    
    def export_downloads(self, file_path: str):
        """Export downloads to file."""
        downloads_data = [d.to_dict() for d in self.downloads.values()]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(downloads_data, f, indent=2, default=str)
    
    def import_downloads(self, file_path: str):
        """Import downloads from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            downloads_data = json.load(f)
        
        for data in downloads_data:
            download = DownloadItem.from_dict(data)
            self.downloads[download.id] = download
            self.download_history.save_download(download)
            
            # Re-add pending downloads to queue
            if download.state == DownloadState.PENDING:
                self.download_queue.add_download(download)


def show_download_manager(parent=None):
    """Show download manager dialog."""
    from .download_manager_ui import DownloadManagerDialog
    dialog = DownloadManagerDialog(parent)
    dialog.show()
    return dialog
