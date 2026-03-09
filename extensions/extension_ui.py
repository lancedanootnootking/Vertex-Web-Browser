#!/usr/bin/env python3.12
"""
Extension System UI Components

Comprehensive UI for managing extensions, permissions, and developer tools.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem, 
                             QTabWidget, QTextEdit, QFrame, QGroupBox, QCheckBox, 
                             QComboBox, QSpinBox, QProgressBar, QMessageBox, 
                             QDialogButtonBox, QFormLayout, QScrollArea, QSplitter,
                             QMenu, QToolBar, QToolButton, QFileDialog, QStatusBar,
                             QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette

from frontend.themes.modern_theme import theme, style_manager, ui_components
from .advanced_extension_system import Extension, ExtensionManager, ExtensionPermission


class ExtensionItemWidget(QWidget):
    """Widget for displaying extension information."""
    
    def __init__(self, extension: Extension, parent=None):
        super().__init__(parent)
        self.extension = extension
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setProperty("class", "extension_icon")
        
        # Load extension icon
        icon_path = self.extension.path / "icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            icon_label.setText("Extension")
            icon_label.setStyleSheet("font-size: 32px;")
        
        layout.addWidget(icon_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Name and version
        name_label = QLabel(f"<b>{self.extension.manifest.name}</b> v{self.extension.manifest.version}")
        name_label.setProperty("class", "extension_name")
        info_layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(self.extension.manifest.description)
        desc_label.setWordWrap(True)
        desc_label.setProperty("class", "extension_description")
        info_layout.addWidget(desc_label)
        
        # Status
        status_text = "Enabled" if self.extension.enabled else "Disabled"
        if self.extension.error_message:
            status_text += f" (Error: {self.extension.error_message})"
        
        status_label = QLabel(status_text)
        status_label.setProperty("class", "extension_status")
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout)
        
        # Controls
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(5)
        
        # Enable/Disable toggle
        self.toggle_btn = QPushButton("Disable" if self.extension.enabled else "Enable")
        self.toggle_btn.clicked.connect(self.toggle_extension)
        controls_layout.addWidget(self.toggle_btn)
        
        # Options button
        if self.extension.options_page:
            options_btn = QPushButton("Options")
            options_btn.clicked.connect(self.open_options)
            controls_layout.addWidget(options_btn)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setProperty("class", "danger")
        remove_btn.clicked.connect(self.remove_extension)
        controls_layout.addWidget(remove_btn)
        
        layout.addLayout(controls_layout)
        
        # Apply styling
        self.setProperty("class", "extension_item")
        style_manager.apply_stylesheet(self, "card")
    
    def toggle_extension(self):
        """Toggle extension enabled state."""
        manager = ExtensionManager.instance()
        if self.extension.enabled:
            manager.disable_extension(self.extension.id)
            self.toggle_btn.setText("Enable")
        else:
            manager.enable_extension(self.extension.id)
            self.toggle_btn.setText("Disable")
    
    def open_options(self):
        """Open extension options."""
        manager = ExtensionManager.instance()
        if self.extension.options_page:
            options_url = f"extension://{self.extension.id}/{self.extension.options_page}"
            if manager.browser:
                manager.browser.create_new_tab(options_url)
    
    def remove_extension(self):
        """Remove extension."""
        reply = QMessageBox.question(
            self, "Remove Extension",
            f"Are you sure you want to remove '{self.extension.manifest.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            manager = ExtensionManager.instance()
            manager.uninstall_extension(self.extension.id)
            self.parent().refresh_extensions()


class ExtensionPermissionsDialog(QDialog):
    """Dialog for managing extension permissions."""
    
    def __init__(self, extension: Extension, parent=None):
        super().__init__(parent)
        self.extension = extension
        self.setWindowTitle("Extension Permissions")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Extension info
        info_group = QGroupBox("Extension")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Name:", QLabel(self.extension.manifest.name))
        info_layout.addRow("Version:", QLabel(self.extension.manifest.version))
        info_layout.addRow("Description:", QLabel(self.extension.manifest.description))
        
        layout.addWidget(info_group)
        
        # Permissions
        permissions_group = QGroupBox("Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        
        # Required permissions
        required_label = QLabel("Required Permissions:")
        required_label.setProperty("class", "section_header")
        permissions_layout.addWidget(required_label)
        
        required_list = QListWidget()
        for permission in self.extension.manifest.permissions or []:
            item = QListWidgetItem(self._get_permission_display(permission))
            item.setData(Qt.ItemDataRole.UserRole, permission)
            required_list.addItem(item)
        permissions_layout.addWidget(required_list)
        
        # Optional permissions
        if self.extension.manifest.optional_permissions:
            optional_label = QLabel("Optional Permissions:")
            optional_label.setProperty("class", "section_header")
            permissions_layout.addWidget(optional_label)
            
            optional_list = QListWidget()
            for permission in self.extension.manifest.optional_permissions:
                item = QListWidgetItem(self._get_permission_display(permission))
                item.setData(Qt.ItemDataRole.UserRole, permission)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                optional_list.addItem(item)
            permissions_layout.addWidget(optional_list)
        
        layout.addWidget(permissions_group)
        
        # Host permissions
        if self.extension.manifest.host_permissions:
            host_group = QGroupBox("Site Access")
            host_layout = QVBoxLayout(host_group)
            
            host_list = QListWidget()
            for host in self.extension.manifest.host_permissions:
                item = QListWidgetItem(host)
                host_list.addItem(item)
            host_layout.addWidget(host_list)
            
            layout.addWidget(host_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def _get_permission_display(self, permission: str) -> str:
        """Get display text for permission."""
        permission_map = {
            "storage": "Read and change data on your computer",
            "tabs": "Read and change your tabs and browsing activity",
            "bookmarks": "Read and change your bookmarks",
            "history": "Read and change your browsing history",
            "downloads": "Read and change your download history",
            "cookies": "Read and change cookies",
            "webNavigation": "Get information about your navigation",
            "webRequest": "Read and change network requests",
            "scripting": "Execute scripts on web pages",
            "notifications": "Display notifications",
            "geolocation": "Know your location",
            "camera": "Use your camera",
            "microphone": "Use your microphone",
            "clipboardRead": "Read data you copy and paste",
            "clipboardWrite": "Write data you copy and paste",
            "activeTab": "Access the active tab",
            "<all_urls>": "Access all websites",
            "management": "Manage your extensions"
        }
        
        return permission_map.get(permission, permission)


class ExtensionDeveloperDialog(QDialog):
    """Dialog for extension development tools."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extension Developer Tools")
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Load unpacked tab
        load_tab = QWidget()
        load_layout = QVBoxLayout(load_tab)
        
        load_label = QLabel("Load Unpacked Extension:")
        load_layout.addWidget(load_label)
        
        load_btn = QPushButton("Select Extension Directory")
        load_btn.clicked.connect(self.load_unpacked)
        load_layout.addWidget(load_btn)
        
        load_layout.addStretch()
        tab_widget.addTab(load_tab, "Load Unpacked")
        
        # Console tab
        console_tab = QWidget()
        console_layout = QVBoxLayout(console_tab)
        
        console_label = QLabel("Extension Console:")
        console_layout.addWidget(console_label)
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setProperty("class", "console")
        console_layout.addWidget(self.console_output)
        
        console_input_layout = QHBoxLayout()
        self.console_input = QLineEdit()
        self.console_input.setPlaceholderText("Enter JavaScript code...")
        self.console_input.returnPressed.connect(self.execute_console)
        
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_console)
        
        console_input_layout.addWidget(self.console_input)
        console_input_layout.addWidget(execute_btn)
        console_layout.addLayout(console_input_layout)
        
        tab_widget.addTab(console_tab, "Console")
        
        # Inspector tab
        inspector_tab = QWidget()
        inspector_layout = QVBoxLayout(inspector_tab)
        
        inspector_label = QLabel("Extension Inspector:")
        inspector_layout.addWidget(inspector_label)
        
        self.inspector_tree = QTreeWidget()
        self.inspector_tree.setHeaderLabels(["Property", "Value"])
        inspector_layout.addWidget(self.inspector_tree)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_inspector)
        inspector_layout.addWidget(refresh_btn)
        
        tab_widget.addTab(inspector_tab, "Inspector")
        
        layout.addWidget(tab_widget)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def load_unpacked(self):
        """Load unpacked extension."""
        directory = QFileDialog.getExistingDirectory(self, "Select Extension Directory")
        if directory:
            try:
                manager = ExtensionManager.instance()
                extension_id = manager.install_extension(directory)
                self.console_output.append(f"Extension loaded: {extension_id}")
                QMessageBox.information(self, "Success", "Extension loaded successfully!")
            except Exception as e:
                self.console_output.append(f"Error loading extension: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load extension: {e}")
    
    def execute_console(self):
        """Execute console command."""
        code = self.console_input.text()
        if code:
            self.console_output.append(f"> {code}")
            try:
                # Execute in context of first enabled extension
                manager = ExtensionManager.instance()
                extensions = manager.get_all_extensions()
                for ext in extensions:
                    if ext.enabled and ext.sandbox:
                        ext.sandbox.execute_script(code, "console")
                        break
            except Exception as e:
                self.console_output.append(f"Error: {e}")
            self.console_input.clear()
    
    def refresh_inspector(self):
        """Refresh inspector tree."""
        self.inspector_tree.clear()
        
        manager = ExtensionManager.instance()
        extensions = manager.get_all_extensions()
        
        for extension in extensions:
            ext_item = QTreeWidgetItem(self.inspector_tree)
            ext_item.setText(0, extension.manifest.name)
            ext_item.setText(1, extension.id)
            
            # Add properties
            props = [
                ("Enabled", str(extension.enabled)),
                ("Loaded", str(extension.loaded)),
                ("Version", extension.manifest.version),
                ("Path", str(extension.path))
            ]
            
            for prop_name, prop_value in props:
                prop_item = QTreeWidgetItem(ext_item)
                prop_item.setText(0, prop_name)
                prop_item.setText(1, prop_value)
            
            # Add permissions
            if extension.manifest.permissions:
                perms_item = QTreeWidgetItem(ext_item)
                perms_item.setText(0, "Permissions")
                
                for permission in extension.manifest.permissions:
                    perm_item = QTreeWidgetItem(perms_item)
                    perm_item.setText(0, permission)
                    perm_item.setText(1, "")
        
        self.inspector_tree.expandAll()


class ExtensionManagerDialog(QDialog):
    """Main extension manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extensions")
        self.resize(900, 700)
        self.setup_ui()
        self.refresh_extensions()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Install button
        install_btn = QPushButton("Install Extension")
        install_btn.clicked.connect(self.install_extension)
        toolbar_layout.addWidget(install_btn)
        
        # Developer tools button
        dev_btn = QPushButton("Developer Tools")
        dev_btn.clicked.connect(self.open_developer_tools)
        toolbar_layout.addWidget(dev_btn)
        
        # Search
        toolbar_layout.addStretch()
        
        search_label = QLabel("Search:")
        toolbar_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search extensions...")
        self.search_edit.textChanged.connect(self.filter_extensions)
        toolbar_layout.addWidget(self.search_edit)
        
        layout.addWidget(toolbar)
        
        # Main content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Extensions list
        self.extensions_list = QListWidget()
        self.extensions_list.itemClicked.connect(self.select_extension)
        content_splitter.addWidget(self.extensions_list)
        
        # Extension details
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        
        # Extension info
        self.extension_info = QLabel("Select an extension to view details")
        self.extension_info.setWordWrap(True)
        self.details_layout.addWidget(self.extension_info)
        
        # Permissions button
        self.permissions_btn = QPushButton("View Permissions")
        self.permissions_btn.clicked.connect(self.show_permissions)
        self.permissions_btn.setEnabled(False)
        self.details_layout.addWidget(self.permissions_btn)
        
        # Options button
        self.options_btn = QPushButton("Options")
        self.options_btn.clicked.connect(self.open_options)
        self.options_btn.setEnabled(False)
        self.details_layout.addWidget(self.options_btn)
        
        self.details_layout.addStretch()
        content_splitter.addWidget(self.details_widget)
        
        content_splitter.setSizes([300, 600])
        layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def refresh_extensions(self):
        """Refresh extensions list."""
        self.extensions_list.clear()
        
        manager = ExtensionManager.instance()
        extensions = manager.get_all_extensions()
        
        for extension in extensions:
            item = QListWidgetItem(extension.manifest.name)
            item.setData(Qt.ItemDataRole.UserRole, extension)
            
            # Set icon
            icon_path = extension.path / "icon.png"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                item.setIcon(icon)
            
            # Set color based on status
            if extension.enabled:
                item.setForeground(QPalette().color(QPalette.ColorRole.Text))
            else:
                item.setForeground(QPalette().color(QPalette.ColorRole.Disabled))
            
            self.extensions_list.addItem(item)
        
        self.status_bar.showMessage(f"{len(extensions)} extensions loaded")
    
    def select_extension(self, item):
        """Handle extension selection."""
        extension = item.data(Qt.ItemDataRole.UserRole)
        if extension:
            self.update_extension_details(extension)
    
    def update_extension_details(self, extension: Extension):
        """Update extension details display."""
        details_text = f"""
        <h3>{extension.manifest.name}</h3>
        <p><b>Version:</b> {extension.manifest.version}</p>
        <p><b>Description:</b> {extension.manifest.description}</p>
        <p><b>Author:</b> {extension.manifest.author or 'Unknown'}</p>
        <p><b>Status:</b> {'Enabled' if extension.enabled else 'Disabled'}</p>
        <p><b>Installed:</b> {extension.install_time.strftime('%Y-%m-%d %H:%M')}</p>
        """
        
        if extension.error_message:
            details_text += f"<p><b>Error:</b> {extension.error_message}</p>"
        
        self.extension_info.setText(details_text)
        
        # Enable/disable buttons
        self.permissions_btn.setEnabled(True)
        self.options_btn.setEnabled(bool(extension.options_page))
        
        self.current_extension = extension
    
    def filter_extensions(self, text):
        """Filter extensions list."""
        for i in range(self.extensions_list.count()):
            item = self.extensions_list.item(i)
            extension = item.data(Qt.ItemDataRole.UserRole)
            if extension:
                matches = (text.lower() in extension.manifest.name.lower() or
                          text.lower() in extension.manifest.description.lower())
                item.setHidden(not matches)
    
    def install_extension(self):
        """Install new extension."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Extension Package", "", 
            "Extension Files (*.zip *.crx);;All Files (*)"
        )
        
        if file_path:
            try:
                manager = ExtensionManager.instance()
                extension_id = manager.install_extension(file_path)
                QMessageBox.information(self, "Success", "Extension installed successfully!")
                self.refresh_extensions()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to install extension: {e}")
    
    def show_permissions(self):
        """Show extension permissions dialog."""
        if hasattr(self, 'current_extension'):
            dialog = ExtensionPermissionsDialog(self.current_extension, self)
            dialog.exec()
    
    def open_options(self):
        """Open extension options."""
        if hasattr(self, 'current_extension') and self.current_extension.options_page:
            manager = ExtensionManager.instance()
            options_url = f"extension://{self.current_extension.id}/{self.current_extension.options_page}"
            if manager.browser:
                manager.browser.create_new_tab(options_url)
    
    def open_developer_tools(self):
        """Open developer tools dialog."""
        dialog = ExtensionDeveloperDialog(self)
        dialog.exec()


class ExtensionToolbarWidget(QWidget):
    """Widget for extension toolbar buttons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.extension_buttons = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(2)
        
        # Add extension action buttons
        self.refresh_toolbar()
        
        # Apply styling
        self.setProperty("class", "extension_toolbar")
        style_manager.apply_stylesheet(self, "toolbar")
    
    def refresh_toolbar(self):
        """Refresh toolbar buttons."""
        # Clear existing buttons
        for button in self.extension_buttons.values():
            button.deleteLater()
        self.extension_buttons.clear()
        
        manager = ExtensionManager.instance()
        extensions = manager.get_all_extensions()
        
        for extension in extensions:
            if extension.enabled and extension.manifest.action:
                self.add_extension_button(extension)
    
    def add_extension_button(self, extension: Extension):
        """Add extension button to toolbar."""
        action = extension.manifest.action
        
        if 'default_title' in action:
            tooltip = action['default_title']
        else:
            tooltip = extension.manifest.name
        
        button = QToolButton()
        button.setToolTip(tooltip)
        button.setProperty("class", "extension_action")
        
        # Set icon
        if 'default_icon' in action:
            icon_path = extension.path / action['default_icon']
            if icon_path.exists():
                button.setIcon(QIcon(str(icon_path)))
        else:
            button.setText(extension.manifest.name[:1].upper())
        
        # Connect click handler
        button.clicked.connect(lambda: self.on_extension_action(extension))
        
        self.layout().addWidget(button)
        self.extension_buttons[extension.id] = button
    
    def on_extension_action(self, extension: Extension):
        """Handle extension action button click."""
        # Execute extension action
        if extension.sandbox:
            action_script = """
            if (chrome.action && chrome.action.onClicked) {
                chrome.action.onClicked.dispatch();
            }
            """
            extension.sandbox.execute_script(action_script)


class ExtensionContextMenu(QMenu):
    """Context menu for extension management."""
    
    def __init__(self, extension: Extension, parent=None):
        super().__init__(parent)
        self.extension = extension
        self.setup_menu()
    
    def setup_menu(self):
        # Enable/Disable
        if self.extension.enabled:
            disable_action = self.addAction("Disable")
            disable_action.triggered.connect(self.disable_extension)
        else:
            enable_action = self.addAction("Enable")
            enable_action.triggered.connect(self.enable_extension)
        
        self.addSeparator()
        
        # Options
        if self.extension.options_page:
            options_action = self.addAction("Options")
            options_action.triggered.connect(self.open_options)
        
        # Permissions
        permissions_action = self.addAction("Permissions")
        permissions_action.triggered.connect(self.show_permissions)
        
        self.addSeparator()
        
        # Reload
        reload_action = self.addAction("Reload")
        reload_action.triggered.connect(self.reload_extension)
        
        # Remove
        remove_action = self.addAction("Remove")
        remove_action.triggered.connect(self.remove_extension)
    
    def enable_extension(self):
        """Enable extension."""
        manager = ExtensionManager.instance()
        manager.enable_extension(self.extension.id)
    
    def disable_extension(self):
        """Disable extension."""
        manager = ExtensionManager.instance()
        manager.disable_extension(self.extension.id)
    
    def open_options(self):
        """Open extension options."""
        manager = ExtensionManager.instance()
        options_url = f"extension://{self.extension.id}/{self.extension.options_page}"
        if manager.browser:
            manager.browser.create_new_tab(options_url)
    
    def show_permissions(self):
        """Show permissions dialog."""
        dialog = ExtensionPermissionsDialog(self.extension, self.parent())
        dialog.exec()
    
    def reload_extension(self):
        """Reload extension."""
        manager = ExtensionManager.instance()
        manager.reload_extension(self.extension.id)
    
    def remove_extension(self):
        """Remove extension."""
        reply = QMessageBox.question(
            self, "Remove Extension",
            f"Are you sure you want to remove '{self.extension.manifest.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            manager = ExtensionManager.instance()
            manager.uninstall_extension(self.extension.id)
