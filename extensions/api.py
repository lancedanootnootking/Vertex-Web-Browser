#!/usr/bin/env python3
"""
Extension API

Comprehensive API for browser extensions to interact with the browser
and its functionality. Provides tab management, storage, UI, and more.
"""

import logging
import json
import os
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from pathlib import Path
import uuid
import hashlib
import base64

from .hooks import HookAPI, HookType, HookPriority
from .manifest import Permission


class ExtensionAPI:
    """Comprehensive API for browser extensions."""
    
    def __init__(self, extension):
        self.extension = extension
        self.logger = logging.getLogger(__name__)
        
        # Browser components (would be injected by main app)
        self.browser_window = None
        self.backend_app = None
        self.hook_manager = None
        self.storage_manager = None
        
        # Extension-specific data
        self.extension_id = extension.id
        self.extension_path = extension.extension_dir
        self.permissions = extension.permissions
        
        # Hook API
        self.hooks = None
        
        # Storage
        self._local_storage = {}
        self._sync_storage = {}
        self._storage_lock = threading.RLock()
        
        # Event listeners
        self._event_listeners: Dict[str, List[Callable]] = {}
        
        # Message passing
        self._message_handlers: Dict[str, Callable] = {}
        self._port_handlers: Dict[str, Callable] = {}
        
        # Runtime state
        self._context_menu_items: List[Dict[str, Any]] = []
        self._toolbar_buttons: List[Dict[str, Any]] = []
        self._tabs: Dict[str, Dict[str, Any]] = {}
        self._notifications: List[Dict[str, Any]] = []
        
        # Initialize storage
        self._load_storage()
    
    def set_browser_window(self, browser_window):
        """Set reference to browser window."""
        self.browser_window = browser_window
    
    def set_backend_app(self, backend_app):
        """Set reference to backend app."""
        self.backend_app = backend_app
    
    def set_hook_manager(self, hook_manager):
        """Set reference to hook manager."""
        self.hook_manager = hook_manager
        self.hooks = HookAPI(self.extension_id, hook_manager)
    
    def set_storage_manager(self, storage_manager):
        """Set reference to storage manager."""
        self.storage_manager = storage_manager
    
    # Tab Management
    def create_tab(self, url: str = None, active: bool = True) -> Optional[str]:
        """Create a new browser tab."""
        if not self._has_permission('tabs'):
            self.logger.warning(f"Extension {self.extension_id} lacks tabs permission")
            return None
        
        if not self.browser_window:
            self.logger.error("Browser window not available")
            return None
        
        try:
            tab = self.browser_window.new_tab(url or "about:blank")
            tab_id = str(uuid.uuid4())
            
            self._tabs[tab_id] = {
                'id': tab_id,
                'url': url or "about:blank",
                'title': "New Tab",
                'active': active,
                'window_id': "main",
                'index': len(self._tabs),
                'pinned': False,
                'audible': False,
                'muted': False,
                'status': "loading",
                'incognito': False,
                'width': 0,
                'height': 0,
                'last_accessed': datetime.now().isoformat()
            }
            
            # Fire hook
            if self.hook_manager:
                from .hooks import BrowserHooks
                browser_hooks = BrowserHooks(self.hook_manager)
                browser_hooks.tab_created(tab_id, url or "about:blank")
            
            return tab_id
            
        except Exception as e:
            self.logger.error(f"Error creating tab: {e}")
            return None
    
    def get_current_tab(self) -> Optional[Dict[str, Any]]:
        """Get information about the current tab."""
        if not self._has_permission('tabs'):
            return None
        
        if not self.browser_window:
            return None
        
        try:
            current_tab = self.browser_window.get_current_tab()
            if current_tab:
                tab_id = str(uuid.uuid4())
                tab_info = {
                    'id': tab_id,
                    'url': current_tab.get_url(),
                    'title': current_tab.get_title(),
                    'active': True,
                    'window_id': "main",
                    'index': 0,
                    'pinned': False,
                    'audible': False,
                    'muted': False,
                    'status': "complete",
                    'incognito': False,
                    'width': 1200,
                    'height': 800,
                    'last_accessed': datetime.now().isoformat()
                }
                
                self._tabs[tab_id] = tab_info
                return tab_info
                
        except Exception as e:
            self.logger.error(f"Error getting current tab: {e}")
        
        return None
    
    def get_tab(self, tab_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tab."""
        if not self._has_permission('tabs'):
            return None
        
        return self._tabs.get(tab_id)
    
    def query_tabs(self, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query tabs with optional filters."""
        if not self._has_permission('tabs'):
            return []
        
        query = query or {}
        tabs = list(self._tabs.values())
        
        # Apply filters
        if 'active' in query:
            tabs = [t for t in tabs if t['active'] == query['active']]
        
        if 'window_id' in query:
            tabs = [t for t in tabs if t['window_id'] == query['window_id']]
        
        if 'url' in query:
            url_pattern = query['url']
            if isinstance(url_pattern, str):
                tabs = [t for t in tabs if url_pattern in t['url']]
            elif hasattr(url_pattern, 'search'):
                tabs = [t for t in tabs if url_pattern.search(t['url'])]
        
        if 'title' in query:
            title_pattern = query['title']
            if isinstance(title_pattern, str):
                tabs = [t for t in tabs if title_pattern.lower() in t['title'].lower()]
        
        return tabs
    
    def update_tab(self, tab_id: str, update_properties: Dict[str, Any]) -> bool:
        """Update tab properties."""
        if not self._has_permission('tabs'):
            return False
        
        if tab_id not in self._tabs:
            return False
        
        try:
            tab = self._tabs[tab_id]
            
            # Update properties
            if 'url' in update_properties:
                tab['url'] = update_properties['url']
                tab['status'] = 'loading'
            
            if 'active' in update_properties:
                tab['active'] = update_properties['active']
            
            if 'pinned' in update_properties:
                tab['pinned'] = update_properties['pinned']
            
            if 'muted' in update_properties:
                tab['muted'] = update_properties['muted']
            
            tab['last_accessed'] = datetime.now().isoformat()
            
            # Fire hook
            if self.hook_manager:
                from .hooks import BrowserHooks
                browser_hooks = BrowserHooks(self.hook_manager)
                browser_hooks.tab_updated(tab_id, tab['url'], tab['title'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating tab: {e}")
            return False
    
    def navigate_tab(self, tab_id: str, url: str) -> bool:
        """Navigate a tab to a URL."""
        if not self._has_permission('tabs'):
            return False
        
        return self.update_tab(tab_id, {'url': url})
    
    def reload_tab(self, tab_id: str) -> bool:
        """Reload a tab."""
        if not self._has_permission('tabs'):
            return False
        
        if tab_id not in self._tabs:
            return False
        
        tab = self._tabs[tab_id]
        return self.update_tab(tab_id, {'url': tab['url']})
    
    def close_tab(self, tab_id: str) -> bool:
        """Close a tab."""
        if not self._has_permission('tabs'):
            return False
        
        if tab_id not in self._tabs:
            return False
        
        try:
            # Fire hook
            if self.hook_manager:
                from .hooks import BrowserHooks
                browser_hooks = BrowserHooks(self.hook_manager)
                browser_hooks.tab_closed(tab_id)
            
            del self._tabs[tab_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing tab: {e}")
            return False
    
    # Bookmarks Management
    def add_bookmark(self, title: str, url: str, folder: str = "Default") -> bool:
        """Add a bookmark."""
        if not self._has_permission('bookmarks'):
            self.logger.warning(f"Extension {self.extension_id} lacks bookmarks permission")
            return False
        
        if not self.browser_window:
            self.logger.error("Browser window not available")
            return False
        
        try:
            # This would integrate with the browser's bookmark system
            bookmark = {
                'id': str(uuid.uuid4()),
                'title': title,
                'url': url,
                'folder': folder,
                'date_added': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat()
            }
            
            # Add to browser's bookmark system
            if hasattr(self.browser_window, 'add_bookmark'):
                self.browser_window.add_bookmark(bookmark)
            
            # Fire hook
            if self.hook_manager:
                from .hooks import BrowserHooks
                browser_hooks = BrowserHooks(self.hook_manager)
                browser_hooks.bookmark_created(bookmark['id'], title, url)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding bookmark: {e}")
            return False
    
    def get_bookmarks(self, folder: str = None) -> List[Dict[str, Any]]:
        """Get bookmarks."""
        if not self._has_permission('bookmarks'):
            return []
        
        if not self.browser_window:
            return []
        
        try:
            if hasattr(self.browser_window, 'get_bookmarks'):
                return self.browser_window.get_bookmarks(folder)
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting bookmarks: {e}")
            return []
    
    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove a bookmark."""
        if not self._has_permission('bookmarks'):
            return False
        
        if not self.browser_window:
            return False
        
        try:
            if hasattr(self.browser_window, 'remove_bookmark'):
                return self.browser_window.remove_bookmark(bookmark_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing bookmark: {e}")
            return False
    
    # History Management
    def get_history(self, search_text: str = None, start_time: datetime = None, 
                   end_time: datetime = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get browsing history."""
        if not self._has_permission('history'):
            return []
        
        if not self.browser_window:
            return []
        
        try:
            if hasattr(self.browser_window, 'get_history'):
                return self.browser_window.get_history(
                    search_text, start_time, end_time, max_results
                )
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return []
    
    def add_history(self, url: str, title: str = None) -> bool:
        """Add an entry to history."""
        if not self._has_permission('history'):
            return False
        
        if not self.browser_window:
            return False
        
        try:
            if hasattr(self.browser_window, 'add_history'):
                return self.browser_window.add_history(url, title)
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding history: {e}")
            return False
    
    # Downloads Management
    def add_download(self, url: str, filename: str = None, save_as: bool = False) -> Optional[str]:
        """Add a download."""
        if not self._has_permission('downloads'):
            return None
        
        if not self.browser_window:
            return None
        
        try:
            if hasattr(self.browser_window, 'add_download'):
                return self.browser_window.add_download(url, filename, save_as)
            return None
            
        except Exception as e:
            self.logger.error(f"Error adding download: {e}")
            return None
    
    def get_downloads(self, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get downloads."""
        if not self._has_permission('downloads'):
            return []
        
        if not self.browser_window:
            return []
        
        try:
            if hasattr(self.browser_window, 'get_downloads'):
                return self.browser_window.get_downloads(query)
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting downloads: {e}")
            return []
    
    def pause_download(self, download_id: str) -> bool:
        """Pause a download."""
        if not self._has_permission('downloads'):
            return False
        
        if not self.browser_window:
            return False
        
        try:
            if hasattr(self.browser_window, 'pause_download'):
                return self.browser_window.pause_download(download_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Error pausing download: {e}")
            return False
    
    def resume_download(self, download_id: str) -> bool:
        """Resume a download."""
        if not self._has_permission('downloads'):
            return False
        
        if not self.browser_window:
            return False
        
        try:
            if hasattr(self.browser_window, 'resume_download'):
                return self.browser_window.resume_download(download_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Error resuming download: {e}")
            return False
    
    def cancel_download(self, download_id: str) -> bool:
        """Cancel a download."""
        if not self._has_permission('downloads'):
            return False
        
        if not self.browser_window:
            return False
        
        try:
            if hasattr(self.browser_window, 'cancel_download'):
                return self.browser_window.cancel_download(download_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Error canceling download: {e}")
            return False
    
    # Storage API
    def get_storage(self, keys: Union[str, List[str], None] = None, 
                   area: str = "local") -> Dict[str, Any]:
        """Get storage data."""
        if not self._has_permission('storage'):
            return {}
        
        with self._storage_lock:
            if area == "local":
                storage = self._local_storage
            elif area == "sync":
                storage = self._sync_storage
            else:
                return {}
            
            if keys is None:
                return storage.copy()
            elif isinstance(keys, str):
                return {keys: storage.get(keys)}
            elif isinstance(keys, list):
                return {k: storage.get(k) for k in keys}
            else:
                return {}
    
    def set_storage(self, items: Dict[str, Any], area: str = "local") -> bool:
        """Set storage data."""
        if not self._has_permission('storage'):
            return False
        
        with self._storage_lock:
            if area == "local":
                storage = self._local_storage
            elif area == "sync":
                storage = self._sync_storage
            else:
                return False
            
            storage.update(items)
            self._save_storage(area)
            
            # Fire hook
            if self.hook_manager:
                from .hooks import BrowserHooks
                browser_hooks = BrowserHooks(self.hook_manager)
                for key, value in items.items():
                    browser_hooks.storage_changed(
                        self.extension_id, area, key, 
                        storage.get(key, None), value
                    )
            
            return True
    
    def remove_storage(self, keys: Union[str, List[str]], area: str = "local") -> bool:
        """Remove storage data."""
        if not self._has_permission('storage'):
            return False
        
        with self._storage_lock:
            if area == "local":
                storage = self._local_storage
            elif area == "sync":
                storage = self._sync_storage
            else:
                return False
            
            if isinstance(keys, str):
                keys = [keys]
            
            removed_items = {}
            for key in keys:
                if key in storage:
                    removed_items[key] = storage[key]
                    del storage[key]
            
            self._save_storage(area)
            
            # Fire hook
            if self.hook_manager:
                from .hooks import BrowserHooks
                browser_hooks = BrowserHooks(self.hook_manager)
                for key, old_value in removed_items.items():
                    browser_hooks.storage_changed(
                        self.extension_id, area, key, old_value, None
                    )
            
            return True
    
    def clear_storage(self, area: str = "local") -> bool:
        """Clear storage data."""
        if not self._has_permission('storage'):
            return False
        
        with self._storage_lock:
            if area == "local":
                self._local_storage.clear()
            elif area == "sync":
                self._sync_storage.clear()
            else:
                return False
            
            self._save_storage(area)
            return True
    
    def _load_storage(self):
        """Load storage from disk."""
        try:
            storage_dir = Path(self.extension_path) / "storage"
            storage_dir.mkdir(exist_ok=True)
            
            # Load local storage
            local_file = storage_dir / "local.json"
            if local_file.exists():
                with open(local_file, 'r') as f:
                    self._local_storage = json.load(f)
            
            # Load sync storage
            sync_file = storage_dir / "sync.json"
            if sync_file.exists():
                with open(sync_file, 'r') as f:
                    self._sync_storage = json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Error loading storage: {e}")
    
    def _save_storage(self, area: str):
        """Save storage to disk."""
        try:
            storage_dir = Path(self.extension_path) / "storage"
            storage_dir.mkdir(exist_ok=True)
            
            if area == "local":
                with open(storage_dir / "local.json", 'w') as f:
                    json.dump(self._local_storage, f, indent=2)
            elif area == "sync":
                with open(storage_dir / "sync.json", 'w') as f:
                    json.dump(self._sync_storage, f, indent=2)
                    
        except Exception as e:
            self.logger.error(f"Error saving storage: {e}")
    
    # Notifications API
    def create_notification(self, notification_id: str = None, 
                          options: Dict[str, Any] = None) -> str:
        """Create a notification."""
        if not self._has_permission('notifications'):
            self.logger.warning(f"Extension {self.extension_id} lacks notifications permission")
            return None
        
        notification_id = notification_id or str(uuid.uuid4())
        options = options or {}
        
        notification = {
            'id': notification_id,
            'type': options.get('type', 'basic'),
            'icon_url': options.get('iconUrl'),
            'title': options.get('title', ''),
            'message': options.get('message', ''),
            'context_message': options.get('contextMessage'),
            'priority': options.get('priority', 0),
            'is_clickable': options.get('isClickable', True),
            'require_interaction': options.get('requireInteraction', False),
            'buttons': options.get('buttons', []),
            'progress': options.get('progress'),
            'timestamp': datetime.now().isoformat()
        }
        
        self._notifications.append(notification)
        
        # In a real implementation, this would show a system notification
        self.logger.info(f"Notification created: {notification['title']} - {notification['message']}")
        
        return notification_id
    
    def clear_notification(self, notification_id: str) -> bool:
        """Clear a notification."""
        for i, notification in enumerate(self._notifications):
            if notification['id'] == notification_id:
                del self._notifications[i]
                return True
        return False
    
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get all notifications."""
        return self._notifications.copy()
    
    # Context Menus API
    def create_context_menu(self, create_properties: Dict[str, Any]) -> str:
        """Create a context menu item."""
        if not self._has_permission('contextMenus'):
            self.logger.warning(f"Extension {self.extension_id} lacks contextMenus permission")
            return None
        
        menu_item = {
            'id': create_properties.get('id', str(uuid.uuid4())),
            'type': create_properties.get('type', 'normal'),
            'title': create_properties.get('title', ''),
            'contexts': create_properties.get('contexts', ['all']),
            'onclick': create_properties.get('onclick'),
            'parent_id': create_properties.get('parentId'),
            'document_url_patterns': create_properties.get('documentUrlPatterns', []),
            'target_url_patterns': create_properties.get('targetUrlPatterns', []),
            'enabled': create_properties.get('enabled', True),
            'visible': create_properties.get('visible', True)
        }
        
        self._context_menu_items.append(menu_item)
        
        # Register click handler
        if menu_item['onclick']:
            self._message_handlers[f"context_menu_{menu_item['id']}"] = menu_item['onclick']
        
        return menu_item['id']
    
    def update_context_menu(self, menu_item_id: str, 
                           update_properties: Dict[str, Any]) -> bool:
        """Update a context menu item."""
        for item in self._context_menu_items:
            if item['id'] == menu_item_id:
                item.update(update_properties)
                return True
        return False
    
    def remove_context_menu(self, menu_item_id: str) -> bool:
        """Remove a context menu item."""
        for i, item in enumerate(self._context_menu_items):
            if item['id'] == menu_item_id:
                del self._context_menu_items[i]
                
                # Remove message handler
                handler_key = f"context_menu_{menu_item_id}"
                if handler_key in self._message_handlers:
                    del self._message_handlers[handler_key]
                
                return True
        return False
    
    def get_context_menus(self) -> List[Dict[str, Any]]:
        """Get all context menu items."""
        return self._context_menu_items.copy()
    
    # Action API (Browser Action)
    def set_action_title(self, title: str, tab_id: str = None):
        """Set the action title."""
        if tab_id:
            # Tab-specific title
            pass
        else:
            # Global title
            if hasattr(self.extension, 'action'):
                self.extension.action['default_title'] = title
    
    def get_action_title(self, tab_id: str = None) -> str:
        """Get the action title."""
        if hasattr(self.extension, 'action'):
            return self.extension.action.get('default_title', '')
        return ''
    
    def set_action_icon(self, icon_data: Union[str, Dict[str, str]], tab_id: str = None):
        """Set the action icon."""
        if tab_id:
            # Tab-specific icon
            pass
        else:
            # Global icon
            if isinstance(icon_data, str):
                # Single icon path
                if hasattr(self.extension, 'action'):
                    self.extension.action['default_icon'] = icon_data
            elif isinstance(icon_data, dict):
                # Multiple sizes
                if hasattr(self.extension, 'action'):
                    self.extension.action['default_icon'] = icon_data
    
    def set_action_badge_text(self, text: str, tab_id: str = None):
        """Set the action badge text."""
        if tab_id:
            # Tab-specific badge
            pass
        else:
            # Global badge
            if hasattr(self.extension, 'action'):
                self.extension.action['default_badge_text'] = text
    
    def get_action_badge_text(self, tab_id: str = None) -> str:
        """Get the action badge text."""
        if hasattr(self.extension, 'action'):
            return self.extension.action.get('default_badge_text', '')
        return ''
    
    def set_action_badge_color(self, color: str, tab_id: str = None):
        """Set the action badge color."""
        if tab_id:
            # Tab-specific color
            pass
        else:
            # Global color
            if hasattr(self.extension, 'action'):
                self.extension.action['default_badge_color'] = color
    
    def get_action_badge_color(self, tab_id: str = None) -> str:
        """Get the action badge color."""
        if hasattr(self.extension, 'action'):
            return self.extension.action.get('default_badge_color', '#000000')
        return '#000000'
    
    # Message Passing API
    def send_message(self, extension_id: str, message: Any, 
                    response_callback: Callable = None) -> bool:
        """Send a message to another extension."""
        try:
            # This would integrate with the browser's message passing system
            if hasattr(self.browser_window, 'send_extension_message'):
                return self.browser_window.send_extension_message(
                    self.extension_id, extension_id, message, response_callback
                )
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    def on_message(self, handler: Callable) -> str:
        """Register a message handler."""
        handler_id = str(uuid.uuid4())
        self._message_handlers[handler_id] = handler
        return handler_id
    
    def remove_message_handler(self, handler_id: str) -> bool:
        """Remove a message handler."""
        if handler_id in self._message_handlers:
            del self._message_handlers[handler_id]
            return True
        return False
    
    def connect(self, extension_id: str, connect_info: Dict[str, Any] = None) -> Optional[str]:
        """Connect to another extension."""
        try:
            port_id = str(uuid.uuid4())
            
            # This would create a port for communication
            if hasattr(self.browser_window, 'connect_extension'):
                port = self.browser_window.connect_extension(
                    self.extension_id, extension_id, port_id, connect_info
                )
                
                if port:
                    self._port_handlers[port_id] = port
                    return port_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error connecting to extension: {e}")
            return None
    
    # Runtime API
    def get_extension_info(self) -> Dict[str, Any]:
        """Get information about the extension."""
        return {
            'id': self.extension.id,
            'name': self.extension.name,
            'version': self.extension.version,
            'description': self.extension.description,
            'author': self.extension.author,
            'homepage_url': getattr(self.extension, 'homepage_url', ''),
            'enabled': self.extension.enabled,
            'options_url': f"chrome-extension://{self.extension.id}/options.html",
            'host_permissions': self.extension.permissions,
            'permissions': self.extension.permissions,
            'install_type': 'normal',
            'update_url': None,
            'manifest_version': getattr(self.extension, 'manifest_version', 2)
        }
    
    def get_url(self, path: str) -> str:
        """Get the full URL for a path within the extension."""
        return f"chrome-extension://{self.extension_id}/{path.lstrip('/')}"
    
    def reload(self) -> bool:
        """Reload the extension."""
        try:
            if hasattr(self.browser_window, 'reload_extension'):
                return self.browser_window.reload_extension(self.extension_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Error reloading extension: {e}")
            return False
    
    # Utility Methods
    def _has_permission(self, permission: str) -> bool:
        """Check if extension has a specific permission."""
        return permission in self.permissions
    
    def log(self, level: str, message: str):
        """Log a message from the extension."""
        if level == 'error':
            self.logger.error(f"[{self.extension_id}] {message}")
        elif level == 'warning':
            self.logger.warning(f"[{self.extension_id}] {message}")
        elif level == 'info':
            self.logger.info(f"[{self.extension_id}] {message}")
        else:
            self.logger.debug(f"[{self.extension_id}] {message}")
    
    def get_manifest(self) -> Dict[str, Any]:
        """Get the extension's manifest."""
        return getattr(self.extension, 'manifest', {})
    
    def get_extension_directory(self) -> str:
        """Get the extension's directory path."""
        return self.extension_path
    
    def add_history_entry(self, url: str, title: str) -> bool:
        """Add a history entry."""
        if not self.extension.has_permission('history'):
            return False
        
        try:
            history_data = {
                'url': url,
                'title': title
            }
            
            response = requests.post(
                'http://127.0.0.1:5000/api/history',
                json=history_data,
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error adding history entry: {e}")
            return False
    
    def clear_history(self) -> bool:
        """Clear browsing history."""
        if not self.extension.has_permission('history'):
            return False
        
        try:
            response = requests.delete(
                'http://127.0.0.1:5000/api/history',
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error clearing history: {e}")
            return False
    
    # Settings Management
    def get_preference(self, key: str) -> Any:
        """Get a browser preference."""
        if not self.extension.has_permission('settings'):
            return None
        
        try:
            response = requests.get(
                f'http://127.0.0.1:5000/api/preferences/{key}',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('value')
        except Exception as e:
            self.logger.error(f"Error getting preference: {e}")
        
        return None
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Set a browser preference."""
        if not self.extension.has_permission('settings'):
            return False
        
        try:
            pref_data = {
                'value': value
            }
            
            response = requests.put(
                f'http://127.0.0.1:5000/api/preferences/{key}',
                json=pref_data,
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error setting preference: {e}")
            return False
    
    # UI Operations
    def show_notification(self, title: str, message: str, duration: int = 5000):
        """Show a notification to the user."""
        if not self.extension.has_permission('notifications'):
            return
        
        try:
            if self.browser_window:
                # Create notification (simplified)
                print(f"NOTIFICATION: {title} - {message}")
                # In a real implementation, this would show a proper notification
        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")
    
    def show_dialog(self, title: str, message: str, dialog_type: str = "info") -> bool:
        """Show a dialog to the user."""
        if not self.extension.has_permission('ui'):
            return False
        
        try:
            if self.browser_window:
                # Show dialog (simplified)
                print(f"DIALOG ({dialog_type}): {title} - {message}")
                return True
        except Exception as e:
            self.logger.error(f"Error showing dialog: {e}")
        
        return False
    
    def add_toolbar_button(self, button_id: str, text: str, callback: Callable, icon: str = None):
        """Add a button to the toolbar."""
        if not self.extension.has_permission('ui'):
            return
        
        try:
            if self.browser_window:
                # Add toolbar button (simplified)
                print(f"TOOLBAR BUTTON: {button_id} - {text}")
                # In a real implementation, this would add a proper button
        except Exception as e:
            self.logger.error(f"Error adding toolbar button: {e}")
    
    def remove_toolbar_button(self, button_id: str):
        """Remove a toolbar button."""
        if not self.extension.has_permission('ui'):
            return
        
        try:
            if self.browser_window:
                # Remove toolbar button (simplified)
                print(f"REMOVE TOOLBAR BUTTON: {button_id}")
        except Exception as e:
            self.logger.error(f"Error removing toolbar button: {e}")
    
    # Network Operations
    def make_request(self, url: str, method: str = "GET", headers: Dict[str, str] = None, 
                    data: Any = None) -> Optional[Dict[str, Any]]:
        """Make an HTTP request."""
        if not self.extension.has_permission('network'):
            return None
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return None
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text,
                'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        
        except Exception as e:
            self.logger.error(f"Error making request: {e}")
            return None
    
    # Storage Operations
    def get_storage_data(self) -> Dict[str, Any]:
        """Get extension storage data."""
        try:
            storage_file = f"extension_storage_{self.extension.id}.json"
            
            import os
            if os.path.exists(storage_file):
                import json
                with open(storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error getting storage data: {e}")
        
        return {}
    
    def set_storage_data(self, data: Dict[str, Any]) -> bool:
        """Set extension storage data."""
        try:
            storage_file = f"extension_storage_{self.extension.id}.json"
            
            import json
            with open(storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting storage data: {e}")
            return False
    
    def get_storage_item(self, key: str) -> Any:
        """Get a specific storage item."""
        storage_data = self.get_storage_data()
        return storage_data.get(key)
    
    def set_storage_item(self, key: str, value: Any) -> bool:
        """Set a specific storage item."""
        storage_data = self.get_storage_data()
        storage_data[key] = value
        return self.set_storage_data(storage_data)
    
    # Security Operations
    def check_url_security(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if a URL is safe."""
        if not self.extension.has_permission('security'):
            return None
        
        try:
            response = requests.post(
                'http://127.0.0.1:5000/api/security/check-url',
                json={'url': url},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error checking URL security: {e}")
        
        return None
    
    # Utility Functions
    def log(self, level: str, message: str):
        """Log a message."""
        if level.lower() == 'debug':
            self.logger.debug(f"[{self.extension.name}] {message}")
        elif level.lower() == 'info':
            self.logger.info(f"[{self.extension.name}] {message}")
        elif level.lower() == 'warning':
            self.logger.warning(f"[{self.extension.name}] {message}")
        elif level.lower() == 'error':
            self.logger.error(f"[{self.extension.name}] {message}")
    
    def get_extension_info(self) -> Dict[str, Any]:
        """Get information about the extension."""
        return self.extension.get_info()
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get information about the browser."""
        return {
            'name': 'Advanced Web Browser',
            'version': '1.0.0',
            'user_agent': 'AdvancedWebBrowser/1.0',
            'platform': 'Python'
        }
    
    def get_current_time(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()
    
    def open_external(self, url: str) -> bool:
        """Open URL in external application."""
        if not self.extension.has_permission('external'):
            return False
        
        try:
            import webbrowser
            webbrowser.open(url)
            return True
        except Exception as e:
            self.logger.error(f"Error opening external URL: {e}")
            return False
    
    # Event System
    def register_event_handler(self, event_name: str, handler: Callable):
        """Register an event handler."""
        if hasattr(self.extension, 'event_handlers'):
            if event_name not in self.extension.event_handlers:
                self.extension.event_handlers[event_name] = []
            self.extension.event_handlers[event_name].append(handler)
    
    def unregister_event_handler(self, event_name: str, handler: Callable):
        """Unregister an event handler."""
        if hasattr(self.extension, 'event_handlers'):
            if event_name in self.extension.event_handlers:
                try:
                    self.extension.event_handlers[event_name].remove(handler)
                except ValueError:
                    pass
    
    def emit_event(self, event_name: str, data: Any = None):
        """Emit an event to other extensions."""
        if self.browser_window and hasattr(self.browser_window, 'extension_manager'):
            self.browser_window.extension_manager.trigger_event(event_name, data)
