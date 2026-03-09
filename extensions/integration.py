#!/usr/bin/env python3
"""
Extension System Integration

Integration layer that connects the extension system with the main browser.
Handles initialization, event routing, and coordination between components.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json

from .loader import ExtensionLoader
from .hooks import HookManager, BrowserHooks
from .security import SecurityManager
from .store import ExtensionStore
from .ui_manager import ExtensionUIManager
from .api import ExtensionAPI


class ExtensionSystem:
    """Main extension system coordinator."""
    
    def __init__(self, browser_instance):
        self.browser = browser_instance
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.loader = ExtensionLoader(browser_instance)
        self.hook_manager = HookManager()
        self.security_manager = SecurityManager()
        self.store = ExtensionStore()
        self.ui_manager = ExtensionUIManager(browser_instance)
        self.browser_hooks = BrowserHooks(self.hook_manager)
        
        # Extension APIs
        self.extension_apis: Dict[str, ExtensionAPI] = {}
        
        # System state
        self.initialized = False
        self.extensions_enabled = True
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Background threads
        self.monitoring_thread = None
        self.update_thread = None
        
        # Initialize system
        self._initialize()
    
    def _initialize(self):
        """Initialize the extension system."""
        try:
            self.logger.info("Initializing extension system...")
            
            # Setup loader callbacks
            self.loader.add_event_handler('extension_loaded', self._on_extension_loaded)
            self.loader.add_event_handler('extension_enabled', self._on_extension_enabled)
            self.loader.add_event_handler('extension_disabled', self._on_extension_disabled)
            self.loader.add_event_handler('extension_unloaded', self._on_extension_unloaded)
            self.loader.add_event_handler('load_error', self._on_load_error)
            
            # Setup store callbacks
            self.store.add_update_callback(self._on_extension_updates)
            
            # Start background monitoring
            self._start_monitoring()
            
            # Start update checker
            self.store.start_update_checker()
            
            # Load installed extensions
            self._load_installed_extensions()
            
            self.initialized = True
            self.logger.info("Extension system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing extension system: {e}")
    
    def _load_installed_extensions(self):
        """Load and enable installed extensions."""
        try:
            extensions = self.loader.list_extensions()
            
            for extension in extensions:
                if extension.get('enabled', False):
                    self.logger.info(f"Enabling extension: {extension['name']}")
                    success, message = self.loader.enable_extension(extension['id'])
                    
                    if not success:
                        self.logger.error(f"Failed to enable {extension['name']}: {message}")
            
        except Exception as e:
            self.logger.error(f"Error loading installed extensions: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring."""
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                # Monitor extension health
                self._monitor_extension_health()
                
                # Check for security events
                self._check_security_events()
                
                # Update UI if needed
                self._update_ui_if_needed()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _monitor_extension_health(self):
        """Monitor health of running extensions."""
        try:
            extensions = self.loader.list_extensions()
            
            for extension in extensions:
                if extension.get('enabled', False):
                    # Check for memory leaks, crashes, etc.
                    extension_id = extension['id']
                    stats = self.hook_manager.get_hook_stats(extension_id)
                    
                    if stats.get('errors', 0) > 10:
                        self.logger.warning(f"Extension {extension_id} has high error count")
                        self._handle_unhealthy_extension(extension_id)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring extension health: {e}")
    
    def _check_security_events(self):
        """Check for security events."""
        try:
            # Get security events from security manager
            security_events = self.security_manager.security_events
            
            # Process recent security events
            recent_events = [
                event for event in security_events
                if event.severity in ['high', 'critical'] and
                time.time() - event.timestamp.timestamp() < 3600  # Last hour
            ]
            
            for event in recent_events:
                if not event.resolved:
                    self._handle_security_event(event)
                    
        except Exception as e:
            self.logger.error(f"Error checking security events: {e}")
    
    def _update_ui_if_needed(self):
        """Update UI if needed."""
        try:
            # Update extension manager UI if browser has one
            if hasattr(self.browser, 'update_extension_ui'):
                extensions = self.loader.list_extensions()
                self.browser.update_extension_ui(extensions)
                
        except Exception as e:
            self.logger.error(f"Error updating UI: {e}")
    
    def _on_extension_loaded(self, extension_id: str):
        """Handle extension loaded event."""
        try:
            self.logger.info(f"Extension loaded: {extension_id}")
            
            # Create API instance
            extension = self.loader.extensions.get(extension_id)
            if extension:
                api = ExtensionAPI(extension)
                api.set_browser_window(self.browser)
                api.set_hook_manager(self.hook_manager)
                
                self.extension_apis[extension_id] = api
                
                # Register with UI manager
                self.ui_manager.register_extension(extension_id, api)
                
                # Fire event
                self._fire_event('extension_loaded', extension_id)
                
        except Exception as e:
            self.logger.error(f"Error handling extension loaded: {e}")
    
    def _on_extension_enabled(self, extension_id: str):
        """Handle extension enabled event."""
        try:
            self.logger.info(f"Extension enabled: {extension_id}")
            
            # Update UI
            if extension_id in self.extension_apis:
                self.ui_manager.update_extension_badge(extension_id, "🟢", "#00ff00")
            
            # Fire event
            self._fire_event('extension_enabled', extension_id)
            
        except Exception as e:
            self.logger.error(f"Error handling extension enabled: {e}")
    
    def _on_extension_disabled(self, extension_id: str):
        """Handle extension disabled event."""
        try:
            self.logger.info(f"Extension disabled: {extension_id}")
            
            # Update UI
            if extension_id in self.extension_apis:
                self.ui_manager.update_extension_badge(extension_id, "🔴", "#ff0000")
            
            # Fire event
            self._fire_event('extension_disabled', extension_id)
            
        except Exception as e:
            self.logger.error(f"Error handling extension disabled: {e}")
    
    def _on_extension_unloaded(self, extension_id: str):
        """Handle extension unloaded event."""
        try:
            self.logger.info(f"Extension unloaded: {extension_id}")
            
            # Clean up API
            if extension_id in self.extension_apis:
                del self.extension_apis[extension_id]
            
            # Unregister from UI manager
            self.ui_manager.unregister_extension(extension_id)
            
            # Clear hooks
            self.hook_manager.clear_extension_hooks(extension_id)
            
            # Fire event
            self._fire_event('extension_unloaded', extension_id)
            
        except Exception as e:
            self.logger.error(f"Error handling extension unloaded: {e}")
    
    def _on_load_error(self, extension_id: str, error: Any):
        """Handle extension load error."""
        try:
            self.logger.error(f"Extension load error: {extension_id} - {error}")
            
            # Update UI to show error
            if extension_id in self.extension_apis:
                self.ui_manager.update_extension_badge(extension_id, "X", "#ff0000")
            
            # Fire event
            self._fire_event('load_error', extension_id, error)
            
        except Exception as e:
            self.logger.error(f"Error handling load error: {e}")
    
    def _on_extension_updates(self, updates: List[Dict[str, Any]]):
        """Handle extension updates."""
        try:
            if updates:
                self.logger.info(f"Found {len(updates)} extension updates")
                
                # Notify user about updates
                if hasattr(self.browser, 'show_notification'):
                    self.browser.show_notification(
                        "Extension Updates Available",
                        f"{len(updates)} extensions have updates available"
                    )
                
                # Fire event
                self._fire_event('extension_updates', updates)
                
        except Exception as e:
            self.logger.error(f"Error handling extension updates: {e}")
    
    def _handle_unhealthy_extension(self, extension_id: str):
        """Handle unhealthy extension."""
        try:
            self.logger.warning(f"Handling unhealthy extension: {extension_id}")
            
            # Get extension info
            extension_info = self.loader.get_extension_info(extension_id)
            
            if extension_info:
                # Disable extension if it's causing problems
                success, message = self.loader.disable_extension(extension_id)
                
                if success:
                    # Notify user
                    if hasattr(self.browser, 'show_notification'):
                        self.browser.show_notification(
                            "Extension Disabled",
                            f"{extension_info['metadata']['name']} was disabled due to errors"
                        )
                
        except Exception as e:
            self.logger.error(f"Error handling unhealthy extension: {e}")
    
    def _handle_security_event(self, event: Any):
        """Handle security event."""
        try:
            self.logger.warning(f"Handling security event: {event.description}")
            
            # Take action based on event type
            if event.event_type == 'threat_detected':
                # Disable threatening extension
                extension_id = event.extension_id
                success, message = self.loader.disable_extension(extension_id)
                
                if success:
                    if hasattr(self.browser, 'show_notification'):
                        self.browser.show_notification(
                            "Security Threat Detected",
                            f"Extension {extension_id} was disabled for security reasons"
                        )
            
            # Mark event as resolved
            event.resolved = True
            event.resolution = "Automatically handled by extension system"
            
        except Exception as e:
            self.logger.error(f"Error handling security event: {e}")
    
    def _fire_event(self, event_name: str, *args):
        """Fire event to all handlers."""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    handler(*args)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_name}: {e}")
    
    # Public API methods
    def install_extension(self, source_path: str, auto_enable: bool = True) -> tuple:
        """Install an extension."""
        return self.loader.install_extension(source_path, auto_enable)
    
    def uninstall_extension(self, extension_id: str) -> tuple:
        """Uninstall an extension."""
        return self.loader.uninstall_extension(extension_id)
    
    def enable_extension(self, extension_id: str) -> tuple:
        """Enable an extension."""
        return self.loader.enable_extension(extension_id)
    
    def disable_extension(self, extension_id: str) -> tuple:
        """Disable an extension."""
        return self.loader.disable_extension(extension_id)
    
    def reload_extension(self, extension_id: str) -> tuple:
        """Reload an extension."""
        return self.loader.update_extension(extension_id, self.loader.extension_paths[extension_id])
    
    def get_extensions(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get list of extensions."""
        return self.loader.list_extensions(enabled_only)
    
    def get_extension_info(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an extension."""
        return self.loader.get_extension_info(extension_id)
    
    def get_extension_api(self, extension_id: str) -> Optional[ExtensionAPI]:
        """Get API instance for an extension."""
        return self.extension_apis.get(extension_id)
    
    def search_extensions(self, query: Dict[str, Any]) -> Any:
        """Search for extensions in store."""
        from .store import SearchQuery
        search_query = SearchQuery(**query)
        return self.store.search(search_query)
    
    def get_featured_extensions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured extensions."""
        return self.store.get_featured(limit)
    
    def get_trending_extensions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending extensions."""
        return self.store.get_trending(limit)
    
    def show_extension_manager(self):
        """Show extension manager UI."""
        try:
            if hasattr(self.browser, 'show_extension_manager'):
                self.browser.show_extension_manager()
            else:
                # Create simple extension manager dialog
                self._create_extension_manager_dialog()
                
        except Exception as e:
            self.logger.error(f"Error showing extension manager: {e}")
    
    def _create_extension_manager_dialog(self):
        """Create a simple extension manager dialog."""
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            
            dialog = tk.Toplevel(self.browser.root)
            dialog.title("Extension Manager")
            dialog.geometry("800x600")
            dialog.transient(self.browser.root)
            dialog.grab_set()
            
            # Create treeview for extensions
            columns = ('Name', 'Version', 'Status', 'Description')
            tree = ttk.Treeview(dialog, columns=columns, show='headings', height=20)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(dialog, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
            scrollbar.pack(side='right', fill='y', padx=(0, 10), pady=10)
            
            # Populate extensions
            extensions = self.get_extensions()
            for ext in extensions:
                status = "Enabled" if ext['enabled'] else "Disabled"
                tree.insert('', 'end', values=(
                    ext['name'],
                    ext['version'],
                    status,
                    ext['description'][:50] + "..." if len(ext['description']) > 50 else ext['description']
                ))
            
            # Button frame
            button_frame = tk.Frame(dialog)
            button_frame.pack(fill='x', padx=10, pady=10)
            
            tk.Button(button_frame, text="Enable All", 
                     command=lambda: self._enable_all_extensions()).pack(side='left', padx=5)
            tk.Button(button_frame, text="Disable All", 
                     command=lambda: self._disable_all_extensions()).pack(side='left', padx=5)
            tk.Button(button_frame, text="Close", 
                     command=dialog.destroy).pack(side='right', padx=5)
            
        except Exception as e:
            self.logger.error(f"Error creating extension manager dialog: {e}")
    
    def _enable_all_extensions(self):
        """Enable all extensions."""
        extensions = self.get_extensions(enabled_only=False)
        for ext in extensions:
            if not ext['enabled']:
                self.enable_extension(ext['id'])
    
    def _disable_all_extensions(self):
        """Disable all extensions."""
        extensions = self.get_extensions()
        for ext in extensions:
            self.disable_extension(ext['id'])
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """Add event handler."""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable):
        """Remove event handler."""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        extensions = self.get_extensions()
        enabled_extensions = [e for e in extensions if e['enabled']]
        
        return {
            'total_extensions': len(extensions),
            'enabled_extensions': len(enabled_extensions),
            'disabled_extensions': len(extensions) - len(enabled_extensions),
            'system_initialized': self.initialized,
            'extensions_enabled': self.extensions_enabled,
            'security_events': len(self.security_manager.security_events),
            'hook_stats': self.hook_manager.get_hook_stats()
        }
    
    def shutdown(self):
        """Shutdown the extension system."""
        try:
            self.logger.info("Shutting down extension system...")
            
            # Stop update checker
            self.store.stop_update_checker()
            
            # Disable all extensions
            extensions = self.get_extensions()
            for ext in extensions:
                if ext['enabled']:
                    self.disable_extension(ext['id'])
            
            # Unload all extensions
            for ext in extensions:
                self.loader.unload_extension(ext['id'])
            
            self.initialized = False
            self.logger.info("Extension system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error shutting down extension system: {e}")
    
    # Browser integration methods
    def on_navigation_start(self, url: str, tab_id: str):
        """Handle navigation start."""
        try:
            # Fire browser hook
            result = self.browser_hooks.before_navigation(url, tab_id)
            
            # Check if navigation should be cancelled
            if result and result.cancel:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling navigation start: {e}")
            return True
    
    def on_navigation_complete(self, url: str, tab_id: str, status_code: int = 200):
        """Handle navigation complete."""
        try:
            # Fire browser hook
            self.browser_hooks.navigation_completed(url, tab_id, status_code)
            
        except Exception as e:
            self.logger.error(f"Error handling navigation complete: {e}")
    
    def on_tab_created(self, tab_id: str, url: str = "about:blank"):
        """Handle tab created."""
        try:
            # Fire browser hook
            self.browser_hooks.tab_created(tab_id, url)
            
        except Exception as e:
            self.logger.error(f"Error handling tab created: {e}")
    
    def on_tab_closed(self, tab_id: str):
        """Handle tab closed."""
        try:
            # Fire browser hook
            self.browser_hooks.tab_closed(tab_id)
            
        except Exception as e:
            self.logger.error(f"Error handling tab closed: {e}")
    
    def on_bookmark_created(self, bookmark_id: str, title: str, url: str):
        """Handle bookmark created."""
        try:
            # Fire browser hook
            self.browser_hooks.bookmark_created(bookmark_id, title, url)
            
        except Exception as e:
            self.logger.error(f"Error handling bookmark created: {e}")
    
    def on_download_started(self, download_id: str, url: str, filename: str):
        """Handle download started."""
        try:
            # Fire browser hook
            self.browser_hooks.download_started(download_id, url, filename)
            
        except Exception as e:
            self.logger.error(f"Error handling download started: {e}")
    
    def on_toolbar_button_clicked(self, extension_id: str, button_id: str):
        """Handle toolbar button click."""
        try:
            # Fire browser hook
            self.browser_hooks.toolbar_button_clicked(extension_id, button_id)
            
        except Exception as e:
            self.logger.error(f"Error handling toolbar button click: {e}")
    
    def on_context_menu_shown(self, tab_id: str, context: Dict[str, Any]):
        """Handle context menu shown."""
        try:
            # Fire browser hook
            self.browser_hooks.context_menu_shown(tab_id, context)
            
        except Exception as e:
            self.logger.error(f"Error handling context menu shown: {e}")
    
    def on_context_menu_item_clicked(self, extension_id: str, item_id: str, 
                                  tab_id: str, context: Dict[str, Any]):
        """Handle context menu item click."""
        try:
            # Fire browser hook
            self.browser_hooks.context_menu_item_clicked(extension_id, item_id, tab_id, context)
            
        except Exception as e:
            self.logger.error(f"Error handling context menu item click: {e}")
