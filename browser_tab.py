"""
Browser Tab

This module contains the browser tab implementation with web content rendering,
navigation controls, and tab management.
"""

import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView


class BrowserTab(QWidget):
    """Individual browser tab with web content rendering."""
    
    # Signals
    title_changed = pyqtSignal(str)
    url_changed = pyqtSignal(str)
    loading_changed = pyqtSignal(bool)
    load_progress = pyqtSignal(int)
    
    def __init__(self, parent=None, url=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Tab state
        self.current_url = url or "about:blank"
        self.title = "New Tab"
        self.loading = False
        self.zoom_level = 1.0
        self.can_go_back_state = False
        self.can_go_forward_state = False
        
        # Create tab layout
        self.setup_tab_layout()
        
        # Setup browser component
        self.setup_browser()
        
        # Load initial URL
        if url:
            self.load_url(url)
    
    def setup_tab_layout(self):
        """Setup the tab layout with browser and controls."""
        # Main frame for tab content
        self.frame = ttk.Frame(self.notebook)
        
        # Tab header with close button
        self.tab_header_frame = ttk.Frame(self.notebook)
        
        # Tab title label
        self.title_label = ttk.Label(self.tab_header_frame, text=self.title)
        self.title_label.pack(side="left", padx=5)
        
        # Close button
        self.close_button = ttk.Button(
            self.tab_header_frame, text="×", width=3,
            command=lambda: self.main_window.close_tab(self.frame)
        )
        self.close_button.pack(side="right", padx=2)
        
        # Find the tab index and update tab
        tab_count = len(self.notebook.tabs())
        self.notebook.insert(tab_count, self.frame, text=self.title)
    
    def setup_browser(self):
        """Setup the browser rendering component."""
        if CEF_AVAILABLE:
            self.setup_cef_browser()
        else:
            self.setup_placeholder_browser()
    
    def setup_cef_browser(self):
        """Setup CEF Python browser."""
        try:
            # Create browser info
            browser_info = cef.BrowserSettings()
            browser_info.windowless_frame_rate = 60
            
            # Create browser
            self.browser = cef.CreateBrowserSync(
                cef.WindowInfo(),
                url=self.current_url,
                settings=browser_info
            )
            
            # Setup browser bindings
            self.setup_cef_bindings()
            
        except Exception as e:
            self.logger.error(f"Error setting up CEF browser: {e}")
            self.setup_placeholder_browser()
    
    def setup_placeholder_browser(self):
        """Setup placeholder browser when CEF is not available."""
        # Create a simple text widget as placeholder
        self.browser_frame = ctk.CTkFrame(self.frame)
        self.browser_frame.pack(fill="both", expand=True)
        
        # Content area
        self.content_text = ctk.CTkTextbox(self.browser_frame)
        self.content_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add placeholder content
        self.content_text.insert("0.0", """
Advanced Web Browser - Placeholder Mode

CEF Python is not installed or could not be loaded.
This is a placeholder implementation.

Features available in this mode:
- Basic URL navigation
- Tab management
- Bookmarks and history (via backend)
- Settings and configuration

To enable full web browsing:
1. Install CEF Python: pip install cefpython3
2. Restart the browser

Current URL: about:blank
        """.strip())
        
        self.content_text.configure(state="disabled")
    
    def setup_cef_bindings(self):
        """Setup CEF browser event bindings."""
        if not CEF_AVAILABLE:
            return
        
        # Create client handler for browser events
        class BrowserClientHandler:
            def __init__(self, tab):
                self.tab = tab
            
            def OnLoadingStateChange(self, browser, is_loading, can_go_back, can_go_forward):
                self.tab.loading = is_loading
                self.tab.can_go_back_state = can_go_back
                self.tab.can_go_forward_state = can_go_forward
                
                # Update UI
                if is_loading:
                    self.tab.main_window.show_progress(0.5)
                    self.tab.main_window.update_status("Loading...")
                else:
                    self.tab.main_window.show_progress(0)
                    self.tab.main_window.update_status("Ready")
                
                self.tab.main_window.update_navigation_buttons(self.tab)
            
            def OnTitleChange(self, browser, title):
                self.tab.title = title
                self.tab.update_tab_title()
                self.tab.main_window.on_tab_changed(None)
            
            def OnAddressChange(self, browser, url):
                self.tab.current_url = url
                self.tab.main_window.address_bar.set_url(url)
        
        # Set client handler
        self.browser.SetClientHandler(BrowserClientHandler(self))
    
    def load_url(self, url: str):
        """Load a URL in the browser."""
        if not url:
            return
        
        # Validate and sanitize URL
        sanitized_url = self.sanitize_url(url)
        
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            try:
                self.browser.LoadURL(sanitized_url)
                self.current_url = sanitized_url
                self.loading = True
                self.main_window.update_status(f"Loading {sanitized_url}...")
            except Exception as e:
                self.logger.error(f"Error loading URL {sanitized_url}: {e}")
                self.show_error_page(f"Failed to load URL: {e}")
        else:
            # Placeholder mode - simulate loading
            self.simulate_url_load(sanitized_url)
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize and normalize URL."""
        # Check if it's a search query or URL
        if not url.startswith(('http://', 'https://', 'about:', 'file://')):
            # Check if it looks like a domain
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                # Treat as search query
                url = f'https://www.google.com/search?q={url}'
        
        # Apply security service if available
        if hasattr(self.main_window, 'backend_app'):
            try:
                # Get security service to sanitize URL
                pass  # Would call security service
            except:
                pass
        
        return url
    
    def simulate_url_load(self, url: str):
        """Simulate URL loading in placeholder mode."""
        self.current_url = url
        self.loading = True
        
        # Update UI
        self.main_window.address_bar.set_url(url)
        self.main_window.update_status(f"Loading {url}...")
        self.main_window.show_progress(0.5)
        
        # Simulate loading delay
        self.frame.after(1000, self.finish_url_load)
    
    def finish_url_load(self):
        """Finish simulated URL loading."""
        self.loading = False
        
        # Update title based on URL
        parsed_url = urlparse(self.current_url)
        if parsed_url.netloc:
            self.title = parsed_url.netloc
        else:
            self.title = "New Tab"
        
        self.update_tab_title()
        
        # Update content
        if hasattr(self, 'content_text'):
            self.content_text.configure(state="normal")
            self.content_text.delete("0.0", "end")
            
            content = f"""
Loaded URL: {self.current_url}

This is a placeholder implementation.
In a full implementation, this would display the actual web content.

Title: {self.title}
URL: {self.current_url}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Features that would be available:
- Full HTML rendering
- JavaScript execution
- CSS styling
- Form submissions
- Link navigation
- Media playback
            """.strip()
            
            self.content_text.insert("0.0", content)
            self.content_text.configure(state="disabled")
        
        # Update UI
        self.main_window.show_progress(0)
        self.main_window.update_status("Ready")
        self.main_window.on_tab_changed(None)
    
    def show_error_page(self, error_message: str):
        """Show an error page."""
        if hasattr(self, 'content_text'):
            self.content_text.configure(state="normal")
            self.content_text.delete("0.0", "end")
            
            content = f"""
Error Page

Failed to load page: {error_message}

This could be due to:
- Network connectivity issues
- Invalid URL
- Server not responding
- Security restrictions

Please check the URL and try again.
            """.strip()
            
            self.content_text.insert("0.0", content)
            self.content_text.configure(state="disabled")
        
        self.title = "Error"
        self.update_tab_title()
        self.main_window.update_status("Error")
    
    def update_tab_title(self):
        """Update the tab title display."""
        # Update tab title in notebook
        tab_index = None
        for i, tab in enumerate(self.notebook.tabs()):
            if tab == self.frame:
                tab_index = i
                break
        
        if tab_index is not None:
            # Truncate long titles
            display_title = self.title[:30] + "..." if len(self.title) > 30 else self.title
            self.notebook.tab(self.frame, text=display_title)
        
        # Update title label
        if hasattr(self, 'title_label'):
            display_title = self.title[:20] + "..." if len(self.title) > 20 else self.title
            self.title_label.configure(text=display_title)
    
    def go_back(self):
        """Navigate back in history."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            if self.browser.CanGoBack():
                self.browser.GoBack()
        else:
            # Placeholder - show message
            self.main_window.update_status("Back navigation not available in placeholder mode")
    
    def go_forward(self):
        """Navigate forward in history."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            if self.browser.CanGoForward():
                self.browser.GoForward()
        else:
            # Placeholder - show message
            self.main_window.update_status("Forward navigation not available in placeholder mode")
    
    def refresh(self):
        """Refresh the current page."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.Reload()
        else:
            # Placeholder - reload current URL
            if self.current_url and self.current_url != "about:blank":
                self.load_url(self.current_url)
    
    def stop(self):
        """Stop loading the current page."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.Stop()
        else:
            # Placeholder - stop loading
            self.loading = False
            self.main_window.show_progress(0)
            self.main_window.update_status("Stopped")
    
    def zoom_in(self):
        """Zoom in the page."""
        self.zoom_level = min(self.zoom_level + 0.1, 3.0)
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.SetZoomLevel(self.zoom_level)
    
    def zoom_out(self):
        """Zoom out the page."""
        self.zoom_level = max(self.zoom_level - 0.1, 0.5)
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.SetZoomLevel(self.zoom_level)
    
    def reset_zoom(self):
        """Reset zoom to default."""
        self.zoom_level = 1.0
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.SetZoomLevel(self.zoom_level)
    
    def get_url(self) -> str:
        """Get current URL."""
        return self.current_url
    
    def get_title(self) -> str:
        """Get current page title."""
        return self.title
    
    def get_zoom_level(self) -> float:
        """Get current zoom level."""
        return self.zoom_level
    
    def can_go_back(self) -> bool:
        """Check if can go back."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            return self.browser.CanGoBack()
        return self.can_go_back_state
    
    def can_go_forward(self) -> bool:
        """Check if can go forward."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            return self.browser.CanGoForward()
        return self.can_go_forward_state
    
    def find_text(self, text: str, forward: bool = True):
        """Find text on the page."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            # Implement find functionality
            pass
        else:
            # Placeholder - simple text search in content
            if hasattr(self, 'content_text'):
                self.content_text.configure(state="normal")
                content = self.content_text.get("0.0", "end")
                
                if text.lower() in content.lower():
                    # Simple highlight (would need proper implementation)
                    self.main_window.update_status(f"Found '{text}'")
                else:
                    self.main_window.update_status(f"'{text}' not found")
                
                self.content_text.configure(state="disabled")
    
    def print_page(self):
        """Print the current page."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.GetFocusedFrame().Print()
        else:
            # Placeholder - show print dialog
            self.main_window.update_status("Printing not available in placeholder mode")
    
    def save_page(self, file_path: str):
        """Save the current page."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            # Implement save functionality
            pass
        else:
            # Placeholder - save content to file
            try:
                if hasattr(self, 'content_text'):
                    content = self.content_text.get("0.0", "end")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.main_window.update_status(f"Page saved to {file_path}")
            except Exception as e:
                self.logger.error(f"Error saving page: {e}")
                self.main_window.update_status("Error saving page")
    
    def get_page_source(self) -> str:
        """Get the page source HTML."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            # Implement getting page source
            return ""
        else:
            # Placeholder - return content
            if hasattr(self, 'content_text'):
                return self.content_text.get("0.0", "end")
            return ""
    
    def execute_javascript(self, script: str):
        """Execute JavaScript in the page."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            self.browser.GetFocusedFrame().ExecuteJavaScript(script, "", 0)
        else:
            # Placeholder - show message
            self.main_window.update_status("JavaScript execution not available in placeholder mode")
    
    def cleanup(self):
        """Cleanup browser resources."""
        if CEF_AVAILABLE and hasattr(self, 'browser'):
            try:
                self.browser.CloseBrowser(True)
                self.browser = None
            except:
                pass


# Import datetime for placeholder mode
from datetime import datetime
