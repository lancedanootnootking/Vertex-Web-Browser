#!/usr/bin/env python3.12
"""
Advanced History Panel with Modern UI

Comprehensive browsing history management with modern blue/grey theme,
search functionality, timeline view, and beautiful UI.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QMenu, QToolBar, QComboBox, QCheckBox, QGroupBox, 
                             QFormLayout, QDialogButtonBox, QFrame, QMessageBox, 
                             QSpinBox, QSlider, QSplitter, QTextEdit, QCalendarWidget, 
                             QDateEdit, QProgressBar, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QDate, QDateTime
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QKeySequence, QPainter, QColor, QLinearGradient
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import urllib.parse

from frontend.themes.modern_theme import theme, style_manager, ui_components


class HistoryItem:
    """Represents a single history item."""
    
    def __init__(self, url: str, title: str, timestamp: str, visits: int = 1):
        self.url = url
        self.title = title
        self.timestamp = timestamp
        self.visits = visits
        self.id = f"history_{timestamp}_{hash(url)}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'timestamp': self.timestamp,
            'visits': self.visits
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HistoryItem':
        """Create from dictionary."""
        item = cls(data['url'], data['title'], data['timestamp'], data.get('visits', 1))
        item.id = data.get('id', f"history_{data['timestamp']}_{hash(data['url'])}")
        return item


class HistoryStatistics:
    """History statistics calculator."""
    
    def __init__(self, history_items: List[HistoryItem]):
        self.history_items = history_items
        self._calculate_stats()
    
    def _calculate_stats(self):
        """Calculate various statistics."""
        self.total_visits = sum(item.visits for item in self.history_items)
        self.unique_domains = len(set(self._extract_domain(item.url) for item in self.history_items))
        self.most_visited = self._get_most_visited()
        self.recent_activity = self._get_recent_activity()
        self.daily_stats = self._get_daily_stats()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def _get_most_visited(self, limit: int = 10) -> List[HistoryItem]:
        """Get most visited pages."""
        return sorted(self.history_items, key=lambda x: x.visits, reverse=True)[:limit]
    
    def _get_recent_activity(self, days: int = 7) -> List[HistoryItem]:
        """Get recent activity."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_date.isoformat()
        
        return [item for item in self.history_items 
                if item.timestamp >= cutoff_timestamp]
    
    def _get_daily_stats(self) -> Dict[str, int]:
        """Get daily visit statistics."""
        daily_counts = {}
        
        for item in self.history_items:
            date = item.timestamp.split('T')[0]
            daily_counts[date] = daily_counts.get(date, 0) + item.visits
        
        return daily_counts


class HistoryTimelineWidget(QWidget):
    """Timeline widget for visualizing history."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_items = []
        self.selected_date = QDate.currentDate()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the timeline UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme.get_spacing('md'))
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.calendar.clicked.connect(self.on_date_selected)
        style_manager.apply_stylesheet(self.calendar, "widget")
        layout.addWidget(self.calendar)
        
        # Date range selector
        range_widget = QFrame()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        
        range_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        style_manager.apply_stylesheet(self.from_date, "combo_box")
        range_layout.addWidget(self.from_date)
        
        range_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        style_manager.apply_stylesheet(self.to_date, "combo_box")
        range_layout.addWidget(self.to_date)
        
        apply_btn = ui_components.create_modern_button("Apply", "primary")
        apply_btn.clicked.connect(self.apply_date_range)
        range_layout.addWidget(apply_btn)
        
        layout.addWidget(range_widget)
        
        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setProperty("class", "caption")
        style_manager.apply_stylesheet(self.stats_label, "label")
        layout.addWidget(self.stats_label)
    
    def set_history_items(self, items: List[HistoryItem]):
        """Set history items."""
        self.history_items = items
        self.update_statistics()
    
    def on_date_selected(self, date: QDate):
        """Handle date selection."""
        self.selected_date = date
        self.emit_date_changed()
    
    def apply_date_range(self):
        """Apply date range filter."""
        self.emit_date_changed()
    
    def emit_date_changed(self):
        """Emit date changed signal."""
        # This would be connected to the main dialog
        pass
    
    def update_statistics(self):
        """Update statistics display."""
        if not self.history_items:
            self.stats_label.setText("No history data")
            return
        
        stats = HistoryStatistics(self.history_items)
        
        text = f"Total visits: {stats.total_visits} | "
        text += f"Unique domains: {stats.unique_domains} | "
        text += f"Date range: {len(stats.daily_stats)} days"
        
        self.stats_label.setText(text)


class HistoryChartWidget(QWidget):
    """Chart widget for visualizing history statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.daily_stats = {}
        self.setMinimumHeight(200)
        self.setMaximumHeight(300)
    
    def set_daily_stats(self, stats: Dict[str, int]):
        """Set daily statistics."""
        self.daily_stats = stats
        self.update()
    
    def paintEvent(self, event):
        """Paint the chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.daily_stats:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data to display")
            return
        
        # Draw simple bar chart
        self.draw_bar_chart(painter)
    
    def draw_bar_chart(self, painter: QPainter):
        """Draw a simple bar chart."""
        rect = self.rect()
        margin = 40
        chart_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Get data
        dates = sorted(self.daily_stats.keys())[-30:]  # Last 30 days
        values = [self.daily_stats[date] for date in dates]
        
        if not values:
            return
        
        max_value = max(values) if values else 1
        
        # Draw axes
        painter.setPen(QColor(theme.get_color('border_grey')))
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), 
                       chart_rect.right(), chart_rect.bottom())
        painter.drawLine(chart_rect.left(), chart_rect.top(), 
                       chart_rect.left(), chart_rect.bottom())
        
        # Draw bars
        bar_width = chart_rect.width() / len(dates) if dates else 1
        bar_spacing = bar_width * 0.2
        
        for i, (date, value) in enumerate(zip(dates, values)):
            if max_value > 0:
                bar_height = (value / max_value) * (chart_rect.height() - 20)
            else:
                bar_height = 0
            
            bar_x = chart_rect.left() + i * bar_width + bar_spacing / 2
            bar_y = chart_rect.bottom() - bar_height
            
            # Draw bar with gradient
            gradient = QLinearGradient(0, bar_y, 0, chart_rect.bottom())
            gradient.setColorAt(0, QColor(theme.get_color('primary_blue')))
            gradient.setColorAt(1, QColor(theme.get_color('primary_blue_dark')))
            
            painter.fillRect(int(bar_x), int(bar_y), int(bar_width - bar_spacing), int(bar_height), gradient)


class HistoryManagerDialog(QDialog):
    """Advanced history manager with modern UI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History Manager")
        self.setGeometry(200, 200, 1400, 900)
        self.setModal(False)
        
        # Apply modern theme
        style_manager.apply_stylesheet(self, "dialog")
        
        # Data
        self.history_items = []
        self.filtered_items = []
        
        # Setup UI
        self.setup_ui()
        self.load_history()
        
        # Setup search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
    
    def setup_ui(self):
        """Setup the history manager UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.create_toolbar(layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left panel - timeline and filters
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - history list
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter sizes
        content_splitter.setSizes([400, 1000])
        
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
        
        # Clear history button
        self.clear_btn = ui_components.create_modern_button("Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        toolbar_layout.addWidget(self.clear_btn)
        
        # Export button
        self.export_btn = ui_components.create_modern_button("Export")
        self.export_btn.clicked.connect(self.export_history)
        toolbar_layout.addWidget(self.export_btn)
        
        # Import button
        self.import_btn = ui_components.create_modern_button("Import")
        self.import_btn.clicked.connect(self.import_history)
        toolbar_layout.addWidget(self.import_btn)
        
        # Separator
        separator = ui_components.create_modern_separator("vertical")
        toolbar_layout.addWidget(separator)
        
        # Time range selector
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
        self.time_range_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.time_range_combo, "combo_box")
        self.time_range_combo.currentTextChanged.connect(self.on_time_range_changed)
        toolbar_layout.addWidget(self.time_range_combo)
        
        # Group by selector
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItems(["No Grouping", "Group by Date", "Group by Site", "Group by Most Visited"])
        self.group_by_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.group_by_combo, "combo_box")
        self.group_by_combo.currentTextChanged.connect(self.on_group_by_changed)
        toolbar_layout.addWidget(self.group_by_combo)
        
        # Sort by selector
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItems(["Sort by Date", "Sort by Title", "Sort by URL", "Sort by Visits"])
        self.sort_by_combo.setMinimumHeight(36)
        style_manager.apply_stylesheet(self.sort_by_combo, "combo_box")
        self.sort_by_combo.currentTextChanged.connect(self.on_sort_by_changed)
        toolbar_layout.addWidget(self.sort_by_combo)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search history...")
        self.search_edit.setMinimumHeight(36)
        self.search_edit.setMaximumWidth(300)
        style_manager.apply_stylesheet(self.search_edit, "address_bar")
        self.search_edit.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_edit)
        
        parent_layout.addWidget(toolbar_container)
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with timeline and statistics."""
        left_panel = QWidget()
        left_panel.setMaximumWidth(450)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                     theme.get_spacing('md'), theme.get_spacing('md'))
        left_layout.setSpacing(theme.get_spacing('md'))
        
        # Timeline section
        timeline_group = QGroupBox("Timeline")
        timeline_layout = QVBoxLayout(timeline_group)
        style_manager.apply_stylesheet(timeline_group, "group_box")
        
        self.timeline_widget = HistoryTimelineWidget()
        timeline_layout.addWidget(self.timeline_widget)
        
        left_layout.addWidget(timeline_group)
        
        # Chart section
        chart_group = QGroupBox("Activity Chart")
        chart_layout = QVBoxLayout(chart_group)
        style_manager.apply_stylesheet(chart_group, "group_box")
        
        self.chart_widget = HistoryChartWidget()
        chart_layout.addWidget(self.chart_widget)
        
        left_layout.addWidget(chart_group)
        
        # Statistics section
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        style_manager.apply_stylesheet(stats_group, "group_box")
        
        self.total_visits_label = QLabel("0")
        self.unique_sites_label = QLabel("0")
        self.avg_daily_label = QLabel("0")
        self.most_visited_label = QLabel("None")
        
        stats_layout.addRow("Total Visits:", self.total_visits_label)
        stats_layout.addRow("Unique Sites:", self.unique_sites_label)
        stats_layout.addRow("Daily Average:", self.avg_daily_label)
        stats_layout.addRow("Most Visited:", self.most_visited_label)
        
        left_layout.addWidget(stats_group)
        
        # Quick filters
        filters_group = QGroupBox("Quick Filters")
        filters_layout = QVBoxLayout(filters_group)
        style_manager.apply_stylesheet(filters_group, "group_box")
        
        # Today checkbox
        self.today_checkbox = QCheckBox("Show only today")
        self.today_checkbox.stateChanged.connect(self.on_quick_filter_changed)
        style_manager.apply_stylesheet(self.today_checkbox, "checkbox")
        filters_layout.addWidget(self.today_checkbox)
        
        # Most visited checkbox
        self.most_visited_checkbox = QCheckBox("Show most visited only")
        self.most_visited_checkbox.stateChanged.connect(self.on_quick_filter_changed)
        style_manager.apply_stylesheet(self.most_visited_checkbox, "checkbox")
        filters_layout.addWidget(self.most_visited_checkbox)
        
        # Private browsing checkbox
        self.private_checkbox = QCheckBox("Exclude private browsing")
        self.private_checkbox.setChecked(True)
        self.private_checkbox.stateChanged.connect(self.on_quick_filter_changed)
        style_manager.apply_stylesheet(self.private_checkbox, "checkbox")
        filters_layout.addWidget(self.private_checkbox)
        
        left_layout.addWidget(filters_group)
        
        return left_panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with history list."""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(theme.get_spacing('md'), theme.get_spacing('md'), 
                                      theme.get_spacing('md'), theme.get_spacing('md'))
        right_layout.setSpacing(theme.get_spacing('md'))
        
        # History list
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Title", "URL", "Visits", "Last Visited"])
        self.history_tree.setRootIsDecorated(True)
        self.history_tree.setAlternatingRowColors(True)
        self.history_tree.setSortingEnabled(True)
        style_manager.apply_stylesheet(self.history_tree, "tree_widget")
        
        # Connect signals
        self.history_tree.itemDoubleClicked.connect(self.open_history_item)
        self.history_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        right_layout.addWidget(self.history_tree)
        
        # Details panel
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        style_manager.apply_stylesheet(details_group, "group_box")
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(120)
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
    
    def load_history(self):
        """Load history from storage."""
        try:
            history_file = Path.home() / '.vertex_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.history_items = [HistoryItem.from_dict(item) for item in history_data]
            else:
                # Create sample history
                self.history_items = self.create_sample_history()
                self.save_history()
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history_items = []
        
        self.filtered_items = self.history_items.copy()
        self.update_ui()
    
    def create_sample_history(self) -> List[HistoryItem]:
        """Create sample history for demonstration."""
        base_time = datetime.now()
        sample_items = []
        
        # Generate sample history for the last few days
        for i in range(50):
            days_ago = i % 30
            hours_ago = i % 24
            timestamp = (base_time - timedelta(days=days_ago, hours=hours_ago)).isoformat()
            
            sample_sites = [
                ("https://duckduckgo.com", "DuckDuckGo"),
                ("https://github.com", "GitHub"),
                ("https://stackoverflow.com", "Stack Overflow"),
                ("https://www.python.org", "Python.org"),
                ("https://docs.qt.io", "Qt Documentation"),
                ("https://developer.mozilla.org", "MDN Web Docs"),
                ("https://www.reddit.com", "Reddit"),
                ("https://news.ycombinator.com", "Hacker News"),
            ]
            
            url, title = sample_sites[i % len(sample_sites)]
            visits = (i % 5) + 1
            
            item = HistoryItem(url, title, timestamp, visits)
            sample_items.append(item)
        
        return sample_items
    
    def save_history(self):
        """Save history to file."""
        try:
            history_file = Path.home() / '.vertex_history.json'
            history_data = [item.to_dict() for item in self.history_items]
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def update_ui(self):
        """Update all UI elements."""
        self.populate_history_list()
        self.update_statistics()
        self.update_timeline()
        self.update_chart()
    
    def populate_history_list(self):
        """Populate the history list."""
        self.history_tree.clear()
        
        if not self.filtered_items:
            return
        
        # Group items if needed
        group_by = self.group_by_combo.currentText()
        if group_by == "Group by Date":
            self.populate_by_date()
        elif group_by == "Group by Site":
            self.populate_by_site()
        elif group_by == "Group by Most Visited":
            self.populate_by_visits()
        else:
            self.populate_flat()
        
        # Resize columns
        for i in range(self.history_tree.columnCount()):
            self.history_tree.resizeColumnToContents(i)
    
    def populate_flat(self):
        """Populate flat list."""
        for item in self.filtered_items:
            tree_item = QTreeWidgetItem(self.history_tree)
            tree_item.setText(0, item.title)
            tree_item.setText(1, item.url)
            tree_item.setText(2, str(item.visits))
            tree_item.setText(3, self.format_timestamp(item.timestamp))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item)
    
    def populate_by_date(self):
        """Populate grouped by date."""
        from collections import defaultdict
        
        grouped = defaultdict(list)
        for item in self.filtered_items:
            date = item.timestamp.split('T')[0]
            grouped[date].append(item)
        
        for date in sorted(grouped.keys(), reverse=True):
            date_item = QTreeWidgetItem(self.history_tree, [date, "", "", ""])
            date_item.setExpanded(True)
            
            for item in sorted(grouped[date], key=lambda x: x.timestamp, reverse=True):
                item_widget = QTreeWidgetItem(date_item)
                item_widget.setText(0, item.title)
                item_widget.setText(1, item.url)
                item_widget.setText(2, str(item.visits))
                item_widget.setText(3, item.timestamp.split('T')[1][:5])
                item_widget.setData(0, Qt.ItemDataRole.UserRole, item)
    
    def populate_by_site(self):
        """Populate grouped by site."""
        from collections import defaultdict
        
        grouped = defaultdict(list)
        for item in self.filtered_items:
            try:
                domain = urllib.parse.urlparse(item.url).netloc
                grouped[domain].append(item)
            except:
                grouped["unknown"].append(item)
        
        for domain in sorted(grouped.keys()):
            domain_item = QTreeWidgetItem(self.history_tree, [domain, "", "", ""])
            domain_item.setExpanded(True)
            
            for item in sorted(grouped[domain], key=lambda x: x.timestamp, reverse=True):
                item_widget = QTreeWidgetItem(domain_item)
                item_widget.setText(0, item.title)
                item_widget.setText(1, item.url)
                item_widget.setText(2, str(item.visits))
                item_widget.setText(3, self.format_timestamp(item.timestamp))
                item_widget.setData(0, Qt.ItemDataRole.UserRole, item)
    
    def populate_by_visits(self):
        """Populate grouped by visit count."""
        from collections import defaultdict
        
        grouped = defaultdict(list)
        for item in self.filtered_items:
            visits = item.visits
            if visits >= 10:
                group = "10+ visits"
            elif visits >= 5:
                group = "5-9 visits"
            elif visits >= 2:
                group = "2-4 visits"
            else:
                group = "1 visit"
            grouped[group].append(item)
        
        for group in ["10+ visits", "5-9 visits", "2-4 visits", "1 visit"]:
            if group in grouped:
                group_item = QTreeWidgetItem(self.history_tree, [group, "", "", ""])
                group_item.setExpanded(True)
                
                for item in sorted(grouped[group], key=lambda x: x.visits, reverse=True):
                    item_widget = QTreeWidgetItem(group_item)
                    item_widget.setText(0, item.title)
                    item_widget.setText(1, item.url)
                    item_widget.setText(2, str(item.visits))
                    item_widget.setText(3, self.format_timestamp(item.timestamp))
                    item_widget.setData(0, Qt.ItemDataRole.UserRole, item)
    
    def format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    return f"{diff.seconds // 60} minutes ago"
                else:
                    return f"{diff.seconds // 3600} hours ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return dt.strftime("%Y-%m-%d")
        except:
            return timestamp
    
    def update_statistics(self):
        """Update statistics display."""
        if not self.filtered_items:
            self.total_visits_label.setText("0")
            self.unique_sites_label.setText("0")
            self.avg_daily_label.setText("0")
            self.most_visited_label.setText("None")
            return
        
        stats = HistoryStatistics(self.filtered_items)
        
        self.total_visits_label.setText(str(stats.total_visits))
        self.unique_sites_label.setText(str(stats.unique_domains))
        
        # Calculate daily average
        if stats.daily_stats:
            avg_daily = sum(stats.daily_stats.values()) / len(stats.daily_stats)
            self.avg_daily_label.setText(f"{avg_daily:.1f}")
        else:
            self.avg_daily_label.setText("0")
        
        # Most visited
        if stats.most_visited:
            most_visited = stats.most_visited[0]
            self.most_visited_label.setText(f"{most_visited.title} ({most_visited.visits})")
        else:
            self.most_visited_label.setText("None")
    
    def update_timeline(self):
        """Update timeline widget."""
        self.timeline_widget.set_history_items(self.filtered_items)
    
    def update_chart(self):
        """Update chart widget."""
        if not self.filtered_items:
            self.chart_widget.set_daily_stats({})
            return
        
        stats = HistoryStatistics(self.filtered_items)
        self.chart_widget.set_daily_stats(stats.daily_stats)
    
    def on_search_changed(self, text):
        """Handle search text change."""
        self.search_timer.start(300)  # 300ms delay
    
    def perform_search(self):
        """Perform history search."""
        query = self.search_edit.text().strip().lower()
        
        if not query:
            self.apply_filters()
            return
        
        # Search in history items
        self.filtered_items = []
        for item in self.history_items:
            if (query in item.title.lower() or 
                query in item.url.lower()):
                self.filtered_items.append(item)
        
        # Apply additional filters
        self.apply_additional_filters()
        self.update_ui()
        
        self.status_label.setText(f"Found {len(self.filtered_items)} matching items")
    
    def on_time_range_changed(self, text):
        """Handle time range change."""
        self.apply_filters()
    
    def on_group_by_changed(self, text):
        """Handle group by change."""
        self.populate_history_list()
    
    def on_sort_by_changed(self, text):
        """Handle sort by change."""
        self.apply_filters()
    
    def on_quick_filter_changed(self):
        """Handle quick filter change."""
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all active filters."""
        self.filtered_items = self.history_items.copy()
        self.apply_additional_filters()
        self.apply_sorting()
        self.update_ui()
    
    def apply_additional_filters(self):
        """Apply additional filters."""
        # Time range filter
        time_range = self.time_range_combo.currentText()
        if time_range != "All Time":
            cutoff_date = self.get_cutoff_date(time_range)
            self.filtered_items = [item for item in self.filtered_items 
                                 if item.timestamp >= cutoff_date]
        
        # Quick filters
        if self.today_checkbox.isChecked():
            today = datetime.now().date().isoformat()
            self.filtered_items = [item for item in self.filtered_items 
                                 if item.timestamp.startswith(today)]
        
        if self.most_visited_checkbox.isChecked():
            self.filtered_items = [item for item in self.filtered_items if item.visits >= 5]
        
        # Note: Private browsing filter would need additional data
        # This is a placeholder implementation
        if self.private_checkbox.isChecked():
            # Filter out items marked as private (if such data exists)
            pass
    
    def apply_sorting(self):
        """Apply sorting."""
        sort_by = self.sort_by_combo.currentText()
        
        if sort_by == "Sort by Date":
            self.filtered_items.sort(key=lambda x: x.timestamp, reverse=True)
        elif sort_by == "Sort by Title":
            self.filtered_items.sort(key=lambda x: x.title.lower())
        elif sort_by == "Sort by URL":
            self.filtered_items.sort(key=lambda x: x.url.lower())
        elif sort_by == "Sort by Visits":
            self.filtered_items.sort(key=lambda x: x.visits, reverse=True)
    
    def get_cutoff_date(self, time_range: str) -> str:
        """Get cutoff date for time range."""
        now = datetime.now()
        
        if time_range == "Today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "Yesterday":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        elif time_range == "Last 7 Days":
            cutoff = now - timedelta(days=7)
        elif time_range == "Last 30 Days":
            cutoff = now - timedelta(days=30)
        elif time_range == "Last 90 Days":
            cutoff = now - timedelta(days=90)
        else:
            cutoff = datetime.min
        
        return cutoff.isoformat()
    
    def open_history_item(self, item: QTreeWidgetItem, column: int):
        """Open history item in browser."""
        history_item = item.data(0, Qt.ItemDataRole.UserRole)
        if history_item:
            # Open in system browser
            import webbrowser
            webbrowser.open(history_item.url)
            
            # Increment visit count
            history_item.visits += 1
            self.save_history()
            self.update_ui()
            
            self.status_label.setText(f"Opened: {history_item.title}")
    
    def show_context_menu(self, position):
        """Show context menu for history items."""
        item = self.history_tree.itemAt(position)
        if not item:
            return
        
        history_item = item.data(0, Qt.ItemDataRole.UserRole)
        if not history_item:
            return
        
        menu = QMenu(self)
        style_manager.apply_stylesheet(menu, "menu")
        
        # Actions
        open_action = menu.addAction("Open in Browser")
        open_action.triggered.connect(lambda: self.open_history_item(item, 0))
        
        open_new_tab_action = menu.addAction("Open in New Tab")
        open_new_tab_action.triggered.connect(lambda: self.open_in_new_tab(history_item))
        
        copy_url_action = menu.addAction("Copy URL")
        copy_url_action.triggered.connect(lambda: self.copy_url(history_item))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete from History")
        delete_action.triggered.connect(lambda: self.delete_history_item(history_item))
        
        menu.addSeparator()
        
        forget_action = menu.addAction("Forget This Site")
        forget_action.triggered.connect(lambda: self.forget_site(history_item.url))
        
        menu.exec(self.history_tree.mapToGlobal(position))
    
    def open_in_new_tab(self, history_item: HistoryItem):
        """Open history item in new tab."""
        # This would communicate with the main browser
        # For now, just open in system browser
        import webbrowser
        webbrowser.open(history_item.url)
        self.status_label.setText(f"Opened in new tab: {history_item.title}")
    
    def copy_url(self, history_item: HistoryItem):
        """Copy URL to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(history_item.url)
        self.status_label.setText("URL copied to clipboard")
    
    def delete_history_item(self, history_item: HistoryItem):
        """Delete history item."""
        reply = QMessageBox.question(
            self, "Delete History Item", 
            f"Are you sure you want to delete '{history_item.title}' from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_items = [item for item in self.history_items if item.id != history_item.id]
            self.save_history()
            self.apply_filters()
            self.status_label.setText(f"Deleted: {history_item.title}")
    
    def forget_site(self, url: str):
        """Remove all history for a site."""
        try:
            domain = urllib.parse.urlparse(url).netloc
        except:
            domain = url
        
        reply = QMessageBox.question(
            self, "Forget Site", 
            f"Are you sure you want to delete all history for '{domain}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            count_before = len(self.history_items)
            self.history_items = [item for item in self.history_items 
                               if domain not in item.url]
            count_deleted = count_before - len(self.history_items)
            self.save_history()
            self.apply_filters()
            self.status_label.setText(f"Deleted {count_deleted} items from {domain}")
    
    def clear_history(self):
        """Clear all history."""
        reply = QMessageBox.question(
            self, "Clear History", 
            "Are you sure you want to clear all browsing history? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_items = []
            self.save_history()
            self.apply_filters()
            self.status_label.setText("History cleared")
    
    def export_history(self):
        """Export history to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "history.json", "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                history_data = [item.to_dict() for item in self.history_items]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(history_data, f, indent=2, ensure_ascii=False)
                self.status_label.setText(f"Exported {len(self.history_items)} history items")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export history: {e}")
    
    def import_history(self):
        """Import history from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import History", "", "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                imported_items = [HistoryItem.from_dict(item) for item in imported_data]
                self.history_items.extend(imported_items)
                self.save_history()
                self.apply_filters()
                self.status_label.setText(f"Imported {len(imported_items)} history items")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import history: {e}")


def show_history_manager(parent=None):
    """Show the history manager dialog."""
    dialog = HistoryManagerDialog(parent)
    dialog.show()
    return dialog
