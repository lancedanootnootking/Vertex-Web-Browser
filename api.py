"""
Extension API

This module provides the API that extensions can use to interact
with the browser and its functionality.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import requests
from datetime import datetime


class ExtensionAPI:
    """API for browser extensions."""
    
    def __init__(self, extension):
        self.extension = extension
        self.logger = logging.getLogger(__name__)
        
        # Browser components (would be injected by main app)
        self.browser_window = None
        self.backend_app = None
    
    def set_browser_window(self, browser_window):
        """Set reference to browser window."""
        self.browser_window = browser_window
    
    def set_backend_app(self, backend_app):
        """Set reference to backend app."""
        self.backend_app = backend_app
    
    # Tab Management
    def create_tab(self, url: str = None) -> Optional[str]:
        """Create a new browser tab."""
        if not self.browser_window:
            self.logger.error("Browser window not available")
            return None
        
        try:
            tab = self.browser_window.new_tab(url)
            return str(id(tab))  # Return tab identifier
        except Exception as e:
            self.logger.error(f"Error creating tab: {e}")
            return None
    
    def get_current_tab(self) -> Optional[Dict[str, Any]]:
        """Get information about the current tab."""
        if not self.browser_window:
            return None
        
        try:
            current_tab = self.browser_window.get_current_tab()
            if current_tab:
                return {
                    'id': str(id(current_tab)),
                    'url': current_tab.get_url(),
                    'title': current_tab.get_title(),
                    'loading': current_tab.loading
                }
        except Exception as e:
            self.logger.error(f"Error getting current tab: {e}")
        
        return None
    
    def navigate_tab(self, tab_id: str, url: str) -> bool:
        """Navigate a tab to a URL."""
        if not self.browser_window:
            return False
        
        try:
            # Find tab by ID (simplified)
            current_tab = self.browser_window.get_current_tab()
            if current_tab and str(id(current_tab)) == tab_id:
                current_tab.load_url(url)
                return True
        except Exception as e:
            self.logger.error(f"Error navigating tab: {e}")
        
        return False
    
    def close_tab(self, tab_id: str) -> bool:
        """Close a tab."""
        if not self.browser_window:
            return False
        
        try:
            # Find tab by ID (simplified)
            current_tab = self.browser_window.get_current_tab()
            if current_tab and str(id(current_tab)) == tab_id:
                self.browser_window.close_current_tab()
                return True
        except Exception as e:
            self.logger.error(f"Error closing tab: {e}")
        
        return False
    
    # Bookmarks Management
    def add_bookmark(self, title: str, url: str, folder: str = "Default") -> bool:
        """Add a bookmark."""
        if not self.extension.has_permission('bookmarks'):
            self.logger.warning("Extension doesn't have bookmarks permission")
            return False
        
        try:
            bookmark_data = {
                'title': title,
                'url': url,
                'folder': folder
            }
            
            response = requests.post(
                'http://127.0.0.1:5000/api/bookmarks',
                json=bookmark_data,
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error adding bookmark: {e}")
            return False
    
    def get_bookmarks(self, folder: str = None) -> List[Dict[str, Any]]:
        """Get bookmarks."""
        if not self.extension.has_permission('bookmarks'):
            return []
        
        try:
            params = {}
            if folder:
                params['folder'] = folder
            
            response = requests.get(
                'http://127.0.0.1:5000/api/bookmarks',
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error getting bookmarks: {e}")
        
        return []
    
    def delete_bookmark(self, bookmark_id: int) -> bool:
        """Delete a bookmark."""
        if not self.extension.has_permission('bookmarks'):
            return False
        
        try:
            response = requests.delete(
                f'http://127.0.0.1:5000/api/bookmarks/{bookmark_id}',
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error deleting bookmark: {e}")
            return False
    
    # History Management
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get browsing history."""
        if not self.extension.has_permission('history'):
            return []
        
        try:
            response = requests.get(
                'http://127.0.0.1:5000/api/history',
                params={'limit': limit},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
        
        return []
    
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
