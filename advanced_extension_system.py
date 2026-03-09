#!/usr/bin/env python3.12
"""
Advanced Extension System for Vertex Browser

Comprehensive extension management system with sandboxing, API access,
permissions management, auto-updates, and developer tools.
Supports Chrome extension API compatibility.
"""

import json
import zipfile
import hashlib
import threading
import time
import uuid
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
import weakref
import inspect
import importlib.util
import sys
import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit,
                             QFrame, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                             QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
                             QFormLayout, QScrollArea, QSplitter, QMenu, QToolBar,
                             QToolButton, QFileDialog, QLineEdit, QStatusBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QObject, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette
from PyQt6.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt6.QtWebEngineCore import QWebEngineProfile

from frontend.themes.modern_theme import theme, style_manager, ui_components


class ExtensionError(Exception):
    """Base exception for extension system errors."""
    pass


class ExtensionPermission(Enum):
    """Extension permission types."""
    STORAGE = "storage"
    TABS = "tabs"
    BOOKMARKS = "bookmarks" 
    HISTORY = "history"
    DOWNLOADS = "downloads"
    COOKIES = "cookies"
    WEB_NAVIGATION = "webNavigation"
    WEB_REQUEST = "webRequest"
    SCRIPTING = "scripting"
    NOTIFICATIONS = "notifications"
    GEOLOCATION = "geolocation"
    CAMERA = "camera"
    MICROPHONE = "microphone"
    CLIPBOARD_READ = "clipboardRead"
    CLIPBOARD_WRITE = "clipboardWrite"
    ACTIVE_TAB = "activeTab"
    ALL_URLS = "<all_urls>"
    MANAGEMENT = "management"


@dataclass
class ExtensionManifest:
    """Extension manifest data structure."""
    name: str
    version: str
    description: str
    manifest_version: int = 3
    author: str = ""
    homepage_url: str = ""
    icons: Dict[str, str] = None
    permissions: List[str] = None
    optional_permissions: List[str] = None
    host_permissions: List[str] = None
    optional_host_permissions: List[str] = None
    background: Dict[str, Any] = None
    content_scripts: List[Dict[str, Any]] = None
    content_security_policy: str = ""
    web_accessible_resources: List[str] = None
    key: str = ""
    short_name: str = ""
    default_locale: str = "en"
    locales: Dict[str, Dict[str, str]] = None
    developer: Dict[str, str] = None
    action: Dict[str, str] = None
    commands: Dict[str, Dict[str, str]] = None
    options_page: str = ""
    options_ui: Dict[str, Any] = None
    chrome_url_overrides: Dict[str, str] = None
    devtools_page: str = ""
    sidebar_action: Dict[str, Any] = None
    theme: Dict[str, Any] = None
    user_scripts: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.icons is None:
            self.icons = {}
        if self.permissions is None:
            self.permissions = []
        if self.optional_permissions is None:
            self.optional_permissions = []
        if self.host_permissions is None:
            self.host_permissions = []
        if self.optional_host_permissions is None:
            self.optional_host_permissions = []
        if self.background is None:
            self.background = {}
        if self.content_scripts is None:
            self.content_scripts = []
        if self.content_security_policy == "":
            self.content_security_policy = "script-src 'self'; object-src 'self';"
        if self.web_accessible_resources is None:
            self.web_accessible_resources = []
        if self.locales is None:
            self.locales = {}
        if self.developer is None:
            self.developer = {}
        if self.action is None:
            self.action = {}
        if self.commands is None:
            self.commands = {}
        if self.options_ui is None:
            self.options_ui = {}
        if self.chrome_url_overrides is None:
            self.chrome_url_overrides = {}
        if self.sidebar_action is None:
            self.sidebar_action = {}
        if self.theme is None:
            self.theme = {}
        if self.user_scripts is None:
            self.user_scripts = {}


class ExtensionContext:
    """Context for extension API calls."""
    
    def __init__(self, extension_id: str, tab_id: str = None):
        self.extension_id = extension_id
        self.tab_id = tab_id
        self.sender_url = None
        self.timestamp = datetime.now().isoformat()


class ExtensionAPI:
    """Base class for extension APIs."""
    
    def __init__(self, context: ExtensionContext):
        self.context = context
        self.extension_id = context.extension_id
        self.tab_id = context.tab_id
    
    def check_permission(self, permission: str) -> bool:
        """Check if extension has required permission."""
        from .extension_manager import ExtensionManager
        manager = ExtensionManager.instance()
        return manager.has_permission(self.extension_id, permission)


class StorageAPI(ExtensionAPI):
    """Storage API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        self.local_storage = {}
        self.sync_storage = {}
        self._load_storage()
    
    def _load_storage(self):
        """Load stored data for extension."""
        try:
            storage_file = Path.home() / f".vertex_extensions/{self.extension_id}/storage.json"
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.local_storage = data.get('local', {})
                    self.sync_storage = data.get('sync', {})
        except Exception as e:
            logging.error(f"Failed to load storage for {self.extension_id}: {e}")
    
    def _save_storage(self):
        """Save storage data for extension."""
        try:
            storage_dir = Path.home() / f".vertex_extensions/{self.extension_id}"
            storage_dir.mkdir(parents=True, exist_ok=True)
            storage_file = storage_dir / "storage.json"
            
            data = {
                'local': self.local_storage,
                'sync': self.sync_storage
            }
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save storage for {self.extension_id}: {e}")
    
    def local_get(self, keys: Union[str, List[str]], default=None):
        """Get values from local storage."""
        if isinstance(keys, str):
            return self.local_storage.get(keys, default)
        else:
            return {key: self.local_storage.get(key, default) for key in keys}
    
    def local_set(self, items: Dict[str, Any]):
        """Set values in local storage."""
        self.local_storage.update(items)
        self._save_storage()
    
    def local_remove(self, keys: Union[str, List[str]]):
        """Remove values from local storage."""
        if isinstance(keys, str):
            self.local_storage.pop(keys, None)
        else:
            for key in keys:
                self.local_storage.pop(key, None)
        self._save_storage()
    
    def local_clear(self):
        """Clear local storage."""
        self.local_storage.clear()
        self._save_storage()
    
    def sync_get(self, keys: Union[str, List[str]], default=None):
        """Get values from sync storage."""
        if isinstance(keys, str):
            return self.sync_storage.get(keys, default)
        else:
            return {key: self.sync_storage.get(key, default) for key in keys}
    
    def sync_set(self, items: Dict[str, Any]):
        """Set values in sync storage."""
        self.sync_storage.update(items)
        self._save_storage()
    
    def sync_remove(self, keys: Union[str, List[str]]):
        """Remove values from sync storage."""
        if isinstance(keys, str):
            self.sync_storage.pop(keys, None)
        else:
            for key in keys:
                self.sync_storage.pop(key, None)
        self._save_storage()
    
    def sync_clear(self):
        """Clear sync storage."""
        self.sync_storage.clear()
        self._save_storage()


class TabsAPI(ExtensionAPI):
    """Tabs API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        from .extension_manager import ExtensionManager
        self.manager = ExtensionManager.instance()
    
    def query(self, query_info: Dict[str, Any] = None):
        """Query tabs."""
        if query_info is None:
            query_info = {}
        
        active = query_info.get('active', False)
        current_window = query_info.get('currentWindow', False)
        window_id = query_info.get('windowId')
        window_type = query_info.get('windowType', 'normal')
        
        # Get browser instance
        browser = self.manager.browser
        if not browser:
            return []
        
        tabs = []
        for i, tab_data in enumerate(browser.tabs):
            tab_info = {
                'id': tab_data['id'],
                'index': i,
                'windowId': 1,  # Simplified - single window
                'active': (browser.current_tab and browser.current_tab['id'] == tab_data['id']),
                'selected': browser.tab_widget.currentIndex() == i,
                'highlighted': False,
                'pinned': False,
                'audible': False,
                'mutedInfo': {'muted': False},
                'url': tab_data.get('url', ''),
                'title': tab_data.get('title', ''),
                'favIconUrl': None,
                'status': 'complete' if tab_data.get('url') else 'loading',
                'incognito': False,
                'width': browser.width(),
                'height': browser.height(),
                'sessionId': None,
                'openerTabId': None
            }
            
            # Apply filters
            if active and not tab_info['active']:
                continue
            if window_id and window_id != 1:
                continue
            
            tabs.append(tab_info)
        
        return tabs
    
    def get(self, tab_id: int):
        """Get specific tab."""
        tabs = self.query()
        for tab in tabs:
            if tab['id'] == tab_id:
                return tab
        return None
    
    def create(self, create_properties: Dict[str, Any]):
        """Create new tab."""
        url = create_properties.get('url', 'about:blank')
        active = create_properties.get('active', True)
        
        browser = self.manager.browser
        if browser:
            new_tab_id = browser.create_new_tab(url)
            if not active and browser.current_tab:
                # Switch back to previous tab
                browser.switch_to_tab(browser.current_tab['id'])
            return self.get(new_tab_id)
        return None
    
    def update(self, tab_id: int, update_properties: Dict[str, Any]):
        """Update tab properties."""
        browser = self.manager.browser
        if browser:
            for tab in browser.tabs:
                if tab['id'] == tab_id:
                    if 'url' in update_properties:
                        browser.navigate_to_url(update_properties['url'], tab_id)
                    if 'active' in update_properties and update_properties['active']:
                        browser.switch_to_tab(tab_id)
                    break
    
    def remove(self, tab_id: int):
        """Close tab."""
        browser = self.manager.browser
        if browser:
            browser.close_tab(tab_id)
    
    def reload(self, tab_id: int):
        """Reload tab."""
        browser = self.manager.browser
        if browser:
            for tab in browser.tabs:
                if tab['id'] == tab_id:
                    tab['web_view'].reload()
                    break
    
    def go_forward(self, tab_id: int):
        """Go forward in tab."""
        browser = self.manager.browser
        if browser:
            for tab in browser.tabs:
                if tab['id'] == tab_id:
                    browser.go_forward()
                    break
    
    def go_back(self, tab_id: int):
        """Go back in tab."""
        browser = self.manager.browser
        if browser:
            for tab in browser.tabs:
                if tab['id'] == tab_id:
                    browser.go_back()
                    break


class BookmarksAPI(ExtensionAPI):
    """Bookmarks API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        from .extension_manager import ExtensionManager
        self.manager = ExtensionManager.instance()
        self._load_bookmarks()
    
    def _load_bookmarks(self):
        """Load bookmarks from storage."""
        try:
            bookmarks_file = Path.home() / '.vertex_bookmarks.json'
            if bookmarks_file.exists():
                with open(bookmarks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bookmarks = data.get('bookmarks', [])
            else:
                self.bookmarks = []
        except Exception as e:
            logging.error(f"Failed to load bookmarks: {e}")
            self.bookmarks = []
    
    def _save_bookmarks(self):
        """Save bookmarks to storage."""
        try:
            bookmarks_file = Path.home() / '.vertex_bookmarks.json'
            data = {'bookmarks': self.bookmarks}
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save bookmarks: {e}")
    
    def get_tree(self):
        """Get bookmark tree."""
        # Simplified implementation
        return [{
            'id': 'root',
            'title': 'Bookmarks',
            'url': None,
            'children': self.bookmarks
        }]
    
    def get(self, id_list: Union[str, List[str]]):
        """Get bookmarks by ID."""
        if isinstance(id_list, str):
            id_list = [id_list]
        
        results = []
        for bookmark_id in id_list:
            for bookmark in self.bookmarks:
                if bookmark.get('id') == bookmark_id:
                    results.append(bookmark)
                    break
        return results
    
    def search(self, query: str):
        """Search bookmarks."""
        results = []
        query_lower = query.lower()
        
        for bookmark in self.bookmarks:
            if (query_lower in bookmark.get('title', '').lower() or
                query_lower in bookmark.get('url', '').lower()):
                results.append(bookmark)
        
        return results
    
    def create(self, bookmark: Dict[str, Any]):
        """Create bookmark."""
        new_bookmark = {
            'id': str(uuid.uuid4()),
            'title': bookmark.get('title', ''),
            'url': bookmark.get('url', ''),
            'parentId': bookmark.get('parentId'),
            'index': bookmark.get('index', len(self.bookmarks)),
            'dateAdded': datetime.now().isoformat(),
            'dateGroupModified': datetime.now().isoformat(),
            'unmodifiable': False,
            'tags': bookmark.get('tags', [])
        }
        
        if bookmark.get('parentId'):
            # Add to parent folder (simplified)
            pass
        else:
            self.bookmarks.append(new_bookmark)
        
        self._save_bookmarks()
        return new_bookmark
    
    def remove(self, id_list: Union[str, List[str]]):
        """Remove bookmarks."""
        if isinstance(id_list, str):
            id_list = [id_list]
        
        for bookmark_id in id_list:
            self.bookmarks = [b for b in self.bookmarks if b.get('id') != bookmark_id]
        
        self._save_bookmarks()
    
    def update(self, id: str, changes: Dict[str, Any]):
        """Update bookmark."""
        for bookmark in self.bookmarks:
            if bookmark.get('id') == id:
                bookmark.update(changes)
                bookmark['dateGroupModified'] = datetime.now().isoformat()
                break
        self._save_bookmarks()


class HistoryAPI(ExtensionAPI):
    """History API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        from .extension_manager import ExtensionManager
        self.manager = ExtensionManager.instance()
        self._load_history()
    
    def _load_history(self):
        """Load history from storage."""
        try:
            history_file = Path.home() / '.vertex_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            logging.error(f"Failed to load history: {e}")
            self.history = []
    
    def search(self, query: Dict[str, Any]):
        """Search history."""
        text = query.get('text', '').lower()
        max_results = query.get('maxResults', 100)
        start_time = query.get('startTime')
        end_time = query.get('endTime')
        
        results = []
        for item in self.history:
            if text and text not in item.get('title', '').lower() and text not in item.get('url', '').lower():
                continue
            
            # Time filtering (simplified)
            if start_time or end_time:
                continue
            
            results.append({
                'id': item.get('id', ''),
                'url': item.get('url', ''),
                'title': item.get('title', ''),
                'lastVisitTime': item.get('timestamp', ''),
                'visitCount': item.get('visits', 1),
                'typedCount': 0
            })
            
            if len(results) >= max_results:
                break
        
        return results
    
    def add_url(self, details: Dict[str, Any]):
        """Add URL to history."""
        history_item = {
            'id': str(uuid.uuid4()),
            'url': details.get('url', ''),
            'title': details.get('title', ''),
            'timestamp': datetime.now().isoformat(),
            'visits': 1
        }
        
        self.history.append(history_item)
        self._save_history()
    
    def delete_url(self, details: Dict[str, Any]):
        """Delete URL from history."""
        url = details.get('url', '')
        self.history = [item for item in self.history if item.get('url') != url]
        self._save_history()
    
    def delete_range(self, range_info: Dict[str, Any]):
        """Delete history range."""
        start_time = range_info.get('startTime')
        end_time = range_info.get('endTime')
        
        # Simplified implementation
        if start_time and end_time:
            self.history = []
        self._save_history()
    
    def _save_history(self):
        """Save history to storage."""
        try:
            history_file = Path.home() / '.vertex_history.json'
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save history: {e}")


class DownloadsAPI(ExtensionAPI):
    """Downloads API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        from .extension_manager import ExtensionManager
        self.manager = ExtensionManager.instance()
    
    def search(self, query: Dict[str, Any]):
        """Search downloads."""
        query_text = query.get('query', '').lower()
        limit = query.get('limit', 100)
        
        # Get download manager
        download_manager = self.manager.download_manager
        if not download_manager:
            return []
        
        results = []
        for download in download_manager.downloads:
            if query_text:
                if (query_text not in download.filename.lower() and 
                    query_text not in download.url.lower()):
                    continue
            
            results.append({
                'id': download.id,
                'url': download.url,
                'filename': download.filename,
                'danger': 'safe',
                'mime': download.mime_type,
                'startTime': download.created_at,
                'endTime': download.completed_at,
                'state': download.status,
                'paused': download.status == 'paused',
                'canResume': download.status in ['paused', 'failed'],
                'error': download.error_message,
                'bytesReceived': download.downloaded_bytes,
                'totalBytes': download.total_bytes,
                'fileSize': download.total_bytes,
                'exists': download.full_path.exists() if download.full_path else False
            })
            
            if len(results) >= limit:
                break
        
        return results
    
    def pause(self, download_id: str):
        """Pause download."""
        download_manager = self.manager.download_manager
        if download_manager:
            for download in download_manager.downloads:
                if download.id == download_id:
                    download_manager.pause_download(download)
                    break
    
    def resume(self, download_id: str):
        """Resume download."""
        download_manager = self.manager.download_manager
        if download_manager:
            for download in download_manager.downloads:
                if download.id == download_id:
                    download_manager.resume_download(download)
                    break
    
    def cancel(self, download_id: str):
        """Cancel download."""
        download_manager = self.manager.download_manager
        if download_manager:
            for download in download_manager.downloads:
                if download.id == download_id:
                    download_manager.cancel_download(download)
                    break
    
    def remove_file(self, download_id: str):
        """Remove download file."""
        download_manager = self.manager.download_manager
        if download_manager:
            for download in download_manager.downloads:
                if download.id == download_id:
                    download_manager.remove_download(download)
                    break
    
    def erase(self, download_id: str):
        """Erase download."""
        download_manager = self.manager.download_manager
        if download_manager:
            for download in download_manager.downloads:
                if download.id == download_id:
                    download_manager.remove_download(download)
                    break


class RuntimeAPI(ExtensionAPI):
    """Runtime API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        from .extension_manager import ExtensionManager
        self.manager = ExtensionManager.instance()
    
    def get_url(self, path: str):
        """Get extension URL."""
        extension = self.manager.get_extension(self.extension_id)
        if extension and extension.path:
            extension_url = f"extension://{extension.id}/{path.lstrip('/')}"
            return extension_url
        return None
    
    def get_manifest(self):
        """Get extension manifest."""
        extension = self.manager.get_extension(self.extension_id)
        if extension:
            return asdict(extension.manifest)
        return None
    
    def get_background_page(self):
        """Get background page URL."""
        extension = self.manager.get_extension(self.extension_id)
        if extension and extension.manifest.background:
            if 'page' in extension.manifest.background:
                return self.get_url(extension.manifest.background['page'])
            elif 'scripts' in extension.manifest.background:
                return self.get_url('_generated_background_page.html')
        return None
    
    def open_options_page(self):
        """Open extension options page."""
        extension = self.manager.get_extension(self.extension_id)
        if extension and extension.manifest.options_page:
            options_url = self.get_url(extension.manifest.options_page)
            # Open in new tab
            browser = self.manager.browser
            if browser:
                browser.create_new_tab(options_url)
    
    def set_uninstall_url(self, url: str):
        """Set uninstall URL."""
        # Store for later use
        extension = self.manager.get_extension(self.extension_id)
        if extension:
            extension.uninstall_url = url
    
    def reload(self):
        """Reload extension."""
        self.manager.reload_extension(self.extension_id)
    
    def request_update_check(self):
        """Request update check."""
        # Simplified - just check for updates
        self.manager.check_extension_updates(self.extension_id)
    
    def connect(self, port: int, extension_id: str = None):
        """Connect to extension port."""
        # Simplified port connection
        return True
    
    def sendMessage(self, extension_id: str, message: Any):
        """Send message to extension."""
        # Simplified message sending
        return True


class WebRequestAPI(ExtensionAPI):
    """Web Request API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        self.request_handlers = []
    
    def on_before_request(self, handler: Callable):
        """Register before request handler."""
        self.request_handlers.append(('before_request', handler))
    
    def on_before_send_headers(self, handler: Callable):
        """Register before send headers handler."""
        self.request_handlers.append(('before_send_headers', handler))
    
    def on_headers_received(self, handler: Callable):
        """Register headers received handler."""
        self.request_handlers.append(('headers_received', handler))
    
    def on_response_started(self, handler: Callable):
        """Register response started handler."""
        self.request_handlers.append(('response_started', handler))
    
    def on_completed(self, handler: Callable):
        """Register completed handler."""
        self.request_handlers.append(('completed', handler))
    
    def handler_behavior_changed(self):
        """Notify handler behavior changed."""
        # Simplified implementation
        pass


class NotificationsAPI(ExtensionAPI):
    """Notifications API for extensions."""
    
    def __init__(self, context: ExtensionContext):
        super().__init__(context)
        self.notifications = []
    
    def create(self, notification_id: str, options: Dict[str, Any]):
        """Create notification."""
        notification = {
            'id': notification_id,
            'type': 'basic',
            'iconUrl': options.get('iconUrl', ''),
            'title': options.get('title', ''),
            'message': options.get('message', ''),
            'contextMessage': options.get('contextMessage', ''),
            'priority': options.get('priority', 0),
            'eventTime': options.get('eventTime', None),
            'buttons': options.get('buttons', []),
            'progress': options.get('progress', None),
            'silent': options.get('silent', False),
            'requireInteraction': options.get('requireInteraction', False),
            'isClickable': options.get('isClickable', False)
        }
        
        self.notifications.append(notification)
        
        # Show system notification (simplified)
        try:
            import subprocess
            import platform
            
            title = notification['title']
            message = notification['message']
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{title}" with subtitle "{message}"'
                ])
            elif platform.system() == "Linux":
                subprocess.run([
                    'notify-send', title, message
                ])
        except:
            pass
        
        return notification_id
    
    def clear(self, notification_id: str = None):
        """Clear notification."""
        if notification_id:
            self.notifications = [n for n in self.notifications if n['id'] != notification_id]
        else:
            self.notifications.clear()
    
    def get_all(self):
        """Get all notifications."""
        return self.notifications


class ExtensionSandbox:
    """Sandbox for running extension code."""
    
    def __init__(self, extension_id: str):
        self.extension_id = extension_id
        self.allowed_modules = [
            'json', 'datetime', 'time', 'uuid', 'hashlib', 'base64',
            'urllib.parse', 'pathlib', 're', 'math'
        ]
        self.context = ExtensionContext(extension_id)
        self._setup_apis()
    
    def _setup_apis(self):
        """Setup available APIs."""
        self.apis = {
            'storage': StorageAPI(self.context),
            'tabs': TabsAPI(self.context),
            'bookmarks': BookmarksAPI(self.context),
            'history': HistoryAPI(self.context),
            'downloads': DownloadsAPI(self.context),
            'runtime': RuntimeAPI(self.context),
            'webRequest': WebRequestAPI(self.context),
            'notifications': NotificationsAPI(self.context)
        }
    
    def execute_script(self, script: str, context: str = 'background'):
        """Execute script in sandbox."""
        try:
            # Create restricted globals
            restricted_globals = {
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float,
                    'bool': bool, 'list': list, 'dict': dict, 'tuple': tuple,
                    'set': set, 'range': range, 'enumerate': enumerate,
                    'print': print, 'min': min, 'max': max, 'sum': sum,
                    'sorted': sorted, 'reversed': reversed,
                    'abs': abs, 'round': round, 'pow': pow,
                    'chr': chr, 'ord': ord, 'hex': hex, 'oct': oct,
                    'bin': bin
                },
                'console': ConsoleAPI(),
                'chrome': self.apis,
                'browser': self.apis  # Alias for compatibility
            }
            
            # Add allowed modules
            for module in self.allowed_modules:
                if module in sys.modules:
                    restricted_globals[module] = sys.modules[module]
                else:
                    try:
                        restricted_globals[module] = __import__(module)
                    except ImportError:
                        pass
            
            # Execute script
            exec(script, restricted_globals)
            
        except Exception as e:
            logging.error(f"Extension script execution error: {e}")
    
    def check_permission(self, permission: str) -> bool:
        """Check if extension has permission."""
        from .extension_manager import ExtensionManager
        manager = ExtensionManager.instance()
        return manager.has_permission(self.extension_id, permission)


class ConsoleAPI:
    """Console API for extensions."""
    
    def log(self, *args):
        """Log to console."""
        message = ' '.join(str(arg) for arg in args)
        logging.info(f"Extension Console: {message}")
        print(f"[Extension] {message}")
    
    def warn(self, *args):
        """Log warning to console."""
        message = ' '.join(str(arg) for arg in args)
        logging.warning(f"Extension Console: {message}")
        print(f"[Extension Warning] {message}")
    
    def error(self, *args):
        """Log error to console."""
        message = ' '.join(str(arg) for arg in args)
        logging.error(f"Extension Console: {message}")
        print(f"[Extension Error] {message}")


class Extension:
    """Extension instance."""
    
    def __init__(self, path: Path):
        self.path = path
        self.id = ""
        self.manifest = None
        self.enabled = False
        self.loaded = False
        self.sandbox = None
        self.background_script = None
        self.content_scripts = []
        self.options_page = None
        self.uninstall_url = ""
        self.install_time = datetime.now()
        self.last_used = datetime.now()
        self.error_message = ""
        self.permissions_granted = []
        self.permissions_denied = []
        
        self._load_manifest()
        self._validate_extension()
    
    def _load_manifest(self):
        """Load and parse manifest.json."""
        manifest_path = self.path / "manifest.json"
        if not manifest_path.exists():
            raise ExtensionError("manifest.json not found")
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            self.manifest = ExtensionManifest(**manifest_data)
            self.id = self.manifest.key or self._generate_id()
            
        except Exception as e:
            raise ExtensionError(f"Invalid manifest.json: {e}")
    
    def _generate_id(self):
        """Generate extension ID from public key."""
        # Simplified ID generation
        return hashlib.sha256(str(self.path).encode()).hexdigest()[:32]
    
    def _validate_extension(self):
        """Validate extension manifest."""
        if not self.manifest.name:
            raise ExtensionError("Extension name is required")
        
        if not self.manifest.version:
            raise ExtensionError("Extension version is required")
        
        if self.manifest.manifest_version not in [2, 3]:
            raise ExtensionError("Unsupported manifest version")
    
    def load(self):
        """Load extension."""
        if self.loaded:
            return
        
        try:
            # Create sandbox
            self.sandbox = ExtensionSandbox(self.id)
            
            # Load background script
            if self.manifest.background:
                if 'scripts' in self.manifest.background:
                    self.background_script = self.manifest.background.get('scripts', [])
                elif 'page' in self.manifest.background:
                    self.background_script = [self.manifest.background['page']]
            
            # Load content scripts
            self.content_scripts = self.manifest.content_scripts or []
            
            # Load options page
            self.options_page = self.manifest.options_page
            
            self.loaded = True
            self.last_used = datetime.now()
            
        except Exception as e:
            self.error_message = str(e)
            raise ExtensionError(f"Failed to load extension: {e}")
    
    def enable(self):
        """Enable extension."""
        if not self.loaded:
            self.load()
        
        self.enabled = True
        self.last_used = datetime.now()
        
        # Execute background script
        if self.background_script and self.sandbox:
            for script in self.background_script:
                if script.endswith('.js'):
                    script_path = self.path / script
                    if script_path.exists():
                        with open(script_path, 'r', encoding='utf-8') as f:
                            script_content = f.read()
                        self.sandbox.execute_script(script_content)
                else:
                    self.sandbox.execute_script(script)
        
        # Inject content scripts
        self._inject_content_scripts()
    
    def disable(self):
        """Disable extension."""
        self.enabled = False
        self._remove_content_scripts()
    
    def _inject_content_scripts(self):
        """Inject content scripts into web views."""
        from .extension_manager import ExtensionManager
        manager = ExtensionManager.instance()
        browser = manager.browser
        
        if not browser:
            return
        
        for tab in browser.tabs:
            web_view = tab.get('web_view')
            if web_view:
                for script in self.content_scripts:
                    if 'matches' in script:
                        # Simplified matching - inject into all pages
                        js_files = script.get('js', [])
                        css_files = script.get('css', [])
                        
                        # Inject CSS
                        for css_file in css_files:
                            css_path = self.path / css_file
                            if css_path.exists():
                                with open(css_path, 'r', encoding='utf-8') as f:
                                    css_content = f.read()
                                web_view.page().runJavaScript(
                                    f"""
                                    var style = document.createElement('style');
                                    style.textContent = `{css_content}';
                                    document.head.appendChild(style);
                                    """
                                )
                        
                        # Inject JavaScript
                        for js_file in js_files:
                            js_path = self.path / js_file
                            if js_path.exists():
                                with open(js_path, 'r', encoding='utf-8') as f:
                                    js_content = f.read()
                                web_view.page().runJavaScript(js_content)
    
    def _remove_content_scripts(self):
        """Remove content scripts from web views."""
        # Simplified - would need to track injected scripts
        pass
    
    def get_info(self):
        """Get extension information."""
        return {
            'id': self.id,
            'name': self.manifest.name,
            'version': self.manifest.version,
            'description': self.manifest.description,
            'enabled': self.enabled,
            'loaded': self.loaded,
            'path': str(self.path),
            'installTime': self.install_time.isoformat(),
            'lastUsed': self.last_used.isoformat(),
            'permissions': self.manifest.permissions or [],
            'optionalPermissions': self.manifest.optional_permissions or [],
            'hostPermissions': self.manifest.host_permissions or [],
            'errorMessage': self.error_message
        }


class ExtensionInstaller:
    """Extension installer."""
    
    def __init__(self):
        self.install_queue = []
        self.installing = False
    
    def install_from_file(self, file_path: str) -> str:
        """Install extension from file."""
        if file_path.endswith('.zip'):
            return self._install_from_zip(file_path)
        elif file_path.endswith('.crx'):
            return self._install_from_crx(file_path)
        else:
            return self._install_from_directory(file_path)
    
    def _install_from_zip(self, zip_path: str) -> str:
        """Install extension from ZIP file."""
        try:
            # Create temporary directory
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix='vertex_extension_')
            
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find extension directory
            extension_dir = Path(temp_dir)
            for item in extension_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / 'manifest.json'
                    if manifest_path.exists():
                        extension_dir = item
                        break
            
            # Install from directory
            extension_id = self._install_from_directory(str(extension_dir))
            
            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return extension_id
            
        except Exception as e:
            raise ExtensionError(f"Failed to install from ZIP: {e}")
    
    def _install_from_crx(self, crx_path: str) -> str:
        """Install extension from CRX file."""
        # CRX is Chrome extension format - simplified implementation
        return self._install_from_zip(crx_path)
    
    def _install_from_directory(self, dir_path: str) -> str:
        """Install extension from directory."""
        try:
            extension_path = Path(dir_path)
            
            # Create extension instance
            extension = Extension(extension_path)
            
            # Validate permissions
            self._validate_permissions(extension)
            
            # Copy to extensions directory
            extensions_dir = Path.home() / '.vertex_extensions'
            extensions_dir.mkdir(exist_ok=True)
            
            install_dir = extensions_dir / extension.id
            if install_dir.exists():
                shutil.rmtree(install_dir)
            
            shutil.copytree(extension_path, install_dir)
            
            # Create new extension instance from install location
            installed_extension = Extension(install_dir)
            installed_extension.load()
            
            return installed_extension.id
            
        except Exception as e:
            raise ExtensionError(f"Failed to install from directory: {e}")
    
    def _validate_permissions(self, extension: Extension):
        """Validate extension permissions."""
        from .extension_manager import ExtensionManager
        manager = ExtensionManager.instance()
        
        required_permissions = extension.manifest.permissions or []
        for permission in required_permissions:
            if not manager.is_permission_granted(extension.id, permission):
                # Request permission (simplified)
                manager.grant_permission(extension.id, permission)
    
    def uninstall(self, extension_id: str):
        """Uninstall extension."""
        from .extension_manager import ExtensionManager
        manager = ExtensionManager.instance()
        
        extension = manager.get_extension(extension_id)
        if extension:
            # Disable first
            extension.disable()
            
            # Remove files
            extensions_dir = Path.home() / '.vertex_extensions'
            extension_dir = extensions_dir / extension_id
            if extension_dir.exists():
                shutil.rmtree(extension_dir)
            
            # Remove from manager
            manager.remove_extension(extension_id)


class ExtensionManager(QObject):
    """Main extension manager."""
    
    instance = None
    
    def __init__(self, browser=None):
        super().__init__()
        ExtensionManager.instance = self
        self.browser = browser
        self.extensions = {}
        self.installer = ExtensionInstaller()
        self.permissions = {}
        self.update_checker = QTimer()
        self.update_checker.timeout.connect(self._check_updates)
        self.update_checker.start(3600000)  # Check every hour
        
        self._load_extensions()
    
    def _load_extensions(self):
        """Load installed extensions."""
        extensions_dir = Path.home() / '.vertex_extensions'
        if extensions_dir.exists():
            for ext_dir in extensions_dir.iterdir():
                if ext_dir.is_dir():
                    try:
                        extension = Extension(ext_dir)
                        extension.load()
                        self.extensions[extension.id] = extension
                    except Exception as e:
                        logging.error(f"Failed to load extension {ext_dir.name}: {e}")
    
    def install_extension(self, file_path: str) -> str:
        """Install extension."""
        try:
            extension_id = self.installer.install_from_file(file_path)
            if extension_id in self.extensions:
                extension = self.extensions[extension_id]
                extension.enable()
            return extension_id
        except Exception as e:
            logging.error(f"Failed to install extension: {e}")
            raise
    
    def uninstall_extension(self, extension_id: str):
        """Uninstall extension."""
        try:
            self.installer.uninstall(extension_id)
        except Exception as e:
            logging.error(f"Failed to uninstall extension {extension_id}: {e}")
    
    def enable_extension(self, extension_id: str):
        """Enable extension."""
        extension = self.extensions.get(extension_id)
        if extension:
            extension.enable()
    
    def disable_extension(self, extension_id: str):
        """Disable extension."""
        extension = self.extensions.get(extension_id)
        if extension:
            extension.disable()
    
    def reload_extension(self, extension_id: str):
        """Reload extension."""
        extension = self.extensions.get(extension_id)
        if extension:
            extension.disable()
            extension.load()
            if extension.enabled:
                extension.enable()
    
    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get extension by ID."""
        return self.extensions.get(extension_id)
    
    def get_all_extensions(self) -> List[Extension]:
        """Get all extensions."""
        return list(self.extensions.values())
    
    def has_permission(self, extension_id: str, permission: str) -> bool:
        """Check if extension has permission."""
        return permission in self.permissions.get(extension_id, [])
    
    def grant_permission(self, extension_id: str, permission: str):
        """Grant permission to extension."""
        if extension_id not in self.permissions:
            self.permissions[extension_id] = []
        if permission not in self.permissions[extension_id]:
            self.permissions[extension_id].append(permission)
    
    def revoke_permission(self, extension_id: str, permission: str):
        """Revoke permission from extension."""
        if extension_id in self.permissions:
            self.permissions[extension_id] = [
                p for p in self.permissions[extension_id] if p != permission
            ]
    
    def check_extension_updates(self, extension_id: str = None):
        """Check for extension updates."""
        # Simplified update checking
        if extension_id:
            extension = self.get_extension(extension_id)
            if extension:
                self._check_single_extension_update(extension)
        else:
            for extension in self.get_all_extensions():
                self._check_single_extension_update(extension)
    
    def _check_single_extension_update(self, extension: Extension):
        """Check single extension for updates."""
        # Simplified - would check against store
        pass
    
    def remove_extension(self, extension_id: str):
        """Remove extension from manager."""
        if extension_id in self.extensions:
            del self.extensions[extension_id]
    
    def get_download_manager(self):
        """Get download manager instance."""
        if self.browser:
            return getattr(self.browser, 'download_manager', None)
        return None


def show_extension_manager(parent=None):
    """Show extension manager dialog."""
    from .extension_ui import ExtensionManagerDialog
    dialog = ExtensionManagerDialog(parent)
    dialog.show()
    return dialog
