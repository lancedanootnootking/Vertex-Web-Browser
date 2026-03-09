#!/usr/bin/env python3.12
"""
Ad Blocker UI Components

Comprehensive UI for managing ad blocking, filter lists, and statistics.
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
                             QHeaderView, QAbstractItemView, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QSortFilterProxyModel
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette, QPainter, QColor

from frontend.themes.modern_theme import theme, style_manager, ui_components
from .advanced_ad_blocker import (AdBlockEngine, FilterList, FilterRule, FilterType, 
                                 BlockStatistics, RuleParser)


class FilterListUpdateThread(QThread):
    """Thread for updating filter lists."""
    
    progress = pyqtSignal(str, int)  # list_name, progress
    completed = pyqtSignal(str, bool)  # list_name, success
    all_completed = pyqtSignal(dict)  # results
    
    def __init__(self, engine: AdBlockEngine):
        super().__init__()
        self.engine = engine
    
    def run(self):
        """Update all filter lists."""
        results = {}
        
        filter_lists = list(self.engine.filter_lists.items())
        total = len(filter_lists)
        
        for i, (name, filter_list) in enumerate(filter_lists):
            if filter_list.url:
                self.progress.emit(name, int((i / total) * 100))
                
                try:
                    success = filter_list.update_from_url()
                    results[name] = success
                    self.completed.emit(name, success)
                except Exception as e:
                    results[name] = False
                    self.completed.emit(name, False)
        
        self.all_completed.emit(results)


class StatisticsWidget(QWidget):
    """Widget for displaying ad blocking statistics."""
    
    def __init__(self, engine: AdBlockEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Summary cards
        summary_layout = QHBoxLayout()
        
        # Total requests card
        total_card = QFrame()
        total_card.setProperty("class", "stat_card")
        total_layout = QVBoxLayout(total_card)
        
        total_label = QLabel("Total Requests")
        total_label.setProperty("class", "stat_label")
        total_layout.addWidget(total_label)
        
        self.total_value = QLabel("0")
        self.total_value.setProperty("class", "stat_value")
        total_layout.addWidget(self.total_value)
        
        summary_layout.addWidget(total_card)
        
        # Blocked requests card
        blocked_card = QFrame()
        blocked_card.setProperty("class", "stat_card")
        blocked_layout = QVBoxLayout(blocked_card)
        
        blocked_label = QLabel("Blocked")
        blocked_label.setProperty("class", "stat_label")
        blocked_layout.addWidget(blocked_label)
        
        self.blocked_value = QLabel("0")
        self.blocked_value.setProperty("class", "stat_value")
        blocked_layout.addWidget(self.blocked_value)
        
        summary_layout.addWidget(blocked_card)
        
        # Block rate card
        rate_card = QFrame()
        rate_card.setProperty("class", "stat_card")
        rate_layout = QVBoxLayout(rate_card)
        
        rate_label = QLabel("Block Rate")
        rate_label.setProperty("class", "stat_label")
        rate_layout.addWidget(rate_label)
        
        self.rate_value = QLabel("0%")
        self.rate_value.setProperty("class", "stat_value")
        rate_layout.addWidget(self.rate_value)
        
        summary_layout.addWidget(rate_card)
        
        layout.addLayout(summary_layout)
        
        # Session statistics
        session_group = QGroupBox("Session Statistics")
        session_layout = QFormLayout(session_group)
        
        self.ads_blocked_label = QLabel("0")
        session_layout.addRow("Ads Blocked:", self.ads_blocked_label)
        
        self.trackers_blocked_label = QLabel("0")
        session_layout.addRow("Trackers Blocked:", self.trackers_blocked_label)
        
        self.malware_blocked_label = QLabel("0")
        session_layout.addRow("Malware Blocked:", self.malware_blocked_label)
        
        self.social_blocked_label = QLabel("0")
        session_layout.addRow("Social Widgets Blocked:", self.social_blocked_label)
        
        layout.addWidget(session_group)
        
        # Top blocked domains
        domains_group = QGroupBox("Top Blocked Domains")
        domains_layout = QVBoxLayout(domains_group)
        
        self.domains_list = QListWidget()
        self.domains_list.setMaximumHeight(150)
        domains_layout.addWidget(self.domains_list)
        
        layout.addWidget(domains_group)
        
        # Blocked by type
        types_group = QGroupBox("Blocked by Type")
        types_layout = QVBoxLayout(types_group)
        
        self.types_list = QListWidget()
        self.types_list.setMaximumHeight(150)
        types_layout.addWidget(self.types_list)
        
        layout.addWidget(types_group)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset Statistics")
        reset_btn.clicked.connect(self.reset_statistics)
        controls_layout.addWidget(reset_btn)
        
        controls_layout.addStretch()
        
        export_btn = QPushButton("Export Statistics")
        export_btn.clicked.connect(self.export_statistics)
        controls_layout.addWidget(export_btn)
        
        layout.addLayout(controls_layout)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def update_statistics(self):
        """Update statistics display."""
        stats = self.engine.get_statistics()
        
        # Update summary cards
        self.total_value.setText(str(stats['total_requests']))
        self.blocked_value.setText(str(stats['blocked_requests']))
        self.rate_value.setText(f"{stats['block_rate']:.1f}%")
        
        # Update session stats
        session_stats = stats['session_stats']
        self.ads_blocked_label.setText(str(session_stats['ads_blocked']))
        self.trackers_blocked_label.setText(str(session_stats['trackers_blocked']))
        self.malware_blocked_label.setText(str(session_stats['malware_blocked']))
        self.social_blocked_label.setText(str(session_stats['social_blocked']))
        
        # Update top domains
        self.domains_list.clear()
        for domain, count in stats['top_blocked_domains'][:10]:
            item = QListWidgetItem(f"{domain}: {count}")
            self.domains_list.addItem(item)
        
        # Update types
        self.types_list.clear()
        for req_type, count in stats['top_blocked_types']:
            item = QListWidgetItem(f"{req_type}: {count}")
            self.types_list.addItem(item)
    
    def reset_statistics(self):
        """Reset statistics."""
        reply = QMessageBox.question(
            self, "Reset Statistics",
            "Are you sure you want to reset all statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.engine.reset_statistics()
            self.update_statistics()
    
    def export_statistics(self):
        """Export statistics to file."""
        stats = self.engine.get_statistics()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Statistics", "adblock_stats.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2, default=str)
                QMessageBox.information(self, "Success", "Statistics exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export statistics: {e}")


class FilterListsWidget(QWidget):
    """Widget for managing filter lists."""
    
    def __init__(self, engine: AdBlockEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.update_thread = None
        self.setup_ui()
        self.load_filter_lists()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Update all button
        self.update_all_btn = QPushButton("Update All")
        self.update_all_btn.clicked.connect(self.update_all_lists)
        toolbar_layout.addWidget(self.update_all_btn)
        
        # Add custom list button
        add_btn = QPushButton("Add Custom List")
        add_btn.clicked.connect(self.add_custom_list)
        toolbar_layout.addWidget(add_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # Filter lists table
        self.lists_table = QTableWidget()
        self.lists_table.setColumnCount(6)
        self.lists_table.setHorizontalHeaderLabels([
            "Name", "Status", "Last Updated", "Version", "Rules", "Actions"
        ])
        self.lists_table.horizontalHeader().setStretchLastSection(True)
        self.lists_table.setAlternatingRowColors(True)
        self.lists_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.lists_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def load_filter_lists(self):
        """Load filter lists into table."""
        self.lists_table.setRowCount(0)
        
        for name, filter_list in self.engine.filter_lists.items():
            row = self.lists_table.rowCount()
            self.lists_table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(name)
            self.lists_table.setItem(row, 0, name_item)
            
            # Status
            status_text = "Enabled" if filter_list.enabled else "Disabled"
            status_item = QTableWidgetItem(status_text)
            self.lists_table.setItem(row, 1, status_item)
            
            # Last updated
            updated_text = filter_list.last_updated.strftime('%Y-%m-%d %H:%M') if filter_list.last_updated else "Never"
            updated_item = QTableWidgetItem(updated_text)
            self.lists_table.setItem(row, 2, updated_item)
            
            # Version
            version_item = QTableWidgetItem(filter_list.version or "Unknown")
            self.lists_table.setItem(row, 3, version_item)
            
            # Rules count
            rules_count = len(filter_list.rules)
            rules_item = QTableWidgetItem(str(rules_count))
            self.lists_table.setItem(row, 4, rules_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            # Enable/Disable toggle
            toggle_btn = QPushButton("Disable" if filter_list.enabled else "Enable")
            toggle_btn.clicked.connect(lambda checked, fl=filter_list: self.toggle_list(fl))
            actions_layout.addWidget(toggle_btn)
            
            # Update button
            if filter_list.url:
                update_btn = QPushButton("Update")
                update_btn.clicked.connect(lambda checked, fl=filter_list: self.update_list(fl))
                actions_layout.addWidget(update_btn)
            
            # Remove button (custom lists only)
            if name == "Custom":
                remove_btn = QPushButton("Remove")
                remove_btn.setProperty("class", "danger")
                remove_btn.clicked.connect(lambda checked, fl=filter_list: self.remove_list(fl))
                actions_layout.addWidget(remove_btn)
            
            self.lists_table.setCellWidget(row, 5, actions_widget)
        
        # Resize columns
        self.lists_table.resizeColumnsToContents()
    
    def toggle_list(self, filter_list: FilterList):
        """Toggle filter list enabled state."""
        filter_list.enabled = not filter_list.enabled
        self.engine.load_all_rules()
        self.load_filter_lists()
    
    def update_list(self, filter_list: FilterList):
        """Update single filter list."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        def update_complete():
            self.progress_bar.setVisible(False)
            self.engine.load_all_rules()
            self.load_filter_lists()
        
        # Run update in thread
        def update_thread():
            try:
                success = filter_list.update_from_url()
                QTimer.singleShot(100, update_complete)
            except Exception as e:
                QTimer.singleShot(100, update_complete)
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def update_all_lists(self):
        """Update all filter lists."""
        if self.update_thread and self.update_thread.isRunning():
            return
        
        self.update_thread = FilterListUpdateThread(self.engine)
        self.update_thread.progress.connect(self.update_progress)
        self.update_thread.completed.connect(self.on_list_updated)
        self.update_thread.all_completed.connect(self.on_all_updated)
        self.update_thread.start()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.update_all_btn.setEnabled(False)
    
    def update_progress(self, list_name: str, progress: int):
        """Update progress bar."""
        self.progress_bar.setValue(progress)
    
    def on_list_updated(self, list_name: str, success: bool):
        """Handle single list update completion."""
        status = "✓" if success else "✗"
        print(f"{status} {list_name}")
    
    def on_all_updated(self, results: Dict[str, bool]):
        """Handle all lists update completion."""
        self.progress_bar.setVisible(False)
        self.update_all_btn.setEnabled(True)
        self.engine.load_all_rules()
        self.load_filter_lists()
        
        # Show results
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        QMessageBox.information(
            self, "Update Complete",
            f"Updated {success_count}/{total_count} filter lists successfully."
        )
    
    def add_custom_list(self):
        """Add custom filter list."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Custom Filter List")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Name
        name_layout = QFormLayout()
        name_edit = QLineEdit()
        name_layout.addRow("Name:", name_edit)
        layout.addLayout(name_layout)
        
        # URL or file
        source_layout = QFormLayout()
        source_combo = QComboBox()
        source_combo.addItems(["URL", "Local File"])
        source_edit = QLineEdit()
        source_edit.setPlaceholderText("Enter URL or select file...")
        source_layout.addRow("Source:", source_combo)
        source_layout.addRow("", source_edit)
        layout.addLayout(source_layout)
        
        # File button
        file_btn = QPushButton("Select File")
        file_btn.clicked.connect(lambda: self.select_file(source_edit))
        source_layout.addRow("", file_btn)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            source = source_edit.text().strip()
            
            if name and source:
                try:
                    if source_combo.currentText() == "URL":
                        filter_list = FilterList(name, source)
                    else:
                        filter_list = FilterList(name, path=Path(source))
                    
                    self.engine.filter_lists[name] = filter_list
                    self.load_filter_lists()
                    QMessageBox.information(self, "Success", "Filter list added successfully!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add filter list: {e}")
    
    def select_file(self, line_edit: QLineEdit):
        """Select local file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Filter List File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)
    
    def remove_list(self, filter_list: FilterList):
        """Remove custom filter list."""
        reply = QMessageBox.question(
            self, "Remove Filter List",
            f"Are you sure you want to remove '{filter_list.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.engine.filter_lists[filter_list.name]
            self.load_filter_lists()


class CustomRulesWidget(QWidget):
    """Widget for managing custom rules."""
    
    def __init__(self, engine: AdBlockEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setup_ui()
        self.load_rules()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add rule button
        add_btn = QPushButton("Add Rule")
        add_btn.clicked.connect(self.add_rule)
        toolbar_layout.addWidget(add_btn)
        
        # Import rules button
        import_btn = QPushButton("Import Rules")
        import_btn.clicked.connect(self.import_rules)
        toolbar_layout.addWidget(import_btn)
        
        # Export rules button
        export_btn = QPushButton("Export Rules")
        export_btn.clicked.connect(self.export_rules)
        toolbar_layout.addWidget(export_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar)
        
        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["Rule", "Type", "Hits", "Actions"])
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.setAlternatingRowColors(True)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.rules_table)
        
        # Rule editor
        editor_group = QGroupBox("Rule Editor")
        editor_layout = QVBoxLayout(editor_group)
        
        self.rule_edit = QTextEdit()
        self.rule_edit.setPlaceholderText("Enter filter rule...")
        self.rule_edit.setMaximumHeight(100)
        editor_layout.addWidget(self.rule_edit)
        
        editor_buttons = QHBoxLayout()
        
        test_btn = QPushButton("Test Rule")
        test_btn.clicked.connect(self.test_rule)
        editor_buttons.addWidget(test_btn)
        
        save_btn = QPushButton("Save Rule")
        save_btn.clicked.connect(self.save_rule)
        editor_buttons.addWidget(save_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_editor)
        editor_buttons.addWidget(clear_btn)
        
        editor_buttons.addStretch()
        editor_layout.addLayout(editor_buttons)
        
        layout.addWidget(editor_group)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def load_rules(self):
        """Load custom rules into table."""
        self.rules_table.setRowCount(0)
        
        custom_list = self.engine.filter_lists.get("Custom")
        if not custom_list:
            return
        
        for rule in custom_list.rules:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            
            # Rule text
            rule_item = QTableWidgetItem(rule.text)
            self.rules_table.setItem(row, 0, rule_item)
            
            # Type
            type_item = QTableWidgetItem(rule.type.value)
            self.rules_table.setItem(row, 1, type_item)
            
            # Hit count
            hits_item = QTableWidgetItem(str(rule.hit_count))
            self.rules_table.setItem(row, 2, hits_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            # Enable/Disable toggle
            toggle_btn = QPushButton("Disable" if rule.enabled else "Enable")
            toggle_btn.clicked.connect(lambda checked, r=rule: self.toggle_rule(r))
            actions_layout.addWidget(toggle_btn)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, r=rule: self.edit_rule(r))
            actions_layout.addWidget(edit_btn)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setProperty("class", "danger")
            delete_btn.clicked.connect(lambda checked, r=rule: self.delete_rule(r))
            actions_layout.addWidget(delete_btn)
            
            self.rules_table.setCellWidget(row, 3, actions_widget)
        
        # Resize columns
        self.rules_table.resizeColumnsToContents()
    
    def add_rule(self):
        """Add new rule."""
        self.rule_edit.clear()
        self.rule_edit.setFocus()
    
    def test_rule(self):
        """Test rule syntax."""
        rule_text = self.rule_edit.toPlainText().strip()
        if not rule_text:
            return
        
        rule = RuleParser.parse_rule(rule_text)
        if rule:
            QMessageBox.information(self, "Valid Rule", f"Rule parsed successfully!\n\nType: {rule.type.value}")
        else:
            QMessageBox.warning(self, "Invalid Rule", "Rule syntax is invalid!")
    
    def save_rule(self):
        """Save rule."""
        rule_text = self.rule_edit.toPlainText().strip()
        if not rule_text:
            return
        
        rule = RuleParser.parse_rule(rule_text)
        if rule:
            if self.engine.add_custom_rule(rule_text):
                self.load_rules()
                self.clear_editor()
                QMessageBox.information(self, "Success", "Rule added successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to add rule!")
        else:
            QMessageBox.warning(self, "Invalid Rule", "Rule syntax is invalid!")
    
    def clear_editor(self):
        """Clear rule editor."""
        self.rule_edit.clear()
    
    def toggle_rule(self, rule: FilterRule):
        """Toggle rule enabled state."""
        rule.enabled = not rule.enabled
        self.engine.load_all_rules()
        self.load_rules()
    
    def edit_rule(self, rule: FilterRule):
        """Edit rule."""
        self.rule_edit.setPlainText(rule.text)
        self.rule_edit.setFocus()
    
    def delete_rule(self, rule: FilterRule):
        """Delete rule."""
        reply = QMessageBox.question(
            self, "Delete Rule",
            f"Are you sure you want to delete this rule?\n\n{rule.text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.engine.remove_custom_rule(rule.id):
                self.load_rules()
    
    def import_rules(self):
        """Import rules from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Rules", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                added_count = 0
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('!') and not line.startswith('#'):
                        if self.engine.add_custom_rule(line):
                            added_count += 1
                
                self.load_rules()
                QMessageBox.information(self, "Import Complete", f"Added {added_count} rules.")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import rules: {e}")
    
    def export_rules(self):
        """Export rules to file."""
        custom_list = self.engine.filter_lists.get("Custom")
        if not custom_list or not custom_list.rules:
            QMessageBox.information(self, "No Rules", "No custom rules to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Rules", "custom_rules.txt", "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for rule in custom_list.rules:
                        f.write(rule.text + '\n')
                
                QMessageBox.information(self, "Export Complete", "Rules exported successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export rules: {e}")


class WhitelistWidget(QWidget):
    """Widget for managing whitelist."""
    
    def __init__(self, engine: AdBlockEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setup_ui()
        self.load_whitelist()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Domain whitelist
        domain_group = QGroupBox("Domain Whitelist")
        domain_layout = QVBoxLayout(domain_group)
        
        domain_toolbar = QHBoxLayout()
        domain_add_edit = QLineEdit()
        domain_add_edit.setPlaceholderText("Enter domain...")
        domain_add_btn = QPushButton("Add")
        domain_add_btn.clicked.connect(lambda: self.add_whitelist_item('domain', domain_add_edit))
        domain_toolbar.addWidget(domain_add_edit)
        domain_toolbar.addWidget(domain_add_btn)
        domain_layout.addLayout(domain_toolbar)
        
        self.domain_list = QListWidget()
        domain_layout.addWidget(self.domain_list)
        
        layout.addWidget(domain_group)
        
        # Page whitelist
        page_group = QGroupBox("Page Whitelist")
        page_layout = QVBoxLayout(page_group)
        
        page_toolbar = QHBoxLayout()
        page_add_edit = QLineEdit()
        page_add_edit.setPlaceholderText("Enter page URL...")
        page_add_btn = QPushButton("Add")
        page_add_btn.clicked.connect(lambda: self.add_whitelist_item('page', page_add_edit))
        page_toolbar.addWidget(page_add_edit)
        page_toolbar.addWidget(page_add_btn)
        page_layout.addLayout(page_toolbar)
        
        self.page_list = QListWidget()
        page_layout.addWidget(self.page_list)
        
        layout.addWidget(page_group)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "widget")
    
    def load_whitelist(self):
        """Load whitelist items."""
        self.domain_list.clear()
        self.page_list.clear()
        
        for domain in self.engine.whitelist_domains:
            item = QListWidgetItem(domain)
            item.setData(Qt.ItemDataRole.UserRole, ('domain', domain))
            self.domain_list.addItem(item)
        
        for page in self.engine.whitelist_pages:
            item = QListWidgetItem(page)
            item.setData(Qt.ItemDataRole.UserRole, ('page', page))
            self.page_list.addItem(item)
    
    def add_whitelist_item(self, item_type: str, line_edit: QLineEdit):
        """Add whitelist item."""
        value = line_edit.text().strip()
        if not value:
            return
        
        if item_type == 'domain':
            self.engine.add_whitelist_domain(value)
            item = QListWidgetItem(value)
            item.setData(Qt.ItemDataRole.UserRole, ('domain', value))
            self.domain_list.addItem(item)
        else:
            self.engine.add_whitelist_page(value)
            item = QListWidgetItem(value)
            item.setData(Qt.ItemDataRole.UserRole, ('page', value))
            self.page_list.addItem(item)
        
        line_edit.clear()
    
    def contextMenuEvent(self, event):
        """Handle context menu for whitelist items."""
        widget = self.childAt(event.pos())
        if widget in [self.domain_list, self.page_list]:
            item = widget.currentItem()
            if item:
                item_type, value = item.data(Qt.ItemDataRole.UserRole)
                
                menu = QMenu(self)
                remove_action = menu.addAction("Remove")
                remove_action.triggered.connect(lambda: self.remove_whitelist_item(item_type, value, item))
                
                menu.exec(event.globalPos())
    
    def remove_whitelist_item(self, item_type: str, value: str, item: QListWidgetItem):
        """Remove whitelist item."""
        if item_type == 'domain':
            self.engine.remove_whitelist_domain(value)
            self.domain_list.takeItem(self.domain_list.row(item))
        else:
            self.engine.remove_whitelist_page(value)
            self.page_list.takeItem(self.page_list.row(item))


class AdBlockSettingsDialog(QDialog):
    """Main ad blocker settings dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ad Blocker Settings")
        self.resize(900, 700)
        self.engine = AdBlockEngine()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Statistics tab
        stats_widget = StatisticsWidget(self.engine)
        tab_widget.addTab(stats_widget, "Statistics")
        
        # Filter lists tab
        lists_widget = FilterListsWidget(self.engine)
        tab_widget.addTab(lists_widget, "Filter Lists")
        
        # Custom rules tab
        rules_widget = CustomRulesWidget(self.engine)
        tab_widget.addTab(rules_widget, "Custom Rules")
        
        # Whitelist tab
        whitelist_widget = WhitelistWidget(self.engine)
        tab_widget.addTab(whitelist_widget, "Whitelist")
        
        layout.addWidget(tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Apply styling
        style_manager.apply_stylesheet(self, "dialog")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Save settings
        event.accept()
