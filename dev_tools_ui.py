#!/usr/bin/env python3.12
"""
Developer Tools UI Components

Comprehensive UI for web development tools including console,
inspector, network monitor, and performance profiler.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem, 
                             QTabWidget, QTextEdit, QFrame, QGroupBox, QCheckBox, 
                             QComboBox, QSpinBox, QProgressBar, QMessageBox, 
                             QDialogButtonBox, QFormLayout, QScrollArea, QSplitter,
                             QMenu, QToolBar, QToolButton, QFileDialog, QStatusBar,
                             QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QSlider, QDoubleSpinBox,
                             QDateTimeEdit, QSpinBox, QPlainTextEdit, QCheckBox, QRadioButton,
                             QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QSortFilterProxyModel, QDateTime, QMimeData, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QPainter, QColor, QTextCursor, QTextDocument, QTextFormat, QTextCharFormat, QSyntaxHighlighter, QBrush, QPen

from frontend.themes.modern_theme import theme, style_manager, ui_components
from dev_tools.advanced_dev_tools import (DevToolsManager, ConsoleMessage, NetworkRequest, 
                                         LogLevel, NetworkRequestType, DevToolType)


class ConsoleSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for console output."""
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        
        # Define formats
        self.log_format = QTextCharFormat()
        self.log_format.setForeground(QColor("#333333"))
        
        self.info_format = QTextCharFormat()
        self.info_format.setForeground(QColor("#0066cc"))
        
        self.warn_format = QTextCharFormat()
        self.warn_format.setForeground(QColor("#ff8800"))
        
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#cc0000"))
        
        self.debug_format = QTextCharFormat()
        self.debug_format.setForeground(QColor("#888888"))
        
        self.url_format = QTextCharFormat()
        self.url_format.setForeground(QColor("#0066cc"))
        self.url_format.setFontUnderline(True)
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#009900"))
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#009900"))
    
    def highlightBlock(self, text: str):
        """Highlight text block."""
        # Check for log level prefixes
        if text.startswith("[LOG]"):
            self.setFormat(0, 5, self.log_format)
        elif text.startswith("[INFO]"):
            self.setFormat(0, 6, self.info_format)
        elif text.startswith("[WARN]"):
            self.setFormat(0, 5, self.warn_format)
        elif text.startswith("[ERROR]"):
            self.setFormat(0, 7, self.error_format)
        elif text.startswith("[DEBUG]"):
            self.setFormat(0, 7, self.debug_format)
        
        # Highlight URLs
        url_pattern = re.compile(r'https?://[^\s]+')
        for match in url_pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.url_format)
        
        # Highlight numbers
        number_pattern = re.compile(r'\b\d+\.?\d*\b')
        for match in number_pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)


class ConsoleWidget(QWidget):
    """Console widget for JavaScript execution and logging."""
    
    def __init__(self, dev_tools_manager: DevToolsManager, parent=None):
        super().__init__(parent)
        self.dev_tools_manager = dev_tools_manager
        self.setup_ui()
        self.connect_signals()
        self.load_console_history()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_console)
        toolbar_layout.addWidget(clear_btn)
        
        # Level filter
        toolbar_layout.addWidget(QLabel("Filter:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "Errors", "Warnings", "Info", "Debug", "Log"])
        self.level_combo.currentTextChanged.connect(self.filter_messages)
        toolbar_layout.addWidget(self.level_combo)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # Console output
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setProperty("class", "console_output")
        
        # Setup syntax highlighting
        self.highlighter = ConsoleSyntaxHighlighter(self.console_output.document())
        
        layout.addWidget(self.console_output)
        
        # Input area
        input_group = QGroupBox("Console Input")
        input_layout = QVBoxLayout(input_group)
        
        # Input line
        input_line_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Enter JavaScript expression...")
        self.input_edit.returnPressed.connect(self.execute_javascript)
        input_line_layout.addWidget(self.input_edit)
        
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_javascript)
        input_line_layout.addWidget(execute_btn)
        
        input_layout.addLayout(input_line_layout)
        
        # Multi-line input
        self.multi_line_input = QPlainTextEdit()
        self.multi_line_input.setPlaceholderText("Multi-line JavaScript code...")
        self.multi_line_input.setMaximumHeight(100)
        self.multi_line_input.setVisible(False)
        input_layout.addWidget(self.multi_line_input)
        
        # Multi-line toggle
        multi_line_btn = QPushButton("Multi-line")
        multi_line_btn.setCheckable(True)
        multi_line_btn.toggled.connect(self.toggle_multi_line)
        input_layout.addWidget(multi_line_btn)
        
        layout.addWidget(input_group)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def connect_signals(self):
        """Connect dev tools manager signals."""
        # Would connect to actual signals in real implementation
        pass
    
    def load_console_history(self):
        """Load console messages."""
        messages = self.dev_tools_manager.get_console_messages()
        for message in messages:
            self.add_console_message(message)
    
    def add_console_message(self, message: ConsoleMessage):
        """Add console message to output."""
        timestamp = message.timestamp.strftime('%H:%M:%S.%f')[:-3]
        level_prefix = f"[{message.level.value.upper()}]"
        
        # Format message
        formatted_message = f"{timestamp} {level_prefix} {message.message}"
        
        # Add to console
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Apply formatting based on level
        format_map = {
            LogLevel.LOG: "log",
            LogLevel.INFO: "info", 
            LogLevel.WARN: "warn",
            LogLevel.ERROR: "error",
            LogLevel.DEBUG: "debug"
        }
        
        cursor.insertText(formatted_message + "\n")
        
        # Auto-scroll to bottom
        self.console_output.ensureCursorVisible()
        
        # Limit output size
        document = self.console_output.document()
        if document.blockCount() > 1000:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def execute_javascript(self):
        """Execute JavaScript code."""
        if self.multi_line_input.isVisible():
            code = self.multi_line_input.toPlainText()
        else:
            code = self.input_edit.text()
        
        if not code.strip():
            return
        
        # Add to console as input
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"> {code}\n")
        
        # Execute code
        try:
            result = self.dev_tools_manager.execute_javascript(code)
            
            # Display result
            if result is not None:
                cursor.insertText(f"< {self._format_result(result)}\n")
            else:
                cursor.insertText("< undefined\n")
                
        except Exception as e:
            cursor.insertText(f"< Error: {str(e)}\n")
        
        # Clear input
        if self.multi_line_input.isVisible():
            self.multi_line_input.clear()
        else:
            self.input_edit.clear()
        
        # Auto-scroll
        self.console_output.ensureCursorVisible()
    
    def _format_result(self, result: Any) -> str:
        """Format result for display."""
        if isinstance(result, str):
            return f'"{result}"'
        elif isinstance(result, (list, tuple)):
            return str(result)
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return str(result)
    
    def clear_console(self):
        """Clear console output."""
        self.console_output.clear()
    
    def filter_messages(self, level_text: str):
        """Filter console messages by level."""
        # Would implement filtering logic
        pass
    
    def toggle_multi_line(self, checked: bool):
        """Toggle multi-line input."""
        self.multi_line_input.setVisible(checked)
        self.input_edit.setVisible(not checked)


class NetworkWidget(QWidget):
    """Network monitoring widget."""
    
    def __init__(self, dev_tools_manager: DevToolsManager, parent=None):
        super().__init__(parent)
        self.dev_tools_manager = dev_tools_manager
        self.setup_ui()
        self.connect_signals()
        self.load_network_requests()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_network)
        toolbar_layout.addWidget(clear_btn)
        
        # Type filter
        toolbar_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "XHR", "Script", "Stylesheet", "Image", "Media", "Font", "Document", "WebSocket"])
        self.type_filter.currentTextChanged.connect(self.filter_requests)
        toolbar_layout.addWidget(self.type_filter)
        
        # Status filter
        toolbar_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Success", "Error", "Pending"])
        self.status_filter.currentTextChanged.connect(self.filter_requests)
        toolbar_layout.addWidget(self.status_filter)
        
        # Search
        toolbar_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search URLs...")
        self.search_edit.textChanged.connect(self.filter_requests)
        toolbar_layout.addWidget(self.search_edit)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # Network table
        self.network_table = QTableWidget()
        self.network_table.setColumnCount(7)
        self.network_table.setHorizontalHeaderLabels([
            "Name", "Method", "Status", "Type", "Size", "Time", "Waterfall"
        ])
        self.network_table.horizontalHeader().setStretchLastSection(True)
        self.network_table.setAlternatingRowColors(True)
        self.network_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.network_table.setSortingEnabled(True)
        
        layout.addWidget(self.network_table)
        
        # Details panel
        self.details_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Request details
        self.request_details = QTextEdit()
        self.request_details.setReadOnly(True)
        self.request_details.setMaximumHeight(150)
        self.details_splitter.addWidget(self.request_details)
        
        # Response details
        self.response_details = QTextEdit()
        self.response_details.setReadOnly(True)
        self.response_details.setMaximumHeight(150)
        self.details_splitter.addWidget(self.response_details)
        
        self.details_splitter.setSizes([150, 150])
        self.details_splitter.setVisible(False)
        
        layout.addWidget(self.details_splitter)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def connect_signals(self):
        """Connect signals."""
        self.network_table.itemSelectionChanged.connect(self.show_request_details)
    
    def load_network_requests(self):
        """Load network requests."""
        requests = self.dev_tools_manager.get_network_requests()
        self.populate_table(requests)
    
    def populate_table(self, requests: List[NetworkRequest]):
        """Populate network table with requests."""
        self.network_table.setRowCount(0)
        
        for request in requests:
            row = self.network_table.rowCount()
            self.network_table.insertRow(row)
            
            # Name (URL or filename)
            name = Path(request.url).name or request.url
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(request.url)
            self.network_table.setItem(row, 0, name_item)
            
            # Method
            method_item = QTableWidgetItem(request.method)
            self.network_table.setItem(row, 1, method_item)
            
            # Status
            status_item = QTableWidgetItem(str(request.status))
            if request.status >= 200 and request.status < 300:
                status_item.setForeground(QColor("#009900"))
            elif request.status >= 400:
                status_item.setForeground(QColor("#cc0000"))
            self.network_table.setItem(row, 2, status_item)
            
            # Type
            type_item = QTableWidgetItem(request.request_type.value)
            self.network_table.setItem(row, 3, type_item)
            
            # Size
            size_text = self._format_bytes(request.response_size)
            size_item = QTableWidgetItem(size_text)
            self.network_table.setItem(row, 4, size_item)
            
            # Time
            time_text = f"{request.duration:.2f}s"
            time_item = QTableWidgetItem(time_text)
            self.network_table.setItem(row, 5, time_item)
            
            # Waterfall (simplified - would show timeline)
            waterfall_item = QTableWidgetItem("●")
            waterfall_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.network_table.setItem(row, 6, waterfall_item)
            
            # Store request data
            for col in range(7):
                item = self.network_table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, request)
        
        # Resize columns
        self.network_table.resizeColumnsToContents()
    
    def show_request_details(self):
        """Show selected request details."""
        items = self.network_table.selectedItems()
        if not items:
            self.details_splitter.setVisible(False)
            return
        
        request = items[0].data(Qt.ItemDataRole.UserRole)
        if request:
            self.details_splitter.setVisible(True)
            
            # Request details
            request_text = f"""Request Details:
URL: {request.url}
Method: {request.method}
Status: {request.status} {request.status_text}
Type: {request.request_type.value}
Duration: {request.duration:.3f}s
Size: {self._format_bytes(request.size)}
Response Size: {self._format_bytes(request.response_size)}

Request Headers:
{self._format_headers(request.request_headers)}

Request Body:
{request.request_body or '(empty)'}
"""
            self.request_details.setPlainText(request_text)
            
            # Response details
            response_text = f"""Response Details:
Status: {request.status} {request.status_text}
Cached: {request.cached}
From Service Worker: {request.from_service_worker}

Response Headers:
{self._format_headers(request.response_headers)}

Response Body:
{request.response_body[:1000] + '...' if len(request.response_body) > 1000 else request.response_body}
"""
            self.response_details.setPlainText(response_text)
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes as human readable."""
        if bytes_count == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB"]
        unit_index = 0
        
        while bytes_count >= 1024 and unit_index < len(units) - 1:
            bytes_count /= 1024
            unit_index += 1
        
        return f"{bytes_count:.1f} {units[unit_index]}"
    
    def _format_headers(self, headers: Dict[str, str]) -> str:
        """Format headers for display."""
        if not headers:
            return "(empty)"
        
        lines = []
        for key, value in headers.items():
            lines.append(f"{key}: {value}")
        
        return "\n".join(lines)
    
    def filter_requests(self):
        """Filter network requests."""
        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        search_text = self.search_edit.text().lower()
        
        filters = {}
        
        if type_filter != "All":
            filters['types'] = {NetworkRequestType(type_filter.lower())}
        
        if status_filter != "All":
            if status_filter == "Success":
                filters['status_codes'] = set(range(200, 300))
            elif status_filter == "Error":
                filters['status_codes'] = set(range(400, 600))
        
        if search_text:
            filters['search_text'] = search_text
        
        requests = self.dev_tools_manager.get_network_requests(filters)
        self.populate_table(requests)
    
    def clear_network(self):
        """Clear network requests."""
        self.dev_tools_manager.clear_network()
        self.network_table.setRowCount(0)
        self.details_splitter.setVisible(False)


class ElementsWidget(QWidget):
    """DOM elements inspection widget."""
    
    def __init__(self, dev_tools_manager: DevToolsManager, parent=None):
        super().__init__(parent)
        self.dev_tools_manager = dev_tools_manager
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Select element button
        select_btn = QPushButton("Select Element")
        select_btn.clicked.connect(self.select_element)
        toolbar_layout.addWidget(select_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_elements)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # Main content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # DOM tree
        self.dom_tree = QTreeWidget()
        self.dom_tree.setHeaderLabels(["Element", "ID", "Class"])
        self.dom_tree.setAlternatingRowColors(True)
        self.dom_tree.itemSelectionChanged.connect(self.show_element_details)
        content_splitter.addWidget(self.dom_tree)
        
        # Element details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Element info
        info_group = QGroupBox("Element Information")
        info_layout = QFormLayout(info_group)
        
        self.element_tag = QLabel()
        info_layout.addRow("Tag:", self.element_tag)
        
        self.element_id = QLabel()
        info_layout.addRow("ID:", self.element_id)
        
        self.element_class = QLabel()
        info_layout.addRow("Class:", self.element_class)
        
        self.element_path = QLabel()
        self.element_path.setWordWrap(True)
        info_layout.addRow("Path:", self.element_path)
        
        details_layout.addWidget(info_group)
        
        # Attributes
        self.attributes_table = QTableWidget()
        self.attributes_table.setColumnCount(2)
        self.attributes_table.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.attributes_table.horizontalHeader().setStretchLastSection(True)
        self.attributes_table.setMaximumHeight(150)
        details_layout.addWidget(self.attributes_table)
        
        # Styles
        self.styles_table = QTableWidget()
        self.styles_table.setColumnCount(2)
        self.styles_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.styles_table.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.styles_table)
        
        content_splitter.addWidget(details_widget)
        content_splitter.setSizes([300, 400])
        layout.addWidget(content_splitter)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def select_element(self):
        """Select element from page."""
        # Would implement element selection
        pass
    
    def refresh_elements(self):
        """Refresh DOM tree."""
        # Would reload DOM from page
        self.load_dom_tree()
    
    def load_dom_tree(self):
        """Load DOM tree."""
        # Sample DOM structure - would load from actual page
        self.dom_tree.clear()
        
        # Add root element
        root_item = QTreeWidgetItem(self.dom_tree)
        root_item.setText(0, "html")
        root_item.setData(0, Qt.ItemDataRole.UserRole, {'tagName': 'html'})
        
        # Add body
        body_item = QTreeWidgetItem(root_item)
        body_item.setText(0, "body")
        body_item.setData(0, Qt.ItemDataRole.UserRole, {'tagName': 'body'})
        
        # Add sample elements
        div_item = QTreeWidgetItem(body_item)
        div_item.setText(0, "div")
        div_item.setText(1, "main")
        div_item.setText(2, "container")
        div_item.setData(0, Qt.ItemDataRole, {
            'tagName': 'div',
            'id': 'main',
            'className': 'container'
        })
        
        self.dom_tree.expandAll()
    
    def show_element_details(self):
        """Show selected element details."""
        items = self.dom_tree.selectedItems()
        if not items:
            return
        
        element = items[0].data(Qt.ItemDataRole.UserRole)
        if element:
            self.element_tag.setText(element.get('tagName', ''))
            self.element_id.setText(element.get('id', ''))
            self.element_class.setText(element.get('className', ''))
            
            # Build CSS path
            path = self._build_element_path(element)
            self.element_path.setText(path)
            
            # Show attributes
            self.show_attributes(element)
            
            # Show styles
            self.show_styles(element)
    
    def _build_element_path(self, element: Dict[str, Any]) -> str:
        """Build CSS path for element."""
        # Simplified path building
        tag = element.get('tagName', '').lower()
        element_id = element.get('id', '')
        element_class = element.get('className', '')
        
        path_parts = [tag]
        
        if element_id:
            path_parts.append(f"#{element_id}")
        
        if element_class:
            classes = element_class.split()
            path_parts.append(f".{'.'.join(classes)}")
        
        return " ".join(path_parts)
    
    def show_attributes(self, element: Dict[str, Any]):
        """Show element attributes."""
        self.attributes_table.setRowCount(0)
        
        attributes = element.get('attributes', {})
        for key, value in attributes.items():
            row = self.attributes_table.rowCount()
            self.attributes_table.insertRow(row)
            self.attributes_table.setItem(row, 0, QTableWidgetItem(key))
            self.attributes_table.setItem(row, 1, QTableWidgetItem(value))
        
        self.attributes_table.resizeColumnsToContents()
    
    def show_styles(self, element: Dict[str, Any]):
        """Show element styles."""
        self.styles_table.setRowCount(0)
        
        styles = element.get('computed_styles', {})
        for key, value in styles.items():
            row = self.styles_table.rowCount()
            self.styles_table.insertRow(row)
            self.styles_table.setItem(row, 0, QTableWidgetItem(key))
            self.styles_table.setItem(row, 1, QTableWidgetItem(value))
        
        self.styles_table.resizeColumnsToContents()


class PerformanceWidget(QWidget):
    """Performance profiling widget."""
    
    def __init__(self, dev_tools_manager: DevToolsManager, parent=None):
        super().__init__(parent)
        self.dev_tools_manager = dev_tools_manager
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Start/Stop profiling
        self.profile_btn = QPushButton("Start Profiling")
        self.profile_btn.clicked.connect(self.toggle_profiling)
        toolbar_layout.addWidget(self.profile_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_performance)
        toolbar_layout.addWidget(clear_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # Main content
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Metrics table
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(3)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value", "Unit"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setAlternatingRowColors(True)
        metrics_layout.addWidget(self.metrics_table)
        
        content_splitter.addWidget(metrics_group)
        
        # Profiles
        profiles_group = QGroupBox("Performance Profiles")
        profiles_layout = QVBoxLayout(profiles_group)
        
        self.profiles_list = QListWidget()
        self.profiles_list.itemSelectionChanged.connect(self.show_profile_details)
        profiles_layout.addWidget(self.profiles_list)
        
        # Profile details
        self.profile_details = QTextEdit()
        self.profile_details.setReadOnly(True)
        self.profile_details.setMaximumHeight(200)
        profiles_layout.addWidget(self.profile_details)
        
        content_splitter.addWidget(profiles_group)
        
        content_splitter.setSizes([300, 300])
        layout.addWidget(content_splitter)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def connect_signals(self):
        """Connect signals."""
        # Would connect to actual profiler signals
        pass
    
    def toggle_profiling(self):
        """Toggle performance profiling."""
        if self.dev_tools_manager.performance_profiler.is_profiling:
            # Stop profiling
            results = self.dev_tools_manager.stop_performance_profiling()
            self.profile_btn.setText("Start Profiling")
            
            # Add profile to list
            profile_name = f"Profile {datetime.now().strftime('%H:%M:%S')}"
            profile_item = QListWidgetItem(profile_name)
            profile_item.setData(Qt.ItemDataRole.UserRole, results)
            self.profiles_list.addItem(profile_item)
            
        else:
            # Start profiling
            self.dev_tools_manager.start_performance_profiling()
            self.profile_btn.setText("Stop Profiling")
    
    def clear_performance(self):
        """Clear performance data."""
        self.dev_tools_manager.clear_performance()
        self.metrics_table.setRowCount(0)
        self.profiles_list.clear()
        self.profile_details.clear()
    
    def show_profile_details(self):
        """Show selected profile details."""
        items = self.profiles_list.selectedItems()
        if not items:
            return
        
        profile_data = items[0].data(Qt.ItemDataRole.UserRole)
        if profile_data:
            details = f"""Profile Details:
Duration: {profile_data.get('duration', 0):.3f}s

Markers:
"""
            for marker in profile_data.get('markers', []):
                details += f"  {marker['name']}: {marker['timestamp']:.3f}s\n"
            
            details += "\nMeasurements:\n"
            for measurement in profile_data.get('measurements', []):
                details += f"  {measurement['name']}: {measurement['duration']:.3f}s\n"
            
            self.profile_details.setPlainText(details)
    
    def load_metrics(self):
        """Load performance metrics."""
        metrics = self.dev_tools_manager.get_performance_metrics()
        self.metrics_table.setRowCount(0)
        
        for metric in metrics:
            row = self.metrics_table.rowCount()
            self.metrics_table.insertRow(row)
            self.metrics_table.setItem(row, 0, QTableWidgetItem(metric.name))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(str(metric.value)))
            self.metrics_table.setItem(row, 2, QTableWidgetItem(metric.unit))
        
        self.metrics_table.resizeColumnsToContents()


class DevToolsWindow(QDialog):
    """Main developer tools window."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Developer Tools")
        self.resize(1200, 800)
        self.dev_tools_manager = DevToolsManager(self)
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Console tab
        self.console_widget = ConsoleWidget(self.dev_tools_manager)
        self.tab_widget.addTab(self.console_widget, "Console")
        
        # Elements tab
        self.elements_widget = ElementsWidget(self.dev_tools_manager)
        self.tab_widget.addTab(self.elements_widget, "Elements")
        
        # Network tab
        self.network_widget = NetworkWidget(self.dev_tools_manager)
        self.tab_widget.addTab(self.network_widget, "Network")
        
        # Performance tab
        self.performance_widget = PerformanceWidget(self.dev_tools_manager)
        self.tab_widget.addTab(self.performance_widget, "Performance")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def load_initial_data(self):
        """Load initial data."""
        # Load metrics
        self.performance_widget.load_metrics()
        
        # Load elements
        self.elements_widget.load_dom_tree()
        
        # Update status
        stats = self.dev_tools_manager.get_statistics()
        self.status_bar.showMessage(f"Console: {stats['console']['total_messages']} messages | Network: {stats['network']['total_requests']} requests")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save any unsaved data
        event.accept()
