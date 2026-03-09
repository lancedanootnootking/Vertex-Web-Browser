#!/usr/bin/env python3.12
"""
Advanced Settings Panel with Modern UI

Comprehensive settings management system with modern blue/grey theme,
organized categories, search functionality, and beautiful UI.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QMenu, QToolBar, QComboBox, QCheckBox, QGroupBox, 
                             QFormLayout, QDialogButtonBox, QFrame, QMessageBox, 
                             QSpinBox, QSlider, QSplitter, QTextEdit, QTabWidget,
                             QScrollArea, QButtonGroup, QRadioButton, QProgressBar,
                             QColorDialog, QFontDialog, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QSettings, QUrl
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QKeySequence, QColor, QPalette
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os

from frontend.themes.modern_theme import theme, style_manager, ui_components


class SettingsCategory:
    """Represents a settings category."""
    
    def __init__(self, name: str, icon: str, description: str):
        self.name = name
        self.icon = icon
        self.description = description
        self.settings = {}
    
    def add_setting(self, key: str, setting_type: str, default_value: Any, 
                   label: str, description: str, options: List = None):
        """Add a setting to this category."""
        self.settings[key] = {
            'type': setting_type,
            'default': default_value,
            'current': default_value,
            'label': label,
            'description': description,
            'options': options
        }


class SettingsManager:
    """Manages application settings."""
    
    def __init__(self):
        self.settings_file = Path.home() / '.vertex_settings.json'
        self.categories = {}
        self.setup_default_categories()
        self.load_settings()
    
    def setup_default_categories(self):
        """Setup default settings categories."""
        # General category
        general = SettingsCategory("General", "Settings", "General browser settings")
        general.add_setting("homepage", "string", "https://duckduckgo.com", 
                           "Homepage", "Set your default homepage")
        general.add_setting("search_engine", "combo", "duckduckgo", 
                           "Search Engine", "Choose your default search engine",
                           ["duckduckgo", "google", "bing", "yahoo"])
        general.add_setting("startup_action", "combo", "homepage", 
                           "On Startup", "What to do when browser starts",
                           ["homepage", "new_tab", "restore_session"])
        general.add_setting("downloads_location", "path", str(Path.home() / "Downloads"), 
                           "Downloads", "Default download location")
        general.add_setting("auto_clear_history", "bool", False, 
                           "Auto-clear History", "Clear history on exit")
        general.add_setting("check_updates", "bool", True, 
                           "Check for Updates", "Automatically check for updates")
        
        # Appearance category
        appearance = SettingsCategory("Appearance", "Theme", "Appearance and theme settings")
        appearance.add_setting("theme", "combo", "modern_blue", 
                              "Theme", "Choose application theme",
                              ["modern_blue", "dark", "light", "auto"])
        appearance.add_setting("font_size", "int", 14, 
                              "Font Size", "Base font size for UI")
        appearance.add_setting("font_family", "string", "Inter", 
                              "Font Family", "UI font family")
        appearance.add_setting("animations_enabled", "bool", True, 
                              "Animations", "Enable UI animations")
        appearance.add_setting("compact_mode", "bool", False, 
                              "Compact Mode", "Use more compact UI layout")
        appearance.add_setting("show_bookmarks_bar", "bool", True, 
                              "Bookmarks Bar", "Show bookmarks toolbar")
        appearance.add_setting("show_status_bar", "bool", True, 
                              "Status Bar", "Show status bar")
        
        # Privacy & Security category
        privacy = SettingsCategory("Privacy & Security", "Security", "Privacy and security settings")
        privacy.add_setting("send_do_not_track", "bool", True, 
                           "Do Not Track", "Send Do Not Track header")
        privacy.add_setting("block_third_party_cookies", "bool", False, 
                           "Block 3rd Party Cookies", "Block third-party cookies")
        privacy.add_setting("clear_cookies_on_exit", "bool", False, 
                           "Clear Cookies on Exit", "Clear cookies when browser closes")
        privacy.add_setting("enable_safe_browsing", "bool", True, 
                           "Safe Browsing", "Enable malicious site protection")
        privacy.add_setting("remember_passwords", "bool", True, 
                           "Remember Passwords", "Save passwords for sites")
        privacy.add_setting("auto_fill_forms", "bool", True, 
                           "Auto-fill Forms", "Automatically fill web forms")
        
        # Network category
        network = SettingsCategory("Network", "Connection", "Network and connection settings")
        network.add_setting("proxy_enabled", "bool", False, 
                            "Use Proxy", "Enable proxy server")
        network.add_setting("proxy_host", "string", "", 
                            "Proxy Host", "Proxy server hostname")
        network.add_setting("proxy_port", "int", 8080, 
                            "Proxy Port", "Proxy server port")
        network.add_setting("proxy_type", "combo", "http", 
                            "Proxy Type", "Proxy server type",
                            ["http", "https", "socks5"])
        network.add_setting("max_connections", "int", 6, 
                            "Max Connections", "Maximum concurrent connections")
        network.add_setting("connection_timeout", "int", 30, 
                            "Timeout", "Connection timeout in seconds")
        network.add_setting("user_agent", "string", "", 
                            "User Agent", "Custom user agent string")
        
        # Performance category
        performance = SettingsCategory("Performance", "Speed", "Performance and optimization")
        performance.add_setting("hardware_acceleration", "bool", True, 
                               "Hardware Acceleration", "Use GPU acceleration")
        performance.add_setting("max_tabs", "int", 50, 
                               "Max Tabs", "Maximum number of tabs")
        performance.add_setting("tab_preloading", "bool", True, 
                               "Tab Preloading", "Preload tabs in background")
        performance.add_setting("image_loading", "combo", "all", 
                               "Image Loading", "When to load images",
                               ["all", "wifi_only", "never"])
        performance.add_setting("javascript_enabled", "bool", True, 
                               "JavaScript", "Enable JavaScript")
        performance.add_setting("cache_size", "int", 100, 
                               "Cache Size", "Cache size in MB")
        
        # Extensions category
        extensions = SettingsCategory("Extensions", "Add-ons", "Extension management")
        extensions.add_setting("extensions_enabled", "bool", True, 
                               "Enable Extensions", "Allow browser extensions")
        extensions.add_setting("auto_update_extensions", "bool", True, 
                               "Auto-update Extensions", "Automatically update extensions")
        extensions.add_setting("developer_mode", "bool", False, 
                               "Developer Mode", "Enable extension developer tools")
        extensions.add_setting("allow_external_extensions", "bool", False, 
                               "External Extensions", "Allow external extension sources")
        
        self.categories = {
            "general": general,
            "appearance": appearance,
            "privacy": privacy,
            "network": network,
            "performance": performance,
            "extensions": extensions
        }
    
    def get_setting(self, category: str, key: str) -> Any:
        """Get a setting value."""
        if category in self.categories and key in self.categories[category].settings:
            return self.categories[category].settings[key]['current']
        return None
    
    def set_setting(self, category: str, key: str, value: Any):
        """Set a setting value."""
        if category in self.categories and key in self.categories[category].settings:
            self.categories[category].settings[key]['current'] = value
    
    def reset_setting(self, category: str, key: str):
        """Reset a setting to default."""
        if category in self.categories and key in self.categories[category].settings:
            default = self.categories[category].settings[key]['default']
            self.categories[category].settings[key]['current'] = default
    
    def reset_category(self, category: str):
        """Reset all settings in a category."""
        if category in self.categories:
            for key in self.categories[category].settings:
                self.reset_setting(category, key)
    
    def reset_all(self):
        """Reset all settings to defaults."""
        for category in self.categories:
            self.reset_category(category)
    
    def load_settings(self):
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for category_name, category_data in data.items():
                        if category_name in self.categories:
                            for key, value in category_data.items():
                                self.set_setting(category_name, key, value)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file."""
        try:
            data = {}
            for category_name, category in self.categories.items():
                data[category_name] = {}
                for key, setting in category.settings.items():
                    data[category_name][key] = setting['current']
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def export_settings(self, file_path: str):
        """Export settings to file."""
        try:
            data = {}
            for category_name, category in self.categories.items():
                data[category_name] = {}
                for key, setting in category.settings.items():
                    data[category_name][key] = setting['current']
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to export settings: {e}")
    
    def import_settings(self, file_path: str):
        """Import settings from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category_name, category_data in data.items():
                    if category_name in self.categories:
                        for key, value in category_data.items():
                            self.set_setting(category_name, key, value)
        except Exception as e:
            raise Exception(f"Failed to import settings: {e}")


class SettingsWidget(QWidget):
    """Base widget for different setting types."""
    
    value_changed = pyqtSignal(object)
    
    def __init__(self, setting_data: Dict, parent=None):
        super().__init__(parent)
        self.setting_data = setting_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme.get_spacing('sm'))
        
        # Create appropriate widget based on type
        setting_type = self.setting_data['type']
        
        if setting_type == 'bool':
            self.create_checkbox(layout)
        elif setting_type == 'string':
            self.create_text_input(layout)
        elif setting_type == 'int':
            self.create_spinbox(layout)
        elif setting_type == 'path':
            self.create_path_input(layout)
        elif setting_type == 'combo':
            self.create_combobox(layout)
        elif setting_type == 'color':
            self.create_color_picker(layout)
        elif setting_type == 'font':
            self.create_font_picker(layout)
        
        # Add description
        if self.setting_data.get('description'):
            desc_label = QLabel(self.setting_data['description'])
            desc_label.setProperty("class", "caption")
            desc_label.setWordWrap(True)
            style_manager.apply_stylesheet(desc_label, "label")
            layout.addWidget(desc_label)
    
    def create_checkbox(self, layout):
        """Create checkbox widget."""
        self.checkbox = QCheckBox(self.setting_data['label'])
        self.checkbox.setChecked(self.setting_data['current'])
        style_manager.apply_stylesheet(self.checkbox, "checkbox")
        self.checkbox.toggled.connect(self.on_value_changed)
        layout.addWidget(self.checkbox)
    
    def create_text_input(self, layout):
        """Create text input widget."""
        label = QLabel(self.setting_data['label'])
        style_manager.apply_stylesheet(label, "label")
        layout.addWidget(label)
        
        self.text_input = QLineEdit()
        self.text_input.setText(str(self.setting_data['current']))
        self.text_input.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.text_input, "address_bar")
        self.text_input.textChanged.connect(self.on_value_changed)
        layout.addWidget(self.text_input)
    
    def create_spinbox(self, layout):
        """Create spinbox widget."""
        label = QLabel(self.setting_data['label'])
        style_manager.apply_stylesheet(label, "label")
        layout.addWidget(label)
        
        spinbox_layout = QHBoxLayout()
        
        self.spinbox = QSpinBox()
        self.spinbox.setValue(int(self.setting_data['current']))
        self.spinbox.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.spinbox, "combo_box")
        self.spinbox.valueChanged.connect(self.on_value_changed)
        spinbox_layout.addWidget(self.spinbox)
        
        spinbox_layout.addStretch()
        layout.addLayout(spinbox_layout)
    
    def create_path_input(self, layout):
        """Create path input widget."""
        label = QLabel(self.setting_data['label'])
        style_manager.apply_stylesheet(label, "label")
        layout.addWidget(label)
        
        path_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setText(str(self.setting_data['current']))
        self.path_input.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.path_input, "address_bar")
        self.path_input.textChanged.connect(self.on_value_changed)
        path_layout.addWidget(self.path_input)
        
        browse_btn = ui_components.create_modern_button("Browse")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
    
    def create_combobox(self, layout):
        """Create combobox widget."""
        label = QLabel(self.setting_data['label'])
        style_manager.apply_stylesheet(label, "label")
        layout.addWidget(label)
        
        self.combobox = QComboBox()
        if self.setting_data.get('options'):
            self.combobox.addItems(self.setting_data['options'])
        
        # Set current value
        current_value = str(self.setting_data['current'])
        index = self.combobox.findText(current_value)
        if index >= 0:
            self.combobox.setCurrentIndex(index)
        
        self.combobox.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.combobox, "combo_box")
        self.combobox.currentTextChanged.connect(self.on_value_changed)
        layout.addWidget(self.combobox)
    
    def create_color_picker(self, layout):
        """Create color picker widget."""
        color_layout = QHBoxLayout()
        
        label = QLabel(self.setting_data['label'])
        style_manager.apply_stylesheet(label, "label")
        color_layout.addWidget(label)
        
        self.color_button = QPushButton()
        self.color_button.setMinimumHeight(36)
        self.color_button.setMinimumWidth(100)
        self.update_color_button()
        self.color_button.clicked.connect(self.pick_color)
        style_manager.apply_stylesheet(self.color_button, "button")
        color_layout.addWidget(self.color_button)
        
        color_layout.addStretch()
        layout.addLayout(color_layout)
    
    def create_font_picker(self, layout):
        """Create font picker widget."""
        font_layout = QHBoxLayout()
        
        label = QLabel(self.setting_data['label'])
        style_manager.apply_stylesheet(label, "label")
        font_layout.addWidget(label)
        
        self.font_button = QPushButton()
        self.font_button.setMinimumHeight(36)
        self.update_font_button()
        self.font_button.clicked.connect(self.pick_font)
        style_manager.apply_stylesheet(self.font_button, "button")
        font_layout.addWidget(self.font_button)
        
        font_layout.addStretch()
        layout.addLayout(font_layout)
    
    def browse_path(self):
        """Browse for path."""
        if 'download' in self.setting_data['label'].lower():
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path = QFileDialog.getOpenFileName(self, "Select File")[0]
        
        if path:
            self.path_input.setText(path)
    
    def pick_color(self):
        """Pick a color."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.setting_data['current'] = color.name()
            self.update_color_button()
            self.value_changed.emit(color.name())
    
    def pick_font(self):
        """Pick a font."""
        font, ok = QFontDialog.getFont()
        if ok:
            self.setting_data['current'] = font.toString()
            self.update_font_button()
            self.value_changed.emit(font.toString())
    
    def update_color_button(self):
        """Update color button display."""
        color_name = self.setting_data['current']
        color = QColor(color_name)
        self.color_button.setStyleSheet(f"background-color: {color_name}; color: white;")
        self.color_button.setText(color_name.upper())
    
    def update_font_button(self):
        """Update font button display."""
        font_str = self.setting_data['current']
        self.font_button.setText(font_str)
    
    def on_value_changed(self, value):
        """Handle value change."""
        self.setting_data['current'] = value
        self.value_changed.emit(value)
    
    def get_value(self):
        """Get current value."""
        return self.setting_data['current']


class SettingsPanelDialog(QDialog):
    """Advanced settings panel with modern UI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 1000, 700)
        self.setModal(False)
        
        # Apply modern theme
        style_manager.apply_stylesheet(self, "dialog")
        
        # Settings manager
        self.settings_manager = SettingsManager()
        
        # Setup UI
        self.setup_ui()
        self.load_settings()
        
        # Setup search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
    
    def setup_ui(self):
        """Setup the settings panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.create_toolbar(layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left panel - categories
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - settings
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter sizes
        content_splitter.setSizes([300, 700])
        
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
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search settings...")
        self.search_edit.setMinimumHeight(36)
        self.search_edit.setMaximumWidth(300)
        style_manager.apply_stylesheet(self.search_edit, "address_bar")
        self.search_edit.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_edit)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # Reset buttons
        self.reset_category_btn = ui_components.create_modern_button("Reset Category")
        self.reset_category_btn.clicked.connect(self.reset_current_category)
        toolbar_layout.addWidget(self.reset_category_btn)
        
        self.reset_all_btn = ui_components.create_modern_button("Reset All")
        self.reset_all_btn.clicked.connect(self.reset_all_settings)
        toolbar_layout.addWidget(self.reset_all_btn)
        
        # Import/Export buttons
        self.import_btn = ui_components.create_modern_button("Import")
        self.import_btn.clicked.connect(self.import_settings)
        toolbar_layout.addWidget(self.import_btn)
        
        self.export_btn = ui_components.create_modern_button("Export")
        self.export_btn.clicked.connect(self.export_settings)
        toolbar_layout.addWidget(self.export_btn)
        
        parent_layout.addWidget(toolbar_container)
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with categories."""
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                     theme.get_spacing('md'), theme.get_spacing('md'))
        left_layout.setSpacing(theme.get_spacing('md'))
        
        # Categories tree
        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderLabel("Categories")
        self.categories_tree.setMaximumHeight(400)
        style_manager.apply_stylesheet(self.categories_tree, "tree_widget")
        self.categories_tree.itemClicked.connect(self.on_category_clicked)
        
        # Populate categories
        for category_key, category in self.settings_manager.categories.items():
            item = QTreeWidgetItem(self.categories_tree)
            item.setText(0, f"{category.icon} {category.name}")
            item.setText(1, category.description)
            item.setData(0, Qt.ItemDataRole.UserRole, category_key)
        
        left_layout.addWidget(self.categories_tree)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        style_manager.apply_stylesheet(actions_group, "group_box")
        
        # Theme quick switch
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Quick Theme:"))
        
        self.quick_theme_combo = QComboBox()
        self.quick_theme_combo.addItems(["Modern Blue", "Dark", "Light"])
        self.quick_theme_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.quick_theme_combo, "combo_box")
        self.quick_theme_combo.currentTextChanged.connect(self.quick_theme_changed)
        theme_layout.addWidget(self.quick_theme_combo)
        
        actions_layout.addLayout(theme_layout)
        
        # Font size quick adjust
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Size:"))
        
        self.quick_font_slider = QSlider(Qt.Orientation.Horizontal)
        self.quick_font_slider.setRange(8, 24)
        self.quick_font_slider.setValue(14)
        self.quick_font_slider.valueChanged.connect(self.quick_font_changed)
        font_layout.addWidget(self.quick_font_slider)
        
        self.font_size_label = QLabel("14")
        font_layout.addWidget(self.font_size_label)
        
        actions_layout.addLayout(font_layout)
        
        left_layout.addWidget(actions_group)
        
        # About section
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout(about_group)
        style_manager.apply_stylesheet(about_group, "group_box")
        
        about_text = QLabel("Vertex v1.0\nA modern web browser")
        about_text.setWordWrap(True)
        about_text.setProperty("class", "caption")
        style_manager.apply_stylesheet(about_text, "label")
        about_layout.addWidget(about_text)
        
        left_layout.addWidget(about_group)
        
        return left_panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with settings."""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                      theme.get_spacing('md'), theme.get_spacing('md'))
        right_layout.setSpacing(theme.get_spacing('md'))
        
        # Category title
        self.category_title = QLabel("Select a category")
        self.category_title.setProperty("class", "heading")
        style_manager.apply_stylesheet(self.category_title, "label")
        right_layout.addWidget(self.category_title)
        
        # Category description
        self.category_desc = QLabel("")
        self.category_desc.setWordWrap(True)
        self.category_desc.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.category_desc, "label")
        right_layout.addWidget(self.category_desc)
        
        # Settings scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        style_manager.apply_stylesheet(self.scroll_area, "scroll_area")
        right_layout.addWidget(self.scroll_area)
        
        # Settings container
        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                             theme.get_spacing('md'), theme.get_spacing('md'))
        self.settings_layout.setSpacing(theme.get_spacing('lg'))
        
        self.scroll_area.setWidget(self.settings_container)
        
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
        
        # Progress indicator for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        style_manager.apply_stylesheet(self.progress_bar, "progress_bar")
        status_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(status_container)
    
    def on_category_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle category click."""
        category_key = item.data(0, Qt.ItemDataRole.UserRole)
        if category_key:
            self.show_category_settings(category_key)
    
    def show_category_settings(self, category_key: str):
        """Show settings for a category."""
        category = self.settings_manager.categories[category_key]
        
        # Update title and description
        self.category_title.setText(f"{category.icon} {category.name}")
        self.category_desc.setText(category.description)
        
        # Clear existing settings
        for i in reversed(range(self.settings_layout.count())):
            child = self.settings_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add settings widgets
        for key, setting_data in category.settings.items():
            # Create group for each setting
            group = QGroupBox(setting_data['label'])
            group_layout = QVBoxLayout(group)
            style_manager.apply_stylesheet(group, "group_box")
            
            # Create settings widget
            widget = SettingsWidget(setting_data)
            widget.value_changed.connect(lambda value, k=key: self.on_setting_changed(k, value))
            group_layout.addWidget(widget)
            
            self.settings_layout.addWidget(group)
        
        # Add stretch at bottom
        self.settings_layout.addStretch()
        
        # Update reset button
        self.current_category = category_key
        self.reset_category_btn.setEnabled(True)
        
        self.status_label.setText(f"Showing {category.name} settings")
    
    def on_setting_changed(self, key: str, value):
        """Handle setting change."""
        if hasattr(self, 'current_category'):
            self.settings_manager.set_setting(self.current_category, key, value)
            self.save_settings()
            self.status_label.setText(f"Updated setting: {key}")
    
    def on_search_changed(self, text):
        """Handle search text change."""
        self.search_timer.start(300)  # 300ms delay
    
    def perform_search(self):
        """Perform settings search."""
        query = self.search_edit.text().strip().lower()
        
        if not query:
            # Show all categories
            self.categories_tree.clear()
            for category_key, category in self.settings_manager.categories.items():
                item = QTreeWidgetItem(self.categories_tree)
                item.setText(0, f"{category.icon} {category.name}")
                item.setText(1, category.description)
                item.setData(0, Qt.ItemDataRole.UserRole, category_key)
            return
        
        # Search and highlight matching settings
        self.categories_tree.clear()
        
        for category_key, category in self.settings_manager.categories.items():
            matching_settings = []
            for key, setting in category.settings.items():
                if (query in setting['label'].lower() or 
                    query in setting['description'].lower() or
                    query in key.lower()):
                    matching_settings.append(setting)
            
            if matching_settings:
                item = QTreeWidgetItem(self.categories_tree)
                item.setText(0, f"{category.icon} {category.name} ({len(matching_settings)})")
                item.setText(1, f"Found {len(matching_settings)} matching settings")
                item.setData(0, Qt.ItemDataRole.UserRole, category_key)
                item.setForeground(0, QColor(theme.get_color('primary_blue')))
    
    def reset_current_category(self):
        """Reset current category settings."""
        if hasattr(self, 'current_category'):
            reply = QMessageBox.question(
                self, "Reset Category", 
                f"Are you sure you want to reset all {self.current_category} settings to defaults?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.settings_manager.reset_category(self.current_category)
                self.show_category_settings(self.current_category)
                self.save_settings()
                self.status_label.setText(f"Reset {self.current_category} settings")
    
    def reset_all_settings(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset All Settings", 
            "Are you sure you want to reset all settings to defaults? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_all()
            if hasattr(self, 'current_category'):
                self.show_category_settings(self.current_category)
            self.save_settings()
            self.status_label.setText("Reset all settings to defaults")
    
    def import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                self.settings_manager.import_settings(file_path)
                if hasattr(self, 'current_category'):
                    self.show_category_settings(self.current_category)
                self.status_label.setText("Settings imported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import settings: {e}")
    
    def export_settings(self):
        """Export settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "vertex_settings.json", "JSON Files (*.json);|All Files (*.*)"
        )
        if file_path:
            try:
                self.settings_manager.export_settings(file_path)
                self.status_label.setText("Settings exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export settings: {e}")
    
    def quick_theme_changed(self, theme_name: str):
        """Handle quick theme change."""
        theme_map = {
            "Modern Blue": "modern_blue",
            "Dark": "dark",
            "Light": "light"
        }
        
        theme_key = theme_map.get(theme_name, "modern_blue")
        self.settings_manager.set_setting("appearance", "theme", theme_key)
        self.save_settings()
        self.status_label.setText(f"Theme changed to {theme_name}")
    
    def quick_font_changed(self, size: int):
        """Handle quick font size change."""
        self.font_size_label.setText(str(size))
        self.settings_manager.set_setting("appearance", "font_size", size)
        self.save_settings()
        self.status_label.setText(f"Font size changed to {size}")
    
    def load_settings(self):
        """Load settings into UI."""
        # Set quick theme combo
        current_theme = self.settings_manager.get_setting("appearance", "theme")
        theme_reverse_map = {
            "modern_blue": "Modern Blue",
            "dark": "Dark",
            "light": "Light"
        }
        theme_name = theme_reverse_map.get(current_theme, "Modern Blue")
        index = self.quick_theme_combo.findText(theme_name)
        if index >= 0:
            self.quick_theme_combo.setCurrentIndex(index)
        
        # Set quick font slider
        font_size = self.settings_manager.get_setting("appearance", "font_size")
        self.quick_font_slider.setValue(font_size or 14)
        self.font_size_label.setText(str(font_size or 14))
    
    def save_settings(self):
        """Save settings to file."""
        self.settings_manager.save_settings()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        self.save_settings()
        event.accept()


def show_settings_panel(parent=None):
    """Show the settings panel dialog."""
    dialog = SettingsPanelDialog(parent)
    dialog.show()
    return dialog
