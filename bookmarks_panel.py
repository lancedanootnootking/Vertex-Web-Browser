"""
Bookmarks Panel

This module contains the bookmarks management panel with bookmark
organization, search, and management features.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import logging
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime


class BookmarksPanel:
    """Bookmarks management panel."""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
        # State
        self.bookmarks = []
        self.folders = []
        self.current_folder = "All"
        
        # Setup panel
        self.setup_panel()
        
        # Load initial data
        self.refresh_bookmarks()
    
    def setup_panel(self):
        """Setup the bookmarks panel UI."""
        # Main frame
        self.frame = ctk.CTkFrame(self.parent)
        
        # Header
        header_frame = ctk.CTkFrame(self.frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Title
        title_label = ctk.CTkLabel(header_frame, text="Bookmarks", font=("Arial", 14, "bold"))
        title_label.pack(side="left")
        
        # Add bookmark button
        add_button = ctk.CTkButton(
            header_frame, text="Add", width=50, command=self.add_bookmark_dialog
        )
        add_button.pack(side="right", padx=2)
        
        # Folder selector
        folder_frame = ctk.CTkFrame(self.frame)
        folder_frame.pack(fill="x", padx=5, pady=2)
        
        self.folder_var = tk.StringVar(value="All")
        self.folder_combo = ctk.CTkComboBox(
            folder_frame, variable=self.folder_var, command=self.on_folder_changed
        )
        self.folder_combo.pack(side="left", fill="x", expand=True)
        
        # Search box
        search_frame = ctk.CTkFrame(self.frame)
        search_frame.pack(fill="x", padx=5, pady=2)
        
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var, placeholder_text="Search bookmarks..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Bookmarks list
        list_frame = ctk.CTkFrame(self.frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview for bookmarks
        self.bookmarks_tree = ttk.Treeview(
            list_frame, columns=("title", "url"), show="tree headings", height=15
        )
        
        # Configure columns
        self.bookmarks_tree.heading("#0", text="Title")
        self.bookmarks_tree.heading("title", text="Title")
        self.bookmarks_tree.heading("url", text="URL")
        
        self.bookmarks_tree.column("#0", width=150)
        self.bookmarks_tree.column("title", width=150)
        self.bookmarks_tree.column("url", width=200)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.bookmarks_tree.yview)
        x_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.bookmarks_tree.xview)
        
        self.bookmarks_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack widgets
        self.bookmarks_tree.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.setup_context_menu()
        
        # Bind events
        self.bookmarks_tree.bind("<Double-1>", self.on_double_click)
        self.bookmarks_tree.bind("<Button-3>", self.on_right_click)
    
    def setup_context_menu(self):
        """Setup context menu for bookmarks."""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="Open in New Tab", command=self.open_in_new_tab)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit", command=self.edit_selected)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy URL", command=self.copy_url)
        self.context_menu.add_command(label="Copy Title", command=self.copy_title)
    
    def refresh_bookmarks(self):
        """Refresh bookmarks from backend."""
        try:
            # Get bookmarks from backend
            response = requests.get('http://127.0.0.1:5000/api/bookmarks', timeout=5)
            
            if response.status_code == 200:
                self.bookmarks = response.json()
                self.update_bookmarks_display()
                self.update_folders()
            else:
                self.logger.error(f"Error getting bookmarks: {response.status_code}")
                messagebox.showerror("Error", "Failed to load bookmarks")
                
        except Exception as e:
            self.logger.error(f"Error refreshing bookmarks: {e}")
            messagebox.showerror("Error", f"Failed to load bookmarks: {e}")
    
    def update_bookmarks_display(self):
        """Update the bookmarks tree view."""
        # Clear existing items
        for item in self.bookmarks_tree.get_children():
            self.bookmarks_tree.delete(item)
        
        # Filter bookmarks
        filtered_bookmarks = self.filter_bookmarks()
        
        # Add bookmarks to tree
        for bookmark in filtered_bookmarks:
            self.bookmarks_tree.insert(
                "", "end",
                text=bookmark['title'],
                values=(bookmark['title'], bookmark['url']),
                tags=(str(bookmark['id']),)
            )
    
    def filter_bookmarks(self) -> List[Dict[str, Any]]:
        """Filter bookmarks based on current folder and search."""
        filtered = self.bookmarks.copy()
        
        # Filter by folder
        if self.current_folder != "All":
            filtered = [b for b in filtered if b.get('folder') == self.current_folder]
        
        # Filter by search
        search_text = self.search_var.get().lower()
        if search_text:
            filtered = [
                b for b in filtered 
                if search_text in b['title'].lower() or search_text in b['url'].lower()
            ]
        
        return filtered
    
    def update_folders(self):
        """Update folder list."""
        folders = set()
        for bookmark in self.bookmarks:
            folder = bookmark.get('folder', 'Default')
            folders.add(folder)
        
        self.folders = sorted(list(folders))
        
        # Update combo box
        folder_options = ["All"] + self.folders
        self.folder_combo.configure(values=folder_options)
    
    def on_folder_changed(self, selection):
        """Handle folder selection change."""
        self.current_folder = selection
        self.update_bookmarks_display()
    
    def on_search(self, event):
        """Handle search text change."""
        self.update_bookmarks_display()
    
    def on_double_click(self, event):
        """Handle double-click on bookmark."""
        self.open_selected()
    
    def on_right_click(self, event):
        """Handle right-click on bookmark."""
        # Select item under cursor
        item = self.bookmarks_tree.identify_row(event.y)
        if item:
            self.bookmarks_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def get_selected_bookmark(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected bookmark."""
        selection = self.bookmarks_tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.bookmarks_tree.item(item, "tags")
        if not tags:
            return None
        
        bookmark_id = int(tags[0])
        
        # Find bookmark by ID
        for bookmark in self.bookmarks:
            if bookmark['id'] == bookmark_id:
                return bookmark
        
        return None
    
    def open_selected(self):
        """Open selected bookmark in current tab."""
        bookmark = self.get_selected_bookmark()
        if bookmark:
            current_tab = self.main_window.get_current_tab()
            if current_tab:
                current_tab.load_url(bookmark['url'])
    
    def open_in_new_tab(self):
        """Open selected bookmark in new tab."""
        bookmark = self.get_selected_bookmark()
        if bookmark:
            new_tab = self.main_window.new_tab(bookmark['url'])
    
    def edit_selected(self):
        """Edit selected bookmark."""
        bookmark = self.get_selected_bookmark()
        if bookmark:
            self.edit_bookmark_dialog(bookmark)
    
    def delete_selected(self):
        """Delete selected bookmark."""
        bookmark = self.get_selected_bookmark()
        if bookmark:
            if messagebox.askyesno(
                "Delete Bookmark",
                f"Are you sure you want to delete '{bookmark['title']}'?"
            ):
                try:
                    response = requests.delete(
                        f'http://127.0.0.1:5000/api/bookmarks/{bookmark["id"]}',
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        self.refresh_bookmarks()
                        self.main_window.update_status("Bookmark deleted")
                    else:
                        messagebox.showerror("Error", "Failed to delete bookmark")
                        
                except Exception as e:
                    self.logger.error(f"Error deleting bookmark: {e}")
                    messagebox.showerror("Error", f"Failed to delete bookmark: {e}")
    
    def copy_url(self):
        """Copy selected bookmark URL to clipboard."""
        bookmark = self.get_selected_bookmark()
        if bookmark:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(bookmark['url'])
            self.main_window.update_status("URL copied to clipboard")
    
    def copy_title(self):
        """Copy selected bookmark title to clipboard."""
        bookmark = self.get_selected_bookmark()
        if bookmark:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(bookmark['title'])
            self.main_window.update_status("Title copied to clipboard")
    
    def add_bookmark_dialog(self):
        """Show dialog to add new bookmark."""
        dialog = BookmarkDialog(self.frame, "Add Bookmark", self.main_window)
        if dialog.result:
            self.add_bookmark(dialog.result)
    
    def edit_bookmark_dialog(self, bookmark: Dict[str, Any]):
        """Show dialog to edit bookmark."""
        dialog = BookmarkDialog(
            self.frame, "Edit Bookmark", self.main_window, bookmark
        )
        if dialog.result:
            self.update_bookmark(bookmark['id'], dialog.result)
    
    def add_bookmark(self, bookmark_data: Dict[str, Any]):
        """Add a new bookmark."""
        try:
            response = requests.post(
                'http://127.0.0.1:5000/api/bookmarks',
                json=bookmark_data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.refresh_bookmarks()
                self.main_window.update_status("Bookmark added")
            else:
                messagebox.showerror("Error", "Failed to add bookmark")
                
        except Exception as e:
            self.logger.error(f"Error adding bookmark: {e}")
            messagebox.showerror("Error", f"Failed to add bookmark: {e}")
    
    def update_bookmark(self, bookmark_id: int, bookmark_data: Dict[str, Any]):
        """Update an existing bookmark."""
        try:
            response = requests.put(
                f'http://127.0.0.1:5000/api/bookmarks/{bookmark_id}',
                json=bookmark_data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.refresh_bookmarks()
                self.main_window.update_status("Bookmark updated")
            else:
                messagebox.showerror("Error", "Failed to update bookmark")
                
        except Exception as e:
            self.logger.error(f"Error updating bookmark: {e}")
            messagebox.showerror("Error", f"Failed to update bookmark: {e}")
    
    def bookmark_current_page(self):
        """Bookmark the current page."""
        current_tab = self.main_window.get_current_tab()
        if current_tab:
            url = current_tab.get_url()
            title = current_tab.get_title()
            
            if url and url != "about:blank":
                bookmark_data = {
                    'title': title or 'Untitled',
                    'url': url,
                    'folder': 'Default'
                }
                self.add_bookmark(bookmark_data)
            else:
                messagebox.showinfo("Info", "Cannot bookmark current page")


class BookmarkDialog:
    """Dialog for adding/editing bookmarks."""
    
    def __init__(self, parent, title: str, main_window, bookmark_data: Dict[str, Any] = None):
        self.parent = parent
        self.main_window = main_window
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        # Setup dialog
        self.setup_dialog(bookmark_data)
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_dialog(self, bookmark_data: Dict[str, Any] = None):
        """Setup dialog UI."""
        # Title
        title_frame = ctk.CTkFrame(self.dialog)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(title_frame, text="Title:").pack(side="left")
        self.title_entry = ctk.CTkEntry(title_frame, width=300)
        self.title_entry.pack(side="right", fill="x", expand=True)
        
        # URL
        url_frame = ctk.CTkFrame(self.dialog)
        url_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(url_frame, text="URL:").pack(side="left")
        self.url_entry = ctk.CTkEntry(url_frame, width=300)
        self.url_entry.pack(side="right", fill="x", expand=True)
        
        # Folder
        folder_frame = ctk.CTkFrame(self.dialog)
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(folder_frame, text="Folder:").pack(side="left")
        self.folder_entry = ctk.CTkEntry(folder_frame, width=300)
        self.folder_entry.pack(side="right", fill="x", expand=True)
        
        # Tags
        tags_frame = ctk.CTkFrame(self.dialog)
        tags_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(tags_frame, text="Tags:").pack(side="left")
        self.tags_entry = ctk.CTkEntry(tags_frame, width=300)
        self.tags_entry.pack(side="right", fill="x", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, text="Save", command=self.save
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame, text="Cancel", command=self.cancel
        ).pack(side="right", padx=5)
        
        # Load bookmark data if editing
        if bookmark_data:
            self.title_entry.insert(0, bookmark_data.get('title', ''))
            self.url_entry.insert(0, bookmark_data.get('url', ''))
            self.folder_entry.insert(0, bookmark_data.get('folder', 'Default'))
            
            tags = bookmark_data.get('tags', [])
            if tags:
                self.tags_entry.insert(0, ', '.join(tags))
        
        # Focus title entry
        self.title_entry.focus_set()
    
    def save(self):
        """Save bookmark data."""
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip() or "Default"
        tags_text = self.tags_entry.get().strip()
        
        # Validate
        if not title:
            messagebox.showerror("Error", "Please enter a title")
            return
        
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        # Parse tags
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Store result
        self.result = {
            'title': title,
            'url': url,
            'folder': folder,
            'tags': tags
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()
