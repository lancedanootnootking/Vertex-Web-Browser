#!/usr/bin/env python3.12
"""
History and Bookmarks UI Components

Comprehensive UI for managing history and bookmarks with search,
tags, and organization features.
"""

import os
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
                             QHeaderView, QAbstractItemView, QSlider, QDoubleSpinBox,
                             QDateTimeEdit, QSpinBox, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QSortFilterProxyModel, QDateTime, QMimeData
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QPainter, QColor, QDrag

from frontend.themes.modern_theme import theme, style_manager, ui_components
from backend.advanced_history_bookmarks import (BookmarkManager, HistoryManager, BookmarkItem, 
                                              HistoryItem, BookmarkType, BookmarkSortOrder)


class BookmarkTreeWidget(QTreeWidget):
    """Tree widget for displaying bookmarks."""
    
    bookmark_selected = pyqtSignal(object)  # BookmarkItem
    bookmark_double_clicked = pyqtSignal(object)  # BookmarkItem
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bookmark_manager = None
        self.setup_ui()
        self.setup_drag_drop()
    
    def setup_ui(self):
        self.setHeaderLabels(["Title", "URL", "Tags"])
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(True)
        
        # Connect signals
        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "tree_widget")
    
    def setup_drag_drop(self):
        """Setup drag and drop."""
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
    
    def set_bookmark_manager(self, manager: BookmarkManager):
        """Set bookmark manager."""
        self.bookmark_manager = manager
        self.refresh_tree()
        
        # Connect signals
        self.bookmark_manager.bookmark_added.connect(self.add_bookmark_item)
        self.bookmark_manager.bookmark_updated.connect(self.update_bookmark_item)
        self.bookmark_manager.bookmark_deleted.connect(self.remove_bookmark_item)
    
    def refresh_tree(self):
        """Refresh bookmark tree."""
        self.clear()
        
        if not self.bookmark_manager:
            return
        
        # Add root folders
        root_bookmarks = self.bookmark_manager.get_root_bookmarks()
        for bookmark in root_bookmarks:
            self.add_bookmark_item(bookmark)
    
    def add_bookmark_item(self, bookmark: BookmarkItem):
        """Add bookmark item to tree."""
        if bookmark.is_folder:
            # Create folder item
            item = QTreeWidgetItem(self)
            item.setText(0, bookmark.title)
            item.setText(1, "")
            item.setText(2, "")
            item.setData(0, Qt.ItemDataRole.UserRole, bookmark)
            item.setIcon(0, self.get_folder_icon())
            
            # Add children
            children = self.bookmark_manager.get_children(bookmark.id)
            for child in children:
                self._add_child_item(item, child)
            
            self.expandItem(item)
        else:
            # Find parent item
            parent_item = self.find_parent_item(bookmark.parent_id)
            if parent_item:
                self._add_child_item(parent_item, bookmark)
            else:
                # Add to root
                self._add_child_item(self.invisibleRootItem(), bookmark)
    
    def _add_child_item(self, parent_item: QTreeWidgetItem, bookmark: BookmarkItem):
        """Add child bookmark item."""
        if bookmark.is_separator:
            # Add separator
            separator = QTreeWidgetItem(parent_item)
            separator.setText(0, "---")
            separator.setData(0, Qt.ItemDataRole.UserRole, bookmark)
        else:
            # Add bookmark
            item = QTreeWidgetItem(parent_item)
            item.setText(0, bookmark.title)
            item.setText(1, bookmark.url)
            item.setText(2, ", ".join(sorted(bookmark.tags)))
            item.setData(0, Qt.ItemDataRole.UserRole, bookmark)
            
            if bookmark.is_folder:
                item.setIcon(0, self.get_folder_icon())
            else:
                item.setIcon(0, self.get_bookmark_icon(bookmark))
            
            # Add children if folder
            if bookmark.is_folder:
                children = self.bookmark_manager.get_children(bookmark.id)
                for child in children:
                    self._add_child_item(item, child)
    
    def find_parent_item(self, parent_id: str) -> Optional[QTreeWidgetItem]:
        """Find parent item by ID."""
        if parent_id is None:
            return self.invisibleRootItem()
        
        # Search for item
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            bookmark = item.data(0, Qt.ItemDataRole.UserRole)
            if bookmark and bookmark.id == parent_id:
                return item
            iterator += 1
        
        return None
    
    def update_bookmark_item(self, bookmark: BookmarkItem):
        """Update bookmark item in tree."""
        item = self.find_item(bookmark.id)
        if item:
            item.setText(0, bookmark.title)
            item.setText(1, bookmark.url)
            item.setText(2, ", ".join(sorted(bookmark.tags)))
            
            if bookmark.is_folder:
                item.setIcon(0, self.get_folder_icon())
            else:
                item.setIcon(0, self.get_bookmark_icon(bookmark))
    
    def remove_bookmark_item(self, bookmark_id: str):
        """Remove bookmark item from tree."""
        item = self.find_item(bookmark_id)
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.takeTopLevelItem(self.indexOfTopLevelItem(item))
    
    def find_item(self, bookmark_id: str) -> Optional[QTreeWidgetItem]:
        """Find item by bookmark ID."""
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            bookmark = item.data(0, Qt.ItemDataRole.UserRole)
            if bookmark and bookmark.id == bookmark_id:
                return item
            iterator += 1
        return None
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click."""
        bookmark = item.data(0, Qt.ItemDataRole.UserRole)
        if bookmark:
            self.bookmark_selected.emit(bookmark)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double click."""
        bookmark = item.data(0, Qt.ItemDataRole.UserRole)
        if bookmark and not bookmark.is_folder and not bookmark.is_separator:
            self.bookmark_double_clicked.emit(bookmark)
    
    def get_selected_bookmark(self) -> Optional[BookmarkItem]:
        """Get selected bookmark."""
        items = self.selectedItems()
        if items:
            return items[0].data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def get_folder_icon(self) -> QIcon:
        """Get folder icon."""
        # Would return actual folder icon
        return QIcon()
    
    def get_bookmark_icon(self, bookmark: BookmarkItem) -> QIcon:
        """Get bookmark icon."""
        # Would return favicon or default bookmark icon
        return QIcon()
    
    def contextMenuEvent(self, event):
        """Show context menu."""
        item = self.itemAt(event.pos())
        if item:
            bookmark = item.data(0, Qt.ItemDataRole.UserRole)
            if bookmark:
                menu = QMenu(self)
                
                if not bookmark.is_folder and not bookmark.is_separator:
                    open_action = menu.addAction("Open")
                    open_action.triggered.connect(lambda: self.bookmark_double_clicked.emit(bookmark))
                    
                    menu.addSeparator()
                
                edit_action = menu.addAction("Edit")
                edit_action.triggered.connect(lambda: self.edit_bookmark(bookmark))
                
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self.delete_bookmark(bookmark))
                
                menu.exec(event.globalPos())
    
    def edit_bookmark(self, bookmark: BookmarkItem):
        """Edit bookmark."""
        dialog = BookmarkEditDialog(bookmark, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.bookmark_manager.update_bookmark(bookmark)
    
    def delete_bookmark(self, bookmark: BookmarkItem):
        """Delete bookmark."""
        reply = QMessageBox.question(
            self, "Delete Bookmark",
            f"Are you sure you want to delete '{bookmark.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.bookmark_manager.delete_bookmark(bookmark.id)


class BookmarkEditDialog(QDialog):
    """Dialog for editing bookmarks."""
    
    def __init__(self, bookmark: BookmarkItem, parent=None):
        super().__init__(parent)
        self.bookmark = bookmark
        self.setWindowTitle("Edit Bookmark")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.bookmark.title)
        form_layout.addRow("Title:", self.title_edit)
        
        # URL (for bookmarks only)
        if not self.bookmark.is_folder:
            self.url_edit = QLineEdit()
            self.url_edit.setText(self.bookmark.url)
            form_layout.addRow("URL:", self.url_edit)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setText(", ".join(sorted(self.bookmark.tags)))
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(self.bookmark.notes)
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Favorite checkbox
        self.favorite_check = QCheckBox("Add to Favorites")
        self.favorite_check.setChecked(self.bookmark.is_favorite)
        form_layout.addRow("", self.favorite_check)
        
        # Read later checkbox (for bookmarks only)
        if not self.bookmark.is_folder:
            self.read_later_check = QCheckBox("Read Later")
            self.read_later_check.setChecked(self.bookmark.is_read_later)
            form_layout.addRow("", self.read_later_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def accept(self):
        """Save changes."""
        self.bookmark.title = self.title_edit.text().strip()
        
        if not self.bookmark.is_folder:
            self.bookmark.url = self.url_edit.text().strip()
        
        # Parse tags
        tags_text = self.tags_edit.text().strip()
        if tags_text:
            self.bookmark.tags = set(tag.strip() for tag in tags_text.split(','))
        else:
            self.bookmark.tags = set()
        
        self.bookmark.notes = self.notes_edit.toPlainText().strip()
        self.bookmark.is_favorite = self.favorite_check.isChecked()
        
        if not self.bookmark.is_folder:
            self.bookmark.is_read_later = self.read_later_check.isChecked()
        
        super().accept()


class HistoryListWidget(QListWidget):
    """Widget for displaying history items."""
    
    history_selected = pyqtSignal(object)  # HistoryItem
    history_double_clicked = pyqtSignal(object)  # HistoryItem
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_manager = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Connect signals
        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "list_widget")
    
    def set_history_manager(self, manager: HistoryManager):
        """Set history manager."""
        self.history_manager = manager
        self.refresh_list()
        
        # Connect signals
        self.history_manager.history_added.connect(self.add_history_item)
        self.history_manager.history_updated.connect(self.update_history_item)
        self.history_manager.history_deleted.connect(self.remove_history_item)
        self.history_manager.history_cleared.connect(self.clear)
    
    def refresh_list(self, limit: int = 100):
        """Refresh history list."""
        self.clear()
        
        if not self.history_manager:
            return
        
        history_items = self.history_manager.get_recent_history(limit)
        for item in history_items:
            self.add_history_item(item)
    
    def add_history_item(self, item: HistoryItem):
        """Add history item to list."""
        # Insert at beginning
        list_item = QListWidgetItem()
        self.insertItem(0, list_item)
        
        # Create custom widget for item
        widget = HistoryItemWidget(item, self)
        list_item.setSizeHint(widget.sizeHint())
        self.setItemWidget(list_item, widget)
        
        # Store reference
        list_item.setData(Qt.ItemDataRole.UserRole, item)
    
    def update_history_item(self, item: HistoryItem):
        """Update history item in list."""
        for i in range(self.count()):
            list_item = self.item(i)
            existing_item = list_item.data(Qt.ItemDataRole.UserRole)
            if existing_item and existing_item.id == item.id:
                widget = HistoryItemWidget(item, self)
                list_item.setSizeHint(widget.sizeHint())
                self.setItemWidget(list_item, widget)
                list_item.setData(Qt.ItemDataRole.UserRole, item)
                break
    
    def remove_history_item(self, item_id: str):
        """Remove history item from list."""
        for i in range(self.count()):
            list_item = self.item(i)
            existing_item = list_item.data(Qt.ItemDataRole.UserRole)
            if existing_item and existing_item.id == item_id:
                self.takeItem(i)
                break
    
    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        history_item = item.data(Qt.ItemDataRole.UserRole)
        if history_item:
            self.history_selected.emit(history_item)
    
    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double click."""
        history_item = item.data(Qt.ItemDataRole.UserRole)
        if history_item:
            self.history_double_clicked.emit(history_item)
    
    def get_selected_history_item(self) -> Optional[HistoryItem]:
        """Get selected history item."""
        items = self.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None


class HistoryItemWidget(QWidget):
    """Widget for displaying history item."""
    
    def __init__(self, item: HistoryItem, parent=None):
        super().__init__(parent)
        self.history_item = item
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self.history_item.title)
        title_label.setProperty("class", "history_title")
        title_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # URL
        url_label = QLabel(self.history_item.url)
        url_label.setProperty("class", "history_url")
        url_label.setWordWrap(True)
        layout.addWidget(url_label)
        
        # Visit info
        visit_layout = QHBoxLayout()
        
        # Visit time
        time_text = self.history_item.visit_time.strftime('%Y-%m-%d %H:%M')
        time_label = QLabel(time_text)
        time_label.setProperty("class", "history_time")
        visit_layout.addWidget(time_label)
        
        visit_layout.addStretch()
        
        # Visit count
        if self.history_item.visit_count > 1:
            count_label = QLabel(f"{self.history_item.visit_count} visits")
            count_label.setProperty("class", "history_count")
            visit_layout.addWidget(count_label)
        
        layout.addLayout(visit_layout)
        
        # Apply styling
        self.setProperty("class", "history_item")
        style_manager.apply_stylesheet(self, "card")


class BookmarksManagerDialog(QDialog):
    """Main bookmarks manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks Manager")
        self.resize(800, 600)
        self.bookmark_manager = BookmarkManager(self)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add bookmark button
        add_btn = QPushButton("Add Bookmark")
        add_btn.clicked.connect(self.add_bookmark)
        toolbar_layout.addWidget(add_btn)
        
        # Add folder button
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        toolbar_layout.addWidget(add_folder_btn)
        
        toolbar_layout.addStretch()
        
        # Import/Export buttons
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_bookmarks)
        toolbar_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_bookmarks)
        toolbar_layout.addWidget(export_btn)
        
        layout.addWidget(toolbar)
        
        # Main content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Bookmark tree
        self.bookmark_tree = BookmarkTreeWidget()
        self.bookmark_tree.set_bookmark_manager(self.bookmark_manager)
        self.bookmark_tree.bookmark_double_clicked.connect(self.open_bookmark)
        content_splitter.addWidget(self.bookmark_tree)
        
        # Details panel
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        
        self.details_label = QLabel("Select a bookmark to view details")
        self.details_label.setWordWrap(True)
        self.details_layout.addWidget(self.details_label)
        
        self.details_layout.addStretch()
        content_splitter.addWidget(self.details_widget)
        
        content_splitter.setSizes([500, 300])
        layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def add_bookmark(self):
        """Add new bookmark."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Bookmark")
        dialog.setModal(True)
        dialog.resize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form_layout = QFormLayout()
        
        # Title
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Enter bookmark title...")
        form_layout.addRow("Title:", title_edit)
        
        # URL
        url_edit = QLineEdit()
        url_edit.setPlaceholderText("Enter URL...")
        form_layout.addRow("URL:", url_edit)
        
        # Parent folder
        parent_combo = QComboBox()
        self._populate_folder_combo(parent_combo)
        form_layout.addRow("Folder:", parent_combo)
        
        # Tags
        tags_edit = QLineEdit()
        tags_edit.setPlaceholderText("Enter tags separated by commas...")
        form_layout.addRow("Tags:", tags_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        style_manager.apply_stylesheet(dialog, "dialog")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_edit.text().strip()
            url = url_edit.text().strip()
            
            if title and url:
                # Get selected folder
                parent_id = None
                if parent_combo.currentData():
                    parent_id = parent_combo.currentData()
                
                # Parse tags
                tags_text = tags_edit.text().strip()
                tags = set(tag.strip() for tag in tags_text.split(',')) if tags_text else set()
                
                # Create bookmark
                bookmark = BookmarkItem(
                    title=title,
                    url=url,
                    parent_id=parent_id,
                    tags=tags
                )
                
                self.bookmark_manager.add_bookmark(bookmark)
    
    def add_folder(self):
        """Add new folder."""
        name, ok = QInputDialog.getText(self, "Add Folder", "Enter folder name:")
        if ok and name:
            # Get selected folder as parent
            selected_bookmark = self.bookmark_tree.get_selected_bookmark()
            parent_id = None
            
            if selected_bookmark and selected_bookmark.is_folder:
                parent_id = selected_bookmark.id
            else:
                # Use "Other Bookmarks" as default
                parent_id = self.bookmark_manager.other_bookmarks_id
            
            # Create folder
            folder = BookmarkItem(
                title=name,
                parent_id=parent_id,
                type=BookmarkType.FOLDER
            )
            
            self.bookmark_manager.add_bookmark(folder)
    
    def _populate_folder_combo(self, combo: QComboBox):
        """Populate folder combo box."""
        combo.addItem("Bookmarks Bar", self.bookmark_manager.bookmarks_bar_id)
        combo.addItem("Other Bookmarks", self.bookmark_manager.other_bookmarks_id)
        
        # Add subfolders
        for folder in self.bookmark_manager.folders.values():
            if folder.id not in [self.bookmark_manager.root_folder_id, 
                                self.bookmark_manager.bookmarks_bar_id,
                                self.bookmark_manager.other_bookmarks_id]:
                combo.addItem(folder.title, folder.id)
    
    def import_bookmarks(self):
        """Import bookmarks."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Bookmarks", "", "JSON Files (*.json);;HTML Files (*.html)"
        )
        
        if file_path:
            format = "json" if file_path.endswith('.json') else "html"
            try:
                self.bookmark_manager.import_bookmarks(file_path, format)
                QMessageBox.information(self, "Success", "Bookmarks imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import bookmarks: {e}")
    
    def export_bookmarks(self):
        """Export bookmarks."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Bookmarks", "bookmarks.json", "JSON Files (*.json);;HTML Files (*.html)"
        )
        
        if file_path:
            format = "json" if file_path.endswith('.json') else "html"
            try:
                self.bookmark_manager.export_bookmarks(file_path, format)
                QMessageBox.information(self, "Success", "Bookmarks exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export bookmarks: {e}")
    
    def open_bookmark(self, bookmark: BookmarkItem):
        """Open bookmark in browser."""
        if bookmark.url:
            # Would open in browser
            print(f"Opening bookmark: {bookmark.url}")


class HistoryManagerDialog(QDialog):
    """Main history manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History Manager")
        self.resize(800, 600)
        self.history_manager = HistoryManager(self)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search
        search_label = QLabel("Search:")
        toolbar_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search history...")
        self.search_edit.textChanged.connect(self.search_history)
        toolbar_layout.addWidget(self.search_edit)
        
        toolbar_layout.addStretch()
        
        # Clear history button
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        toolbar_layout.addWidget(clear_btn)
        
        layout.addWidget(toolbar)
        
        # History list
        self.history_list = HistoryListWidget()
        self.history_list.set_history_manager(self.history_manager)
        self.history_list.history_double_clicked.connect(self.open_history_item)
        layout.addWidget(self.history_list)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def search_history(self, query: str):
        """Search history."""
        if query:
            results = self.history_manager.search_history(query)
            self.history_list.clear()
            for item in results:
                self.history_list.add_history_item(item)
        else:
            self.history_list.refresh_list()
    
    def clear_history(self):
        """Clear history."""
        days, ok = QInputDialog.getInt(
            self, "Clear History", 
            "Clear history older than how many days?", 30, 1, 365
        )
        
        if ok:
            reply = QMessageBox.question(
                self, "Clear History",
                f"Are you sure you want to clear history older than {days} days?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.history_manager.clear_history(older_than_days=days)
                self.history_list.refresh_list()
    
    def open_history_item(self, item: HistoryItem):
        """Open history item in browser."""
        if item.url:
            # Would open in browser
            print(f"Opening history item: {item.url}")
