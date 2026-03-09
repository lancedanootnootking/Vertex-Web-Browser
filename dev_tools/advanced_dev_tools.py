#!/usr/bin/env python3.12
"""
Advanced Developer Tools for Vertex Browser

Comprehensive web development tools including inspector, console,
network monitor, performance profiler, and debugging features.
"""

import json
import re
import sys
import time
import threading
import traceback
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import weakref
import asyncio
from urllib.parse import urlparse, parse_qs
import html

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit,
                             QFrame, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                             QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
                             QFormLayout, QScrollArea, QSplitter, QMenu, QToolBar,
                             QToolButton, QFileDialog, QStatusBar, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QSlider, QDoubleSpinBox, QDateTimeEdit, QSpinBox,
                             QPlainTextEdit, QCheckBox, QRadioButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QObject, pyqtSlot, QSortFilterProxyModel, QMimeData
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QPainter, QColor, QTextCursor, QTextDocument, QTextFormat

from frontend.themes.modern_theme import theme, style_manager, ui_components


class DevToolType(Enum):
    """Developer tool types."""
    CONSOLE = "console"
    ELEMENTS = "elements"
    NETWORK = "network"
    SOURCES = "sources"
    PERFORMANCE = "performance"
    MEMORY = "memory"
    APPLICATION = "application"
    SECURITY = "security"
    AUDITS = "audits"


class LogLevel(Enum):
    """Console log levels."""
    LOG = "log"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    DEBUG = "debug"


class NetworkRequestType(Enum):
    """Network request types."""
    XHR = "xhr"
    SCRIPT = "script"
    STYLESHEET = "stylesheet"
    IMAGE = "image"
    MEDIA = "media"
    FONT = "font"
    DOCUMENT = "document"
    WEBSOCKET = "websocket"
    OTHER = "other"


@dataclass
class ConsoleMessage:
    """Console message data structure."""
    id: str
    level: LogLevel
    message: str
    source: str = ""
    line: int = 0
    column: int = 0
    timestamp: datetime = None
    stack_trace: str = ""
    arguments: List[Any] = None
    url: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.arguments is None:
            self.arguments = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'level': self.level.value,
            'message': self.message,
            'source': self.source,
            'line': self.line,
            'column': self.column,
            'timestamp': self.timestamp.isoformat(),
            'stack_trace': self.stack_trace,
            'arguments': self.arguments,
            'url': self.url
        }


@dataclass
class NetworkRequest:
    """Network request data structure."""
    id: str
    url: str
    method: str
    status: int
    status_text: str
    request_type: NetworkRequestType
    started_time: datetime
    duration: float = 0.0
    size: int = 0
    response_size: int = 0
    request_headers: Dict[str, str] = None
    response_headers: Dict[str, str] = None
    request_body: str = ""
    response_body: str = ""
    initiator: str = ""
    priority: str = ""
    cached: bool = False
    from_service_worker: bool = False
    error: str = ""
    
    def __post_init__(self):
        if self.request_headers is None:
            self.request_headers = {}
        if self.response_headers is None:
            self.response_headers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'method': self.method,
            'status': self.status,
            'status_text': self.status_text,
            'request_type': self.request_type.value,
            'started_time': self.started_time.isoformat(),
            'duration': self.duration,
            'size': self.size,
            'response_size': self.response_size,
            'request_headers': self.request_headers,
            'response_headers': self.response_headers,
            'request_body': self.request_body,
            'response_body': self.response_body,
            'initiator': self.initiator,
            'priority': self.priority,
            'cached': self.cached,
            'from_service_worker': self.from_service_worker,
            'error': self.error
        }


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class JavaScriptEngine:
    """JavaScript execution engine for console."""
    
    def __init__(self):
        self.context = {}
        self.history = []
        self.max_history = 1000
        
        # Setup built-in functions
        self._setup_builtins()
    
    def _setup_builtins(self):
        """Setup built-in JavaScript functions."""
        self.context.update({
            'console': self._create_console_object(),
            'document': self._create_document_object(),
            'window': self._create_window_object(),
            'localStorage': self._create_storage_object(),
            'sessionStorage': self._create_storage_object(),
            'fetch': self._create_fetch_function(),
            'setTimeout': self._create_set_timeout_function(),
            'setInterval': self._create_set_interval_function(),
            'clearTimeout': self._create_clear_timeout_function(),
            'clearInterval': self._create_clear_interval_function(),
            '$': self._create_query_selector_function(),
            '$$': self._create_query_selector_all_function(),
            'inspect': self._create_inspect_function(),
            'debugger': self._create_debugger_function()
        })
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Any:
        """Execute JavaScript code."""
        if context:
            exec_context = {**self.context, **context}
        else:
            exec_context = self.context.copy()
        
        try:
            # Add to history
            self.history.append({
                'code': code,
                'timestamp': datetime.now(),
                'result': None
            })
            
            # Limit history size
            if len(self.history) > self.max_history:
                self.history.pop(0)
            
            # Execute code (simplified - would use actual JS engine)
            if code.strip().startswith('var ') or code.strip().startswith('let ') or code.strip().startswith('const '):
                exec(code, exec_context)
                return None
            else:
                result = eval(code, exec_context)
                self.history[-1]['result'] = result
                return result
                
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.history[-1]['error'] = error_msg
            return error_msg
    
    def _create_console_object(self) -> Dict[str, Any]:
        """Create console object."""
        console_messages = []
        
        def log(*args):
            message = ' '.join(str(arg) for arg in args)
            console_messages.append({
                'level': LogLevel.LOG,
                'message': message,
                'timestamp': datetime.now()
            })
        
        def info(*args):
            message = ' '.join(str(arg) for arg in args)
            console_messages.append({
                'level': LogLevel.INFO,
                'message': message,
                'timestamp': datetime.now()
            })
        
        def warn(*args):
            message = ' '.join(str(arg) for arg in args)
            console_messages.append({
                'level': LogLevel.WARN,
                'message': message,
                'timestamp': datetime.now()
            })
        
        def error(*args):
            message = ' '.join(str(arg) for arg in args)
            console_messages.append({
                'level': LogLevel.ERROR,
                'message': message,
                'timestamp': datetime.now()
            })
        
        def debug(*args):
            message = ' '.join(str(arg) for arg in args)
            console_messages.append({
                'level': LogLevel.DEBUG,
                'message': message,
                'timestamp': datetime.now()
            })
        
        return {
            'log': log,
            'info': info,
            'warn': warn,
            'error': error,
            'debug': debug,
            'messages': console_messages
        }
    
    def _create_document_object(self) -> Dict[str, Any]:
        """Create document object."""
        return {
            'title': 'Document',
            'URL': 'about:blank',
            'readyState': 'complete',
            'querySelector': lambda selector: [],
            'querySelectorAll': lambda selector: [],
            'createElement': lambda tag: {'tagName': tag.upper()},
            'getElementById': lambda id: None,
            'getElementsByClassName': lambda cls: [],
            'getElementsByTagName': lambda tag: []
        }
    
    def _create_window_object(self) -> Dict[str, Any]:
        """Create window object."""
        return {
            'location': {'href': 'about:blank'},
            'navigator': {'userAgent': 'Vertex Browser'},
            'performance': {'now': lambda: time.time() * 1000},
            'devicePixelRatio': 1.0,
            'innerWidth': 1024,
            'innerHeight': 768,
            'screen': {'width': 1024, 'height': 768}
        }
    
    def _create_storage_object(self) -> Dict[str, Any]:
        """Create storage object."""
        storage = {}
        
        def setItem(key, value):
            storage[key] = str(value)
        
        def getItem(key):
            return storage.get(key)
        
        def removeItem(key):
            storage.pop(key, None)
        
        def clear():
            storage.clear()
        
        return {
            'setItem': setItem,
            'getItem': getItem,
            'removeItem': removeItem,
            'clear': clear,
            'length': len(storage),
            'key': lambda index: list(storage.keys())[index] if index < len(storage) else None
        }
    
    def _create_fetch_function(self) -> Callable:
        """Create fetch function."""
        def fetch(url, options=None):
            # Simplified fetch implementation
            class Response:
                def __init__(self):
                    self.status = 200
                    self.statusText = "OK"
                    self.ok = True
                    self.headers = {}
                
                def json(self):
                    return {}
                
                def text(self):
                    return ""
            
            return Response()
        
        return fetch
    
    def _create_set_timeout_function(self) -> Callable:
        """Create setTimeout function."""
        timers = []
        
        def setTimeout(callback, delay):
            timer_id = len(timers)
            timers.append({'callback': callback, 'delay': delay})
            return timer_id
        
        return setTimeout
    
    def _create_set_interval_function(self) -> Callable:
        """Create setInterval function."""
        intervals = []
        
        def setInterval(callback, delay):
            interval_id = len(intervals)
            intervals.append({'callback': callback, 'delay': delay})
            return interval_id
        
        return setInterval
    
    def _create_clear_timeout_function(self) -> Callable:
        """Create clearTimeout function."""
        def clearTimeout(timer_id):
            pass
        
        return clearTimeout
    
    def _create_clear_interval_function(self) -> Callable:
        """Create clearInterval function."""
        def clearInterval(interval_id):
            pass
        
        return clearInterval
    
    def _create_query_selector_function(self) -> Callable:
        """Create $ function."""
        def querySelector(selector):
            return None
        
        return querySelector
    
    def _create_query_selector_all_function(self) -> Callable:
        """Create $$ function."""
        def querySelectorAll(selector):
            return []
        
        return querySelectorAll
    
    def _create_inspect_function(self) -> Callable:
        """Create inspect function."""
        def inspect(element):
            return element
        
        return inspect
    
    def _create_debugger_function(self) -> Callable:
        """Create debugger function."""
        def debugger():
            pass
        
        return debugger


class NetworkMonitor:
    """Network request monitoring."""
    
    def __init__(self):
        self.requests = []
        self.active_requests = {}
        self.filters = {
            'types': set(),
            'status_codes': set(),
            'search_text': ''
        }
        self.counter = 0
    
    def start_request(self, url: str, method: str = "GET", request_type: NetworkRequestType = NetworkRequestType.OTHER) -> str:
        """Start monitoring a request."""
        self.counter += 1
        request_id = f"req_{self.counter}_{int(time.time())}"
        
        request = NetworkRequest(
            id=request_id,
            url=url,
            method=method,
            status=0,
            status_text="Pending",
            request_type=request_type,
            started_time=datetime.now()
        )
        
        self.requests.append(request)
        self.active_requests[request_id] = request
        
        return request_id
    
    def update_request(self, request_id: str, status: int, status_text: str, 
                       response_headers: Dict[str, str] = None, response_body: str = ""):
        """Update request status."""
        request = self.active_requests.get(request_id)
        if request:
            request.status = status
            request.status_text = status_text
            request.duration = (datetime.now() - request.started_time).total_seconds()
            
            if response_headers:
                request.response_headers = response_headers
            
            if response_body:
                request.response_body = response_body
                request.response_size = len(response_body)
            
            # Remove from active requests
            if status >= 200:
                self.active_requests.pop(request_id, None)
    
    def set_request_error(self, request_id: str, error: str):
        """Set request error."""
        request = self.active_requests.get(request_id)
        if request:
            request.error = error
            request.status = 0
            request.status_text = "Error"
            request.duration = (datetime.now() - request.started_time).total_seconds()
            self.active_requests.pop(request_id, None)
    
    def get_requests(self, filters: Dict[str, Any] = None) -> List[NetworkRequest]:
        """Get requests with optional filters."""
        filtered_requests = self.requests
        
        if filters:
            # Filter by type
            if filters.get('types'):
                filtered_requests = [r for r in filtered_requests if r.request_type in filters['types']]
            
            # Filter by status code
            if filters.get('status_codes'):
                filtered_requests = [r for r in filtered_requests if r.status in filters['status_codes']]
            
            # Filter by search text
            if filters.get('search_text'):
                search_text = filters['search_text'].lower()
                filtered_requests = [r for r in filtered_requests 
                                   if search_text in r.url.lower() or 
                                   search_text in r.method.lower()]
        
        return filtered_requests
    
    def clear_requests(self):
        """Clear all requests."""
        self.requests.clear()
        self.active_requests.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get network statistics."""
        total_requests = len(self.requests)
        successful_requests = len([r for r in self.requests if 200 <= r.status < 300])
        failed_requests = len([r for r in self.requests if r.status >= 400 or r.error])
        
        total_size = sum(r.response_size for r in self.requests)
        total_time = sum(r.duration for r in self.requests)
        
        requests_by_type = {}
        for request in self.requests:
            requests_by_type[request.request_type.value] = requests_by_type.get(request.request_type.value, 0) + 1
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'total_size': total_size,
            'total_time': total_time,
            'average_time': total_time / total_requests if total_requests > 0 else 0,
            'requests_by_type': requests_by_type
        }


class PerformanceProfiler:
    """Performance profiling and metrics."""
    
    def __init__(self):
        self.metrics = []
        self.profiles = []
        self.is_profiling = False
        self.profile_start_time = None
        self.markers = []
        self.measurements = []
    
    def start_profiling(self, name: str = "Profile"):
        """Start performance profiling."""
        if self.is_profiling:
            return
        
        self.is_profiling = True
        self.profile_start_time = time.time()
        self.markers.clear()
        self.measurements.clear()
        
        profile = {
            'name': name,
            'start_time': self.profile_start_time,
            'markers': [],
            'measurements': []
        }
        
        self.profiles.append(profile)
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop performance profiling and return results."""
        if not self.is_profiling:
            return {}
        
        self.is_profiling = False
        end_time = time.time()
        duration = end_time - self.profile_start_time
        
        if self.profiles:
            self.profiles[-1]['end_time'] = end_time
            self.profiles[-1]['duration'] = duration
            self.profiles[-1]['markers'] = self.markers.copy()
            self.profiles[-1]['measurements'] = self.measurements.copy()
        
        return {
            'duration': duration,
            'markers': self.markers.copy(),
            'measurements': self.measurements.copy()
        }
    
    def add_marker(self, name: str):
        """Add performance marker."""
        if self.is_profiling:
            marker = {
                'name': name,
                'timestamp': time.time() - self.profile_start_time
            }
            self.markers.append(marker)
    
    def add_measurement(self, name: str, start_marker: str, end_marker: str):
        """Add performance measurement."""
        start_time = None
        end_time = None
        
        for marker in self.markers:
            if marker['name'] == start_marker:
                start_time = marker['timestamp']
            elif marker['name'] == end_marker:
                end_time = marker['timestamp']
        
        if start_time is not None and end_time is not None:
            measurement = {
                'name': name,
                'start_marker': start_marker,
                'end_marker': end_marker,
                'duration': end_time - start_time
            }
            self.measurements.append(measurement)
    
    def record_metric(self, name: str, value: float, unit: str = ""):
        """Record performance metric."""
        metric = PerformanceMetric(name=name, value=value, unit=unit)
        self.metrics.append(metric)
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """Get all recorded metrics."""
        return self.metrics.copy()
    
    def get_profiles(self) -> List[Dict[str, Any]]:
        """Get all profiles."""
        return self.profiles.copy()
    
    def clear_metrics(self):
        """Clear all metrics."""
        self.metrics.clear()
    
    def clear_profiles(self):
        """Clear all profiles."""
        self.profiles.clear()
        self.markers.clear()
        self.measurements.clear()
        self.is_profiling = False


class DOMInspector:
    """DOM inspection and manipulation."""
    
    def __init__(self):
        self.elements = []
        self.selected_element = None
        self.highlighted_element = None
    
    def inspect_element(self, element_data: Dict[str, Any]):
        """Inspect element."""
        self.selected_element = element_data
        return element_data
    
    def highlight_element(self, element_data: Dict[str, Any]):
        """Highlight element."""
        self.highlighted_element = element_data
    
    def get_element_info(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed element information."""
        return {
            'tagName': element.get('tagName', ''),
            'id': element.get('id', ''),
            'className': element.get('className', ''),
            'attributes': element.get('attributes', {}),
            'styles': element.get('styles', {}),
            'computed_styles': element.get('computed_styles', {}),
            'box_model': element.get('box_model', {}),
            'accessibility': element.get('accessibility', {}),
            'event_listeners': element.get('event_listeners', [])
        }
    
    def get_element_path(self, element: Dict[str, Any]) -> str:
        """Get element CSS path."""
        path_parts = []
        
        # Build path from element to root
        current = element
        while current:
            tag = current.get('tagName', '').lower()
            if tag:
                if current.get('id'):
                    path_parts.append(f"{tag}#{current['id']}")
                elif current.get('className'):
                    classes = current['className'].split()
                    path_parts.append(f"{tag}.{'.'.join(classes)}")
                else:
                    path_parts.append(tag)
            current = current.get('parentElement')
        
        return ' > '.join(reversed(path_parts))
    
    def find_elements(self, selector: str) -> List[Dict[str, Any]]:
        """Find elements by selector."""
        # Simplified selector matching
        results = []
        
        for element in self.elements:
            if self._matches_selector(element, selector):
                results.append(element)
        
        return results
    
    def _matches_selector(self, element: Dict[str, Any], selector: str) -> bool:
        """Check if element matches selector."""
        # Simplified CSS selector matching
        if selector.startswith('#'):
            # ID selector
            return element.get('id') == selector[1:]
        elif selector.startswith('.'):
            # Class selector
            classes = element.get('className', '').split()
            return selector[1:] in classes
        else:
            # Tag selector
            return element.get('tagName', '').lower() == selector.lower()
    
    def get_computed_styles(self, element: Dict[str, Any]) -> Dict[str, str]:
        """Get computed styles for element."""
        return element.get('computed_styles', {})
    
    def get_box_model(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Get box model information."""
        return element.get('box_model', {
            'content': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
            'padding': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
            'border': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
            'margin': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
        })


class SecurityAuditor:
    """Security auditing and analysis."""
    
    def __init__(self):
        self.issues = []
        self.checks = [
            self._check_https,
            self._check_mixed_content,
            self._check_insecure_forms,
            self._check_missing_headers,
            self._check_console_errors,
            self._check_third_party_scripts
        ]
    
    def audit_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Audit page for security issues."""
        self.issues.clear()
        
        for check in self.checks:
            try:
                check(page_data)
            except Exception as e:
                logging.error(f"Security check failed: {e}")
        
        return self.issues
    
    def _check_https(self, page_data: Dict[str, Any]):
        """Check if page uses HTTPS."""
        url = page_data.get('url', '')
        if url.startswith('http://'):
            self.issues.append({
                'severity': 'high',
                'type': 'insecure_protocol',
                'message': 'Page served over HTTP instead of HTTPS',
                'url': url
            })
    
    def _check_mixed_content(self, page_data: Dict[str, Any]):
        """Check for mixed content."""
        resources = page_data.get('resources', [])
        page_url = page_data.get('url', '')
        
        if page_url.startswith('https://'):
            for resource in resources:
                resource_url = resource.get('url', '')
                if resource_url.startswith('http://'):
                    self.issues.append({
                        'severity': 'medium',
                        'type': 'mixed_content',
                        'message': 'Insecure resource loaded on HTTPS page',
                        'url': resource_url
                    })
    
    def _check_insecure_forms(self, page_data: Dict[str, Any]):
        """Check for insecure forms."""
        forms = page_data.get('forms', [])
        
        for form in forms:
            action = form.get('action', '')
            if action.startswith('http://'):
                self.issues.append({
                    'severity': 'high',
                    'type': 'insecure_form',
                    'message': 'Form submits to insecure URL',
                    'url': action
                })
    
    def _check_missing_headers(self, page_data: Dict[str, Any]):
        """Check for missing security headers."""
        headers = page_data.get('headers', {})
        
        security_headers = [
            'Content-Security-Policy',
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        for header in security_headers:
            if header not in headers:
                self.issues.append({
                    'severity': 'medium',
                    'type': 'missing_header',
                    'message': f'Missing security header: {header}',
                    'header': header
                })
    
    def _check_console_errors(self, page_data: Dict[str, Any]):
        """Check for console errors."""
        console_messages = page_data.get('console_messages', [])
        
        for message in console_messages:
            if message.get('level') == 'error':
                self.issues.append({
                    'severity': 'low',
                    'type': 'console_error',
                    'message': 'JavaScript error detected',
                    'error': message.get('message', '')
                })
    
    def _check_third_party_scripts(self, page_data: Dict[str, Any]):
        """Check for third-party scripts."""
        scripts = page_data.get('scripts', [])
        page_domain = urlparse(page_data.get('url', '')).netloc
        
        for script in scripts:
            script_domain = urlparse(script.get('src', '')).netloc
            if script_domain and script_domain != page_domain:
                self.issues.append({
                    'severity': 'info',
                    'type': 'third_party_script',
                    'message': 'Third-party script detected',
                    'url': script.get('src', '')
                })
    
    def get_security_score(self) -> int:
        """Calculate security score (0-100)."""
        if not self.issues:
            return 100
        
        severity_weights = {
            'high': 30,
            'medium': 15,
            'low': 5,
            'info': 1
        }
        
        total_penalty = sum(severity_weights.get(issue['severity'], 0) for issue in self.issues)
        score = max(0, 100 - total_penalty)
        
        return score


class DevToolsManager:
    """Main developer tools manager."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.js_engine = JavaScriptEngine()
        self.network_monitor = NetworkMonitor()
        self.performance_profiler = PerformanceProfiler()
        self.dom_inspector = DOMInspector()
        self.security_auditor = SecurityAuditor()
        
        self.console_messages = []
        self.active_tool = DevToolType.CONSOLE
        self.is_docked = True
        self.position = "bottom"
        
        # Setup message handling
        self._setup_message_handlers()
    
    def _setup_message_handlers(self):
        """Setup message handlers for different tools."""
        self.message_handlers = {
            DevToolType.CONSOLE: self._handle_console_message,
            DevToolType.NETWORK: self._handle_network_message,
            DevToolType.PERFORMANCE: self._handle_performance_message,
            DevToolType.ELEMENTS: self._handle_elements_message,
            DevToolType.SECURITY: self._handle_security_message
        }
    
    def execute_javascript(self, code: str, context: Dict[str, Any] = None) -> Any:
        """Execute JavaScript code."""
        return self.js_engine.execute(code, context)
    
    def log_console_message(self, level: LogLevel, message: str, **kwargs):
        """Log console message."""
        console_msg = ConsoleMessage(
            id=f"console_{int(time.time() * 1000)}",
            level=level,
            message=message,
            **kwargs
        )
        
        self.console_messages.append(console_msg)
        
        # Limit message history
        if len(self.console_messages) > 1000:
            self.console_messages.pop(0)
    
    def start_network_request(self, url: str, method: str = "GET", request_type: NetworkRequestType = NetworkRequestType.OTHER) -> str:
        """Start monitoring network request."""
        return self.network_monitor.start_request(url, method, request_type)
    
    def update_network_request(self, request_id: str, **kwargs):
        """Update network request."""
        self.network_monitor.update_request(request_id, **kwargs)
    
    def set_network_request_error(self, request_id: str, error: str):
        """Set network request error."""
        self.network_monitor.set_request_error(request_id, error)
    
    def start_performance_profiling(self, name: str = "Profile"):
        """Start performance profiling."""
        self.performance_profiler.start_profiling(name)
    
    def stop_performance_profiling(self) -> Dict[str, Any]:
        """Stop performance profiling."""
        return self.performance_profiler.stop_profiling()
    
    def add_performance_marker(self, name: str):
        """Add performance marker."""
        self.performance_profiler.add_marker(name)
    
    def record_performance_metric(self, name: str, value: float, unit: str = ""):
        """Record performance metric."""
        self.performance_profiler.record_metric(name, value, unit)
    
    def inspect_element(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect DOM element."""
        return self.dom_inspector.inspect_element(element_data)
    
    def highlight_element(self, element_data: Dict[str, Any]):
        """Highlight DOM element."""
        self.dom_inspector.highlight_element(element_data)
    
    def audit_page_security(self, page_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Audit page security."""
        issues = self.security_auditor.audit_page(page_data)
        score = self.security_auditor.get_security_score()
        return issues, score
    
    def get_console_messages(self, level_filter: LogLevel = None) -> List[ConsoleMessage]:
        """Get console messages with optional level filter."""
        if level_filter:
            return [msg for msg in self.console_messages if msg.level == level_filter]
        return self.console_messages.copy()
    
    def get_network_requests(self, filters: Dict[str, Any] = None) -> List[NetworkRequest]:
        """Get network requests with optional filters."""
        return self.network_monitor.get_requests(filters)
    
    def get_performance_metrics(self) -> List[PerformanceMetric]:
        """Get performance metrics."""
        return self.performance_profiler.get_metrics()
    
    def get_performance_profiles(self) -> List[Dict[str, Any]]:
        """Get performance profiles."""
        return self.performance_profiler.get_profiles()
    
    def clear_console(self):
        """Clear console messages."""
        self.console_messages.clear()
    
    def clear_network(self):
        """Clear network requests."""
        self.network_monitor.clear_requests()
    
    def clear_performance(self):
        """Clear performance data."""
        self.performance_profiler.clear_metrics()
        self.performance_profiler.clear_profiles()
    
    def clear_all(self):
        """Clear all dev tools data."""
        self.clear_console()
        self.clear_network()
        self.clear_performance()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dev tools statistics."""
        return {
            'console': {
                'total_messages': len(self.console_messages),
                'errors': len([m for m in self.console_messages if m.level == LogLevel.ERROR]),
                'warnings': len([m for m in self.console_messages if m.level == LogLevel.WARN])
            },
            'network': self.network_monitor.get_statistics(),
            'performance': {
                'total_metrics': len(self.performance_profiler.get_metrics()),
                'total_profiles': len(self.performance_profiler.get_profiles()),
                'is_profiling': self.performance_profiler.is_profiling
            }
        }
    
    def export_data(self, file_path: str, data_types: List[str] = None):
        """Export dev tools data."""
        if data_types is None:
            data_types = ['console', 'network', 'performance']
        
        export_data = {}
        
        if 'console' in data_types:
            export_data['console'] = [msg.to_dict() for msg in self.console_messages]
        
        if 'network' in data_types:
            export_data['network'] = [req.to_dict() for req in self.network_monitor.requests]
        
        if 'performance' in data_types:
            export_data['performance'] = {
                'metrics': [asdict(metric) for metric in self.performance_profiler.get_metrics()],
                'profiles': self.performance_profiler.get_profiles()
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def import_data(self, file_path: str):
        """Import dev tools data."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Import console messages
        if 'console' in data:
            for msg_data in data['console']:
                msg = ConsoleMessage(
                    id=msg_data['id'],
                    level=LogLevel(msg_data['level']),
                    message=msg_data['message'],
                    source=msg_data.get('source', ''),
                    line=msg_data.get('line', 0),
                    column=msg_data.get('column', 0),
                    timestamp=datetime.fromisoformat(msg_data['timestamp']),
                    stack_trace=msg_data.get('stack_trace', ''),
                    arguments=msg_data.get('arguments', []),
                    url=msg_data.get('url', '')
                )
                self.console_messages.append(msg)
        
        # Import network requests
        if 'network' in data:
            for req_data in data['network']:
                req = NetworkRequest(
                    id=req_data['id'],
                    url=req_data['url'],
                    method=req_data['method'],
                    status=req_data['status'],
                    status_text=req_data['status_text'],
                    request_type=NetworkRequestType(req_data['request_type']),
                    started_time=datetime.fromisoformat(req_data['started_time']),
                    duration=req_data['duration'],
                    size=req_data['size'],
                    response_size=req_data['response_size'],
                    request_headers=req_data.get('request_headers', {}),
                    response_headers=req_data.get('response_headers', {}),
                    request_body=req_data.get('request_body', ''),
                    response_body=req_data.get('response_body', ''),
                    initiator=req_data.get('initiator', ''),
                    priority=req_data.get('priority', ''),
                    cached=req_data.get('cached', False),
                    from_service_worker=req_data.get('from_service_worker', False),
                    error=req_data.get('error', '')
                )
                self.network_monitor.requests.append(req)
        
        # Import performance data
        if 'performance' in data:
            perf_data = data['performance']
            
            # Import metrics
            for metric_data in perf_data.get('metrics', []):
                metric = PerformanceMetric(
                    name=metric_data['name'],
                    value=metric_data['value'],
                    unit=metric_data.get('unit', ''),
                    timestamp=datetime.fromisoformat(metric_data['timestamp'])
                )
                self.performance_profiler.metrics.append(metric)
            
            # Import profiles
            self.performance_profiler.profiles.extend(perf_data.get('profiles', []))


def show_dev_tools(parent=None):
    """Show developer tools window."""
    from .dev_tools_ui import DevToolsWindow
    window = DevToolsWindow(parent)
    window.show()
    return window
