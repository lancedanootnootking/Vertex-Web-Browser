#!/usr/bin/env python3
"""
Extension Hooks System

Provides a comprehensive hook system for extensions to intercept
and modify browser behavior at various points.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import json
import re


class HookType(Enum):
    """Types of hooks available for extensions."""
    # Navigation hooks
    BEFORE_NAVIGATION = "before_navigation"
    NAVIGATION_COMMITTED = "navigation_committed"
    NAVIGATION_COMPLETED = "navigation_completed"
    NAVIGATION_FAILED = "navigation_failed"
    
    # Request hooks
    BEFORE_REQUEST = "before_request"
    REQUEST_SENT = "request_sent"
    RESPONSE_RECEIVED = "response_received"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_ERROR = "request_error"
    
    # Content hooks
    CONTENT_LOADED = "content_loaded"
    DOM_READY = "dom_ready"
    CONTENT_SCRIPT_INJECTED = "content_script_injected"
    
    # Tab hooks
    TAB_CREATED = "tab_created"
    TAB_UPDATED = "tab_updated"
    TAB_ACTIVATED = "tab_activated"
    TAB_CLOSED = "tab_closed"
    
    # Bookmark hooks
    BOOKMARK_CREATED = "bookmark_created"
    BOOKMARK_UPDATED = "bookmark_updated"
    BOOKMARK_REMOVED = "bookmark_removed"
    
    # Download hooks
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    
    # Extension hooks
    EXTENSION_INSTALLED = "extension_installed"
    EXTENSION_ENABLED = "extension_enabled"
    EXTENSION_DISABLED = "extension_disabled"
    EXTENSION_UNINSTALLED = "extension_uninstalled"
    
    # UI hooks
    MENU_CREATED = "menu_created"
    TOOLBAR_BUTTON_CLICKED = "toolbar_button_clicked"
    CONTEXT_MENU_SHOWN = "context_menu_shown"
    CONTEXT_MENU_ITEM_CLICKED = "context_menu_item_clicked"
    
    # Storage hooks
    STORAGE_CHANGED = "storage_changed"
    STORAGE_CLEARED = "storage_cleared"


class HookPriority(Enum):
    """Hook execution priority."""
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


class HookResult:
    """Result of a hook execution."""
    
    def __init__(self, success: bool = True, data: Any = None, 
                 cancel: bool = False, modified: bool = False):
        self.success = success
        self.data = data
        self.cancel = cancel
        self.modified = modified
        self.timestamp = datetime.now()


@dataclass
class HookContext:
    """Context passed to hook handlers."""
    extension_id: str
    hook_type: HookType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: float = 0.0
    error: Optional[Exception] = None


@dataclass
class HookRegistration:
    """Registration information for a hook."""
    extension_id: str
    hook_type: HookType
    handler: Callable
    priority: HookPriority = HookPriority.NORMAL
    filter_func: Optional[Callable] = None
    once: bool = False
    active: bool = True
    registration_time: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    total_execution_time: float = 0.0


class HookManager:
    """Manages extension hooks and their execution."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hooks: Dict[HookType, List[HookRegistration]] = {}
        self.global_filters: List[Callable] = []
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        # Initialize hook types
        for hook_type in HookType:
            self.hooks[hook_type] = []
    
    def register_hook(self, extension_id: str, hook_type: HookType, 
                     handler: Callable, priority: HookPriority = HookPriority.NORMAL,
                     filter_func: Optional[Callable] = None, once: bool = False) -> str:
        """Register a hook for an extension."""
        with self.lock:
            registration = HookRegistration(
                extension_id=extension_id,
                hook_type=hook_type,
                handler=handler,
                priority=priority,
                filter_func=filter_func,
                once=once
            )
            
            # Insert in priority order
            hooks_list = self.hooks[hook_type]
            insert_pos = 0
            for i, hook_reg in enumerate(hooks_list):
                if registration.priority.value < hook_reg.priority.value:
                    insert_pos = i
                    break
                insert_pos = i + 1
            
            hooks_list.insert(insert_pos, registration)
            
            # Initialize stats
            if extension_id not in self.execution_stats:
                self.execution_stats[extension_id] = {
                    'total_executions': 0,
                    'total_time': 0.0,
                    'errors': 0,
                    'hooks_registered': 0
                }
            
            self.execution_stats[extension_id]['hooks_registered'] += 1
            
            self.logger.debug(f"Registered hook {hook_type.value} for extension {extension_id}")
            return f"{extension_id}_{hook_type.value}_{id(registration)}"
    
    def unregister_hook(self, extension_id: str, hook_type: HookType, handler: Callable = None) -> bool:
        """Unregister hooks for an extension."""
        with self.lock:
            hooks_list = self.hooks[hook_type]
            removed_count = 0
            
            if handler:
                # Remove specific handler
                hooks_list[:] = [h for h in hooks_list 
                               if not (h.extension_id == extension_id and h.handler == handler)]
            else:
                # Remove all hooks for extension
                original_count = len(hooks_list)
                hooks_list[:] = [h for h in hooks_list if h.extension_id != extension_id]
                removed_count = original_count - len(hooks_list)
            
            if removed_count > 0:
                self.execution_stats[extension_id]['hooks_registered'] -= removed_count
                self.logger.debug(f"Unregistered {removed_count} hooks for extension {extension_id}")
                return True
            
            return False
    
    def unregister_all_hooks(self, extension_id: str) -> int:
        """Unregister all hooks for an extension."""
        with self.lock:
            total_removed = 0
            
            for hook_type in HookType:
                hooks_list = self.hooks[hook_type]
                original_count = len(hooks_list)
                hooks_list[:] = [h for h in hooks_list if h.extension_id != extension_id]
                removed = original_count - len(hooks_list)
                total_removed += removed
            
            if extension_id in self.execution_stats:
                self.execution_stats[extension_id]['hooks_registered'] = 0
            
            self.logger.info(f"Unregistered all {total_removed} hooks for extension {extension_id}")
            return total_removed
    
    def execute_hook(self, hook_type: HookType, data: Dict[str, Any], 
                    extension_id: Optional[str] = None) -> HookResult:
        """Execute all registered hooks for a given type."""
        start_time = time.time()
        
        with self.lock:
            hooks_list = self.hooks[hook_type].copy()
        
        results = []
        context = HookContext(
            extension_id=extension_id or "system",
            hook_type=hook_type,
            data=data.copy()
        )
        
        try:
            for registration in hooks_list:
                # Skip inactive hooks
                if not registration.active:
                    continue
                
                # Skip if extension is specified and doesn't match
                if extension_id and registration.extension_id != extension_id:
                    continue
                
                # Apply filters
                if registration.filter_func and not registration.filter_func(context):
                    continue
                
                # Apply global filters
                if not all(filter_func(context) for filter_func in self.global_filters):
                    continue
                
                hook_start = time.time()
                
                try:
                    # Execute hook
                    result = registration.handler(context)
                    
                    # Update registration stats
                    registration.execution_count += 1
                    registration.last_execution = datetime.now()
                    execution_time = time.time() - hook_start
                    registration.total_execution_time += execution_time
                    
                    # Update extension stats
                    if registration.extension_id in self.execution_stats:
                        self.execution_stats[registration.extension_id]['total_executions'] += 1
                        self.execution_stats[registration.extension_id]['total_time'] += execution_time
                    
                    # Handle result
                    if isinstance(result, HookResult):
                        results.append(result)
                        
                        # If hook requests cancellation, stop execution
                        if result.cancel:
                            context.execution_time = time.time() - start_time
                            return result
                        
                        # Update data if modified
                        if result.modified and result.data is not None:
                            context.data.update(result.data)
                    elif result is not None:
                        # Convert to HookResult
                        hook_result = HookResult(data=result, modified=True)
                        results.append(hook_result)
                        
                        if isinstance(result, dict) and result.get('cancel'):
                            context.execution_time = time.time() - start_time
                            return hook_result
                        
                        if isinstance(result, dict):
                            context.data.update(result)
                    
                    # Remove one-time hooks
                    if registration.once:
                        registration.active = False
                        with self.lock:
                            if registration in self.hooks[hook_type]:
                                self.hooks[hook_type].remove(registration)
                    
                except Exception as e:
                    self.logger.error(f"Error executing hook {hook_type.value} for extension {registration.extension_id}: {e}")
                    
                    # Update error stats
                    if registration.extension_id in self.execution_stats:
                        self.execution_stats[registration.extension_id]['errors'] += 1
                    
                    context.error = e
            
            context.execution_time = time.time() - start_time
            
            # Combine results
            combined_result = HookResult(
                success=not any(not r.success for r in results),
                data=context.data,
                cancel=any(r.cancel for r in results),
                modified=any(r.modified for r in results)
            )
            
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Error executing hooks {hook_type.value}: {e}")
            context.execution_time = time.time() - start_time
            context.error = e
            return HookResult(success=False, data=context.data)
    
    def add_global_filter(self, filter_func: Callable):
        """Add a global filter that applies to all hooks."""
        self.global_filters.append(filter_func)
    
    def remove_global_filter(self, filter_func: Callable):
        """Remove a global filter."""
        if filter_func in self.global_filters:
            self.global_filters.remove(filter_func)
    
    def get_hook_stats(self, extension_id: Optional[str] = None) -> Dict[str, Any]:
        """Get hook execution statistics."""
        with self.lock:
            if extension_id:
                return self.execution_stats.get(extension_id, {})
            
            # Return stats for all extensions
            return self.execution_stats.copy()
    
    def get_registered_hooks(self, extension_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about registered hooks."""
        with self.lock:
            result = {}
            
            for hook_type, hooks_list in self.hooks.items():
                hook_info = []
                
                for registration in hooks_list:
                    if extension_id and registration.extension_id != extension_id:
                        continue
                    
                    hook_info.append({
                        'extension_id': registration.extension_id,
                        'hook_type': registration.hook_type.value,
                        'priority': registration.priority.value,
                        'once': registration.once,
                        'active': registration.active,
                        'registration_time': registration.registration_time.isoformat(),
                        'execution_count': registration.execution_count,
                        'last_execution': registration.last_execution.isoformat() if registration.last_execution else None,
                        'total_execution_time': registration.total_execution_time,
                        'average_execution_time': registration.total_execution_time / max(registration.execution_count, 1)
                    })
                
                if hook_info:
                    result[hook_type.value] = hook_info
            
            return result
    
    def clear_extension_hooks(self, extension_id: str):
        """Clear all hooks for an extension."""
        self.unregister_all_hooks(extension_id)
        
        # Clear stats
        if extension_id in self.execution_stats:
            del self.execution_stats[extension_id]


class HookAPI:
    """API for extensions to register and manage hooks."""
    
    def __init__(self, extension_id: str, hook_manager: HookManager):
        self.extension_id = extension_id
        self.hook_manager = hook_manager
        self.logger = logging.getLogger(__name__)
        self.registered_hooks: List[str] = []
    
    def register_hook(self, hook_type: Union[str, HookType], handler: Callable, 
                     priority: Union[str, HookPriority] = HookPriority.NORMAL,
                     filter_func: Optional[Callable] = None, once: bool = False) -> str:
        """Register a hook."""
        # Convert string to enum
        if isinstance(hook_type, str):
            try:
                hook_type = HookType(hook_type)
            except ValueError:
                raise ValueError(f"Invalid hook type: {hook_type}")
        
        if isinstance(priority, str):
            try:
                priority = HookPriority(priority)
            except ValueError:
                raise ValueError(f"Invalid priority: {priority}")
        
        hook_id = self.hook_manager.register_hook(
            self.extension_id, hook_type, handler, priority, filter_func, once
        )
        
        self.registered_hooks.append(hook_id)
        return hook_id
    
    def unregister_hook(self, hook_type: Union[str, HookType], handler: Callable = None):
        """Unregister a hook."""
        if isinstance(hook_type, str):
            try:
                hook_type = HookType(hook_type)
            except ValueError:
                raise ValueError(f"Invalid hook type: {hook_type}")
        
        return self.hook_manager.unregister_hook(self.extension_id, hook_type, handler)
    
    def unregister_all_hooks(self):
        """Unregister all hooks for this extension."""
        count = self.hook_manager.unregister_all_hooks(self.extension_id)
        self.registered_hooks.clear()
        return count
    
    def create_url_filter(self, patterns: List[str]) -> Callable:
        """Create a URL filter function."""
        compiled_patterns = [re.compile(pattern) for pattern in patterns]
        
        def url_filter(context: HookContext) -> bool:
            url = context.data.get('url', '')
            return any(pattern.search(url) for pattern in compiled_patterns)
        
        return url_filter
    
    def create_domain_filter(self, domains: List[str]) -> Callable:
        """Create a domain filter function."""
        def domain_filter(context: HookContext) -> bool:
            url = context.data.get('url', '')
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                return domain in domains
            except:
                return False
        
        return domain_filter
    
    def create_data_filter(self, key: str, value: Any) -> Callable:
        """Create a data filter function."""
        def data_filter(context: HookContext) -> bool:
            return context.data.get(key) == value
        
        return data_filter
    
    def get_hook_stats(self) -> Dict[str, Any]:
        """Get hook execution statistics for this extension."""
        return self.hook_manager.get_hook_stats(self.extension_id)
    
    def get_registered_hooks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about registered hooks for this extension."""
        return self.hook_manager.get_registered_hooks(self.extension_id)


class BrowserHooks:
    """Integration layer for browser hooks."""
    
    def __init__(self, hook_manager: HookManager):
        self.hook_manager = hook_manager
        self.logger = logging.getLogger(__name__)
    
    def before_navigation(self, url: str, tab_id: str, 
                        source_frame_id: Optional[str] = None) -> HookResult:
        """Called before navigation starts."""
        return self.hook_manager.execute_hook(
            HookType.BEFORE_NAVIGATION,
            {
                'url': url,
                'tab_id': tab_id,
                'source_frame_id': source_frame_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def navigation_committed(self, url: str, tab_id: str, 
                            transition_type: str = "link") -> HookResult:
        """Called when navigation is committed."""
        return self.hook_manager.execute_hook(
            HookType.NAVIGATION_COMMITTED,
            {
                'url': url,
                'tab_id': tab_id,
                'transition_type': transition_type,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def navigation_completed(self, url: str, tab_id: str, 
                            status_code: int = 200) -> HookResult:
        """Called when navigation completes."""
        return self.hook_manager.execute_hook(
            HookType.NAVIGATION_COMPLETED,
            {
                'url': url,
                'tab_id': tab_id,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def before_request(self, url: str, method: str = "GET", 
                      headers: Optional[Dict[str, str]] = None,
                      body: Optional[str] = None) -> HookResult:
        """Called before a request is sent."""
        return self.hook_manager.execute_hook(
            HookType.BEFORE_REQUEST,
            {
                'url': url,
                'method': method,
                'headers': headers or {},
                'body': body,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def response_received(self, url: str, status_code: int, 
                          headers: Dict[str, str], tab_id: str) -> HookResult:
        """Called when a response is received."""
        return self.hook_manager.execute_hook(
            HookType.RESPONSE_RECEIVED,
            {
                'url': url,
                'status_code': status_code,
                'headers': headers,
                'tab_id': tab_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def content_loaded(self, url: str, tab_id: str, 
                       content: Optional[str] = None) -> HookResult:
        """Called when page content is loaded."""
        return self.hook_manager.execute_hook(
            HookType.CONTENT_LOADED,
            {
                'url': url,
                'tab_id': tab_id,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def tab_created(self, tab_id: str, url: str = "about:blank") -> HookResult:
        """Called when a new tab is created."""
        return self.hook_manager.execute_hook(
            HookType.TAB_CREATED,
            {
                'tab_id': tab_id,
                'url': url,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def tab_updated(self, tab_id: str, url: str, title: str) -> HookResult:
        """Called when a tab is updated."""
        return self.hook_manager.execute_hook(
            HookType.TAB_UPDATED,
            {
                'tab_id': tab_id,
                'url': url,
                'title': title,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def tab_activated(self, tab_id: str) -> HookResult:
        """Called when a tab becomes active."""
        return self.hook_manager.execute_hook(
            HookType.TAB_ACTIVATED,
            {
                'tab_id': tab_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def tab_closed(self, tab_id: str) -> HookResult:
        """Called when a tab is closed."""
        return self.hook_manager.execute_hook(
            HookType.TAB_CLOSED,
            {
                'tab_id': tab_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def bookmark_created(self, bookmark_id: str, title: str, url: str) -> HookResult:
        """Called when a bookmark is created."""
        return self.hook_manager.execute_hook(
            HookType.BOOKMARK_CREATED,
            {
                'bookmark_id': bookmark_id,
                'title': title,
                'url': url,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def download_started(self, download_id: str, url: str, filename: str) -> HookResult:
        """Called when a download starts."""
        return self.hook_manager.execute_hook(
            HookType.DOWNLOAD_STARTED,
            {
                'download_id': download_id,
                'url': url,
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def download_completed(self, download_id: str, file_path: str) -> HookResult:
        """Called when a download completes."""
        return self.hook_manager.execute_hook(
            HookType.DOWNLOAD_COMPLETED,
            {
                'download_id': download_id,
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def storage_changed(self, extension_id: str, area: str, 
                       key: str, old_value: Any, new_value: Any) -> HookResult:
        """Called when extension storage changes."""
        return self.hook_manager.execute_hook(
            HookType.STORAGE_CHANGED,
            {
                'extension_id': extension_id,
                'area': area,
                'key': key,
                'old_value': old_value,
                'new_value': new_value,
                'timestamp': datetime.now().isoformat()
            },
            extension_id=extension_id
        )
    
    def toolbar_button_clicked(self, extension_id: str, button_id: str) -> HookResult:
        """Called when a toolbar button is clicked."""
        return self.hook_manager.execute_hook(
            HookType.TOOLBAR_BUTTON_CLICKED,
            {
                'extension_id': extension_id,
                'button_id': button_id,
                'timestamp': datetime.now().isoformat()
            },
            extension_id=extension_id
        )
    
    def context_menu_shown(self, tab_id: str, context: Dict[str, Any]) -> HookResult:
        """Called when context menu is shown."""
        return self.hook_manager.execute_hook(
            HookType.CONTEXT_MENU_SHOWN,
            {
                'tab_id': tab_id,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def context_menu_item_clicked(self, extension_id: str, item_id: str, 
                                  tab_id: str, context: Dict[str, Any]) -> HookResult:
        """Called when context menu item is clicked."""
        return self.hook_manager.execute_hook(
            HookType.CONTEXT_MENU_ITEM_CLICKED,
            {
                'extension_id': extension_id,
                'item_id': item_id,
                'tab_id': tab_id,
                'context': context,
                'timestamp': datetime.now().isoformat()
            },
            extension_id=extension_id
        )
