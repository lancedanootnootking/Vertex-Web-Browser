#!/usr/bin/env python3.12
"""
Advanced Bookmark Manager with Modern UI

Comprehensive bookmark management system with modern blue/grey theme,
search functionality, folder organization, and beautiful UI.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QMenu, QToolBar, QComboBox, QCheckBox, QGroupBox, 
                             QFormLayout, QDialogButtonBox, QFrame, QMessageBox, 
                             QSpinBox, QSlider, QSplitter, QTextEdit, QScrollArea, 
                             QProgressBar, QFileDialog, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QUrl, QDir
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QKeySequence
from pathlib import Path
import json
from datetime import datetime
import urllib.parse
import requests
from typing import Dict, List, Any, Optional

from frontend.themes.modern_theme import theme, style_manager, ui_components


class BookmarkFaviconLoader(QThread):
    """Thread for loading bookmark favicons."""
    favicon_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.favicon_url = self.get_favicon_url(url)
    
    def get_favicon_url(self, url: str) -> str:
        """Get favicon URL for a given URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            return f"{domain}/favicon.ico"
        except:
            return ""
    
    def run(self):
        """Load favicon from URL."""
        try:
            if self.favicon_url:
                response = requests.get(self.favicon_url, timeout=5)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        self.favicon_loaded.emit(self.url, pixmap)
        except:
            pass


class BookmarkEditDialog(QDialog):
    """Dialog for editing bookmark properties."""
    
    def __init__(self, bookmark_data: Dict = None, parent=None):
        super().__init__(parent)
        self.bookmark_data = bookmark_data or {}
        self.setWindowTitle("Edit Bookmark" if bookmark_data else "Add Bookmark")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Apply modern theme
        style_manager.apply_stylesheet(self, "dialog")
        
        self.setup_ui()
        self.load_bookmark_data()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(theme.get_spacing('lg'), theme.get_spacing('lg'), 
                                 theme.get_spacing('lg'), theme.get_spacing('lg'))
        layout.setSpacing(theme.get_spacing('md'))
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(theme.get_spacing('md'))
        
        # Title field
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter bookmark title...")
        self.title_edit.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.title_edit, "address_bar")
        form_layout.addRow("Title:", self.title_edit)
        
        # URL field
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        self.url_edit.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.url_edit, "address_bar")
        form_layout.addRow("URL:", self.url_edit)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Add a description (optional)...")
        self.description_edit.setMaximumHeight(100)
        style_manager.apply_stylesheet(self.description_edit, "text_edit")
        form_layout.addRow("Description:", self.description_edit)
        
        # Folder selection
        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(True)
        self.folder_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.folder_combo, "combo_box")
        form_layout.addRow("Folder:", self.folder_combo)
        
        # Tags field
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        self.tags_edit.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.tags_edit, "address_bar")
        form_layout.addRow("Tags:", self.tags_edit)
        
        layout.addLayout(form_layout)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        style_manager.apply_stylesheet(options_group, "group_box")
        
        self.private_checkbox = QCheckBox("Private bookmark")
        style_manager.apply_stylesheet(self.private_checkbox, "checkbox")
        options_layout.addWidget(self.private_checkbox)
        
        self.readonly_checkbox = QCheckBox("Read-only")
        style_manager.apply_stylesheet(self.readonly_checkbox, "checkbox")
        options_layout.addWidget(self.readonly_checkbox)
        
        layout.addWidget(options_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Style buttons
        for button in button_box.buttons():
            style_manager.apply_stylesheet(button, "button")
        
        layout.addWidget(button_box)
    
    def load_bookmark_data(self):
        """Load existing bookmark data into form."""
        if self.bookmark_data:
            self.title_edit.setText(self.bookmark_data.get('title', ''))
            self.url_edit.setText(self.bookmark_data.get('url', ''))
            self.description_edit.setPlainText(self.bookmark_data.get('description', ''))
            self.folder_combo.setCurrentText(self.bookmark_data.get('folder', 'General'))
            self.tags_edit.setText(', '.join(self.bookmark_data.get('tags', [])))
            self.private_checkbox.setChecked(self.bookmark_data.get('private', False))
            self.readonly_checkbox.setChecked(self.bookmark_data.get('readonly', False))
    
    def get_bookmark_data(self) -> Dict:
        """Get bookmark data from form."""
        tags = [tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()]
        
        return {
            'title': self.title_edit.text().strip(),
            'url': self.url_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'folder': self.folder_combo.currentText().strip() or 'General',
            'tags': tags,
            'private': self.private_checkbox.isChecked(),
            'readonly': self.readonly_checkbox.isChecked(),
            'created': self.bookmark_data.get('created', datetime.now().isoformat()),
            'modified': datetime.now().isoformat(),
            'id': self.bookmark_data.get('id', f"bookmark_{datetime.now().timestamp()}")
        }


class BookmarkManagerDialog(QDialog):
    """Advanced bookmark manager with modern UI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmark Manager")
        self.setGeometry(200, 200, 1200, 800)
        self.setModal(False)
        
        # Apply modern theme
        style_manager.apply_stylesheet(self, "dialog")
        
        # Data
        self.bookmarks = []
        self.folders = ['General', 'Favorites', 'Work', 'Personal', 'Research']
        self.favicon_loaders = {}
        
        # Setup UI
        self.setup_ui()
        self.load_bookmarks()
        
        # Setup search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
    
    def setup_ui(self):
        """Setup the bookmark manager UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.create_toolbar(layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left panel - folders and search
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - bookmarks list
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter sizes
        content_splitter.setSizes([300, 900])
        
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
        
        # Add bookmark button
        self.add_btn = ui_components.create_modern_button("Add Bookmark", "primary")
        self.add_btn.clicked.connect(self.add_bookmark)
        toolbar_layout.addWidget(self.add_btn)
        
        # New folder button
        self.new_folder_btn = ui_components.create_modern_button("New Folder")
        self.new_folder_btn.clicked.connect(self.create_folder)
        toolbar_layout.addWidget(self.new_folder_btn)
        
        # Import/Export buttons
        self.import_btn = ui_components.create_modern_button("Import")
        self.import_btn.clicked.connect(self.import_bookmarks)
        toolbar_layout.addWidget(self.import_btn)
        
        self.export_btn = ui_components.create_modern_button("Export")
        self.export_btn.clicked.connect(self.export_bookmarks)
        toolbar_layout.addWidget(self.export_btn)
        
        # Separator
        separator = ui_components.create_modern_separator("vertical")
        toolbar_layout.addWidget(separator)
        
        # View options
        self.view_combo = QComboBox()
        self.view_combo.addItems(["All Bookmarks", "Recent", "Most Visited", "By Tag"])
        self.view_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.view_combo, "combo_box")
        toolbar_layout.addWidget(self.view_combo)
        
        # Sort options
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sort by Title", "Sort by Date", "Sort by URL", "Sort by Folder"])
        self.sort_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.sort_combo, "combo_box")
        toolbar_layout.addWidget(self.sort_combo)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search bookmarks...")
        self.search_edit.setMinimumHeight(36)
        self.search_edit.setMaximumWidth(300)
        style_manager.apply_stylesheet(self.search_edit, "address_bar")
        self.search_edit.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_edit)
        
        parent_layout.addWidget(toolbar_container)
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with folders and quick access."""
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                     theme.get_spacing('md'), theme.get_spacing('md'))
        left_layout.setSpacing(theme.get_spacing('md'))
        
        # Quick access section
        quick_group = QGroupBox("Quick Access")
        quick_layout = QVBoxLayout(quick_group)
        style_manager.apply_stylesheet(quick_group, "group_box")
        
        # Quick buttons
        self.all_bookmarks_btn = ui_components.create_modern_button("📚 All Bookmarks")
        self.all_bookmarks_btn.clicked.connect(lambda: self.filter_by_folder(None))
        quick_layout.addWidget(self.all_bookmarks_btn)
        
        self.recent_btn = ui_components.create_modern_button("🕐 Recent")
        self.recent_btn.clicked.connect(self.show_recent)
        quick_layout.addWidget(self.recent_btn)
        
        self.favorites_btn = ui_components.create_modern_button("⭐ Favorites")
        self.favorites_btn.clicked.connect(lambda: self.filter_by_folder("Favorites"))
        quick_layout.addWidget(self.favorites_btn)
        
        left_layout.addWidget(quick_group)
        
        # Folders section
        folders_group = QGroupBox("Folders")
        folders_layout = QVBoxLayout(folders_group)
        style_manager.apply_stylesheet(folders_group, "group_box")
        
        # Folders tree
        self.folders_tree = QTreeWidget()
        self.folders_tree.setHeaderLabel("Bookmarks")
        self.folders_tree.setMaximumHeight(200)
        style_manager.apply_stylesheet(self.folders_tree, "tree_widget")
        self.folders_tree.itemClicked.connect(self.on_folder_clicked)
        folders_layout.addWidget(self.folders_tree)
        
        left_layout.addWidget(folders_group)
        
        # Tags section
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        style_manager.apply_stylesheet(tags_group, "group_box")
        
        # Tags cloud
        self.tags_widget = QWidget()
        self.tags_layout = QVBoxLayout(self.tags_widget)
        tags_layout.addWidget(self.tags_widget)
        
        left_layout.addWidget(tags_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        style_manager.apply_stylesheet(stats_group, "group_box")
        
        self.total_label = QLabel("0")
        self.folders_label = QLabel("0")
        self.tags_label = QLabel("0")
        
        stats_layout.addRow("Total Bookmarks:", self.total_label)
        stats_layout.addRow("Folders:", self.folders_label)
        stats_layout.addRow("Tags:", self.tags_label)
        
        left_layout.addWidget(stats_group)
        
        return left_panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with bookmarks list."""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                      theme.get_spacing('md'), theme.get_spacing('md'))
        right_layout.setSpacing(theme.get_spacing('md'))
        
        # Bookmarks list
        self.bookmarks_tree = QTreeWidget()
        self.bookmarks_tree.setHeaderLabels(["Title", "URL", "Folder", "Tags", "Date Added"])
        self.bookmarks_tree.setRootIsDecorated(False)
        self.bookmarks_tree.setAlternatingRowColors(True)
        self.bookmarks_tree.setSortingEnabled(True)
        style_manager.apply_stylesheet(self.bookmarks_tree, "tree_widget")
        
        # Connect signals
        self.bookmarks_tree.itemDoubleClicked.connect(self.edit_bookmark)
        self.bookmarks_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bookmarks_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        right_layout.addWidget(self.bookmarks_tree)
        
        # Details panel
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        style_manager.apply_stylesheet(details_group, "group_box")
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        style_manager.apply_stylesheet(self.details_text, "text_edit")
        details_layout.addWidget(self.details_text)
        
        right_layout.addWidget(details_group)
        
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
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        style_manager.apply_stylesheet(self.progress_bar, "progress_bar")
        status_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(status_container)
    
    def load_bookmarks(self):
        """Load bookmarks from storage."""
        try:
            bookmarks_file = Path.home() / '.vertex_bookmarks.json'
            if bookmarks_file.exists():
                with open(bookmarks_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            else:
                # Create sample bookmarks
                self.bookmarks = self.create_sample_bookmarks()
                self.save_bookmarks()
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = []
        
        self.populate_folders_tree()
        self.populate_bookmarks_list()
        self.update_statistics()
    
    def create_sample_bookmarks(self) -> List[Dict]:
        """Create sample bookmarks for demonstration."""
        return [
            {
                'id': 'bookmark_1',
                'title': 'DuckDuckGo',
                'url': 'https://duckduckgo.com',
                'description': 'Privacy-focused search engine',
                'folder': 'General',
                'tags': ['search', 'privacy'],
                'private': False,
                'readonly': False,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'visits': 42
            },
            {
                'id': 'bookmark_2',
                'title': 'GitHub',
                'url': 'https://github.com',
                'description': 'Code hosting platform',
                'folder': 'Work',
                'tags': ['development', 'code'],
                'private': False,
                'readonly': False,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'visits': 128
            },
            {
                'id': 'bookmark_3',
                'title': 'Stack Overflow',
                'url': 'https://stackoverflow.com',
                'description': 'Programming Q&A',
                'folder': 'Work',
                'tags': ['programming', 'help'],
                'private': False,
                'readonly': False,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'visits': 256
            }
        ]
    
    def populate_folders_tree(self):
        """Populate the folders tree widget."""
        self.folders_tree.clear()
        
        # Add folders
        for folder in sorted(self.folders):
            item = QTreeWidgetItem(self.folders_tree, [folder])
            # Count bookmarks in folder
            count = len([b for b in self.bookmarks if b.get('folder') == folder])
            item.setText(1, f"({count})")
        
        # Add tags
        tags = set()
        for bookmark in self.bookmarks:
            tags.update(bookmark.get('tags', []))
        
        tags_item = QTreeWidgetItem(self.folders_tree, ["Tags"])
        for tag in sorted(tags):
            tag_item = QTreeWidgetItem(tags_item, [f"#{tag}"])
            count = len([b for b in self.bookmarks if tag in b.get('tags', [])])
            tag_item.setText(1, f"({count})")
    
    def populate_bookmarks_list(self, filter_folder=None):
        """Populate the bookmarks list."""
        self.bookmarks_tree.clear()
        
        filtered_bookmarks = self.bookmarks
        if filter_folder:
            filtered_bookmarks = [b for b in self.bookmarks if b.get('folder') == filter_folder]
        
        for bookmark in sorted(filtered_bookmarks, key=lambda x: x.get('title', '').lower()):
            item = QTreeWidgetItem(self.bookmarks_tree)
            item.setText(0, bookmark.get('title', ''))
            item.setText(1, bookmark.get('url', ''))
            item.setText(2, bookmark.get('folder', ''))
            item.setText(3, ', '.join(bookmark.get('tags', [])))
            item.setText(4, bookmark.get('created', '').split('T')[0])
            item.setData(0, Qt.ItemDataRole.UserRole, bookmark)
            
            # Load favicon
            self.load_favicon(bookmark.get('url', ''), item)
        
        # Resize columns
        for i in range(self.bookmarks_tree.columnCount()):
            self.bookmarks_tree.resizeColumnToContents(i)
    
    def load_favicon(self, url: str, item: QTreeWidgetItem):
        """Load favicon for a bookmark."""
        if url not in self.favicon_loaders:
            loader = BookmarkFaviconLoader(url)
            loader.favicon_loaded.connect(lambda favicon_url, pixmap: self.on_favicon_loaded(url, item, pixmap))
            self.favicon_loaders[url] = loader
            loader.start()
    
    def on_favicon_loaded(self, url: str, item: QTreeWidgetItem, pixmap: QPixmap):
        """Handle favicon loaded."""
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            item.setIcon(0, QIcon(scaled_pixmap))
        
        # Clean up loader
        if url in self.favicon_loaders:
            del self.favicon_loaders[url]
    
    def update_statistics(self):
        """Update statistics display."""
        self.total_label.setText(str(len(self.bookmarks)))
        
        folders = set(b.get('folder', 'General') for b in self.bookmarks)
        self.folders_label.setText(str(len(folders)))
        
        tags = set()
        for bookmark in self.bookmarks:
            tags.update(bookmark.get('tags', []))
        self.tags_label.setText(str(len(tags)))
    
    def on_search_changed(self, text):
        """Handle search text change."""
        self.search_timer.start(300)  # 300ms delay
    
    def perform_search(self):
        """Perform bookmark search."""
        query = self.search_edit.text().strip().lower()
        
        if not query:
            self.populate_bookmarks_list()
            return
        
        # Clear current list
        self.bookmarks_tree.clear()
        
        # Search bookmarks
        for bookmark in self.bookmarks:
            if (query in bookmark.get('title', '').lower() or 
                query in bookmark.get('url', '').lower() or
                query in bookmark.get('description', '').lower() or
                any(query in tag.lower() for tag in bookmark.get('tags', []))):
                
                item = QTreeWidgetItem(self.bookmarks_tree)
                item.setText(0, bookmark.get('title', ''))
                item.setText(1, bookmark.get('url', ''))
                item.setText(2, bookmark.get('folder', ''))
                item.setText(3, ', '.join(bookmark.get('tags', [])))
                item.setText(4, bookmark.get('created', '').split('T')[0])
                item.setData(0, Qt.ItemDataRole.UserRole, bookmark)
        
        # Update status
        self.status_label.setText(f"Found {self.bookmarks_tree.topLevelItemCount()} bookmarks")
    
    def on_folder_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle folder click."""
        folder_name = item.text(0)
        if folder_name == "Tags":
            # Handle tags selection
            return
        elif folder_name.startswith("#"):
            # Filter by tag
            tag = folder_name[1:]
            self.filter_by_tag(tag)
        else:
            # Filter by folder
            self.filter_by_folder(folder_name)
    
    def filter_by_folder(self, folder: str):
        """Filter bookmarks by folder."""
        self.populate_bookmarks_list(folder)
        if folder:
            self.status_label.setText(f"Showing bookmarks in '{folder}'")
        else:
            self.status_label.setText("Showing all bookmarks")
    
    def filter_by_tag(self, tag: str):
        """Filter bookmarks by tag."""
        self.bookmarks_tree.clear()
        
        for bookmark in self.bookmarks:
            if tag in bookmark.get('tags', []):
                item = QTreeWidgetItem(self.bookmarks_tree)
                item.setText(0, bookmark.get('title', ''))
                item.setText(1, bookmark.get('url', ''))
                item.setText(2, bookmark.get('folder', ''))
                item.setText(3, ', '.join(bookmark.get('tags', [])))
                item.setText(4, bookmark.get('created', '').split('T')[0])
                item.setData(0, Qt.ItemDataRole.UserRole, bookmark)
        
        self.status_label.setText(f"Showing bookmarks with tag '{tag}'")
    
    def show_recent(self):
        """Show recent bookmarks."""
        self.bookmarks_tree.clear()
        
        # Sort by creation date and show top 20
        recent_bookmarks = sorted(self.bookmarks, key=lambda x: x.get('created', ''), reverse=True)[:20]
        
        for bookmark in recent_bookmarks:
            item = QTreeWidgetItem(self.bookmarks_tree)
            item.setText(0, bookmark.get('title', ''))
            item.setText(1, bookmark.get('url', ''))
            item.setText(2, bookmark.get('folder', ''))
            item.setText(3, ', '.join(bookmark.get('tags', [])))
            item.setText(4, bookmark.get('created', '').split('T')[0])
            item.setData(0, Qt.ItemDataRole.UserRole, bookmark)
        
        self.status_label.setText("Showing recent bookmarks")
    
    def add_bookmark(self):
        """Add a new bookmark."""
        dialog = BookmarkEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            bookmark_data = dialog.get_bookmark_data()
            self.bookmarks.append(bookmark_data)
            self.save_bookmarks()
            self.refresh_ui()
            self.status_label.setText(f"Added bookmark: {bookmark_data['title']}")
    
    def edit_bookmark(self, item: QTreeWidgetItem, column: int):
        """Edit selected bookmark."""
        bookmark_data = item.data(0, Qt.ItemDataRole.UserRole)
        if bookmark_data:
            dialog = BookmarkEditDialog(bookmark_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_bookmark_data()
                # Update bookmark in list
                for i, bookmark in enumerate(self.bookmarks):
                    if bookmark['id'] == updated_data['id']:
                        self.bookmarks[i] = updated_data
                        break
                self.save_bookmarks()
                self.refresh_ui()
                self.status_label.setText(f"Updated bookmark: {updated_data['title']}")
    
    def create_folder(self):
        """Create a new folder."""
        from PyQt6.QtWidgets import QInputDialog
        
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name.strip():
            if folder_name not in self.folders:
                self.folders.append(folder_name.strip())
                self.populate_folders_tree()
                self.status_label.setText(f"Created folder: {folder_name}")
            else:
                QMessageBox.warning(self, "Folder Exists", "A folder with this name already exists.")
    
    def import_bookmarks(self):
        """Import bookmarks from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Bookmarks", "", "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_bookmarks = json.load(f)
                
                # Merge with existing bookmarks
                self.bookmarks.extend(imported_bookmarks)
                self.save_bookmarks()
                self.refresh_ui()
                self.status_label.setText(f"Imported {len(imported_bookmarks)} bookmarks")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import bookmarks: {e}")
    
    def export_bookmarks(self):
        """Export bookmarks to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Bookmarks", "bookmarks.json", "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
                self.status_label.setText(f"Exported {len(self.bookmarks)} bookmarks")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export bookmarks: {e}")
    
    def show_context_menu(self, position):
        """Show context menu for bookmarks."""
        item = self.bookmarks_tree.itemAt(position)
        if not item:
            return
        
        bookmark_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not bookmark_data:
            return
        
        menu = QMenu(self)
        style_manager.apply_stylesheet(menu, "menu")
        
        # Actions
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.edit_bookmark(item, 0))
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_bookmark(bookmark_data))
        
        menu.addSeparator()
        
        open_action = menu.addAction("Open in Browser")
        open_action.triggered.connect(lambda: self.open_bookmark(bookmark_data))
        
        copy_action = menu.addAction("Copy URL")
        copy_action.triggered.connect(lambda: self.copy_bookmark_url(bookmark_data))
        
        menu.exec(self.bookmarks_tree.mapToGlobal(position))
    
    def delete_bookmark(self, bookmark_data: Dict):
        """Delete a bookmark."""
        reply = QMessageBox.question(
            self, "Delete Bookmark", 
            f"Are you sure you want to delete '{bookmark_data.get('title', '')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.bookmarks = [b for b in self.bookmarks if b['id'] != bookmark_data['id']]
            self.save_bookmarks()
            self.refresh_ui()
            self.status_label.setText(f"Deleted bookmark: {bookmark_data['title']}")
    
    def open_bookmark(self, bookmark_data: Dict):
        """Open bookmark in browser."""
        url = bookmark_data.get('url', '')
        if url:
            # Increment visit count
            for bookmark in self.bookmarks:
                if bookmark['id'] == bookmark_data['id']:
                    bookmark['visits'] = bookmark.get('visits', 0) + 1
                    break
            self.save_bookmarks()
            
            # Open in system browser
            import webbrowser
            webbrowser.open(url)
    
    def copy_bookmark_url(self, bookmark_data: Dict):
        """Copy bookmark URL to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(bookmark_data.get('url', ''))
        self.status_label.setText("URL copied to clipboard")
    
    def save_bookmarks(self):
        """Save bookmarks to file."""
        try:
            bookmarks_file = Path.home() / '.vertex_bookmarks.json'
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def refresh_ui(self):
        """Refresh all UI elements."""
        self.populate_folders_tree()
        self.populate_bookmarks_list()
        self.update_statistics()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop any running favicon loaders
        for loader in self.favicon_loaders.values():
            loader.terminate()
            loader.wait()
        event.accept()


def show_bookmark_manager(parent=None):
    """Show the bookmark manager dialog."""
    dialog = BookmarkManagerDialog(parent)
    dialog.show()
    return dialog
