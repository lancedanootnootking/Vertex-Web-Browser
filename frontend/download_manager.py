#!/usr/bin/env python3.12
"""
Advanced Download Manager with Modern UI

Comprehensive download management system with modern blue/grey theme,
progress tracking, pause/resume functionality, and beautiful UI.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QMenu, QToolBar, QProgressBar, QComboBox, QCheckBox, 
                             QGroupBox, QFormLayout, QDialogButtonBox, QFrame, 
                             QMessageBox, QSpinBox, QSlider, QSplitter, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QUrl, QFileInfo
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QKeySequence
from pathlib import Path
import json
import requests
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import urllib.parse
import os

from frontend.themes.modern_theme import theme, style_manager, ui_components


class DownloadItem:
    """Represents a single download."""
    
    def __init__(self, url: str, filename: str = None, save_path: str = None):
        self.url = url
        self.filename = filename or self.extract_filename(url)
        self.save_path = save_path or str(Path.home() / "Downloads")
        self.full_path = Path(self.save_path) / self.filename
        
        # Download state
        self.status = "pending"  # pending, downloading, paused, completed, failed, cancelled
        self.progress = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.speed = 0.0  # bytes per second
        self.time_remaining = 0  # seconds
        
        # Metadata
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.completed_at = None
        self.error_message = ""
        self.mime_type = ""
        self.file_size_display = ""
        
        # Download thread
        self.download_thread = None
        self.should_pause = False
        self.should_cancel = False
        
        self.id = f"download_{int(time.time())}_{hash(url)}"
    
    def extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            filename = Path(parsed.path).name
            if not filename:
                filename = "download"
            if not Path(filename).suffix:
                filename += ".html"
            return filename
        except:
            return "download"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'filename': self.filename,
            'save_path': self.save_path,
            'full_path': str(self.full_path),
            'status': self.status,
            'progress': self.progress,
            'downloaded_bytes': self.downloaded_bytes,
            'total_bytes': self.total_bytes,
            'speed': self.speed,
            'time_remaining': self.time_remaining,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error_message': self.error_message,
            'mime_type': self.mime_type,
            'file_size_display': self.file_size_display
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DownloadItem':
        """Create from dictionary."""
        item = cls(data['url'], data['filename'], data['save_path'])
        item.id = data['id']
        item.status = data['status']
        item.progress = data['progress']
        item.downloaded_bytes = data['downloaded_bytes']
        item.total_bytes = data['total_bytes']
        item.speed = data['speed']
        item.time_remaining = data['time_remaining']
        item.created_at = data['created_at']
        item.started_at = data['started_at']
        item.completed_at = data['completed_at']
        item.error_message = data['error_message']
        item.mime_type = data['mime_type']
        item.file_size_display = data['file_size_display']
        item.full_path = Path(data['full_path'])
        return item


class DownloadWorker(QThread):
    """Worker thread for downloading files."""
    
    progress_updated = pyqtSignal(str, float, int, int, float, int)
    status_changed = pyqtSignal(str, str)
    finished = pyqtSignal(str)
    
    def __init__(self, download_item: DownloadItem):
        super().__init__()
        self.download_item = download_item
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Vertex Browser/1.0'
        })
    
    def run(self):
        """Run the download."""
        try:
            self.download_item.status = "downloading"
            self.download_item.started_at = datetime.now().isoformat()
            self.status_changed.emit(self.download_item.id, "downloading")
            
            # Get file info first
            try:
                response = self.session.head(self.download_item.url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    content_length = response.headers.get('content-length')
                    if content_length:
                        self.download_item.total_bytes = int(content_length)
                        self.download_item.file_size_display = self.format_bytes(int(content_length))
                    
                    content_type = response.headers.get('content-type', '')
                    self.download_item.mime_type = content_type
            except:
                pass
            
            # Download the file
            response = self.session.get(self.download_item.url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            self.download_item.full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress tracking
            downloaded = 0
            start_time = time.time()
            last_update_time = start_time
            
            with open(self.download_item.full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.download_item.should_cancel:
                        self.download_item.status = "cancelled"
                        self.status_changed.emit(self.download_item.id, "cancelled")
                        # Delete partial file
                        if self.download_item.full_path.exists():
                            self.download_item.full_path.unlink()
                        return
                    
                    while self.download_item.should_pause:
                        time.sleep(0.1)
                        if self.download_item.should_cancel:
                            self.download_item.status = "cancelled"
                            self.status_changed.emit(self.download_item.id, "cancelled")
                            if self.download_item.full_path.exists():
                                self.download_item.full_path.unlink()
                            return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.download_item.downloaded_bytes = downloaded
                        
                        # Calculate progress
                        if self.download_item.total_bytes > 0:
                            progress = (downloaded / self.download_item.total_bytes) * 100
                            self.download_item.progress = progress
                        else:
                            progress = 0
                            self.download_item.progress = 0
                        
                        # Calculate speed
                        current_time = time.time()
                        if current_time - last_update_time >= 1.0:  # Update every second
                            elapsed_time = current_time - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                            self.download_item.speed = speed
                            
                            # Calculate time remaining
                            if self.download_item.total_bytes > 0 and speed > 0:
                                remaining_bytes = self.download_item.total_bytes - downloaded
                                self.download_item.time_remaining = int(remaining_bytes / speed)
                            else:
                                self.download_item.time_remaining = 0
                            
                            self.progress_updated.emit(
                                self.download_item.id, progress, 
                                downloaded, self.download_item.total_bytes,
                                speed, self.download_item.time_remaining
                            )
                            last_update_time = current_time
            
            # Download completed
            self.download_item.status = "completed"
            self.download_item.progress = 100.0
            self.download_item.completed_at = datetime.now().isoformat()
            self.status_changed.emit(self.download_item.id, "completed")
            self.finished.emit(self.download_item.id)
            
        except Exception as e:
            self.download_item.status = "failed"
            self.download_item.error_message = str(e)
            self.status_changed.emit(self.download_item.id, "failed")
            self.finished.emit(self.download_item.id)
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes for display."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def pause(self):
        """Pause the download."""
        self.download_item.should_pause = True
    
    def resume(self):
        """Resume the download."""
        self.download_item.should_pause = False
    
    def cancel(self):
        """Cancel the download."""
        self.download_item.should_cancel = True


class DownloadManagerDialog(QDialog):
    """Advanced download manager with modern UI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.setGeometry(200, 200, 1200, 800)
        self.setModal(False)
        
        # Apply modern theme
        style_manager.apply_stylesheet(self, "dialog")
        
        # Data
        self.downloads = []
        self.download_workers = {}
        self.download_queue = []
        
        # Settings
        self.max_concurrent_downloads = 3
        self.default_save_path = str(Path.home() / "Downloads")
        
        # Setup UI
        self.setup_ui()
        self.load_downloads()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_downloads)
        self.update_timer.start(1000)  # Update every second
    
    def setup_ui(self):
        """Setup the download manager UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.create_toolbar(layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left panel - queue and settings
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - downloads list
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter sizes
        content_splitter.setSizes([300, 900])
        
        # Status bar
        self.create_status_bar(layout)
    
    def create_toolbar(self, parent_layout):
        """Create the toolbar."""
        toolbar_container = QFrame()
        toolbar_container.setProperty("class", "card")
        style_manager.apply_stylesheet(toolbar_container, "frame")
        
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('sm'), 
                                         theme.get_spacing('md'), theme.get_spacing('sm'))
        toolbar_layout.setSpacing(theme.get_spacing('sm'))
        
        # New download button
        self.new_download_btn = ui_components.create_modern_button("New Download", "primary")
        self.new_download_btn.clicked.connect(self.add_new_download)
        toolbar_layout.addWidget(self.new_download_btn)
        
        # Pause all button
        self.pause_all_btn = ui_components.create_modern_button("Pause All")
        self.pause_all_btn.clicked.connect(self.pause_all_downloads)
        toolbar_layout.addWidget(self.pause_all_btn)
        
        # Resume all button
        self.resume_all_btn = ui_components.create_modern_button("Resume All")
        self.resume_all_btn.clicked.connect(self.resume_all_downloads)
        toolbar_layout.addWidget(self.resume_all_btn)
        
        # Clear completed button
        self.clear_completed_btn = ui_components.create_modern_button("Clear Completed")
        self.clear_completed_btn.clicked.connect(self.clear_completed_downloads)
        toolbar_layout.addWidget(self.clear_completed_btn)
        
        # Separator
        separator = ui_components.create_modern_separator("vertical")
        toolbar_layout.addWidget(separator)
        
        # View options
        self.view_combo = QComboBox()
        self.view_combo.addItems(["All Downloads", "Downloading", "Completed", "Paused", "Failed"])
        self.view_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.view_combo, "combo_box")
        self.view_combo.currentTextChanged.connect(self.on_view_changed)
        toolbar_layout.addWidget(self.view_combo)
        
        # Sort options
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sort by Date", "Sort by Name", "Sort by Size", "Sort by Progress"])
        self.sort_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.sort_combo, "combo_box")
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        toolbar_layout.addWidget(self.sort_combo)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search downloads...")
        self.search_edit.setMinimumHeight(36)
        self.search_edit.setMaximumWidth(300)
        style_manager.apply_stylesheet(self.search_edit, "address_bar")
        self.search_edit.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_edit)
        
        parent_layout.addWidget(toolbar_container)
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with queue and settings."""
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                     theme.get_spacing('md'), theme.get_spacing('md'))
        left_layout.setSpacing(theme.get_spacing('md'))
        
        # Queue section
        queue_group = QGroupBox("Download Queue")
        queue_layout = QVBoxLayout(queue_group)
        style_manager.apply_stylesheet(queue_group, "group_box")
        
        # Queue list
        self.queue_tree = QTreeWidget()
        self.queue_tree.setHeaderLabels(["File", "Size", "Status"])
        self.queue_tree.setMaximumHeight(150)
        style_manager.apply_stylesheet(self.queue_tree, "tree_widget")
        queue_layout.addWidget(self.queue_tree)
        
        # Queue controls
        queue_controls = QHBoxLayout()
        
        self.start_queue_btn = ui_components.create_modern_button("Start")
        self.start_queue_btn.clicked.connect(self.start_queue)
        queue_controls.addWidget(self.start_queue_btn)
        
        self.stop_queue_btn = ui_components.create_modern_button("Stop")
        self.stop_queue_btn.clicked.connect(self.stop_queue)
        queue_controls.addWidget(self.stop_queue_btn)
        
        queue_layout.addLayout(queue_controls)
        left_layout.addWidget(queue_group)
        
        # Settings section
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        style_manager.apply_stylesheet(settings_group, "group_box")
        
        # Max concurrent downloads
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(self.max_concurrent_downloads)
        self.max_concurrent_spin.valueChanged.connect(self.on_max_concurrent_changed)
        style_manager.apply_stylesheet(self.max_concurrent_spin, "combo_box")
        settings_layout.addRow("Max Concurrent:", self.max_concurrent_spin)
        
        # Default save path
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setText(self.default_save_path)
        self.save_path_edit.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.save_path_edit, "address_bar")
        
        browse_btn = ui_components.create_modern_button("Browse")
        browse_btn.clicked.connect(self.browse_save_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.save_path_edit)
        path_layout.addWidget(browse_btn)
        settings_layout.addRow("Save Path:", path_layout)
        
        # Auto-open files
        self.auto_open_checkbox = QCheckBox("Auto-open completed downloads")
        style_manager.apply_stylesheet(self.auto_open_checkbox, "checkbox")
        settings_layout.addRow(self.auto_open_checkbox)
        
        left_layout.addWidget(settings_group)
        
        # Statistics section
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        style_manager.apply_stylesheet(stats_group, "group_box")
        
        self.total_downloads_label = QLabel("0")
        self.active_downloads_label = QLabel("0")
        self.completed_downloads_label = QLabel("0")
        self.failed_downloads_label = QLabel("0")
        
        stats_layout.addRow("Total Downloads:", self.total_downloads_label)
        stats_layout.addRow("Active:", self.active_downloads_label)
        stats_layout.addRow("Completed:", self.completed_downloads_label)
        stats_layout.addRow("Failed:", self.failed_downloads_label)
        
        left_layout.addWidget(stats_group)
        
        return left_panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with downloads list."""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                      theme.get_spacing('md'), theme.get_spacing('md'))
        right_layout.setSpacing(theme.get_spacing('md'))
        
        # Downloads list
        self.downloads_tree = QTreeWidget()
        self.downloads_tree.setHeaderLabels(["File", "Size", "Progress", "Speed", "Time Left", "Status"])
        self.downloads_tree.setRootIsDecorated(False)
        self.downloads_tree.setAlternatingRowColors(True)
        self.downloads_tree.setSortingEnabled(True)
        style_manager.apply_stylesheet(self.downloads_tree, "tree_widget")
        
        # Connect signals
        self.downloads_tree.itemDoubleClicked.connect(self.open_download)
        self.downloads_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.downloads_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        right_layout.addWidget(self.downloads_tree)
        
        # Details panel
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        style_manager.apply_stylesheet(details_group, "group_box")
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(120)
        self.details_text.setReadOnly(True)
        style_manager.apply_stylesheet(self.details_text, "text_edit")
        details_layout.addWidget(self.details_text)
        
        right_layout.addWidget(details_group)
        
        return right_panel
    
    def create_status_bar(self, parent_layout):
        """Create the status bar."""
        status_container = QFrame()
        status_container.setProperty("class", "card")
        style_manager.apply_stylesheet(status_container, "frame")
        
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('sm'), 
                                        theme.get_spacing('md'), theme.get_spacing('sm'))
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.status_label, "label")
        status_layout.addWidget(self.status_label)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        self.overall_progress.setMaximumWidth(200)
        style_manager.apply_stylesheet(self.overall_progress, "progress_bar")
        status_layout.addWidget(self.overall_progress)
        
        # Speed indicator
        self.speed_label = QLabel("0 KB/s")
        self.speed_label.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.speed_label, "label")
        status_layout.addWidget(self.speed_label)
        
        parent_layout.addWidget(status_container)
    
    def add_new_download(self):
        """Add a new download."""
        from PyQt6.QtWidgets import QInputDialog
        
        url, ok = QInputDialog.getText(self, "New Download", "Enter URL:")
        if ok and url.strip():
            self.start_download(url.strip())
    
    def start_download(self, url: str, filename: str = None, save_path: str = None):
        """Start a new download."""
        download_item = DownloadItem(url, filename, save_path)
        self.downloads.append(download_item)
        
        # Add to queue
        self.download_queue.append(download_item)
        
        # Start download if there's room
        self.process_queue()
        
        # Update UI
        self.update_downloads()
        self.save_downloads()
        
        self.status_label.setText(f"Added download: {download_item.filename}")
    
    def process_queue(self):
        """Process the download queue."""
        active_count = len([d for d in self.downloads if d.status == "downloading"])
        
        while (active_count < self.max_concurrent_downloads and 
               self.download_queue and 
               not any(d.status == "downloading" for d in self.download_queue if d in self.download_queue)):
            
            download_item = self.download_queue.pop(0)
            if download_item.status in ["pending", "paused"]:
                self.start_download_worker(download_item)
                active_count += 1
    
    def start_download_worker(self, download_item: DownloadItem):
        """Start download worker for an item."""
        worker = DownloadWorker(download_item)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.status_changed.connect(self.on_status_changed)
        worker.finished.connect(self.on_download_finished)
        
        self.download_workers[download_item.id] = worker
        worker.start()
    
    def on_progress_updated(self, download_id: str, progress: float, downloaded: int, 
                           total: int, speed: float, time_remaining: int):
        """Handle download progress update."""
        for item in self.downloads:
            if item.id == download_id:
                item.progress = progress
                item.downloaded_bytes = downloaded
                item.total_bytes = total
                item.speed = speed
                item.time_remaining = time_remaining
                break
        
        self.update_downloads()
    
    def on_status_changed(self, download_id: str, status: str):
        """Handle download status change."""
        for item in self.downloads:
            if item.id == download_id:
                item.status = status
                break
        
        self.update_downloads()
        self.process_queue()
    
    def on_download_finished(self, download_id: str):
        """Handle download completion."""
        # Clean up worker
        if download_id in self.download_workers:
            del self.download_workers[download_id]
        
        self.update_downloads()
        self.process_queue()
    
    def update_downloads(self):
        """Update the downloads UI."""
        self.downloads_tree.clear()
        
        filtered_downloads = self.get_filtered_downloads()
        
        for item in filtered_downloads:
            tree_item = QTreeWidgetItem(self.downloads_tree)
            tree_item.setText(0, item.filename)
            tree_item.setText(1, item.file_size_display or "Unknown")
            tree_item.setText(2, f"{item.progress:.1f}%")
            tree_item.setText(3, self.format_speed(item.speed))
            tree_item.setText(4, self.format_time(item.time_remaining))
            tree_item.setText(5, item.status.capitalize())
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item)
            
            # Add progress bar widget
            progress_bar = QProgressBar()
            progress_bar.setValue(int(item.progress))
            progress_bar.setMaximumHeight(20)
            style_manager.apply_stylesheet(progress_bar, "progress_bar")
            
            # Set status color
            if item.status == "completed":
                tree_item.setForeground(5, QColor(theme.get_color('success_green')))
            elif item.status == "failed":
                tree_item.setForeground(5, QColor(theme.get_color('error_red')))
            elif item.status == "downloading":
                tree_item.setForeground(5, QColor(theme.get_color('primary_blue')))
            elif item.status == "paused":
                tree_item.setForeground(5, QColor(theme.get_color('warning_yellow')))
        
        # Update queue
        self.update_queue()
        
        # Update statistics
        self.update_statistics()
        
        # Update overall progress
        self.update_overall_progress()
        
        # Update speed indicator
        total_speed = sum(item.speed for item in self.downloads if item.status == "downloading")
        self.speed_label.setText(self.format_speed(total_speed))
    
    def get_filtered_downloads(self) -> List[DownloadItem]:
        """Get filtered downloads based on current view."""
        view = self.view_combo.currentText()
        search_query = self.search_edit.text().strip().lower()
        
        filtered = self.downloads
        
        # Filter by view
        if view == "Downloading":
            filtered = [d for d in filtered if d.status == "downloading"]
        elif view == "Completed":
            filtered = [d for d in filtered if d.status == "completed"]
        elif view == "Paused":
            filtered = [d for d in filtered if d.status == "paused"]
        elif view == "Failed":
            filtered = [d for d in filtered if d.status == "failed"]
        
        # Filter by search
        if search_query:
            filtered = [d for d in filtered 
                       if search_query in d.filename.lower() or 
                          search_query in d.url.lower()]
        
        # Sort
        self.sort_downloads(filtered)
        
        return filtered
    
    def sort_downloads(self, downloads: List[DownloadItem]):
        """Sort downloads based on current sort option."""
        sort_by = self.sort_combo.currentText()
        
        if sort_by == "Sort by Date":
            downloads.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "Sort by Name":
            downloads.sort(key=lambda x: x.filename.lower())
        elif sort_by == "Sort by Size":
            downloads.sort(key=lambda x: x.total_bytes, reverse=True)
        elif sort_by == "Sort by Progress":
            downloads.sort(key=lambda x: x.progress, reverse=True)
    
    def update_queue(self):
        """Update the queue display."""
        self.queue_tree.clear()
        
        for item in self.download_queue:
            queue_item = QTreeWidgetItem(self.queue_tree)
            queue_item.setText(0, item.filename)
            queue_item.setText(1, item.file_size_display or "Unknown")
            queue_item.setText(2, item.status.capitalize())
            queue_item.setData(0, Qt.ItemDataRole.UserRole, item)
    
    def update_statistics(self):
        """Update statistics display."""
        total = len(self.downloads)
        active = len([d for d in self.downloads if d.status == "downloading"])
        completed = len([d for d in self.downloads if d.status == "completed"])
        failed = len([d for d in self.downloads if d.status == "failed"])
        
        self.total_downloads_label.setText(str(total))
        self.active_downloads_label.setText(str(active))
        self.completed_downloads_label.setText(str(completed))
        self.failed_downloads_label.setText(str(failed))
    
    def update_overall_progress(self):
        """Update overall progress bar."""
        downloading = [d for d in self.downloads if d.status == "downloading"]
        
        if downloading:
            total_progress = sum(d.progress for d in downloading)
            avg_progress = total_progress / len(downloading)
            self.overall_progress.setValue(int(avg_progress))
            self.overall_progress.setVisible(True)
        else:
            self.overall_progress.setVisible(False)
    
    def format_speed(self, speed: float) -> str:
        """Format speed for display."""
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if speed < 1024.0:
                return f"{speed:.1f} {unit}"
            speed /= 1024.0
        return f"{speed:.1f} TB/s"
    
    def format_time(self, seconds: int) -> str:
        """Format time for display."""
        if seconds <= 0:
            return "Unknown"
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def on_view_changed(self, text):
        """Handle view change."""
        self.update_downloads()
    
    def on_sort_changed(self, text):
        """Handle sort change."""
        self.update_downloads()
    
    def on_search_changed(self, text):
        """Handle search change."""
        self.update_downloads()
    
    def on_max_concurrent_changed(self, value):
        """Handle max concurrent downloads change."""
        self.max_concurrent_downloads = value
        self.process_queue()
    
    def browse_save_path(self):
        """Browse for save path."""
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if path:
            self.save_path_edit.setText(path)
            self.default_save_path = path
    
    def pause_all_downloads(self):
        """Pause all downloads."""
        for item in self.downloads:
            if item.status == "downloading":
                if item.id in self.download_workers:
                    self.download_workers[item.id].pause()
                item.status = "paused"
        
        self.update_downloads()
        self.status_label.setText("All downloads paused")
    
    def resume_all_downloads(self):
        """Resume all downloads."""
        for item in self.downloads:
            if item.status == "paused":
                if item.id in self.download_workers:
                    self.download_workers[item.id].resume()
                else:
                    # Restart the download
                    self.download_queue.append(item)
                item.status = "downloading"
        
        self.process_queue()
        self.update_downloads()
        self.status_label.setText("All downloads resumed")
    
    def clear_completed_downloads(self):
        """Clear completed downloads."""
        completed_count = len([d for d in self.downloads if d.status == "completed"])
        
        reply = QMessageBox.question(
            self, "Clear Completed", 
            f"Are you sure you want to remove {completed_count} completed downloads?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.downloads = [d for d in self.downloads if d.status != "completed"]
            self.save_downloads()
            self.update_downloads()
            self.status_label.setText(f"Cleared {completed_count} completed downloads")
    
    def start_queue(self):
        """Start the download queue."""
        self.process_queue()
        self.status_label.setText("Queue started")
    
    def stop_queue(self):
        """Stop the download queue."""
        # Cancel all active downloads
        for item in self.downloads:
            if item.status == "downloading":
                if item.id in self.download_workers:
                    self.download_workers[item.id].cancel()
                item.status = "cancelled"
        
        self.update_downloads()
        self.status_label.setText("Queue stopped")
    
    def open_download(self, item: QTreeWidgetItem, column: int):
        """Open downloaded file."""
        download_item = item.data(0, Qt.ItemDataRole.UserRole)
        if download_item and download_item.status == "completed":
            try:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(download_item.full_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(download_item.full_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(download_item.full_path)])
                
                self.status_label.setText(f"Opened: {download_item.filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")
    
    def show_context_menu(self, position):
        """Show context menu for downloads."""
        item = self.downloads_tree.itemAt(position)
        if not item:
            return
        
        download_item = item.data(0, Qt.ItemDataRole.UserRole)
        if not download_item:
            return
        
        menu = QMenu(self)
        style_manager.apply_stylesheet(menu, "menu")
        
        # Actions based on status
        if download_item.status == "downloading":
            pause_action = menu.addAction("Pause")
            pause_action.triggered.connect(lambda: self.pause_download(download_item))
            
            cancel_action = menu.addAction("Cancel")
            cancel_action.triggered.connect(lambda: self.cancel_download(download_item))
        
        elif download_item.status == "paused":
            resume_action = menu.addAction("Resume")
            resume_action.triggered.connect(lambda: self.resume_download(download_item))
            
            cancel_action = menu.addAction("Cancel")
            cancel_action.triggered.connect(lambda: self.cancel_download(download_item))
        
        elif download_item.status == "completed":
            open_action = menu.addAction("Open File")
            open_action.triggered.connect(lambda: self.open_download(item, 0))
            
            open_folder_action = menu.addAction("Open Folder")
            open_folder_action.triggered.connect(lambda: self.open_folder(download_item))
            
            retry_action = menu.addAction("Redownload")
            retry_action.triggered.connect(lambda: self.retry_download(download_item))
        
        elif download_item.status == "failed":
            retry_action = menu.addAction("Retry")
            retry_action.triggered.connect(lambda: self.retry_download(download_item))
        
        elif download_item.status == "cancelled":
            retry_action = menu.addAction("Retry")
            retry_action.triggered.connect(lambda: self.retry_download(download_item))
        
        menu.addSeparator()
        
        # Common actions
        copy_url_action = menu.addAction("Copy URL")
        copy_url_action.triggered.connect(lambda: self.copy_url(download_item))
        
        remove_action = menu.addAction("Remove from List")
        remove_action.triggered.connect(lambda: self.remove_download(download_item))
        
        menu.exec(self.downloads_tree.mapToGlobal(position))
    
    def pause_download(self, download_item: DownloadItem):
        """Pause a download."""
        if download_item.id in self.download_workers:
            self.download_workers[download_item.id].pause()
        download_item.status = "paused"
        self.update_downloads()
        self.status_label.setText(f"Paused: {download_item.filename}")
    
    def resume_download(self, download_item: DownloadItem):
        """Resume a download."""
        if download_item.id in self.download_workers:
            self.download_workers[download_item.id].resume()
        else:
            self.download_queue.append(download_item)
        download_item.status = "downloading"
        self.process_queue()
        self.update_downloads()
        self.status_label.setText(f"Resumed: {download_item.filename}")
    
    def cancel_download(self, download_item: DownloadItem):
        """Cancel a download."""
        if download_item.id in self.download_workers:
            self.download_workers[download_item.id].cancel()
        download_item.status = "cancelled"
        
        # Remove from queue
        if download_item in self.download_queue:
            self.download_queue.remove(download_item)
        
        self.update_downloads()
        self.status_label.setText(f"Cancelled: {download_item.filename}")
    
    def retry_download(self, download_item: DownloadItem):
        """Retry a failed download."""
        # Reset download state
        download_item.status = "pending"
        download_item.progress = 0.0
        download_item.downloaded_bytes = 0
        download_item.speed = 0.0
        download_item.time_remaining = 0
        download_item.error_message = ""
        
        # Remove partial file
        if download_item.full_path.exists():
            download_item.full_path.unlink()
        
        # Add to queue
        self.download_queue.append(download_item)
        self.process_queue()
        self.update_downloads()
        self.status_label.setText(f"Retrying: {download_item.filename}")
    
    def remove_download(self, download_item: DownloadItem):
        """Remove download from list."""
        if download_item.status == "downloading":
            reply = QMessageBox.question(
                self, "Remove Download", 
                f"Download '{download_item.filename}' is still downloading. Remove anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Cancel download first
            self.cancel_download(download_item)
        
        # Remove from lists
        self.downloads = [d for d in self.downloads if d.id != download_item.id]
        if download_item in self.download_queue:
            self.download_queue.remove(download_item)
        
        self.save_downloads()
        self.update_downloads()
        self.status_label.setText(f"Removed: {download_item.filename}")
    
    def open_folder(self, download_item: DownloadItem):
        """Open the folder containing the downloaded file."""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", str(download_item.full_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(download_item.full_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(download_item.full_path.parent)])
            
            self.status_label.setText(f"Opened folder for: {download_item.filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder: {e}")
    
    def copy_url(self, download_item: DownloadItem):
        """Copy download URL to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(download_item.url)
        self.status_label.setText("URL copied to clipboard")
    
    def load_downloads(self):
        """Load downloads from storage."""
        try:
            downloads_file = Path.home() / '.vertex_downloads.json'
            if downloads_file.exists():
                with open(downloads_file, 'r', encoding='utf-8') as f:
                    downloads_data = json.load(f)
                    self.downloads = [DownloadItem.from_dict(item) for item in downloads_data]
            else:
                self.downloads = []
        except Exception as e:
            print(f"Error loading downloads: {e}")
            self.downloads = []
    
    def save_downloads(self):
        """Save downloads to file."""
        try:
            downloads_file = Path.home() / '.vertex_downloads.json'
            downloads_data = [item.to_dict() for item in self.downloads]
            with open(downloads_file, 'w', encoding='utf-8') as f:
                json.dump(downloads_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving downloads: {e}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop all downloads
        for worker in self.download_workers.values():
            worker.cancel()
        
        # Wait for workers to finish
        for worker in self.download_workers.values():
            worker.wait()
        
        # Save downloads
        self.save_downloads()
        event.accept()


def show_download_manager(parent=None):
    """Show the download manager dialog."""
    dialog = DownloadManagerDialog(parent)
    dialog.show()
    return dialog
