"""
Main Browser Window

This module contains the main browser window implementation with tabbed browsing,
menu bar, toolbar, and status bar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .browser_tab import BrowserTab
from .address_bar import AddressBar
from .bookmarks_panel import BookmarksPanel
from .history_panel import HistoryPanel
from .settings_panel import SettingsPanel
from .themes.theme_manager import ThemeManager


class BrowserMainWindow:
    """Main browser window with tabbed interface."""
    
    def __init__(self, config: Dict[str, Any], backend_app, extension_manager):
        self.config = config
        self.backend_app = backend_app
        self.extension_manager = extension_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(config.get('browser', {}).get('theme', 'dark'))
        
        # Setup main window
        self.setup_window()
        
        # Initialize components
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_tabbed_browser()
        self.setup_status_bar()
        self.setup_side_panels()
        
        # Load initial state
        self.load_initial_state()
        
        # Bind events
        self.bind_events()
    
    def setup_window(self):
        """Setup the main window properties."""
        ctk.set_appearance_mode(self.theme_manager.get_current_theme())
        
        self.root = ctk.CTk()
        self.root.title("Advanced Web Browser")
        
        # Set window size from config
        ui_config = self.config.get('ui', {})
        width = ui_config.get('window_width', 1200)
        height = ui_config.get('window_height', 800)
        
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(800, 600)
        
        # Center window on screen
        self.center_window()
        
        # Set icon (placeholder)
        try:
            self.root.iconbitmap("browser_icon.ico")
        except:
            pass  # Icon file not found, continue without it
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_menu_bar(self):
        """Setup the menu bar."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Tab", command=self.new_tab, accelerator="Ctrl+T")
        file_menu.add_command(label="New Window", command=self.new_window, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Open File", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Page As", command=self.save_page, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Print", command=self.print_page, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_browser, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", command=self.find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Find Next", command=self.find_next, accelerator="F3")
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl+Plus")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+Minus")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label="Full Screen", command=self.toggle_fullscreen, accelerator="F11")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Bookmarks Bar", command=self.toggle_bookmarks_bar)
        view_menu.add_checkbutton(label="Show Status Bar", command=self.toggle_status_bar)
        view_menu.add_checkbutton(label="Show Side Panel", command=self.toggle_side_panel)
        
        # History menu
        history_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="History", menu=history_menu)
        history_menu.add_command(label="Show History", command=self.show_history)
        history_menu.add_command(label="Clear History", command=self.clear_history)
        history_menu.add_separator()
        history_menu.add_command(label="Recently Closed", command=self.show_recently_closed)
        
        # Bookmarks menu
        bookmarks_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Bookmarks", menu=bookmarks_menu)
        bookmarks_menu.add_command(label="Bookmark Page", command=self.bookmark_page, accelerator="Ctrl+D")
        bookmarks_menu.add_command(label="Bookmark All Tabs", command=self.bookmark_all_tabs)
        bookmarks_menu.add_separator()
        bookmarks_menu.add_command(label="Show Bookmarks", command=self.show_bookmarks)
        bookmarks_menu.add_command(label="Manage Bookmarks", command=self.manage_bookmarks)
        
        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Developer Tools", command=self.show_dev_tools, accelerator="F12")
        tools_menu.add_command(label="Extensions", command=self.show_extensions)
        tools_menu.add_command(label="Settings", command=self.show_settings)
        tools_menu.add_separator()
        tools_menu.add_checkbutton(label="Private Browsing", command=self.toggle_private_browsing)
        tools_menu.add_command(label="Clear Browsing Data", command=self.clear_browsing_data)
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
    
    def setup_toolbar(self):
        """Setup the toolbar with navigation controls."""
        self.toolbar_frame = ctk.CTkFrame(self.root)
        self.toolbar_frame.pack(fill="x", padx=5, pady=5)
        
        # Navigation buttons
        self.back_button = ctk.CTkButton(
            self.toolbar_frame, text="←", width=30, command=self.go_back
        )
        self.back_button.pack(side="left", padx=2)
        
        self.forward_button = ctk.CTkButton(
            self.toolbar_frame, text="→", width=30, command=self.go_forward
        )
        self.forward_button.pack(side="left", padx=2)
        
        self.refresh_button = ctk.CTkButton(
            self.toolbar_frame, text="↻", width=30, command=self.refresh_page
        )
        self.refresh_button.pack(side="left", padx=2)
        
        self.home_button = ctk.CTkButton(
            self.toolbar_frame, text="⌂", width=30, command=self.go_home
        )
        self.home_button.pack(side="left", padx=2)
        
        # Address bar
        self.address_bar = AddressBar(self.toolbar_frame, self)
        self.address_bar.pack(side="left", fill="x", expand=True, padx=5)
        
        # Search button
        self.search_button = ctk.CTkButton(
            self.toolbar_frame, text="🔍", width=30, command=self.quick_search
        )
        self.search_button.pack(side="left", padx=2)
        
        # Menu button
        self.menu_button = ctk.CTkButton(
            self.toolbar_frame, text="☰", width=30, command=self.show_context_menu
        )
        self.menu_button.pack(side="left", padx=2)
    
    def setup_tabbed_browser(self):
        """Setup the tabbed browser interface."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind tab events
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.bind("<Button-3>", self.on_tab_right_click)
        
        # Create initial tab
        self.new_tab()
    
    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = ctk.CTkFrame(self.root)
        self.status_bar.pack(fill="x", side="bottom")
        
        # Status label
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready")
        self.status_label.pack(side="left", padx=5)
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self.status_bar)
        self.progress_bar.pack(side="left", padx=5, fill="x", expand=True)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()
        
        # Zoom indicator
        self.zoom_label = ctk.CTkLabel(self.status_bar, text="100%")
        self.zoom_label.pack(side="right", padx=5)
        
        # Security indicator
        self.security_label = ctk.CTkLabel(self.status_bar, text="🔒")
        self.security_label.pack(side="right", padx=5)
    
    def setup_side_panels(self):
        """Setup side panels for bookmarks, history, etc."""
        self.side_panel_frame = ctk.CTkFrame(self.root)
        
        # Create side panel notebook
        self.side_notebook = ttk.Notebook(self.side_panel_frame)
        self.side_notebook.pack(fill="both", expand=True)
        
        # Bookmarks panel
        self.bookmarks_panel = BookmarksPanel(self.side_notebook, self)
        self.side_notebook.add(self.bookmarks_panel.frame, text="Bookmarks")
        
        # History panel
        self.history_panel = HistoryPanel(self.side_notebook, self)
        self.side_notebook.add(self.history_panel.frame, text="History")
        
        # Initially hide side panel
        self.side_panel_visible = False
    
    def bind_events(self):
        """Bind keyboard and mouse events."""
        # Keyboard shortcuts
        self.root.bind("<Control-t>", lambda e: self.new_tab())
        self.root.bind("<Control-n>", lambda e: self.new_window())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-q>", lambda e: self.quit_browser())
        self.root.bind("<Control-d>", lambda e: self.bookmark_page())
        self.root.bind("<Control-f>", lambda e: self.find())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<F12>", lambda e: self.show_dev_tools())
        
        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self.quit_browser)
    
    def load_initial_state(self):
        """Load initial browser state."""
        # Restore last session if configured
        if self.config.get('browser', {}).get('restore_last_session', False):
            self.restore_last_session()
        else:
            # Load homepage
            homepage = self.config.get('browser', {}).get('default_homepage', 'https://www.google.com')
            current_tab = self.get_current_tab()
            if current_tab:
                current_tab.load_url(homepage)
    
    def new_tab(self, url=None):
        """Create a new browser tab."""
        tab = BrowserTab(self.notebook, self, url)
        self.notebook.add(tab.frame, text="New Tab")
        self.notebook.select(tab.frame)
        
        # Update tab count in status
        self.update_status()
        
        return tab
    
    def close_current_tab(self):
        """Close the current tab."""
        current = self.notebook.select()
        if current:
            tab_count = len(self.notebook.tabs())
            if tab_count > 1:
                self.notebook.forget(current)
                self.update_status()
            else:
                # Don't close the last tab, just clear it
                current_tab = self.get_current_tab()
                if current_tab:
                    current_tab.load_url("about:blank")
    
    def close_tab(self, tab_frame):
        """Close a specific tab."""
        tab_count = len(self.notebook.tabs())
        if tab_count > 1:
            self.notebook.forget(tab_frame)
            self.update_status()
        else:
            # Don't close the last tab
            current_tab = self.get_current_tab()
            if current_tab:
                current_tab.load_url("about:blank")
    
    def get_current_tab(self) -> Optional[BrowserTab]:
        """Get the currently active tab."""
        current = self.notebook.select()
        if current:
            for tab in self.notebook.tabs():
                if tab == current:
                    # Find the BrowserTab instance for this frame
                    for child in self.notebook.winfo_children():
                        if hasattr(child, 'frame') and child.frame == current:
                            return child
        return None
    
    def on_tab_changed(self, event):
        """Handle tab change event."""
        current_tab = self.get_current_tab()
        if current_tab:
            # Update address bar
            self.address_bar.set_url(current_tab.get_url())
            
            # Update window title
            title = current_tab.get_title()
            if title:
                self.root.title(f"{title} - Advanced Web Browser")
            else:
                self.root.title("Advanced Web Browser")
            
            # Update navigation buttons
            self.update_navigation_buttons(current_tab)
    
    def on_tab_right_click(self, event):
        """Handle right-click on tab."""
        # Show context menu for tab
        pass
    
    def update_navigation_buttons(self, tab):
        """Update navigation button states."""
        if tab:
            self.back_button.configure(state="normal" if tab.can_go_back() else "disabled")
            self.forward_button.configure(state="normal" if tab.can_go_forward() else "disabled")
    
    def go_back(self):
        """Navigate back in current tab."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.go_back()
    
    def go_forward(self):
        """Navigate forward in current tab."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.go_forward()
    
    def refresh_page(self):
        """Refresh current page."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.refresh()
    
    def go_home(self):
        """Navigate to homepage."""
        homepage = self.config.get('browser', {}).get('default_homepage', 'https://www.google.com')
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.load_url(homepage)
    
    def quick_search(self):
        """Perform quick search."""
        query = self.address_bar.get_text()
        if query:
            search_url = f"https://www.google.com/search?q={query}"
            current_tab = self.get_current_tab()
            if current_tab:
                current_tab.load_url(search_url)
    
    def show_context_menu(self):
        """Show context menu."""
        # Implement context menu
        pass
    
    def update_status(self, message="Ready"):
        """Update status bar."""
        self.status_label.configure(text=message)
        
        # Update tab count
        tab_count = len(self.notebook.tabs())
        if tab_count > 1:
            self.root.title(f"{tab_count} tabs - Advanced Web Browser")
    
    def show_progress(self, value=0):
        """Show progress bar."""
        if value > 0:
            self.progress_bar.pack(side="left", padx=5, fill="x", expand=True)
            self.progress_bar.set(value)
        else:
            self.progress_bar.pack_forget()
    
    def toggle_bookmarks_bar(self):
        """Toggle bookmarks bar visibility."""
        # Implement bookmarks bar toggle
        pass
    
    def toggle_status_bar(self):
        """Toggle status bar visibility."""
        if self.status_bar.winfo_ismapped():
            self.status_bar.pack_forget()
        else:
            self.status_bar.pack(fill="x", side="bottom")
    
    def toggle_side_panel(self):
        """Toggle side panel visibility."""
        if self.side_panel_visible:
            self.side_panel_frame.pack_forget()
            self.side_panel_visible = False
        else:
            self.side_panel_frame.pack(fill="both", side="left", padx=5, pady=5)
            self.side_panel_visible = True
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
    
    def toggle_private_browsing(self):
        """Toggle private browsing mode."""
        # Implement private browsing toggle
        pass
    
    def show_history(self):
        """Show history panel."""
        self.toggle_side_panel()
        self.side_notebook.select(self.history_panel.frame)
    
    def show_bookmarks(self):
        """Show bookmarks panel."""
        self.toggle_side_panel()
        self.side_notebook.select(self.bookmarks_panel.frame)
    
    def show_settings(self):
        """Show settings dialog."""
        settings_window = SettingsWindow(self.root, self.config, self)
        settings_window.run()
    
    def show_dev_tools(self):
        """Show developer tools."""
        # Implement developer tools
        pass
    
    def show_extensions(self):
        """Show extensions manager."""
        # Implement extensions manager
        pass
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Advanced Web Browser",
            "Advanced Web Browser v1.0\n\n"
            "A modern web browser with advanced features\n"
            "including tabbed browsing, security features,\n"
            "and extensible architecture.\n\n"
            "Built with Python and CustomTkinter"
        )
    
    def show_help(self):
        """Show help documentation."""
        # Implement help system
        pass
    
    def check_updates(self):
        """Check for browser updates."""
        # Implement update checking
        messagebox.showinfo("Updates", "You are running the latest version.")
    
    def bookmark_page(self):
        """Bookmark current page."""
        current_tab = self.get_current_tab()
        if current_tab:
            url = current_tab.get_url()
            title = current_tab.get_title()
            if url and url != "about:blank":
                # Add bookmark via backend
                try:
                    import requests
                    response = requests.post(
                        'http://127.0.0.1:5000/api/bookmarks',
                        json={'title': title, 'url': url},
                        timeout=5
                    )
                    if response.status_code == 200:
                        self.update_status("Bookmark added")
                        self.bookmarks_panel.refresh_bookmarks()
                    else:
                        messagebox.showerror("Error", "Failed to add bookmark")
                except Exception as e:
                    self.logger.error(f"Error adding bookmark: {e}")
                    messagebox.showerror("Error", f"Failed to add bookmark: {e}")
    
    def clear_history(self):
        """Clear browsing history."""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all browsing history?"):
            try:
                import requests
                response = requests.delete('http://127.0.0.1:5000/api/history', timeout=5)
                if response.status_code == 200:
                    self.update_status("History cleared")
                    self.history_panel.refresh_history()
                else:
                    messagebox.showerror("Error", "Failed to clear history")
            except Exception as e:
                self.logger.error(f"Error clearing history: {e}")
                messagebox.showerror("Error", f"Failed to clear history: {e}")
    
    def clear_browsing_data(self):
        """Clear all browsing data."""
        # Implement comprehensive data clearing
        pass
    
    def save_session(self):
        """Save current session."""
        tabs_data = []
        for tab_frame in self.notebook.tabs():
            # Get tab data for each tab
            pass
        
        # Save session via backend
        pass
    
    def restore_last_session(self):
        """Restore last session."""
        # Implement session restoration
        pass
    
    def new_window(self):
        """Open new browser window."""
        # Implement new window
        pass
    
    def open_file(self):
        """Open local file."""
        # Implement file opening
        pass
    
    def save_page(self):
        """Save current page."""
        # Implement page saving
        pass
    
    def print_page(self):
        """Print current page."""
        # Implement printing
        pass
    
    def find(self):
        """Find on page."""
        # Implement find functionality
        pass
    
    def find_next(self):
        """Find next occurrence."""
        # Implement find next
        pass
    
    def undo(self):
        """Undo action."""
        # Implement undo
        pass
    
    def redo(self):
        """Redo action."""
        # Implement redo
        pass
    
    def cut(self):
        """Cut selection."""
        # Implement cut
        pass
    
    def copy(self):
        """Copy selection."""
        # Implement copy
        pass
    
    def paste(self):
        """Paste content."""
        # Implement paste
        pass
    
    def zoom_in(self):
        """Zoom in."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.zoom_in()
            self.update_zoom_label()
    
    def zoom_out(self):
        """Zoom out."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.zoom_out()
            self.update_zoom_label()
    
    def reset_zoom(self):
        """Reset zoom to default."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.reset_zoom()
            self.update_zoom_label()
    
    def update_zoom_label(self):
        """Update zoom label."""
        current_tab = self.get_current_tab()
        if current_tab:
            zoom_level = current_tab.get_zoom_level()
            self.zoom_label.configure(text=f"{int(zoom_level * 100)}%")
    
    def quit_browser(self):
        """Quit the browser."""
        if self.config.get('browser', {}).get('restore_last_session', False):
            self.save_session()
        
        # Cleanup
        self.backend_app.stop()
        self.extension_manager.unload_extensions()
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the browser main loop."""
        self.root.mainloop()
