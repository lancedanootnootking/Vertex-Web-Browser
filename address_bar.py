"""
Address Bar

This module contains the address bar implementation with autocomplete,
URL validation, and search functionality.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import logging
from typing import List, Optional, Callable
import requests
from urllib.parse import urlparse


class AddressBar:
    """Address bar with autocomplete and search functionality."""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
        # State
        self.current_url = ""
        self.suggestions = []
        self.selected_suggestion_index = -1
        
        # Setup address bar components
        self.setup_address_bar()
        
        # Bind events
        self.bind_events()
    
    def setup_address_bar(self):
        """Setup the address bar components."""
        # Main frame
        self.frame = ctk.CTkFrame(self.parent)
        
        # URL entry
        self.url_entry = ctk.CTkEntry(
            self.frame,
            placeholder_text="Enter URL or search...",
            width=400,
            height=30
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        
        # Security indicator
        self.security_indicator = ctk.CTkLabel(self.frame, text="Secure", width=20)
        self.security_indicator.pack(side="right", padx=5)
        
        # Autocomplete listbox (initially hidden)
        self.autocomplete_frame = tk.Toplevel(self.parent)
        self.autocomplete_frame.withdraw()
        self.autocomplete_frame.overrideredirect(True)
        
        self.autocomplete_listbox = tk.Listbox(
            self.autocomplete_frame,
            height=8,
            font=("Arial", 10)
        )
        self.autocomplete_listbox.pack(fill="both", expand=True)
        
        # Style autocomplete
        self.autocomplete_listbox.configure(
            selectbackground="#0078D7",
            selectforeground="white"
        )
    
    def bind_events(self):
        """Bind keyboard and mouse events."""
        # Entry events
        self.url_entry.bind("<KeyRelease>", self.on_key_release)
        self.url_entry.bind("<Return>", self.on_enter)
        self.url_entry.bind("<Escape>", self.hide_autocomplete)
        self.url_entry.bind("<Up>", self.on_arrow_up)
        self.url_entry.bind("<Down>", self.on_arrow_down)
        self.url_entry.bind("<Tab>", self.on_tab)
        
        # Focus events
        self.url_entry.bind("<FocusIn>", self.on_focus_in)
        self.url_entry.bind("<FocusOut>", self.on_focus_out)
        
        # Autocomplete events
        self.autocomplete_listbox.bind("<ButtonRelease-1>", self.on_suggestion_click)
        self.autocomplete_listbox.bind("<Return>", self.on_suggestion_select)
        
        # Hide autocomplete when clicking elsewhere
        self.parent.bind_all("<Button-1>", self.hide_on_click)
    
    def on_key_release(self, event):
        """Handle key release in address bar."""
        text = self.url_entry.get()
        
        # Show suggestions if text is not empty
        if text and len(text) > 2:
            self.show_suggestions(text)
        else:
            self.hide_autocomplete()
    
    def on_enter(self, event):
        """Handle Enter key press."""
        text = self.url_entry.get().strip()
        
        if self.autocomplete_frame.winfo_ismapped():
            # If autocomplete is visible, select the suggestion
            self.on_suggestion_select(None)
        else:
            # Navigate to URL
            self.navigate_to_url(text)
    
    def on_arrow_up(self, event):
        """Handle Up arrow key."""
        if self.autocomplete_frame.winfo_ismapped():
            self.select_previous_suggestion()
            return "break"  # Prevent default behavior
        return None
    
    def on_arrow_down(self, event):
        """Handle Down arrow key."""
        if self.autocomplete_frame.winfo_ismapped():
            self.select_next_suggestion()
            return "break"  # Prevent default behavior
        return None
    
    def on_tab(self, event):
        """Handle Tab key."""
        if self.autocomplete_frame.winfo_ismapped():
            self.on_suggestion_select(None)
            return "break"
        return None
    
    def on_focus_in(self, event):
        """Handle focus in event."""
        # Select all text when focused
        self.url_entry.select_range(0, "end")
    
    def on_focus_out(self, event):
        """Handle focus out event."""
        # Hide autocomplete when focus is lost
        self.hide_autocomplete()
    
    def on_suggestion_click(self, event):
        """Handle click on suggestion."""
        self.on_suggestion_select(event)
    
    def on_suggestion_select(self, event):
        """Handle selection of a suggestion."""
        if self.autocomplete_frame.winfo_ismapped():
            selection = self.autocomplete_listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(self.suggestions):
                    suggestion = self.suggestions[index]
                    self.url_entry.delete(0, "end")
                    self.url_entry.insert(0, suggestion['text'])
                    self.current_url = suggestion['url']
        
        self.hide_autocomplete()
        self.navigate_to_url(self.url_entry.get())
    
    def hide_on_click(self, event):
        """Hide autocomplete when clicking outside."""
        if event.widget not in [self.url_entry, self.autocomplete_listbox]:
            self.hide_autocomplete()
    
    def show_suggestions(self, query: str):
        """Show autocomplete suggestions for query."""
        try:
            # Get suggestions from backend
            suggestions = self.get_suggestions_from_backend(query)
            self.suggestions = suggestions
            
            if suggestions:
                # Update listbox
                self.autocomplete_listbox.delete(0, "end")
                for suggestion in suggestions:
                    display_text = suggestion.get('display_text', suggestion['text'])
                    self.autocomplete_listbox.insert("end", display_text)
                
                # Position and show autocomplete
                self.position_autocomplete()
                self.autocomplete_frame.deiconify()
                self.autocomplete_frame.lift()
                
                # Reset selection
                self.selected_suggestion_index = -1
            else:
                self.hide_autocomplete()
                
        except Exception as e:
            self.logger.error(f"Error showing suggestions: {e}")
            self.hide_autocomplete()
    
    def position_autocomplete(self):
        """Position autocomplete listbox below address bar."""
        try:
            # Get address bar position
            entry_x = self.url_entry.winfo_rootx()
            entry_y = self.url_entry.winfo_rooty()
            entry_height = self.url_entry.winfo_height()
            
            # Position autocomplete frame
            self.autocomplete_frame.geometry(
                f"{self.url_entry.winfo_width()}x200+{entry_x}+{entry_y + entry_height}"
            )
            
        except Exception as e:
            self.logger.error(f"Error positioning autocomplete: {e}")
    
    def hide_autocomplete(self, event=None):
        """Hide autocomplete suggestions."""
        self.autocomplete_frame.withdraw()
        self.selected_suggestion_index = -1
    
    def select_next_suggestion(self):
        """Select the next suggestion in the list."""
        if not self.suggestions:
            return
        
        self.selected_suggestion_index = min(
            self.selected_suggestion_index + 1,
            len(self.suggestions) - 1
        )
        
        self.autocomplete_listbox.selection_clear(0, "end")
        self.autocomplete_listbox.selection_set(self.selected_suggestion_index)
        self.autocomplete_listbox.see(self.selected_suggestion_index)
        
        # Update entry with selected suggestion
        if self.selected_suggestion_index >= 0:
            suggestion = self.suggestions[self.selected_suggestion_index]
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, suggestion['text'])
    
    def select_previous_suggestion(self):
        """Select the previous suggestion in the list."""
        if not self.suggestions:
            return
        
        self.selected_suggestion_index = max(
            self.selected_suggestion_index - 1,
            -1
        )
        
        if self.selected_suggestion_index >= 0:
            self.autocomplete_listbox.selection_clear(0, "end")
            self.autocomplete_listbox.selection_set(self.selected_suggestion_index)
            self.autocomplete_listbox.see(self.selected_suggestion_index)
            
            # Update entry with selected suggestion
            suggestion = self.suggestions[self.selected_suggestion_index]
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, suggestion['text'])
        else:
            # Restore original query
            # This would need to store the original query
            pass
    
    def get_suggestions_from_backend(self, query: str) -> List[dict]:
        """Get suggestions from backend services."""
        suggestions = []
        
        try:
            # Get history suggestions
            history_response = requests.get(
                'http://127.0.0.1:5000/api/history',
                params={'limit': 20, 'search': query},
                timeout=2
            )
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                for item in history_data[:5]:  # Limit to 5 history suggestions
                    suggestions.append({
                        'text': item['url'],
                        'url': item['url'],
                        'display_text': f"📄 {item['title']}",
                        'type': 'history',
                        'title': item['title']
                    })
            
            # Get bookmark suggestions
            bookmarks_response = requests.get(
                'http://127.0.0.1:5000/api/bookmarks',
                timeout=2
            )
            
            if bookmarks_response.status_code == 200:
                bookmarks_data = bookmarks_response.json()
                for item in bookmarks_data:
                    if query.lower() in item['title'].lower() or query.lower() in item['url'].lower():
                        suggestions.append({
                            'text': item['url'],
                            'url': item['url'],
                            'display_text': f"⭐ {item['title']}",
                            'type': 'bookmark',
                            'title': item['title']
                        })
            
            # Add search suggestions
            search_suggestions = [
                f"Search for '{query}'",
                f"Search '{query}' on Google",
                f"Search '{query}' on Wikipedia"
            ]
            
            for search_text in search_suggestions:
                suggestions.append({
                    'text': search_text,
                    'url': f"https://www.google.com/search?q={query}",
                    'display_text': f"Search {search_text}",
                    'type': 'search',
                    'query': query
                })
            
            # Sort suggestions by relevance (simple implementation)
            suggestions.sort(key=lambda x: (
                0 if x['type'] == 'bookmark' else
                1 if x['type'] == 'history' else
                2 if x['type'] == 'search' else 3
            ))
            
        except Exception as e:
            self.logger.error(f"Error getting suggestions from backend: {e}")
            # Add basic suggestions as fallback
            suggestions.append({
                'text': f"Search for '{query}'",
                'url': f"https://www.google.com/search?q={query}",
                'display_text': f"Search for '{query}'",
                'type': 'search',
                'query': query
            })
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    def navigate_to_url(self, url_text: str):
        """Navigate to the specified URL or search."""
        if not url_text.strip():
            return
        
        # Validate and format URL
        url = self.format_url(url_text)
        
        # Update current URL
        self.current_url = url
        
        # Update security indicator
        self.update_security_indicator(url)
        
        # Navigate in current tab
        current_tab = self.main_window.get_current_tab()
        if current_tab:
            current_tab.load_url(url)
    
    def format_url(self, url_text: str) -> str:
        """Format and validate URL."""
        url_text = url_text.strip()
        
        # Check if it's already a valid URL
        if url_text.startswith(('http://', 'https://', 'about:', 'file://')):
            return url_text
        
        # Check if it looks like a domain (contains dots and no spaces)
        if '.' in url_text and ' ' not in url_text:
            # Add https:// if no protocol specified
            return f'https://{url_text}'
        
        # Otherwise, treat as search query
        return f'https://www.google.com/search?q={url_text}'
    
    def update_security_indicator(self, url: str):
        """Update security indicator based on URL."""
        try:
            parsed_url = urlparse(url)
            
            if parsed_url.scheme == 'https':
                self.security_indicator.configure(text="Secure")
                self.security_indicator.configure(text_color="green")
            elif parsed_url.scheme == 'http':
                self.security_indicator.configure(text="Warning")
                self.security_indicator.configure(text_color="orange")
            elif url.startswith('about:'):
                self.security_indicator.configure(text="Info")
                self.security_indicator.configure(text_color="gray")
            else:
                self.security_indicator.configure(text="Web")
                self.security_indicator.configure(text_color="blue")
                
        except Exception:
            self.security_indicator.configure(text="?")
            self.security_indicator.configure(text_color="gray")
    
    def set_url(self, url: str):
        """Set the current URL in the address bar."""
        self.current_url = url
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self.update_security_indicator(url)
    
    def get_text(self) -> str:
        """Get the current text in the address bar."""
        return self.url_entry.get()
    
    def clear(self):
        """Clear the address bar."""
        self.url_entry.delete(0, "end")
        self.current_url = ""
        self.security_indicator.configure(text="Web")
    
    def focus(self):
        """Focus the address bar."""
        self.url_entry.focus_set()
    
    def select_all(self):
        """Select all text in the address bar."""
        self.url_entry.select_range(0, "end")
    
    def get_selected_text(self) -> str:
        """Get the selected text."""
        try:
            return self.url_entry.selection_get()
        except:
            return ""
    
    def copy_url(self):
        """Copy the current URL to clipboard."""
        if self.current_url:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.current_url)
            self.main_window.update_status("URL copied to clipboard")
    
    def paste_and_go(self):
        """Paste from clipboard and navigate."""
        try:
            clipboard_text = self.parent.clipboard_get()
            if clipboard_text:
                self.set_url(clipboard_text)
                self.navigate_to_url(clipboard_text)
        except:
            pass
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is properly formatted."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) or url.startswith('about:')
        except:
            return False
    
    def show_url_info(self):
        """Show information about current URL."""
        if not self.current_url:
            return
        
        try:
            # Get security report from backend
            response = requests.post(
                'http://127.0.0.1:5000/api/security/check-url',
                json={'url': self.current_url},
                timeout=5
            )
            
            if response.status_code == 200:
                security_data = response.json()
                is_safe = security_data.get('safe', True)
                
                if is_safe:
                    self.main_window.update_status("URL appears safe")
                else:
                    self.main_window.update_status("Warning: URL may be unsafe")
            
        except Exception as e:
            self.logger.error(f"Error checking URL security: {e}")
            self.main_window.update_status("Unable to verify URL safety")
    
    def cleanup(self):
        """Cleanup address bar resources."""
        try:
            self.autocomplete_frame.destroy()
        except:
            pass
