"""
History Panel

This module contains the browsing history panel with history
search, filtering, and management features.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import logging
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta


class HistoryPanel:
    """Browsing history management panel."""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
        # State
        self.history = []
        self.current_filter = "All Time"
        
        # Setup panel
        self.setup_panel()
        
        # Load initial data
        self.refresh_history()
    
    def setup_panel(self):
        """Setup the history panel UI."""
        # Main frame
        self.frame = ctk.CTkFrame(self.parent)
        
        # Header
        header_frame = ctk.CTkFrame(self.frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Title
        title_label = ctk.CTkLabel(header_frame, text="History", font=("Arial", 14, "bold"))
        title_label.pack(side="left")
        
        # Clear history button
        clear_button = ctk.CTkButton(
            header_frame, text="Clear", width=50, command=self.clear_history
        )
        clear_button.pack(side="right", padx=2)
        
        # Filter frame
        filter_frame = ctk.CTkFrame(self.frame)
        filter_frame.pack(fill="x", padx=5, pady=2)
        
        # Time filter
        self.filter_var = tk.StringVar(value="All Time")
        self.filter_combo = ctk.CTkComboBox(
            filter_frame, variable=self.filter_var, command=self.on_filter_changed
        )
        self.filter_combo.pack(side="left", fill="x", expand=True)
        
        # Set filter options
        filter_options = [
            "All Time", "Today", "Yesterday", "Last 7 Days", 
            "Last 30 Days", "Last 90 Days"
        ]
        self.filter_combo.configure(values=filter_options)
        
        # Search box
        search_frame = ctk.CTkFrame(self.frame)
        search_frame.pack(fill="x", padx=5, pady=2)
        
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var, placeholder_text="Search history..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # History list
        list_frame = ctk.CTkFrame(self.frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview for history
        self.history_tree = ttk.Treeview(
            list_frame, columns=("url", "visits", "last_visited"), 
            show="tree headings", height=15
        )
        
        # Configure columns
        self.history_tree.heading("#0", text="Title")
        self.history_tree.heading("url", text="URL")
        self.history_tree.heading("visits", text="Visits")
        self.history_tree.heading("last_visited", text="Last Visited")
        
        self.history_tree.column("#0", width=150)
        self.history_tree.column("url", width=200)
        self.history_tree.column("visits", width=60)
        self.history_tree.column("last_visited", width=120)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_tree.yview)
        x_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.history_tree.xview)
        
        self.history_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack widgets
        self.history_tree.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.setup_context_menu()
        
        # Bind events
        self.history_tree.bind("<Double-1>", self.on_double_click)
        self.history_tree.bind("<Button-3>", self.on_right_click)
    
    def setup_context_menu(self):
        """Setup context menu for history."""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="Open in New Tab", command=self.open_in_new_tab)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy URL", command=self.copy_url)
        self.context_menu.add_command(label="Copy Title", command=self.copy_title)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Entry", command=self.delete_selected)
        self.context_menu.add_command(label="Delete Domain", command=self.delete_domain)
    
    def refresh_history(self):
        """Refresh history from backend."""
        try:
            # Get history from backend
            response = requests.get('http://127.0.0.1:5000/api/history', timeout=5)
            
            if response.status_code == 200:
                self.history = response.json()
                self.update_history_display()
            else:
                self.logger.error(f"Error getting history: {response.status_code}")
                messagebox.showerror("Error", "Failed to load history")
                
        except Exception as e:
            self.logger.error(f"Error refreshing history: {e}")
            messagebox.showerror("Error", f"Failed to load history: {e}")
    
    def update_history_display(self):
        """Update the history tree view."""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Filter history
        filtered_history = self.filter_history()
        
        # Add history entries to tree
        for entry in filtered_history:
            # Format last visited time
            last_visited = entry.get('last_visited', '')
            if last_visited:
                try:
                    dt = datetime.fromisoformat(last_visited.replace('Z', '+00:00'))
                    last_visited = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            self.history_tree.insert(
                "", "end",
                text=entry.get('title', 'Untitled'),
                values=(
                    entry.get('url', ''),
                    entry.get('visit_count', 1),
                    last_visited
                ),
                tags=(str(entry['id']),)
            )
    
    def filter_history(self) -> List[Dict[str, Any]]:
        """Filter history based on current filter and search."""
        filtered = self.history.copy()
        
        # Filter by time
        if self.current_filter != "All Time":
            cutoff_date = self.get_cutoff_date(self.current_filter)
            if cutoff_date:
                filtered = [
                    entry for entry in filtered 
                    if entry.get('last_visited') and 
                    datetime.fromisoformat(entry['last_visited'].replace('Z', '+00:00')) >= cutoff_date
                ]
        
        # Filter by search
        search_text = self.search_var.get().lower()
        if search_text:
            filtered = [
                entry for entry in filtered 
                if search_text in entry.get('title', '').lower() or 
                search_text in entry.get('url', '').lower()
            ]
        
        return filtered
    
    def get_cutoff_date(self, filter_option: str) -> Optional[datetime]:
        """Get cutoff date for time filter."""
        now = datetime.now()
        
        if filter_option == "Today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_option == "Yesterday":
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_option == "Last 7 Days":
            return now - timedelta(days=7)
        elif filter_option == "Last 30 Days":
            return now - timedelta(days=30)
        elif filter_option == "Last 90 Days":
            return now - timedelta(days=90)
        
        return None
    
    def on_filter_changed(self, selection):
        """Handle filter selection change."""
        self.current_filter = selection
        self.update_history_display()
    
    def on_search(self, event):
        """Handle search text change."""
        self.update_history_display()
    
    def on_double_click(self, event):
        """Handle double-click on history entry."""
        self.open_selected()
    
    def on_right_click(self, event):
        """Handle right-click on history entry."""
        # Select item under cursor
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def get_selected_entry(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected history entry."""
        selection = self.history_tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.history_tree.item(item, "tags")
        if not tags:
            return None
        
        entry_id = int(tags[0])
        
        # Find entry by ID
        for entry in self.history:
            if entry['id'] == entry_id:
                return entry
        
        return None
    
    def open_selected(self):
        """Open selected history entry in current tab."""
        entry = self.get_selected_entry()
        if entry:
            current_tab = self.main_window.get_current_tab()
            if current_tab:
                current_tab.load_url(entry['url'])
    
    def open_in_new_tab(self):
        """Open selected history entry in new tab."""
        entry = self.get_selected_entry()
        if entry:
            new_tab = self.main_window.new_tab(entry['url'])
    
    def copy_url(self):
        """Copy selected entry URL to clipboard."""
        entry = self.get_selected_entry()
        if entry:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(entry['url'])
            self.main_window.update_status("URL copied to clipboard")
    
    def copy_title(self):
        """Copy selected entry title to clipboard."""
        entry = self.get_selected_entry()
        if entry:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(entry.get('title', 'Untitled'))
            self.main_window.update_status("Title copied to clipboard")
    
    def delete_selected(self):
        """Delete selected history entry."""
        entry = self.get_selected_entry()
        if entry:
            if messagebox.askyesno(
                "Delete History Entry",
                f"Are you sure you want to delete this history entry?"
            ):
                try:
                    # Note: This would need a specific API endpoint for deleting single entries
                    # For now, we'll show a message
                    messagebox.showinfo("Info", "Delete single entry not yet implemented")
                    
                except Exception as e:
                    self.logger.error(f"Error deleting history entry: {e}")
                    messagebox.showerror("Error", f"Failed to delete history entry: {e}")
    
    def delete_domain(self):
        """Delete all history for the selected domain."""
        entry = self.get_selected_entry()
        if entry:
            url = entry['url']
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                if messagebox.askyesno(
                    "Delete Domain History",
                    f"Are you sure you want to delete all history for {domain}?"
                ):
                    # Note: This would need a specific API endpoint for deleting domain history
                    messagebox.showinfo("Info", "Delete domain history not yet implemented")
                    
            except Exception as e:
                self.logger.error(f"Error deleting domain history: {e}")
                messagebox.showerror("Error", f"Failed to delete domain history: {e}")
    
    def clear_history(self):
        """Clear all browsing history."""
        if messagebox.askyesno(
            "Clear History",
            "Are you sure you want to clear all browsing history? This action cannot be undone."
        ):
            try:
                response = requests.delete('http://127.0.0.1:5000/api/history', timeout=5)
                
                if response.status_code == 200:
                    self.history = []
                    self.update_history_display()
                    self.main_window.update_status("History cleared")
                else:
                    messagebox.showerror("Error", "Failed to clear history")
                    
            except Exception as e:
                self.logger.error(f"Error clearing history: {e}")
                messagebox.showerror("Error", f"Failed to clear history: {e}")
    
    def export_history(self):
        """Export history to file."""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                title="Export History",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                # Get all history for export
                response = requests.get('http://127.0.0.1:5000/api/history', params={'limit': 10000}, timeout=10)
                
                if response.status_code == 200:
                    history_data = response.json()
                    
                    if filename.endswith('.csv'):
                        # Export as CSV
                        import csv
                        
                        with open(filename, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['Title', 'URL', 'Visit Count', 'Last Visited'])
                            
                            for entry in history_data:
                                writer.writerow([
                                    entry.get('title', ''),
                                    entry.get('url', ''),
                                    entry.get('visit_count', 1),
                                    entry.get('last_visited', '')
                                ])
                    else:
                        # Export as JSON
                        export_data = {
                            'exported_at': datetime.now().isoformat(),
                            'history': history_data
                        }
                        
                        import json
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(export_data, f, indent=2)
                    
                    self.main_window.update_status(f"History exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export history")
                    
        except Exception as e:
            self.logger.error(f"Error exporting history: {e}")
            messagebox.showerror("Error", f"Failed to export history: {e}")
    
    def get_history_stats(self):
        """Get history statistics."""
        try:
            stats = {
                'total_entries': len(self.history),
                'unique_domains': len(set(entry.get('url', '').split('/')[2] for entry in self.history if entry.get('url'))),
                'most_visited': max(self.history, key=lambda x: x.get('visit_count', 0)) if self.history else None,
                'recent_entries': len([e for e in self.history if self.is_recent(e.get('last_visited'))])
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting history stats: {e}")
            return {}
    
    def is_recent(self, last_visited: str) -> bool:
        """Check if entry is recent (visited in last 24 hours)."""
        if not last_visited:
            return False
        
        try:
            dt = datetime.fromisoformat(last_visited.replace('Z', '+00:00'))
            return datetime.now() - dt < timedelta(hours=24)
        except:
            return False
    
    def show_statistics(self):
        """Show history statistics dialog."""
        stats = self.get_history_stats()
        
        stats_text = f"""
History Statistics

Total Entries: {stats.get('total_entries', 0)}
Unique Domains: {stats.get('unique_domains', 0)}
Recent Entries (24h): {stats.get('recent_entries', 0)}

Most Visited:
{stats.get('most_visited', {}).get('title', 'N/A')}
{stats.get('most_visited', {}).get('url', 'N/A')}
Visits: {stats.get('most_visited', {}).get('visit_count', 0)}
        """.strip()
        
        messagebox.showinfo("History Statistics", stats_text)
