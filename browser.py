#!/usr/bin/env python3.12
"""
Advanced Web Browser with Tabs and Navigation Features

Complete browser with tabs, address bar, history, bookmarks, resource downloading,
extension system, developer tools, and SSL/TLS support.
"""

import sys
import os
import threading
import time
import webbrowser
import requests
from pathlib import Path
import urllib3
import json
from datetime import datetime
import queue
import hashlib
import shutil
import urllib.parse
import ssl
import socket
import subprocess
import platform

# PyQt6 imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QPushButton, QLineEdit, 
                             QLabel, QFrame, QMenuBar, QMenu, QFileDialog,
                             QMessageBox, QStatusBar, QTextEdit, QSplitter,
                             QToolBar, QComboBox, QSpinBox, QCheckBox, QGroupBox,
                             QProgressBar, QListWidget, QListWidgetItem, QDialog,
                             QDialogButtonBox, QFormLayout, QGridLayout, QScrollArea,
                             QGraphicsDropShadowEffect, QToolButton, QSizePolicy,
                             QSpacerItem, QButtonGroup)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl, QDir, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QIcon, QFont, QPixmap, QKeySequence, QAction, QPalette, QColor, QPainter, QLinearGradient, QBrush
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile

# Import modern theme
from frontend.themes.modern_theme import theme, style_manager, animation_manager, ui_components

# PyQt6 WebEngine is always available with PyQt6-WebEngine
WEBENGINE_AVAILABLE = True

# Import extension system
try:
    from extensions.integration import ExtensionSystem
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False
    print("Extension system not available")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DownloadItem:
    """Represents a single download item."""
    
    def __init__(self, url, filename=None, download_dir=None):
        self.id = str(int(time.time() * 1000000))
        self.url = url
        self.filename = filename or self._extract_filename(url)
        self.download_dir = download_dir or str(Path.home() / "Downloads")
        self.full_path = Path(self.download_dir) / self.filename
        self.size = 0
        self.downloaded = 0
        self.status = "pending"  # pending, downloading, paused, completed, failed, cancelled
        self.speed = 0
        self.progress = 0.0
        self.start_time = None
        self.end_time = None
        self.thread = None
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancel_event = threading.Event()
        self.error_message = ""
        self.file_hash = ""
        self.content_type = ""
        self.resumable = False
        
    def _extract_filename(self, url):
        """Extract filename from URL."""
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        if path:
            filename = Path(path).name
            if filename:
                return filename
        return f"download_{self.id[:8]}"
    
    def get_speed_string(self):
        """Get human-readable speed."""
        if self.speed < 1024:
            return f"{self.speed:.1f} B/s"
        elif self.speed < 1024 * 1024:
            return f"{self.speed / 1024:.1f} KB/s"
        else:
            return f"{self.speed / (1024 * 1024):.1f} MB/s"
    
    def get_size_string(self):
        """Get human-readable size."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"
    
    def get_progress_string(self):
        """Get progress percentage string."""
        return f"{self.progress:.1f}%"
    
    def get_eta_string(self):
        """Get estimated time remaining."""
        if self.speed <= 0 or self.downloaded >= self.size:
            return "Unknown"
        
        remaining = self.size - self.downloaded
        eta_seconds = remaining / self.speed
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f}s"
        elif eta_seconds < 3600:
            return f"{eta_seconds / 60:.0f}m"
        else:
            return f"{eta_seconds / 3600:.1f}h"

class DownloadManager:
    """Manages all downloads with pause/resume functionality."""
    
    def __init__(self, browser):
        self.browser = browser
        self.downloads = []
        self.download_queue = queue.Queue()
        self.max_concurrent = 3
        self.active_downloads = []
        self.download_history_file = Path.home() / '.browser_downloads.json'
        self.default_download_dir = str(Path.home() / "Downloads")
        
        # Ensure download directory exists
        Path(self.default_download_dir).mkdir(exist_ok=True)
        
        # Load download history
        self.load_download_history()
        
        # Start download worker thread
        self.worker_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.worker_thread.start()
    
    def load_download_history(self):
        """Load download history from file."""
        try:
            if self.download_history_file.exists():
                with open(self.download_history_file, 'r') as f:
                    history = json.load(f)
                    # Convert to DownloadItem objects for completed downloads
                    for item in history:
                        if item.get('status') == 'completed':
                            download = DownloadItem(item['url'], item['filename'], item.get('download_dir'))
                            download.status = item['status']
                            download.size = item.get('size', 0)
                            download.downloaded = item.get('downloaded', 0)
                            download.start_time = item.get('start_time')
                            download.end_time = item.get('end_time')
                            download.file_hash = item.get('file_hash', '')
                            download.content_type = item.get('content_type', '')
                            self.downloads.append(download)
        except Exception as e:
            print(f"Failed to load download history: {e}")
    
    def save_download_history(self):
        """Save download history to file."""
        try:
            history = []
            for download in self.downloads:
                if download.status in ['completed', 'failed', 'cancelled']:
                    history.append({
                        'url': download.url,
                        'filename': download.filename,
                        'download_dir': download.download_dir,
                        'status': download.status,
                        'size': download.size,
                        'downloaded': download.downloaded,
                        'start_time': download.start_time,
                        'end_time': download.end_time,
                        'file_hash': download.file_hash,
                        'content_type': download.content_type
                    })
            
            with open(self.download_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Failed to save download history: {e}")
    
    def add_download(self, url, filename=None, download_dir=None):
        """Add a new download to the queue."""
        # Check if already downloading
        for download in self.downloads:
            if download.url == url and download.status in ['pending', 'downloading', 'paused']:
                QMessageBox.information(None, "Already Downloading", f"This file is already being downloaded: {download.filename}")
                return download
        
        download = DownloadItem(url, filename, download_dir)
        self.downloads.append(download)
        self.download_queue.put(download)
        
        # Update UI
        if hasattr(self.browser, 'download_manager_window'):
            self.browser.update_download_list()
        
        return download
    
    def _download_worker(self):
        """Background worker thread for downloads."""
        while True:
            try:
                # Wait for download task
                download = self.download_queue.get(timeout=1)
                
                # Check if we can start new download
                if len(self.active_downloads) < self.max_concurrent:
                    self.active_downloads.append(download)
                    download.thread = threading.Thread(target=self._download_file, args=(download,), daemon=True)
                    download.thread.start()
                else:
                    # Re-queue if max concurrent reached
                    self.download_queue.put(download)
                
                self.download_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Download worker error: {e}")
    
    def _download_file(self, download):
        """Download a file with pause/resume support."""
        try:
            download.status = "downloading"
            download.start_time = datetime.now().isoformat()
            
            # Check if file exists and can be resumed
            resume_pos = 0
            if download.full_path.exists():
                resume_pos = download.full_path.stat().st_size
                download.downloaded = resume_pos
                download.resumable = True
            
            # Get file info
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            response = requests.get(download.url, headers=headers, stream=True, timeout=30, verify=False)
            
            # Get file info
            if 'content-length' in response.headers:
                download.size = int(response.headers['content-length']) + resume_pos
            download.content_type = response.headers.get('content-type', '')
            
            # Check if server supports resume
            download.resumable = response.headers.get('accept-ranges') == 'bytes'
            
            # Open file for writing
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(download.full_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # Check for pause/cancel
                    if download.cancel_event.is_set():
                        download.status = "cancelled"
                        break
                    
                    download.pause_event.wait()
                    if download.status == "paused":
                        continue
                    
                    if chunk:
                        f.write(chunk)
                        download.downloaded += len(chunk)
                        
                        # Update progress
                        if download.size > 0:
                            download.progress = (download.downloaded / download.size) * 100
                        
                        # Calculate speed
                        if download.start_time:
                            elapsed = (datetime.now() - datetime.fromisoformat(download.start_time)).total_seconds()
                            if elapsed > 0:
                                download.speed = download.downloaded / elapsed
            
            # Update status
            if download.status != "cancelled" and download.status != "paused":
                if download.downloaded >= download.size and download.size > 0:
                    download.status = "completed"
                    download.end_time = datetime.now().isoformat()
                    download.progress = 100.0
                    
                    # Calculate file hash
                    try:
                        download.file_hash = self._calculate_file_hash(download.full_path)
                    except:
                        pass
                    
                    # Save to history
                    self.save_download_history()
                else:
                    download.status = "failed"
                    download.error_message = "Download incomplete"
            
        except Exception as e:
            download.status = "failed"
            download.error_message = str(e)
        
        finally:
            # Remove from active downloads
            if download in self.active_downloads:
                self.active_downloads.remove(download)
            
            # Update UI
            if hasattr(self.browser, 'download_manager_window'):
                self.browser.update_download_list()
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def pause_download(self, download_id):
        """Pause a download."""
        for download in self.downloads:
            if download.id == download_id and download.status == "downloading":
                download.status = "paused"
                download.pause_event.clear()
                return True
        return False
    
    def resume_download(self, download_id):
        """Resume a paused download."""
        for download in self.downloads:
            if download.id == download_id and download.status == "paused":
                download.status = "downloading"
                download.pause_event.set()
                
                # Re-queue if not in active downloads
                if download not in self.active_downloads:
                    self.download_queue.put(download)
                return True
        return False
    
    def cancel_download(self, download_id):
        """Cancel a download."""
        for download in self.downloads:
            if download.id == download_id and download.status in ['pending', 'downloading', 'paused']:
                download.cancel_event.set()
                download.status = "cancelled"
                
                # Remove partial file
                try:
                    if download.full_path.exists():
                        download.full_path.unlink()
                except:
                    pass
                
                # Remove from active downloads
                if download in self.active_downloads:
                    self.active_downloads.remove(download)
                
                # Update UI
                if hasattr(self.browser, 'download_manager_window'):
                    self.browser.update_download_list()
                return True
        return False
    
    def retry_download(self, download_id):
        """Retry a failed download."""
        for download in self.downloads:
            if download.id == download_id and download.status == 'failed':
                # Reset download state
                download.status = "pending"
                download.downloaded = 0
                download.progress = 0.0
                download.speed = 0
                download.error_message = ""
                download.cancel_event.clear()
                download.pause_event.set()
                
                # Re-queue
                self.download_queue.put(download)
                return True
        return False
    
    def get_download_stats(self):
        """Get overall download statistics."""
        total_downloads = len(self.downloads)
        completed = len([d for d in self.downloads if d.status == 'completed'])
        failed = len([d for d in self.downloads if d.status == 'failed'])
        downloading = len([d for d in self.downloads if d.status == 'downloading'])
        paused = len([d for d in self.downloads if d.status == 'paused'])
        
        total_size = sum(d.size for d in self.downloads if d.status == 'completed')
        total_downloaded = sum(d.downloaded for d in self.downloads if d.status in ['downloading', 'paused', 'completed'])
        
        return {
            'total': total_downloads,
            'completed': completed,
            'failed': failed,
            'downloading': downloading,
            'paused': paused,
            'total_size': total_size,
            'total_downloaded': total_downloaded
        }

class AdvancedBrowser(QMainWindow):
    """Advanced browser with tabs, navigation, and full features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vertex")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Apply modern theme
        theme.apply_theme(QApplication.instance())
        style_manager.apply_stylesheet(self, "main_window")
        
        # Set window properties for modern look
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # Load and set window icon
        try:
            icon_path = Path(__file__).parent / "Vertex Browser.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            print(f"Could not load browser icon: {e}")
        
        # Browser state
        self.tabs = []
        self.current_tab = None
        self.history = []
        self.bookmarks = []
        
        # Download manager
        self.download_manager = DownloadManager(self)
        self.download_manager_window = None
        
        # Web view availability
        self.webview_available = WEBENGINE_AVAILABLE
        if self.webview_available:
            print("Embedded web view available")
        else:
            print("Embedded web view not available")
        
        # Data files
        self.history_file = Path.home() / '.browser_history.json'
        self.bookmarks_file = Path.home() / '.browser_bookmarks.json'
        
        # Load saved data
        self.load_history()
        self.load_bookmarks()
        
        # Create session with SSL handling
        self.session = requests.Session()
        self.session.verify = False
        
        # Developer tools
        self.developer_tools_window = None
        self.console_messages = []
        self.network_requests = []
        
        # SSL/TLS configuration
        self.setup_ssl_context()
        
        # Setup UI with modern theme
        self.setup_ui()
        
        # Initialize extension system
        self.extension_system = None
        if EXTENSIONS_AVAILABLE:
            try:
                self.extension_system = ExtensionSystem(self)
                print("Extension system initialized")
            except Exception as e:
                print(f"Failed to initialize extension system: {e}")
        
        # Create initial tab with animation
        self.create_new_tab("about:blank")
        
        # Apply animations
        self.setup_animations()
    
    def setup_ui(self):
        """Setup the tabbed user interface with modern design."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with modern spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(theme.get_spacing('xs'), theme.get_spacing('xs'), 
                                      theme.get_spacing('xs'), theme.get_spacing('xs'))
        main_layout.setSpacing(theme.get_spacing('xs'))
        
        # Create modern toolbar
        self.create_modern_toolbar(main_layout)
        
        # Create modern tab widget
        self.create_modern_tab_widget(main_layout)
        
        # Create modern status bar
        self.create_modern_status_bar()
        
        # Create menu bar
        self.create_menu_bar()
    
    def create_modern_toolbar(self, parent_layout):
        """Create modern navigation toolbar with enhanced features."""
        # Main toolbar container
        toolbar_container = QFrame()
        toolbar_container.setProperty("class", "card")
        style_manager.apply_stylesheet(toolbar_container, "frame")
        
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('sm'), 
                                         theme.get_spacing('md'), theme.get_spacing('sm'))
        toolbar_layout.setSpacing(theme.get_spacing('sm'))
        
        # Navigation button group
        nav_group = QButtonGroup()
        
        # Back button with modern styling
        self.back_btn = self.create_modern_toolbar_button("←", "Back", "navigate_back")
        nav_group.addButton(self.back_btn)
        toolbar_layout.addWidget(self.back_btn)
        
        # Forward button
        self.forward_btn = self.create_modern_toolbar_button("→", "Forward", "navigate_forward")
        nav_group.addButton(self.forward_btn)
        toolbar_layout.addWidget(self.forward_btn)
        
        # Refresh button
        self.refresh_btn = self.create_modern_toolbar_button("↻", "Refresh", "navigate_refresh")
        nav_group.addButton(self.refresh_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        
        # Home button
        self.home_btn = self.create_modern_toolbar_button("Home", "Home", "navigate_home")
        nav_group.addButton(self.home_btn)
        toolbar_layout.addWidget(self.home_btn)
        
        # Separator
        separator = ui_components.create_modern_separator("vertical")
        toolbar_layout.addWidget(separator)
        
        # Address bar container with modern styling
        address_container = QFrame()
        address_layout = QHBoxLayout(address_container)
        address_layout.setContentsMargins(0, 0, 0, 0)
        address_layout.setSpacing(theme.get_spacing('xs'))
        
        # Lock/security indicator
        self.security_indicator = QLabel("Secure")
        self.security_indicator.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.security_indicator, "label")
        address_layout.addWidget(self.security_indicator)
        
        # Modern address bar
        self.address_entry = QLineEdit()
        self.address_entry.setPlaceholderText("Search or enter address...")
        self.address_entry.setMinimumHeight(40)
        style_manager.apply_stylesheet(self.address_entry, "address_bar")
        address_layout.addWidget(self.address_entry)
        
        # Search button
        self.search_btn = self.create_modern_toolbar_button("Search", "Search", "search")
        address_layout.addWidget(self.search_btn)
        
        toolbar_layout.addWidget(address_container, 1)  # Stretch
        
        # Separator
        separator2 = ui_components.create_modern_separator("vertical")
        toolbar_layout.addWidget(separator2)
        
        # Extension toolbar area
        self.extension_toolbar = QFrame()
        extension_layout = QHBoxLayout(self.extension_toolbar)
        extension_layout.setContentsMargins(0, 0, 0, 0)
        extension_layout.setSpacing(theme.get_spacing('xs'))
        toolbar_layout.addWidget(self.extension_toolbar)
        
        # Menu buttons
        self.bookmarks_btn = self.create_modern_toolbar_button("Bookmarks", "Bookmarks", "bookmarks")
        toolbar_layout.addWidget(self.bookmarks_btn)
        
        self.history_btn = self.create_modern_toolbar_button("History", "History", "history")
        toolbar_layout.addWidget(self.history_btn)
        
        self.downloads_btn = self.create_modern_toolbar_button("Downloads", "Downloads", "downloads")
        toolbar_layout.addWidget(self.downloads_btn)
        
        self.settings_btn = self.create_modern_toolbar_button("Settings", "Settings", "settings")
        toolbar_layout.addWidget(self.settings_btn)
        
        # Add toolbar to main layout
        parent_layout.addWidget(toolbar_container)
    
    def create_modern_toolbar_button(self, symbol: str, tooltip: str, action_name: str) -> QToolButton:
        """Create a modern toolbar button with enhanced styling."""
        button = QToolButton()
        button.setText(symbol)
        button.setToolTip(tooltip)
        button.setMinimumSize(36, 36)
        button.setMaximumSize(36, 36)
        
        # Set modern font for symbols
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        button.setFont(font)
        
        # Apply modern styling
        style_manager.apply_stylesheet(button, "button")
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 50))
        button.setGraphicsEffect(shadow)
        
        # Connect to action
        if action_name == "navigate_back":
            button.clicked.connect(self.go_back)
        elif action_name == "navigate_forward":
            button.clicked.connect(self.go_forward)
        elif action_name == "navigate_refresh":
            button.clicked.connect(self.refresh_page)
        elif action_name == "navigate_home":
            button.clicked.connect(self.go_home)
        elif action_name == "search":
            button.clicked.connect(self.search_from_address)
        elif action_name == "bookmarks":
            button.clicked.connect(self.show_bookmark_manager)
        elif action_name == "history":
            button.clicked.connect(self.show_history)
        elif action_name == "downloads":
            button.clicked.connect(self.show_download_manager)
        elif action_name == "settings":
            button.clicked.connect(self.show_settings)
        
        return button
    
    def create_modern_tab_widget(self, parent_layout):
        """Create modern tab widget with enhanced features."""
        # Tab widget container
        tab_container = QFrame()
        tab_container.setProperty("class", "card")
        style_manager.apply_stylesheet(tab_container, "frame")
        
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(theme.get_spacing('sm'), theme.get_spacing('sm'), 
                                     theme.get_spacing('sm'), theme.get_spacing('sm'))
        tab_layout.setSpacing(0)
        
        # Modern tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideRight)
        
        # Apply modern tab styling
        style_manager.apply_stylesheet(self.tab_widget, "tab_widget")
        
        # Custom tab bar with enhanced features
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setUsesScrollButtons(True)
        
        # Connect signals
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        tab_layout.addWidget(self.tab_widget)
        parent_layout.addWidget(tab_container, 1)  # Stretch
    
    def create_modern_status_bar(self):
        """Create modern status bar with enhanced information."""
        self.status_bar = QStatusBar()
        self.status_bar.setProperty("class", "modern")
        style_manager.apply_stylesheet(self.status_bar, "status_bar")
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.status_label, "label")
        self.status_bar.addWidget(self.status_label)
        
        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        style_manager.apply_stylesheet(self.progress_bar, "progress_bar")
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Page info
        self.page_info_label = QLabel("")
        self.page_info_label.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.page_info_label, "label")
        self.status_bar.addPermanentWidget(self.page_info_label)
        
        # Zoom level
        self.zoom_label = QLabel("100%")
        self.zoom_label.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.zoom_label, "label")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        self.setStatusBar(self.status_bar)
    
    def setup_animations(self):
        """Setup UI animations and transitions."""
        # Tab change animations
        self.tab_animation = QPropertyAnimation(self.tab_widget, b"geometry")
        self.tab_animation.setDuration(250)
        self.tab_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Button hover animations
        self.button_animations = {}
        
        # Status bar animation
        self.status_animation = QPropertyAnimation(self.status_label, b"geometry")
        self.status_animation.setDuration(150)
        self.status_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def on_tab_changed(self, index):
        """Handle tab change with animation."""
        if index >= 0 and index < len(self.tabs):
            self.current_tab = self.tabs[index]
            # Update address bar
            if self.current_tab:
                self.address_entry.setText(self.current_tab.get('url', ''))
                # Update navigation buttons
                self.update_navigation_buttons()
    
    def search_from_address(self):
        """Perform search from address bar."""
        query = self.address_entry.text().strip()
        if query:
            self.navigate_to_url(query, self.current_tab['id'] if self.current_tab else 0)
    
    def show_settings(self):
        """Show settings dialog."""
        try:
            from frontend.settings_panel import show_settings_panel
            show_settings_panel(self)
        except ImportError as e:
            print(f"Could not import settings panel: {e}")
            QMessageBox.information(self, "Settings", "Settings dialog would be implemented here.")
    
    def add_current_bookmark(self):
        """Add current page to bookmarks."""
        if self.current_tab and self.current_tab['url']:
            try:
                from frontend.bookmark_manager import BookmarkEditDialog
                
                bookmark_data = {
                    'title': self.current_tab['title'],
                    'url': self.current_tab['url'],
                    'description': f"Bookmarked from {self.current_tab['url']}",
                    'folder': 'General',
                    'tags': [],
                    'private': False,
                    'readonly': False,
                }
                
                dialog = BookmarkEditDialog(bookmark_data, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    new_bookmark = dialog.get_bookmark_data()
                    
                    # Load existing bookmarks
                    bookmarks_file = Path.home() / '.vertex_bookmarks.json'
                    bookmarks = []
                    if bookmarks_file.exists():
                        try:
                            with open(bookmarks_file, 'r', encoding='utf-8') as f:
                                bookmarks = json.load(f)
                        except:
                            pass
                    
                    bookmarks.append(new_bookmark)
                    
                    # Save bookmarks
                    with open(bookmarks_file, 'w', encoding='utf-8') as f:
                        json.dump(bookmarks, f, indent=2, ensure_ascii=False)
                    
                    QMessageBox.information(self, "Bookmark Added", f"Bookmark added for: {new_bookmark['title']}")
                    
            except ImportError as e:
                print(f"Could not import bookmark manager: {e}")
                # Fallback to simple bookmark
                bookmark = {
                    'title': self.current_tab['title'],
                    'url': self.current_tab['url'],
                    'timestamp': datetime.now().isoformat()
                }
                self.bookmarks.append(bookmark)
                self.save_bookmarks()
                QMessageBox.information(self, "Bookmark Added", f"Bookmark added for: {bookmark['title']}")
        else:
            QMessageBox.information(self, "No Tab", "No active tab to bookmark.")
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Tab", self.create_new_tab)
        file_menu.addAction("Close Tab", lambda: self.close_tab(self.current_tab['id']) if self.current_tab else None)
        file_menu.addSeparator()
        file_menu.addAction("Open File", self.open_local_file)
        file_menu.addAction("Save Page As...", self.save_page_as)
        file_menu.addSeparator()
        file_menu.addAction("Print", self.print_page)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo", self.undo_action)
        edit_menu.addAction("Redo", self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction("Cut", self.cut_action)
        edit_menu.addAction("Copy", self.copy_action)
        edit_menu.addAction("Paste", self.paste_action)
        edit_menu.addAction("Select All", self.select_all_action)
        edit_menu.addSeparator()
        edit_menu.addAction("Find", self.find_in_page)
        edit_menu.addAction("Find Next", self.find_next)
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Zoom In", self.zoom_in)
        view_menu.addAction("Zoom Out", self.zoom_out)
        view_menu.addAction("Reset Zoom", self.reset_zoom)
        view_menu.addSeparator()
        view_menu.addAction("View Source", self.view_source)
        view_menu.addAction("View Page Info", self.view_page_info)
        view_menu.addSeparator()
        view_menu.addAction("Full Screen", self.toggle_fullscreen)
        
        # History menu
        history_menu = menubar.addMenu("History")
        history_menu.addAction("Show History", self.show_history)
        history_menu.addSeparator()
        history_menu.addAction("Back", self.go_back)
        history_menu.addAction("Forward", self.go_forward)
        history_menu.addAction("Home", self.go_home)
        
        # Bookmarks menu
        bookmarks_menu = menubar.addMenu("Bookmarks")
        bookmarks_menu.addAction("Add Bookmark", self.add_current_bookmark)
        bookmarks_menu.addAction("Bookmark Manager", self.show_bookmark_manager)
        bookmarks_menu.addAction("Import Bookmarks", self.import_bookmarks)
        bookmarks_menu.addAction("Export Bookmarks", self.export_bookmarks)
        bookmarks_menu.addSeparator()
        
        # Add recent bookmarks
        recent_bookmarks = [b for b in self.bookmarks if b.get('type') == 'bookmark'][-5:]
        for bookmark in recent_bookmarks:
            bookmarks_menu.addAction(
                bookmark['title'][:30], 
                lambda u=bookmark['url']: self.navigate_to_url(u, self.current_tab['id'])
            )
        
        # Downloads menu
        downloads_menu = menubar.addMenu("Downloads")
        downloads_menu.addAction("Download Settings", self.create_download_settings_dialog)
        downloads_menu.addAction("Clear History", self.clear_browser_history)
        downloads_menu.addAction("Clear Cache", self.clear_cache)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction("Developer Tools", self.show_developer_tools)
        tools_menu.addAction("Extensions", self.show_extensions)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)
        help_menu.addAction("Help", self.show_help)
        help_menu.addAction("Check for Updates", self.check_for_updates)
    
    def open_local_file(self):
        """Open a local file in the browser."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            QDir.homePath(),
            "HTML files (*.html *.htm);;Text files (*.txt);;Images (*.png *.jpg *.jpeg *.gif *.bmp);;All files (*.*)"
        )
        
        if filename:
            file_url = f"file://{filename}"
            self.navigate_to_url(file_url, self.current_tab['id'])
    
    def save_page_as(self):
        """Save the current page as a file."""
        if not self.current_tab:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Page As",
            QDir.homePath(),
            "HTML files (*.html);;Text files (*.txt);;All files (*.*)"
        )
        
        if filename:
            try:
                # Get page content
                if self.current_tab['view_mode'] == 'web' and hasattr(self.current_tab, 'web_view'):
                    # Try to get HTML content from embedded browser
                    content = f"<html><body><h1>Page saved from: {self.current_tab['url']}</h1></body></html>"
                else:
                    # Get content from text view
                    content = self.current_tab['details_text'].toPlainText()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(self, "Success", f"Page saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save page:\n{e}")
    
    def print_page(self):
        """Print the current page."""
        QMessageBox.information(self, "Print", "Print functionality would be implemented here.")
    
    def undo_action(self):
        """Undo action."""
        if self.current_tab and hasattr(self.current_tab, 'details_text'):
            try:
                self.current_tab['details_text'].undo()
            except:
                pass
    
    def redo_action(self):
        """Redo action."""
        if self.current_tab and hasattr(self.current_tab, 'details_text'):
            try:
                self.current_tab['details_text'].redo()
            except:
                pass
    
    def cut_action(self):
        """Cut selected text."""
        if self.current_tab and hasattr(self.current_tab, 'details_text'):
            try:
                self.current_tab['details_text'].cut()
            except:
                pass
    
    def copy_action(self):
        """Copy selected text."""
        if self.current_tab and hasattr(self.current_tab, 'details_text'):
            try:
                self.current_tab['details_text'].copy()
            except:
                pass
    
    def paste_action(self):
        """Paste text."""
        if self.current_tab and hasattr(self.current_tab, 'details_text'):
            try:
                self.current_tab['details_text'].paste()
            except:
                pass
    
    def select_all_action(self):
        """Select all text."""
        if self.current_tab and hasattr(self.current_tab, 'details_text'):
            try:
                self.current_tab['details_text'].selectAll()
            except:
                pass
    
    def run(self):
        """Run the browser application."""
        self.show()
        
    def find_in_page(self):
        """Find text in page."""
        if not self.current_tab:
            return
        
        # Create find dialog
        find_dialog = tk.Toplevel(self.root)
        find_dialog.title("Find in Page")
        find_dialog.geometry("400x150")
        find_dialog.transient(self.root)
        find_dialog.grab_set()
        
        # Find entry
        tk.Label(find_dialog, text="Find:").pack(anchor="w", padx=10, pady=(10, 2))
        find_var = tk.StringVar()
        find_entry = tk.Entry(find_dialog, textvariable=find_var, width=40)
        find_entry.pack(padx=10, pady=(0, 10))
        find_entry.focus()
        
        # Options
        options_frame = tk.Frame(find_dialog)
        options_frame.pack(padx=10, pady=5)
        
        case_var = tk.BooleanVar()
        case_check = tk.Checkbutton(options_frame, text="Match case", variable=case_var)
        case_check.pack(side="left")
        
        # Buttons
        button_frame = tk.Frame(find_dialog)
        button_frame.pack(pady=10)
        
        def find_next():
            text = self.current_tab['details_text']
            search_term = find_var.get()
            if not search_term:
                return
            
            # Configure search
            options = {}
            if not case_var.get():
                options = {"regexp": True, "nocase": True}
            
            # Find next occurrence
            pos = text.search(search_term, "insert", "end", **options)
            if pos:
                text.mark_set("insert", pos)
                text.see(pos)
                # Highlight the match
                end_pos = f"{pos}+{len(search_term)}c"
                text.tag_remove("sel", "1.0", "end")
                text.tag_add("sel", pos, end_pos)
            else:
                messagebox.showinfo("Not Found", f"'{search_term}' not found")
        
        def find_previous():
            text = self.current_tab['details_text']
            search_term = find_var.get()
            if not search_term:
                return
            
            # Configure search
            options = {}
            if not case_var.get():
                options = {"regexp": True, "nocase": True}
            
            # Find previous occurrence
            pos = text.search(search_term, "insert", "1.0", backwards=True, **options)
            if pos:
                text.mark_set("insert", pos)
                text.see(pos)
                # Highlight the match
                end_pos = f"{pos}+{len(search_term)}c"
                text.tag_remove("sel", "1.0", "end")
                text.tag_add("sel", pos, end_pos)
            else:
                messagebox.showinfo("Not Found", f"'{search_term}' not found")
        
        tk.Button(button_frame, text="Find Next", command=find_next).pack(side="left", padx=2)
        tk.Button(button_frame, text="Find Previous", command=find_previous).pack(side="left", padx=2)
        tk.Button(button_frame, text="Close", command=find_dialog.destroy).pack(side="right", padx=2)
        
        # Bind Enter key
        find_entry.bind("<Return>", lambda e: find_next())
    
    def find_next(self):
        """Find next occurrence."""
        # This would find the next occurrence of the last search term
        pass
    
    def zoom_in(self):
        """Zoom in the page."""
        messagebox.showinfo("Zoom", "Zoom functionality would be implemented here.")
    
    def zoom_out(self):
        """Zoom out the page."""
        messagebox.showinfo("Zoom", "Zoom functionality would be implemented here.")
    
    def reset_zoom(self):
        """Reset zoom to default."""
        messagebox.showinfo("Zoom", "Zoom reset would be implemented here.")
    
    def view_source(self):
        """View page source."""
        if not self.current_tab:
            return
        
        # Create source viewer window
        source_win = tk.Toplevel(self.root)
        source_win.title(f"Source: {self.current_tab['url']}")
        source_win.geometry("800x600")
        source_win.transient(self.root)
        
        # Source text
        source_text = scrolledtext.ScrolledText(source_win, wrap="none", font=('Courier', 10))
        source_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load source
        try:
            response = requests.get(self.current_tab['url'], timeout=10, verify=False)
            source_text.insert(1.0, response.text)
        except Exception as e:
            source_text.insert(1.0, f"Error loading source: {e}")
        
        source_text.configure(state='disabled')
    
    def view_page_info(self):
        """View page information."""
        if not self.current_tab:
            return
        
        # Create info dialog
        info_win = tk.Toplevel(self.root)
        info_win.title("Page Information")
        info_win.geometry("400x300")
        info_win.transient(self.root)
        
        # Info frame
        info_frame = tk.Frame(info_win)
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Display information
        info_text = f"""
URL: {self.current_tab['url']}
Title: {self.current_tab['url']}
View Mode: {self.current_tab['view_mode'].title()}
History Entries: {len(self.current_tab['history'])}
Current Index: {self.current_tab['history_index']}
        """
        
        tk.Label(info_frame, text=info_text, justify="left", anchor="w").pack(fill="both", expand=True)
        
        tk.Button(info_frame, text="Close", command=info_win.destroy).pack(pady=10)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
    
    def clear_browser_history(self):
        """Clear browser history."""
        if messagebox.askyesno("Clear History", "Clear all browsing history? This cannot be undone."):
            self.history = []
            self.save_history()
            
            # Clear tab histories
            for tab in self.tabs:
                tab['history'] = []
                tab['history_index'] = -1
            
            messagebox.showinfo("History Cleared", "Browsing history has been cleared.")
    
    def clear_cache(self):
        """Clear browser cache."""
        messagebox.showinfo("Clear Cache", "Cache clearing would be implemented here.")
    
    def show_developer_tools(self):
        """Show developer tools."""
        if self.developer_tools_window and self.developer_tools_window.winfo_exists():
            self.developer_tools_window.lift()
            return
        
        # Create developer tools window
        self.developer_tools_window = tk.Toplevel(self.root)
        self.developer_tools_window.title("Developer Tools")
        self.developer_tools_window.geometry("1000x600")
        self.developer_tools_window.transient(self.root)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.developer_tools_window)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Console tab
        console_frame = ttk.Frame(notebook)
        notebook.add(console_frame, text="Console")
        
        # Console output
        console_output = scrolledtext.ScrolledText(console_frame, wrap="word", height=20)
        console_output.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add existing console messages
        for msg in self.console_messages:
            console_output.insert("end", f"[{msg['timestamp']}] {msg['level']}: {msg['message']}\n")
        
        # Console input
        input_frame = tk.Frame(console_frame)
        input_frame.pack(fill="x", padx=5, pady=5)
        
        input_var = tk.StringVar()
        input_entry = tk.Entry(input_frame, textvariable=input_var, font=('Courier', 10))
        input_entry.pack(side="left", fill="x", expand=True)
        input_entry.bind("<Return>", lambda e: self.execute_console_command(input_var.get(), console_output))
        
        execute_btn = tk.Button(input_frame, text="Execute", command=lambda: self.execute_console_command(input_var.get(), console_output))
        execute_btn.pack(side="right", padx=5)
        
        # Network tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Network")
        
        # Network request treeview
        columns = ('Method', 'URL', 'Status', 'Type', 'Size', 'Time')
        network_tree = ttk.Treeview(network_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            network_tree.heading(col, text=col)
            network_tree.column(col, width=150)
        
        # Add scrollbar
        network_scrollbar = ttk.Scrollbar(network_frame, orient='vertical', command=network_tree.yview)
        network_tree.configure(yscrollcommand=network_scrollbar.set)
        
        network_tree.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
        network_scrollbar.pack(side='right', fill='y', padx=(0, 5), pady=5)
        
        # Add existing network requests
        for req in self.network_requests:
            network_tree.insert('', 'end', values=(
                req['method'],
                req['url'][:50] + "..." if len(req['url']) > 50 else req['url'],
                req['status'],
                req['type'],
                req['size'],
                req['time']
            ))
        
        # Elements tab
        elements_frame = ttk.Frame(notebook)
        notebook.add(elements_frame, text="Elements")
        
        # Element treeview
        element_tree = ttk.Treeview(elements_frame, columns=('tag', 'class', 'id'), show='tree headings')
        element_tree.heading('#0', text='Element')
        element_tree.heading('tag', text='Tag')
        element_tree.heading('class', text='Class')
        element_tree.heading('id', text='ID')
        
        element_tree.column('#0', width=200)
        element_tree.column('tag', width=100)
        element_tree.column('class', width=150)
        element_tree.column('id', width=150)
        
        element_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add sample DOM structure (in real implementation, this would parse actual page)
        self.add_sample_dom_structure(element_tree)
        
        # Storage tab
        storage_frame = ttk.Frame(notebook)
        notebook.add(storage_frame, text="Storage")
        
        # Storage treeview
        storage_notebook = ttk.Notebook(storage_frame)
        storage_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Local storage
        local_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(local_frame, text="Local Storage")
        
        local_tree = ttk.Treeview(local_frame, columns=('key', 'value'), show='headings')
        local_tree.heading('key', text='Key')
        local_tree.heading('value', text='Value')
        local_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Session storage
        session_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(session_frame, text="Session Storage")
        
        session_tree = ttk.Treeview(session_frame, columns=('key', 'value'), show='headings')
        session_tree.heading('key', text='Key')
        session_tree.heading('value', text='Value')
        session_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cookies
        cookies_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(cookies_frame, text="Cookies")
        
        cookies_tree = ttk.Treeview(cookies_frame, columns=('name', 'value', 'domain', 'path'), show='headings')
        cookies_tree.heading('name', text='Name')
        cookies_tree.heading('value', text='Value')
        cookies_tree.heading('domain', text='Domain')
        cookies_tree.heading('path', text='Path')
        cookies_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add sample data (in real implementation, this would read actual storage)
        self.add_sample_storage_data(local_tree, session_tree, cookies_tree)
        
        # Clear button
        clear_btn = tk.Button(console_frame, text="Clear Console", command=lambda: console_output.delete(1.0, "end"))
        clear_btn.pack(pady=5)
    
    def execute_console_command(self, command, console_output):
        """Execute a console command."""
        if not command.strip():
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            # Simple command evaluation (in real implementation, this would be more sophisticated)
            if command.startswith('console.log'):
                # Extract the argument
                arg = command[11:].strip()
                if arg.startswith("'") and arg.endswith("'"):
                    arg = arg[1:-1]
                elif arg.startswith('"') and arg.endswith('"'):
                    arg = arg[1:-1]
                
                result = arg
                console_output.insert("end", f"[{timestamp}] log: {result}\n")
                self.console_messages.append({
                    'timestamp': timestamp,
                    'level': 'log',
                    'message': result
                })
            
            elif command == 'clear()':
                console_output.delete(1.0, "end")
                console_output.insert("end", f"[{timestamp}] Console cleared\n")
            
            elif command == 'help()':
                help_text = """
Available commands:
- console.log(message) - Log a message
- clear() - Clear console
- help() - Show this help
- document.title - Get page title
- window.location - Get current URL
                """
                console_output.insert("end", f"[{timestamp}] {help_text}\n")
            
            else:
                # Try to evaluate as JavaScript-like expression
                if 'document.title' in command:
                    if self.current_tab:
                        title = self.current_tab.get('title', 'Unknown')
                        console_output.insert("end", f"[{timestamp}] {title}\n")
                        self.console_messages.append({
                            'timestamp': timestamp,
                            'level': 'result',
                            'message': title
                        })
                elif 'window.location' in command:
                    if self.current_tab:
                        url = self.current_tab.get('url', 'Unknown')
                        console_output.insert("end", f"[{timestamp}] {url}\n")
                        self.console_messages.append({
                            'timestamp': timestamp,
                            'level': 'result',
                            'message': url
                        })
                else:
                    console_output.insert("end", f"[{timestamp}] Unknown command: {command}\n")
                    self.console_messages.append({
                        'timestamp': timestamp,
                        'level': 'error',
                        'message': f"Unknown command: {command}"
                    })
        
        except Exception as e:
            console_output.insert("end", f"[{timestamp}] Error: {str(e)}\n")
            self.console_messages.append({
                'timestamp': timestamp,
                'level': 'error',
                'message': str(e)
            })
        
        console_output.see("end")
    
    def add_sample_dom_structure(self, tree):
        """Add sample DOM structure to elements tree."""
        # Root
        root = tree.insert('', 'end', text='document', values=('', '', ''))
        
        # Head
        head = tree.insert(root, 'end', text='head', values=('head', '', ''))
        tree.insert(head, 'end', text='title', values=('title', '', ''))
        tree.insert(head, 'end', text='meta', values=('meta', '', ''))
        tree.insert(head, 'end', text='link', values=('link', '', ''))
        
        # Body
        body = tree.insert(root, 'end', text='body', values=('body', '', ''))
        header = tree.insert(body, 'end', text='header', values=('header', 'site-header', ''))
        tree.insert(header, 'end', text='nav', values=('nav', 'main-nav', ''))
        
        main = tree.insert(body, 'end', text='main', values=('main', 'content', ''))
        article = tree.insert(main, 'end', text='article', values=('article', 'post', 'post-1'))
        tree.insert(article, 'end', text='h1', values=('h1', 'title', ''))
        tree.insert(article, 'end', text='p', values=('p', 'content', ''))
        
        footer = tree.insert(body, 'end', text='footer', values=('footer', 'site-footer', ''))
        tree.insert(footer, 'end', text='div', values=('div', 'copyright', ''))
    
    def add_sample_storage_data(self, local_tree, session_tree, cookies_tree):
        """Add sample storage data."""
        # Local storage
        local_data = [
            ('theme', 'dark'),
            ('language', 'en'),
            ('last_visit', datetime.now().isoformat()),
            ('user_preferences', '{"fontSize": 14, "showBookmarks": true}')
        ]
        
        for key, value in local_data:
            local_tree.insert('', 'end', values=(key, value))
        
        # Session storage
        session_data = [
            ('session_id', 'abc123def456'),
            ('csrf_token', 'xyz789uvw012'),
            ('page_views', '42')
        ]
        
        for key, value in session_data:
            session_tree.insert('', 'end', values=(key, value))
        
        # Cookies
        cookie_data = [
            ('session_id', 'abc123def456', '.example.com', '/'),
            ('preferences', 'dark_mode%3Dtrue', '.example.com', '/'),
            ('analytics_id', 'GA-12345678', '.example.com', '/')
        ]
        
        for name, value, domain, path in cookie_data:
            cookies_tree.insert('', 'end', values=(name, value, domain, path))
    
    def setup_ssl_context(self):
        """Setup SSL/TLS context for secure connections."""
        try:
            # Create SSL context
            self.ssl_context = ssl.create_default_context()
            
            # Allow self-signed certificates for development
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            
            # Configure cipher suites
            self.ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            # Set minimum TLS version
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            print("SSL/TLS context configured successfully")
            
        except Exception as e:
            print(f"Error setting up SSL context: {e}")
            self.ssl_context = None
    
    def log_network_request(self, method, url, status, request_type, size, duration):
        """Log a network request for developer tools."""
        self.network_requests.append({
            'method': method,
            'url': url,
            'status': status,
            'type': request_type,
            'size': size,
            'time': f"{duration:.2f}ms",
            'timestamp': datetime.now()
        })
        
        # Keep only last 100 requests
        if len(self.network_requests) > 100:
            self.network_requests = self.network_requests[-100:]
    
    def log_console_message(self, level, message):
        """Log a console message for developer tools."""
        self.console_messages.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'level': level,
            'message': message
        })
        
        # Keep only last 50 messages
        if len(self.console_messages) > 50:
            self.console_messages = self.console_messages[-50:]
    
    def show_extensions(self):
        """Show extensions manager."""
        if self.extension_system:
            self.extension_system.show_extension_manager()
        else:
            messagebox.showinfo("Extensions", "Extension system is not available.")
    
    def show_about(self):
        """Show about dialog."""
        about_win = tk.Toplevel(self.root)
        about_win.title("About Advanced Web Browser")
        about_win.geometry("400x300")
        about_win.transient(self.root)
        
        # About frame
        about_frame = tk.Frame(about_win)
        about_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # About text
        about_text = """
Advanced Web Browser
Version 1.0

A modern web browser with:
• Tabbed browsing
• Download management
• Bookmark system
• History tracking
• Embedded web view

Built with Python and Tkinter
        """
        
        tk.Label(about_frame, text=about_text, justify="center").pack(expand=True)
        
        tk.Button(about_frame, text="Close", command=about_win.destroy).pack(pady=10)
    
    def show_help(self):
        """Show help dialog."""
        help_win = tk.Toplevel(self.root)
        help_win.title("Help")
        help_win.geometry("600x400")
        help_win.transient(self.root)
        
        # Help text
        help_text = scrolledtext.ScrolledText(help_win, wrap="word")
        help_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        help_content = """
Advanced Web Browser - Help

Navigation:
• Enter URLs or search terms in the address bar
• Use Back/Forward buttons to navigate
• Use Home button to go to the home page

Tabs:
• Click + to create a new tab
• Click tab buttons to switch between tabs
• Right-click tabs for more options

Bookmarks:
• Click "Add Bookmark" to save current page
• Use "Bookmarks" button to manage bookmarks
• Import/export bookmarks for backup

Downloads:
• Click "Downloads" to open download manager
• Pause/resume/cancel downloads
• Choose download locations
• View download history

Shortcuts:
• Ctrl+T: New tab
• Ctrl+W: Close tab
• Ctrl+F: Find in page
• Ctrl+L: Focus address bar

For more help, visit the project documentation.
        """
        
        help_text.insert(1.0, help_content)
        help_text.configure(state='disabled')
    
    def check_for_updates(self):
        """Check for updates."""
        messagebox.showinfo("Updates", "Update checking would be implemented here.")
    
    def create_new_tab(self, url="about:blank"):
        """Create a new browser tab with modern styling."""
        tab_id = len(self.tabs)
        
        # Create tab widget with modern styling
        tab_widget = QWidget()
        tab_widget.setProperty("class", "tab_content")
        style_manager.apply_stylesheet(tab_widget, "widget")
        
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # Create web view for tab
        web_view = QWebEngineView()
        web_view.setProperty("class", "web_view")
        
        # Connect web view signals
        web_view.titleChanged.connect(lambda title: self.on_tab_title_changed(tab_id, title))
        web_view.urlChanged.connect(lambda url: self.on_tab_url_changed(tab_id, url))
        web_view.loadStarted.connect(lambda: self.on_tab_load_started(tab_id))
        web_view.loadFinished.connect(lambda success: self.on_tab_load_finished(tab_id, success))
        
        tab_layout.addWidget(web_view)
        
        # Create tab data
        tab_data = {
            'id': tab_id,
            'title': f"Tab {tab_id + 1}",
            'url': url,
            'history': [],
            'history_index': -1,
            'widget': tab_widget,
            'web_view': web_view,
            'view_mode': 'web',
            'loading': False,
            'favicon': None,
        }
        
        # Add tab to tab widget with modern styling
        index = self.tab_widget.addTab(tab_widget, tab_data['title'])
        self.tab_widget.setCurrentIndex(index)
        
        # Add to tabs list
        self.tabs.append(tab_data)
        self.current_tab = tab_data
        
        # Load URL if provided
        if url and url != "about:blank":
            self.navigate_to_url(url, tab_id)
        else:
            # Load a welcome page for new tabs
            self.load_welcome_page(tab_id)
        
        # Apply tab animation
        self.animate_tab_creation(index)
        
        return tab_id
    
    def load_welcome_page(self, tab_id):
        """Load a welcome page for new tabs."""
        tab = self.tabs[tab_id] if tab_id < len(self.tabs) else None
        if tab and tab['web_view']:
            welcome_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Welcome</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #1A237E 0%, #3949AB 100%);
                        color: white;
                        margin: 0;
                        padding: 0;
                        height: 100vh;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                    }}
                    .container {{
                        max-width: 600px;
                        padding: 40px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                    }}
                    h1 {{
                        font-size: 48px;
                        margin-bottom: 20px;
                        background: linear-gradient(45deg, #2196F3, #03A9F4);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    }}
                    .search-box {{
                        margin: 30px 0;
                    }}
                    input {{
                        width: 80%;
                        padding: 15px 20px;
                        border: none;
                        border-radius: 25px;
                        background: rgba(255, 255, 255, 0.2);
                        color: white;
                        font-size: 16px;
                        backdrop-filter: blur(10px);
                    }}
                    input::placeholder {{
                        color: rgba(255, 255, 255, 0.7);
                    }}
                    button {{
                        padding: 15px 30px;
                        margin: 10px;
                        border: none;
                        border-radius: 25px;
                        background: linear-gradient(45deg, #2196F3, #03A9F4);
                        color: white;
                        font-size: 16px;
                        cursor: pointer;
                        transition: transform 0.2s;
                    }}
                    button:hover {{
                        transform: translateY(-2px);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Vertex</h1>
                    <p style="font-size: 18px; opacity: 0.9;">Start browsing the web</p>
                    
                    <div class="search-box">
                        <input type="text" placeholder="Search the web or enter a URL..." id="searchInput">
                        <br>
                        <button onclick="performSearch()">Search</button>
                    </div>
                    
                    <p style="opacity: 0.7; font-size: 14px; margin-top: 30px;">
                        Start browsing by typing a search query or URL in the address bar above
                    </p>
                </div>
                
                <script>
                    function performSearch() {{
                        const query = document.getElementById('searchInput').value;
                        if (query) {{
                            window.location.href = `https://duckduckgo.com/?q=${{encodeURIComponent(query)}}`;
                        }}
                    }}
                    
                    document.getElementById('searchInput').addEventListener('keypress', function(e) {{
                        if (e.key === 'Enter') {{
                            performSearch();
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            tab['web_view'].setHtml(welcome_html, QUrl("about:blank"))
    
    def animate_tab_creation(self, index):
        """Animate tab creation."""
        if index >= 0:
            # Create a subtle scale animation for new tabs
            animation = QPropertyAnimation(self.tab_widget, b"geometry")
            animation.setDuration(200)
            animation.setEasingCurve(QEasingCurve.Type.OutBack)
            animation.start()
    
    def on_tab_title_changed(self, tab_id, title):
        """Handle tab title change."""
        if tab_id < len(self.tabs):
            self.tabs[tab_id]['title'] = title
            # Update tab widget title
            index = self.get_tab_index(tab_id)
            if index >= 0:
                self.tab_widget.setTabText(index, title)
    
    def on_tab_url_changed(self, tab_id, url):
        """Handle tab URL change."""
        if tab_id < len(self.tabs):
            self.tabs[tab_id]['url'] = url.toString()
            # Update address bar if this is the current tab
            if self.current_tab and self.current_tab['id'] == tab_id:
                self.address_entry.setText(url.toString())
                self.update_security_indicator(url.toString())
    
    def on_tab_load_started(self, tab_id):
        """Handle tab load start."""
        if tab_id < len(self.tabs):
            self.tabs[tab_id]['loading'] = True
            # Show progress bar
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            # Update status
            self.status_label.setText("Loading...")
    
    def on_tab_load_finished(self, tab_id, success):
        """Handle tab load finish."""
        if tab_id < len(self.tabs):
            self.tabs[tab_id]['loading'] = False
            # Hide progress bar
            self.progress_bar.setVisible(False)
            # Update status
            if success:
                self.status_label.setText("Ready")
            else:
                self.status_label.setText("Load failed")
    
    def get_tab_index(self, tab_id):
        """Get tab widget index by tab ID."""
        for i, tab in enumerate(self.tabs):
            if tab['id'] == tab_id:
                return i
        return -1
    
    def update_security_indicator(self, url):
        """Update security indicator based on URL."""
        if url.startswith('https://'):
            self.security_indicator.setText("Secure")
            self.security_indicator.setToolTip("Secure connection")
        elif url.startswith('http://'):
            self.security_indicator.setText("Not Secure")
            self.security_indicator.setToolTip("Not secure")
        else:
            self.security_indicator.setText("Local")
            self.security_indicator.setToolTip("Local page")
    
    def close_tab(self, tab_id):
        """Close a browser tab."""
        if len(self.tabs) <= 1:
            return  # Don't close the last tab
        
        # Find tab
        tab_to_close = None
        for i, tab in enumerate(self.tabs):
            if tab['id'] == tab_id:
                tab_to_close = tab
                index = i
                break
        
        if tab_to_close:
            # Remove from tab widget
            self.tab_widget.removeTab(index)
            
            # Remove from tabs list
            self.tabs.remove(tab_to_close)
            
            # Set new current tab if needed
            if self.current_tab == tab_to_close:
                self.current_tab = self.tabs[0] if self.tabs else None
                if self.current_tab:
                    # Find the index of the new current tab
                    for i, tab in enumerate(self.tabs):
                        if tab == self.current_tab:
                            self.tab_widget.setCurrentIndex(i)
                            break
    
    def navigate_to_address(self):
        """Navigate to address in address bar."""
        url = self.address_entry.text().strip()
        if self.current_tab and url:
            self.navigate_to_url(url, self.current_tab['id'])
    
    def navigate_to_url(self, url, tab_id):
        """Navigate to a URL in a specific tab."""
        # Find tab
        tab = None
        for t in self.tabs:
            if t['id'] == tab_id:
                tab = t
                break
        
        if not tab or not tab['web_view']:
            return
        
        # Clean and process the input
        original_input = url.strip()
        processed_url = original_input
        
        # Check if the input is a URL or a search query
        if self.is_url(original_input):
            # It's a URL, format it properly
            if not original_input.startswith(('http://', 'https://', 'file://', 'about:', 'ftp://')):
                processed_url = 'https://' + original_input
        else:
            # It's a search query, convert to search URL
            processed_url = self.create_search_url(original_input)
            print(f"Searching for: {original_input}")
        
        # Load the URL
        tab['url'] = processed_url
        tab['web_view'].load(QUrl(processed_url))
        
        # Update address bar to show the original input for search queries
        if tab == self.current_tab:
            if self.is_url(original_input):
                self.address_entry.setText(processed_url)
            else:
                self.address_entry.setText(original_input)
        
        # Add to history (use the processed URL for URLs, original query for searches)
        history_entry = processed_url if self.is_url(original_input) else original_input
        tab['history'].append(history_entry)
        tab['history_index'] = len(tab['history']) - 1
        
        # Add to global history
        self.add_to_history(processed_url)
        
        # Update status bar
        if self.is_url(original_input):
            self.status_label.setText(f"Loading: {processed_url}")
        else:
            self.status_label.setText(f"Searching for: {original_input}")
        
        # Update navigation buttons
        self.update_navigation_buttons()
    
    def switch_to_tab(self, tab_id):
        """Switch to a specific tab."""
        # Find tab
        tab = None
        for i, t in enumerate(self.tabs):
            if t['id'] == tab_id:
                tab = t
                self.tab_widget.setCurrentIndex(i)
                break
        
        if tab:
            self.current_tab = tab
            # Update address bar
            self.address_entry.setText(tab['url'])
    
    def go_back(self):
        """Go back in history."""
        if self.current_tab and self.current_tab['history_index'] > 0:
            self.current_tab['history_index'] -= 1
            url = self.current_tab['history'][self.current_tab['history_index']]
            self.navigate_to_url(url, self.current_tab['id'])
    
    def go_forward(self):
        """Go forward in history."""
        if (self.current_tab and 
            self.current_tab['history_index'] < len(self.current_tab['history']) - 1):
            self.current_tab['history_index'] += 1
            url = self.current_tab['history'][self.current_tab['history_index']]
            self.navigate_to_url(url, self.current_tab['id'])
    
    def refresh_page(self):
        """Refresh current page."""
        if self.current_tab and self.current_tab['web_view']:
            self.current_tab['web_view'].reload()
    
    def go_home(self):
        """Go to home page."""
        if self.current_tab:
            self.navigate_to_url("about:blank", self.current_tab['id'])
    
    def add_to_history(self, url):
        """Add URL to global history."""
        if url not in self.history:
            self.history.append({
                'url': url,
                'title': url,
                'timestamp': datetime.now().isoformat()
            })
    
    def is_url(self, text):
        """Check if text is a URL."""
        text = text.strip()
        
        # Check for common URL patterns
        if text.startswith(('http://', 'https://', 'file://', 'about:', 'ftp://')):
            return True
        
        # Check for domain-like patterns
        if '.' in text and not text.isspace():
            # Check if it looks like a domain (has at least one dot and no spaces)
            # and doesn't contain common search query indicators
            words = text.split()
            if len(words) == 1:  # Single word without spaces
                # Check if it has domain-like structure
                if '.' in text and not text.endswith('.'):
                    # Additional checks for common TLDs
                    common_tlds = ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co', '.ai', '.dev']
                    if any(text.lower().endswith(tld) for tld in common_tlds):
                        return True
                    # If it has dots but doesn't look like a search query, treat as URL
                    if text.count('.') >= 1 and len(text) > 3:
                        return True
        
        return False
    
    def create_search_url(self, query):
        """Create a search URL for the given query."""
        # Use DuckDuckGo for privacy-focused search
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://duckduckgo.com/?q={encoded_query}"
    
    def load_history(self):
        """Load browser history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Failed to load history: {e}")
            self.history = []
    
    def save_history(self):
        """Save browser history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")
    
    def load_bookmarks(self):
        """Load bookmarks from file."""
        try:
            if self.bookmarks_file.exists():
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
        except Exception as e:
            print(f"Failed to load bookmarks: {e}")
            self.bookmarks = []
    
    def save_bookmarks(self):
        """Save bookmarks to file."""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Failed to save bookmarks: {e}")
    
    def setup_ssl_context(self):
        """Setup SSL/TLS context."""
        try:
            # Create SSL context
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            print("SSL/TLS context configured successfully")
        except Exception as e:
            print(f"SSL/TLS context setup failed: {e}")
    
    # Placeholder methods for menu items
    def show_bookmark_manager(self):
        """Show bookmark manager."""
        try:
            from frontend.bookmark_manager import show_bookmark_manager
            show_bookmark_manager(self)
        except ImportError as e:
            print(f"Could not import bookmark manager: {e}")
            QMessageBox.information(self, "Bookmarks", "Bookmark manager would be implemented here.")
    
    def show_history(self):
        """Show browser history."""
        try:
            from frontend.history_manager import show_history_manager
            show_history_manager(self)
        except ImportError as e:
            print(f"Could not import history manager: {e}")
            QMessageBox.information(self, "History", f"History contains {len(self.history)} items.")
    
    def show_download_manager(self):
        """Show download manager."""
        try:
            from frontend.download_manager import show_download_manager
            show_download_manager(self)
        except ImportError as e:
            print(f"Could not import download manager: {e}")
            QMessageBox.information(self, "Downloads", "Download manager would be implemented here.")
    
    def zoom_in(self):
        """Zoom in."""
        QMessageBox.information(self, "Zoom", "Zoom in would be implemented here.")
    
    def zoom_out(self):
        """Zoom out."""
        QMessageBox.information(self, "Zoom", "Zoom out would be implemented here.")
    
    def reset_zoom(self):
        """Reset zoom."""
        QMessageBox.information(self, "Zoom", "Reset zoom would be implemented here.")
    
    def view_source(self):
        """View page source."""
        QMessageBox.information(self, "View Source", "View source would be implemented here.")
    
    def view_page_info(self):
        """View page info."""
        QMessageBox.information(self, "Page Info", "Page info would be implemented here.")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def import_bookmarks(self):
        """Import bookmarks."""
        QMessageBox.information(self, "Import", "Import bookmarks would be implemented here.")
    
    def export_bookmarks(self):
        """Export bookmarks."""
        QMessageBox.information(self, "Export", "Export bookmarks would be implemented here.")
    
    def clear_browser_history(self):
        """Clear browser history."""
        self.history = []
        self.save_history()
        QMessageBox.information(self, "History Cleared", "Browser history has been cleared.")
    
    def clear_cache(self):
        """Clear cache."""
        QMessageBox.information(self, "Cache Cleared", "Cache would be cleared here.")
    
    def show_developer_tools(self):
        """Show developer tools."""
        QMessageBox.information(self, "Developer Tools", "Developer tools would be implemented here.")
    
    def show_extensions(self):
        """Show extensions."""
        QMessageBox.information(self, "Extensions", "Extensions would be implemented here.")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Vertex Browser", "Vertex Browser\nA modern web browser built with PyQt6")
    
    def show_help(self):
        """Show help."""
        QMessageBox.information(self, "Help", "Help would be implemented here.")
    
    def find_in_page(self):
        """Find text in page."""
        QMessageBox.information(self, "Find", "Find in page would be implemented here.")
    
    def find_next(self):
        """Find next occurrence."""
        QMessageBox.information(self, "Find", "Find next would be implemented here.")
    
    def create_download_settings_dialog(self):
        """Create download settings dialog."""
        QMessageBox.information(self, "Download Settings", "Download settings would be implemented here.")
    
    def update_navigation_buttons(self):
        """Update navigation button states."""
        if not self.current_tab:
            return
        
        can_go_back = self.current_tab['history_index'] > 0
        can_go_forward = (self.current_tab['history_index'] < 
                        len(self.current_tab['history']) - 1)
        
        # Update toolbar buttons
        self.back_btn.setEnabled(can_go_back)
        self.forward_btn.setEnabled(can_go_forward)
        
        # Update button opacity based on state
        back_opacity = 1.0 if can_go_back else 0.3
        forward_opacity = 1.0 if can_go_forward else 0.3
        
        self.back_btn.setStyleSheet(f"QToolButton {{ opacity: {back_opacity}; }}")
        self.forward_btn.setStyleSheet(f"QToolButton {{ opacity: {forward_opacity}; }}")
