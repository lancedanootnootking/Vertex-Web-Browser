#!/usr/bin/env python3.12
"""
Download Manager UI Components

Comprehensive UI for managing downloads, queue, and settings.
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
                             QDateTimeEdit, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QSortFilterProxyModel, QDateTime
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QPainter, QColor

from frontend.themes.modern_theme import theme, style_manager, ui_components
from backend.advanced_download_manager import (DownloadManager, DownloadItem, DownloadState, 
                                             DownloadPriority, DownloadQueue)


class DownloadItemWidget(QWidget):
    """Widget for displaying download item."""
    
    def __init__(self, download_item: DownloadItem, parent=None):
        super().__init__(parent)
        self.download_item = download_item
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Filename
        self.filename_label = QLabel()
        self.filename_label.setProperty("class", "download_filename")
        self.filename_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.filename_label)
        
        header_layout.addStretch()
        
        # File size
        self.size_label = QLabel()
        self.size_label.setProperty("class", "download_size")
        header_layout.addWidget(self.size_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setProperty("class", "download_progress")
        layout.addWidget(self.progress_bar)
        
        # Details
        details_layout = QHBoxLayout()
        
        # Speed
        self.speed_label = QLabel()
        self.speed_label.setProperty("class", "download_speed")
        details_layout.addWidget(self.speed_label)
        
        details_layout.addStretch()
        
        # ETA
        self.eta_label = QLabel()
        self.eta_label.setProperty("class", "download_eta")
        details_layout.addWidget(self.eta_label)
        
        details_layout.addStretch()
        
        # Status
        self.status_label = QLabel()
        self.status_label.setProperty("class", "download_status")
        details_layout.addWidget(self.status_label)
        
        layout.addLayout(details_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Pause/Resume button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "danger")
        self.cancel_btn.clicked.connect(self.cancel_download)
        controls_layout.addWidget(self.cancel_btn)
        
        # Retry button (for failed downloads)
        self.retry_btn = QPushButton("Retry")
        self.retry_btn.clicked.connect(self.retry_download)
        self.retry_btn.setVisible(False)
        controls_layout.addWidget(self.retry_btn)
        
        # Open button (for completed downloads)
        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self.open_file)
        self.open_btn.setVisible(False)
        controls_layout.addWidget(self.open_btn)
        
        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_download)
        controls_layout.addWidget(self.remove_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Apply styling
        self.setProperty("class", "download_item")
        style_manager.apply_stylesheet(self, "card")
    
    def update_display(self):
        """Update display with current download state."""
        # Update filename
        self.filename_label.setText(self.download_item.filename)
        
        # Update size
        size_text = self._format_bytes(self.download_item.file_size)
        if self.download_item.downloaded_bytes > 0:
            size_text += f" / {self._format_bytes(self.download_item.downloaded_bytes)}"
        self.size_label.setText(size_text)
        
        # Update progress bar
        self.progress_bar.setValue(int(self.download_item.progress))
        
        # Update speed
        if self.download_item.is_active:
            speed_text = f"{self._format_bytes(int(self.download_item.speed))}/s"
        else:
            speed_text = ""
        self.speed_label.setText(speed_text)
        
        # Update ETA
        if self.download_item.is_active and self.download_item.eta > 0:
            eta_text = f"ETA: {self._format_time(self.download_item.eta)}"
        else:
            eta_text = ""
        self.eta_label.setText(eta_text)
        
        # Update status
        status_text = self.download_item.state.value.replace('_', ' ').title()
        if self.download_item.error_message:
            status_text += f" ({self.download_item.error_message})"
        self.status_label.setText(status_text)
        
        # Update buttons based on state
        self.pause_btn.setVisible(self.download_item.state == DownloadState.DOWNLOADING)
        self.retry_btn.setVisible(self.download_item.state == DownloadState.FAILED)
        self.open_btn.setVisible(self.download_item.state == DownloadState.COMPLETED)
        self.cancel_btn.setVisible(self.download_item.state in [DownloadState.DOWNLOADING, DownloadState.PENDING])
        self.remove_btn.setVisible(self.download_item.is_finished)
        
        # Update pause button text
        if self.download_item.state == DownloadState.DOWNLOADING:
            self.pause_btn.setText("Pause")
        elif self.download_item.state == DownloadState.PAUSED:
            self.pause_btn.setText("Resume")
    
    def toggle_pause(self):
        """Toggle pause/resume."""
        if self.download_item.state == DownloadState.DOWNLOADING:
            self.parent().parent().parent().manager.pause_download(self.download_item.id)
        elif self.download_item.state == DownloadState.PAUSED:
            self.parent().parent().parent().manager.resume_download(self.download_item.id)
    
    def cancel_download(self):
        """Cancel download."""
        reply = QMessageBox.question(
            self, "Cancel Download",
            f"Are you sure you want to cancel '{self.download_item.filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent().parent().parent().manager.cancel_download(self.download_item.id)
    
    def retry_download(self):
        """Retry failed download."""
        self.parent().parent().parent().manager.retry_download(self.download_item.id)
    
    def open_file(self):
        """Open downloaded file."""
        if self.download_item.full_path.exists():
            os.startfile(str(self.download_item.full_path))  # Windows
            # On other platforms, you would use different methods
    
    def remove_download(self):
        """Remove download from list."""
        reply = QMessageBox.question(
            self, "Remove Download",
            f"Are you sure you want to remove '{self.download_item.filename}' from the list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent().parent().parent().manager.remove_download(self.download_item)
            self.parent().removeItemWidget(self)
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes as human readable string."""
        if bytes_count == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        
        while bytes_count >= 1024 and unit_index < len(units) - 1:
            bytes_count /= 1024
            unit_index += 1
        
        return f"{bytes_count:.1f} {units[unit_index]}"
    
    def _format_time(self, seconds: int) -> str:
        """Format time as human readable string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class DownloadsListWidget(QScrollArea):
    """Widget for displaying downloads list."""
    
    def __init__(self, manager: DownloadManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.download_widgets = {}
        self.filter_state = None
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container widget
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(5, 5, 5, 5)
        self.container_layout.setSpacing(10)
        
        self.setWidget(self.container)
        
        # Apply styling
        self.setProperty("class", "downloads_list")
        style_manager.apply_stylesheet(self, "scroll_area")
    
    def connect_signals(self):
        """Connect manager signals."""
        self.manager.download_added.connect(self.add_download)
        self.manager.download_updated.connect(self.update_download)
        self.manager.download_completed.connect(self.on_download_completed)
        self.manager.download_failed.connect(self.on_download_failed)
    
    def add_download(self, download_item: DownloadItem):
        """Add download to list."""
        widget = DownloadItemWidget(download_item, self)
        self.download_widgets[download_item.id] = widget
        self.container_layout.addWidget(widget)
        
        # Apply filter if active
        if self.filter_state:
            self.apply_filter()
    
    def update_download(self, download_item: DownloadItem):
        """Update download display."""
        widget = self.download_widgets.get(download_item.id)
        if widget:
            widget.update_display()
    
    def on_download_completed(self, download_item: DownloadItem):
        """Handle download completion."""
        self.update_download(download_item)
        # Could show notification here
    
    def on_download_failed(self, download_item: DownloadItem, error: str):
        """Handle download failure."""
        self.update_download(download_item)
        # Could show error notification here
    
    def remove_download(self, download_item: DownloadItem):
        """Remove download from list."""
        widget = self.download_widgets.get(download_item.id)
        if widget:
            self.container_layout.removeWidget(widget)
            widget.deleteLater()
            del self.download_widgets[download_item.id]
    
    def set_filter(self, state: DownloadState = None):
        """Set filter for downloads."""
        self.filter_state = state
        self.apply_filter()
    
    def apply_filter(self):
        """Apply current filter."""
        for download_id, widget in self.download_widgets.items():
            widget.setVisible(
                self.filter_state is None or 
                widget.download_item.state == self.filter_state
            )
    
    def clear_completed(self):
        """Clear completed downloads."""
        completed_downloads = [
            d for d in self.manager.get_downloads() 
            if d.state == DownloadState.COMPLETED
        ]
        
        reply = QMessageBox.question(
            self, "Clear Completed",
            f"Remove {len(completed_downloads)} completed downloads?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for download in completed_downloads:
                self.manager.remove_download(download)


class QueueWidget(QWidget):
    """Widget for managing download queue."""
    
    def __init__(self, manager: DownloadManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Queue status
        status_group = QGroupBox("Queue Status")
        status_layout = QFormLayout(status_group)
        
        self.total_downloads_label = QLabel("0")
        status_layout.addRow("Total Downloads:", self.total_downloads_label)
        
        self.active_downloads_label = QLabel("0")
        status_layout.addRow("Active Downloads:", self.active_downloads_label)
        
        self.queued_downloads_label = QLabel("0")
        status_layout.addRow("Queued Downloads:", self.queued_downloads_label)
        
        self.max_concurrent_label = QLabel("3")
        status_layout.addRow("Max Concurrent:", self.max_concurrent_label)
        
        layout.addWidget(status_group)
        
        # Queue settings
        settings_group = QGroupBox("Queue Settings")
        settings_layout = QFormLayout(settings_group)
        
        # Max concurrent downloads
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(3)
        self.max_concurrent_spin.valueChanged.connect(self.on_max_concurrent_changed)
        settings_layout.addRow("Max Concurrent:", self.max_concurrent_spin)
        
        layout.addWidget(settings_group)
        
        # Speed limits
        speed_group = QGroupBox("Speed Limits")
        speed_layout = QVBoxLayout(speed_group)
        
        # Default speed limit
        default_layout = QHBoxLayout()
        default_label = QLabel("Default:")
        default_layout.addWidget(default_label)
        
        self.default_speed_spin = QSpinBox()
        self.default_speed_spin.setRange(0, 10000000)  # Up to 10 MB/s
        self.default_speed_spin.setSuffix(" KB/s")
        self.default_speed_spin.setValue(0)
        self.default_speed_spin.valueChanged.connect(self.on_speed_limit_changed)
        default_layout.addWidget(self.default_speed_spin)
        
        default_layout.addStretch()
        speed_layout.addLayout(default_layout)
        
        # WiFi speed limit
        wifi_layout = QHBoxLayout()
        wifi_label = QLabel("WiFi:")
        wifi_layout.addWidget(wifi_label)
        
        self.wifi_speed_spin = QSpinBox()
        self.wifi_speed_spin.setRange(0, 10000000)
        self.wifi_speed_spin.setSuffix(" KB/s")
        self.wifi_speed_spin.setValue(0)
        self.wifi_speed_spin.valueChanged.connect(self.on_wifi_speed_changed)
        wifi_layout.addWidget(self.wifi_speed_spin)
        
        wifi_layout.addStretch()
        speed_layout.addLayout(wifi_layout)
        
        # Mobile speed limit
        mobile_layout = QHBoxLayout()
        mobile_label = QLabel("Mobile:")
        mobile_layout.addWidget(mobile_label)
        
        self.mobile_speed_spin = QSpinBox()
        self.mobile_speed_spin.setRange(0, 10000000)
        self.mobile_speed_spin.setSuffix(" KB/s")
        self.mobile_speed_spin.setValue(0)
        self.mobile_speed_spin.valueChanged.connect(self.on_mobile_speed_changed)
        mobile_layout.addWidget(self.mobile_speed_spin)
        
        mobile_layout.addStretch()
        speed_layout.addLayout(mobile_layout)
        
        layout.addWidget(speed_group)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def update_status(self):
        """Update queue status display."""
        status = self.manager.get_queue_status()
        
        self.total_downloads_label.setText(str(status['total_downloads']))
        self.active_downloads_label.setText(str(status['active_downloads']))
        self.queued_downloads_label.setText(str(status['queued_downloads']))
        self.max_concurrent_label.setText(str(status['max_concurrent']))
    
    def on_max_concurrent_changed(self, value: int):
        """Handle max concurrent change."""
        self.manager.set_max_concurrent(value)
    
    def on_speed_limit_changed(self, value: int):
        """Handle default speed limit change."""
        self.manager.set_speed_limit(value * 1024 if value > 0 else None, 'default')
    
    def on_wifi_speed_changed(self, value: int):
        """Handle WiFi speed limit change."""
        self.manager.set_speed_limit(value * 1024 if value > 0 else None, 'wifi')
    
    def on_mobile_speed_changed(self, value: int):
        """Handle mobile speed limit change."""
        self.manager.set_speed_limit(value * 1024 if value > 0 else None, 'mobile')


class HistoryWidget(QWidget):
    """Widget for download history."""
    
    def __init__(self, manager: DownloadManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Export button
        export_btn = QPushButton("Export History")
        export_btn.clicked.connect(self.export_history)
        toolbar_layout.addWidget(export_btn)
        
        # Import button
        import_btn = QPushButton("Import History")
        import_btn.clicked.connect(self.import_history)
        toolbar_layout.addWidget(import_btn)
        
        # Clear history button
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        toolbar_layout.addWidget(clear_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Filename", "Size", "Date", "Status", "Speed", "Duration"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.history_table)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def load_history(self):
        """Load download history."""
        downloads = self.manager.get_downloads()
        
        self.history_table.setRowCount(0)
        
        for download in downloads:
            if download.is_finished:
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                # Filename
                filename_item = QTableWidgetItem(download.filename)
                self.history_table.setItem(row, 0, filename_item)
                
                # Size
                size_text = self._format_bytes(download.file_size)
                size_item = QTableWidgetItem(size_text)
                self.history_table.setItem(row, 1, size_item)
                
                # Date
                date_text = download.created_at.strftime('%Y-%m-%d %H:%M')
                date_item = QTableWidgetItem(date_text)
                self.history_table.setItem(row, 2, date_item)
                
                # Status
                status_item = QTableWidgetItem(download.state.value.title())
                self.history_table.setItem(row, 3, status_item)
                
                # Speed
                speed_text = f"{self._format_bytes(int(download.speed))}/s" if download.speed > 0 else "N/A"
                speed_item = QTableWidgetItem(speed_text)
                self.history_table.setItem(row, 4, speed_item)
                
                # Duration
                duration = "N/A"
                if download.started_at and download.completed_at:
                    duration_seconds = (download.completed_at - download.started_at).total_seconds()
                    duration = self._format_duration(int(duration_seconds))
                duration_item = QTableWidgetItem(duration)
                self.history_table.setItem(row, 5, duration_item)
        
        # Resize columns
        self.history_table.resizeColumnsToContents()
    
    def export_history(self):
        """Export download history."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "download_history.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.manager.export_downloads(file_path)
                QMessageBox.information(self, "Success", "History exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export history: {e}")
    
    def import_history(self):
        """Import download history."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import History", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.manager.import_downloads(file_path)
                self.load_history()
                QMessageBox.information(self, "Success", "History imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import history: {e}")
    
    def clear_history(self):
        """Clear download history."""
        days, ok = QInputDialog.getInt(
            self, "Clear History", 
            "Clear downloads older than how many days?", 30, 1, 365
        )
        
        if ok:
            reply = QMessageBox.question(
                self, "Clear History",
                f"Are you sure you want to clear downloads older than {days} days?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.manager.clear_history(days)
                self.load_history()
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes as human readable string."""
        if bytes_count == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        
        while bytes_count >= 1024 and unit_index < len(units) - 1:
            bytes_count /= 1024
            unit_index += 1
        
        return f"{bytes_count:.1f} {units[unit_index]}"
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration as human readable string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class DownloadManagerDialog(QDialog):
    """Main download manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.resize(1000, 700)
        self.manager = DownloadManager(self)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # New download button
        new_btn = QPushButton("New Download")
        new_btn.clicked.connect(self.new_download)
        toolbar_layout.addWidget(new_btn)
        
        # Clear completed button
        clear_btn = QPushButton("Clear Completed")
        clear_btn.clicked.connect(self.clear_completed)
        toolbar_layout.addWidget(clear_btn)
        
        toolbar_layout.addStretch()
        
        # Filter combo
        filter_label = QLabel("Filter:")
        toolbar_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Downloading", "Paused", "Completed", "Failed"])
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        toolbar_layout.addWidget(self.filter_combo)
        
        layout.addWidget(toolbar)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Downloads tab
        downloads_widget = QWidget()
        downloads_layout = QVBoxLayout(downloads_widget)
        
        self.downloads_list = DownloadsListWidget(self.manager)
        downloads_layout.addWidget(self.downloads_list)
        
        tab_widget.addTab(downloads_widget, "Downloads")
        
        # Queue tab
        queue_widget = QueueWidget(self.manager)
        tab_widget.addTab(queue_widget, "Queue")
        
        # History tab
        history_widget = HistoryWidget(self.manager)
        tab_widget.addTab(history_widget, "History")
        
        layout.addWidget(tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def new_download(self):
        """Create new download."""
        dialog = QDialog(self)
        dialog.setWindowTitle("New Download")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # URL
        url_layout = QFormLayout()
        url_edit = QLineEdit()
        url_edit.setPlaceholderText("Enter download URL...")
        url_layout.addRow("URL:", url_edit)
        layout.addLayout(url_layout)
        
        # Filename
        filename_layout = QFormLayout()
        filename_edit = QLineEdit()
        filename_edit.setPlaceholderText("Optional: custom filename...")
        filename_layout.addRow("Filename:", filename_edit)
        layout.addLayout(filename_layout)
        
        # Download directory
        dir_layout = QFormLayout()
        dir_edit = QLineEdit()
        dir_edit.setText(str(Path.home() / "Downloads"))
        dir_edit.setReadOnly(True)
        dir_btn = QPushButton("Browse...")
        dir_btn.clicked.connect(lambda: self.select_directory(dir_edit))
        dir_layout.addRow("Directory:", dir_edit)
        dir_layout.addRow("", dir_btn)
        layout.addLayout(dir_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = url_edit.text().strip()
            filename = filename_edit.text().strip() or None
            directory = Path(dir_edit.text())
            
            if url:
                self.manager.create_download(url, filename, directory)
    
    def select_directory(self, line_edit: QLineEdit):
        """Select download directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            line_edit.setText(directory)
    
    def clear_completed(self):
        """Clear completed downloads."""
        self.downloads_list.clear_completed()
    
    def on_filter_changed(self, filter_text: str):
        """Handle filter change."""
        filter_map = {
            "All": None,
            "Downloading": DownloadState.DOWNLOADING,
            "Paused": DownloadState.PAUSED,
            "Completed": DownloadState.COMPLETED,
            "Failed": DownloadState.FAILED
        }
        
        state = filter_map.get(filter_text)
        self.downloads_list.set_filter(state)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop manager
        self.manager.download_queue.stop()
        event.accept()
