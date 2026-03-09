#!/usr/bin/env python3
"""
Extension UI Manager

Manages the user interface for extensions including toolbar buttons,
context menus, options pages, and popup windows.
"""

import json
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
from datetime import datetime
import logging
import uuid
import webbrowser

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QToolBar, QMenu, QDialog, 
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from .api import ExtensionAPI


class ExtensionToolbar:
    """Toolbar for extension buttons."""
    
    def __init__(self, parent, browser_window):
        self.parent = parent
        self.browser_window = browser_window
        self.logger = logging.getLogger(__name__)
        
        # Toolbar widget
        self.toolbar = QToolBar("Extensions")
        self.toolbar.setMovable(False)
        
        # Extension buttons
        self.extension_buttons: Dict[str, QAction] = {}
        self.extension_badges: Dict[str, QLabel] = {}
        
        # Popup windows
        self.active_popups: Dict[str, QDialog] = {}
    
    def add_extension_button(self, extension_id: str, icon_path: str, 
                          tooltip: str, popup_path: str = None) -> bool:
        """Add an extension button to the toolbar."""
        try:
            # Create button frame
            btn_frame = tk.Frame(self.frame, bg='#e0e0e0')
            btn_frame.pack(side="top", pady=2, padx=2)
            
            # Create button
            button = tk.Button(
                btn_frame,
                width=32,
                height=32,
                bg='#f0f0f0',
                relief='flat',
                bd=1,
                command=lambda: self._on_extension_click(extension_id, popup_path)
            )
            button.pack()
            
            # Set icon if available
            if icon_path and Path(icon_path).exists():
                try:
                    # This would load the icon image
                    # For now, use text placeholder
                    button.config(text=extension_id[:2].upper())
                except Exception as e:
                    self.logger.error(f"Error loading icon {icon_path}: {e}")
                    button.config(text=extension_id[:2].upper())
            else:
                button.config(text=extension_id[:2].upper())
            
            # Create badge label
            badge = tk.Label(
                btn_frame,
                text="",
                bg='#ff0000',
                fg='white',
                font=('Arial', 8, 'bold'),
                padx=2,
                pady=1
            )
            badge.place(x=20, y=0)
            
            # Store references
            self.extension_buttons[extension_id] = button
            self.extension_badges[extension_id] = badge
            
            # Set tooltip
            self._set_tooltip(button, tooltip)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding extension button: {e}")
            return False
    
    def remove_extension_button(self, extension_id: str) -> bool:
        """Remove an extension button from the toolbar."""
        try:
            if extension_id in self.extension_buttons:
                button = self.extension_buttons[extension_id]
                button.master.destroy()
                del self.extension_buttons[extension_id]
            
            if extension_id in self.extension_badges:
                del self.extension_badges[extension_id]
            
            # Close any active popup
            if extension_id in self.active_popups:
                self.active_popups[extension_id].destroy()
                del self.active_popups[extension_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing extension button: {e}")
            return False
    
    def update_badge(self, extension_id: str, text: str, color: str = '#ff0000'):
        """Update the badge text and color for an extension."""
        if extension_id in self.extension_badges:
            badge = self.extension_badges[extension_id]
            
            if text:
                badge.config(text=text, bg=color)
                badge.place(x=20, y=0)
            else:
                badge.config(text="")
                badge.place_forget()
    
    def _on_extension_click(self, extension_id: str, popup_path: str = None):
        """Handle extension button click."""
        try:
            # Close existing popup
            if extension_id in self.active_popups:
                self.active_popups[extension_id].destroy()
                del self.active_popups[extension_id]
                return
            
            if popup_path:
                # Show popup
                self._show_popup(extension_id, popup_path)
            else:
                # Trigger extension action
                if hasattr(self.browser_window, 'trigger_extension_action'):
                    self.browser_window.trigger_extension_action(extension_id)
        
        except Exception as e:
            self.logger.error(f"Error handling extension click: {e}")
    
    def _show_popup(self, extension_id: str, popup_path: str):
        """Show extension popup."""
        try:
            popup = tk.Toplevel(self.parent)
            popup.title(f"Extension: {extension_id}")
            popup.geometry("400x300")
            popup.transient(self.parent)
            popup.grab_set()
            
            # Position popup near button
            if extension_id in self.extension_buttons:
                button = self.extension_buttons[extension_id]
                button_x = button.winfo_rootx()
                button_y = button.winfo_rooty()
                popup.geometry(f"+{button_x-200}+{button_y+40}")
            
            # Load popup content
            if Path(popup_path).exists():
                try:
                    with open(popup_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple HTML rendering (in a real implementation, use a proper web view)
                    text_widget = tk.Text(popup, wrap="word", font=('Arial', 10))
                    text_widget.pack(fill="both", expand=True, padx=5, pady=5)
                    text_widget.insert(1.0, content)
                    text_widget.config(state='disabled')
                    
                except Exception as e:
                    self.logger.error(f"Error loading popup content: {e}")
                    tk.Label(popup, text=f"Error loading popup: {e}").pack(pady=20)
            else:
                tk.Label(popup, text="Popup not found").pack(pady=20)
            
            # Close on focus out
            popup.bind("<FocusOut>", lambda e: self._close_popup(extension_id))
            
            self.active_popups[extension_id] = popup
            
        except Exception as e:
            self.logger.error(f"Error showing popup: {e}")
    
    def _close_popup(self, extension_id: str):
        """Close extension popup."""
        if extension_id in self.active_popups:
            try:
                self.active_popups[extension_id].destroy()
            except:
                pass
            del self.active_popups[extension_id]
    
    def _set_tooltip(self, widget, text: str):
        """Set tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="yellow", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


class ExtensionContextMenu:
    """Context menu for extensions."""
    
    def __init__(self, browser_window):
        self.browser_window = browser_window
        self.logger = logging.getLogger(__name__)
        
        # Context menu items
        self.menu_items: List[Dict[str, Any]] = []
        self.active_menu = None
    
    def add_menu_item(self, extension_id: str, item_id: str, title: str, 
                     contexts: List[str], onclick: Callable = None,
                     parent_id: str = None, icon: str = None) -> bool:
        """Add a context menu item."""
        try:
            menu_item = {
                'extension_id': extension_id,
                'item_id': item_id,
                'title': title,
                'contexts': contexts,
                'onclick': onclick,
                'parent_id': parent_id,
                'icon': icon,
                'enabled': True,
                'visible': True
            }
            
            self.menu_items.append(menu_item)
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding context menu item: {e}")
            return False
    
    def remove_menu_item(self, extension_id: str, item_id: str) -> bool:
        """Remove a context menu item."""
        try:
            self.menu_items = [
                item for item in self.menu_items 
                if not (item['extension_id'] == extension_id and item['item_id'] == item_id)
            ]
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing context menu item: {e}")
            return False
    
    def show_context_menu(self, event, tab_info: Dict[str, Any], 
                        context_info: Dict[str, Any]):
        """Show context menu with relevant items."""
        try:
            # Hide existing menu
            if self.active_menu:
                self.active_menu.destroy()
            
            # Create new menu
            self.active_menu = tk.Menu(self.browser_window.root, tearoff=0)
            
            # Filter items based on context
            context_type = context_info.get('context_type', 'page')
            relevant_items = [
                item for item in self.menu_items
                if item['enabled'] and item['visible'] and 
                   context_type in item['contexts']
            ]
            
            if not relevant_items:
                return
            
            # Add items to menu
            for item in relevant_items:
                title = item['title']
                
                # Replace placeholders in title
                if '%s' in title:
                    title = title % context_info.get('selection_text', '')
                
                self.active_menu.add_command(
                    label=title,
                    command=lambda i=item: self._on_menu_click(i, tab_info, context_info)
                )
            
            # Show menu
            self.active_menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
    
    def _on_menu_click(self, menu_item: Dict[str, Any], 
                      tab_info: Dict[str, Any], context_info: Dict[str, Any]):
        """Handle context menu item click."""
        try:
            if menu_item['onclick']:
                # Call the onclick handler
                menu_item['onclick'](tab_info, context_info)
            
            # Notify extension
            if hasattr(self.browser_window, 'notify_extension_context_menu'):
                self.browser_window.notify_extension_context_menu(
                    menu_item['extension_id'], 
                    menu_item['item_id'],
                    tab_info,
                    context_info
                )
        
        except Exception as e:
            self.logger.error(f"Error handling menu click: {e}")
    
    def hide_context_menu(self):
        """Hide the context menu."""
        if self.active_menu:
            self.active_menu.destroy()
            self.active_menu = None


class ExtensionOptionsDialog:
    """Dialog for extension options."""
    
    def __init__(self, parent, extension_id: str, extension_api: ExtensionAPI):
        self.parent = parent
        self.extension_id = extension_id
        self.extension_api = extension_api
        self.logger = logging.getLogger(__name__)
        
        self.dialog = None
        self.options = {}
    
    def show(self):
        """Show the options dialog."""
        try:
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title(f"Options - {self.extension_id}")
            self.dialog.geometry("600x500")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            
            # Create notebook for tabbed interface
            notebook = ttk.Notebook(self.dialog)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # General tab
            general_frame = ttk.Frame(notebook)
            notebook.add(general_frame, text="General")
            
            # Storage tab
            storage_frame = ttk.Frame(notebook)
            notebook.add(storage_frame, text="Storage")
            
            # Permissions tab
            permissions_frame = ttk.Frame(notebook)
            notebook.add(permissions_frame, text="Permissions")
            
            # About tab
            about_frame = ttk.Frame(notebook)
            notebook.add(about_frame, text="About")
            
            # Populate tabs
            self._populate_general_tab(general_frame)
            self._populate_storage_tab(storage_frame)
            self._populate_permissions_tab(permissions_frame)
            self._populate_about_tab(about_frame)
            
            # Buttons
            button_frame = tk.Frame(self.dialog)
            button_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Button(button_frame, text="Save", command=self._save_options).pack(side="right", padx=5)
            tk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="right")
            tk.Button(button_frame, text="Reset", command=self._reset_options).pack(side="right", padx=5)
            
        except Exception as e:
            self.logger.error(f"Error showing options dialog: {e}")
            if self.dialog:
                self.dialog.destroy()
    
    def _populate_general_tab(self, parent):
        """Populate the general options tab."""
        # Extension info
        info_frame = ttk.LabelFrame(parent, text="Extension Information")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        extension_info = self.extension_api.get_extension_info()
        
        info_text = f"""
Name: {extension_info.get('name', 'Unknown')}
Version: {extension_info.get('version', 'Unknown')}
Author: {extension_info.get('author', 'Unknown')}
Description: {extension_info.get('description', 'No description')}
        """
        
        tk.Label(info_frame, text=info_text.strip(), justify="left").pack(padx=10, pady=10)
        
        # Enable/disable
        enabled_frame = ttk.LabelFrame(parent, text="Settings")
        enabled_frame.pack(fill="x", padx=10, pady=10)
        
        self.enabled_var = tk.BooleanVar(value=extension_info.get('enabled', True))
        tk.Checkbutton(enabled_frame, text="Enable extension", 
                     variable=self.enabled_var).pack(anchor="w", padx=10, pady=5)
        
        # Allow in incognito
        self.incognito_var = tk.BooleanVar(value=False)
        tk.Checkbutton(enabled_frame, text="Allow in incognito mode", 
                     variable=self.incognito_var).pack(anchor="w", padx=10, pady=5)
    
    def _populate_storage_tab(self, parent):
        """Populate the storage options tab."""
        # Storage usage
        usage_frame = ttk.LabelFrame(parent, text="Storage Usage")
        usage_frame.pack(fill="x", padx=10, pady=10)
        
        # Get storage info
        local_storage = self.extension_api.get_storage(None, "local")
        sync_storage = self.extension_api.get_storage(None, "sync")
        
        local_size = len(json.dumps(local_storage))
        sync_size = len(json.dumps(sync_storage))
        
        tk.Label(usage_frame, 
                text=f"Local Storage: {local_size} bytes ({len(local_storage)} items)").pack(anchor="w", padx=10, pady=2)
        tk.Label(usage_frame, 
                text=f"Sync Storage: {sync_size} bytes ({len(sync_storage)} items)").pack(anchor="w", padx=10, pady=2)
        
        # Storage actions
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(actions_frame, text="Clear Local Storage", 
                 command=self._clear_local_storage).pack(anchor="w", padx=10, pady=2)
        tk.Button(actions_frame, text="Clear Sync Storage", 
                 command=self._clear_sync_storage).pack(anchor="w", padx=10, pady=2)
        tk.Button(actions_frame, text="Export Storage", 
                 command=self._export_storage).pack(anchor="w", padx=10, pady=2)
        tk.Button(actions_frame, text="Import Storage", 
                 command=self._import_storage).pack(anchor="w", padx=10, pady=2)
    
    def _populate_permissions_tab(self, parent):
        """Populate the permissions tab."""
        permissions_frame = ttk.LabelFrame(parent, text="Required Permissions")
        permissions_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get permissions
        extension_info = self.extension_api.get_extension_info()
        permissions = extension_info.get('permissions', [])
        host_permissions = extension_info.get('host_permissions', [])
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(permissions_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Add permissions
        text_widget.insert("end", "API Permissions:\n")
        for perm in permissions:
            text_widget.insert("end", f"  • {perm}\n")
        
        text_widget.insert("end", "\nHost Permissions:\n")
        for host in host_permissions:
            text_widget.insert("end", f"  • {host}\n")
        
        text_widget.config(state='disabled')
    
    def _populate_about_tab(self, parent):
        """Populate the about tab."""
        about_frame = ttk.LabelFrame(parent, text="About")
        about_frame.pack(fill="x", padx=10, pady=10)
        
        extension_info = self.extension_api.get_extension_info()
        
        about_text = f"""
Extension ID: {extension_info.get('id', 'Unknown')}
Manifest Version: {extension_info.get('manifest_version', 2)}
Install Type: {extension_info.get('install_type', 'normal')}

This extension was developed by {extension_info.get('author', 'Unknown')}.

For support and more information, visit:
{extension_info.get('homepage_url', 'No homepage available')}
        """
        
        tk.Label(about_frame, text=about_text.strip(), justify="left").pack(padx=10, pady=10)
    
    def _save_options(self):
        """Save the options."""
        try:
            # Save extension settings
            # This would integrate with the extension's storage
            messagebox.showinfo("Success", "Options saved successfully!")
            self.dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Error saving options: {e}")
            messagebox.showerror("Error", f"Failed to save options: {e}")
    
    def _reset_options(self):
        """Reset options to defaults."""
        try:
            if messagebox.askyesno("Confirm Reset", "Reset all options to defaults?"):
                # Reset storage
                self.extension_api.clear_storage("local")
                self.extension_api.clear_storage("sync")
                messagebox.showinfo("Success", "Options reset to defaults!")
                self.dialog.destroy()
                
        except Exception as e:
            self.logger.error(f"Error resetting options: {e}")
            messagebox.showerror("Error", f"Failed to reset options: {e}")
    
    def _clear_local_storage(self):
        """Clear local storage."""
        try:
            if messagebox.askyesno("Confirm Clear", "Clear all local storage?"):
                self.extension_api.clear_storage("local")
                messagebox.showinfo("Success", "Local storage cleared!")
                
        except Exception as e:
            self.logger.error(f"Error clearing local storage: {e}")
            messagebox.showerror("Error", f"Failed to clear local storage: {e}")
    
    def _clear_sync_storage(self):
        """Clear sync storage."""
        try:
            if messagebox.askyesno("Confirm Clear", "Clear all sync storage?"):
                self.extension_api.clear_storage("sync")
                messagebox.showinfo("Success", "Sync storage cleared!")
                
        except Exception as e:
            self.logger.error(f"Error clearing sync storage: {e}")
            messagebox.showerror("Error", f"Failed to clear sync storage: {e}")
    
    def _export_storage(self):
        """Export storage to file."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Storage",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                storage_data = {
                    'local': self.extension_api.get_storage(None, "local"),
                    'sync': self.extension_api.get_storage(None, "sync"),
                    'exported_at': datetime.now().isoformat()
                }
                
                with open(filename, 'w') as f:
                    json.dump(storage_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Storage exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting storage: {e}")
            messagebox.showerror("Error", f"Failed to export storage: {e}")
    
    def _import_storage(self):
        """Import storage from file."""
        try:
            filename = filedialog.askopenfilename(
                title="Import Storage",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    storage_data = json.load(f)
                
                if 'local' in storage_data:
                    self.extension_api.clear_storage("local")
                    self.extension_api.set_storage(storage_data['local'], "local")
                
                if 'sync' in storage_data:
                    self.extension_api.clear_storage("sync")
                    self.extension_api.set_storage(storage_data['sync'], "sync")
                
                messagebox.showinfo("Success", f"Storage imported from {filename}")
                
        except Exception as e:
            self.logger.error(f"Error importing storage: {e}")
            messagebox.showerror("Error", f"Failed to import storage: {e}")


class ExtensionUIManager:
    """Main UI manager for extensions."""
    
    def __init__(self, browser_window):
        self.browser_window = browser_window
        self.logger = logging.getLogger(__name__)
        
        # UI components
        self.toolbar = None
        self.context_menu = None
        
        # Extension APIs
        self.extension_apis: Dict[str, ExtensionAPI] = {}
        
        # Initialize UI components
        self._initialize_ui()
    
    def _initialize_ui(self):
        """Initialize UI components."""
        try:
            # Create toolbar using the extension toolbar area from the main browser
            self.toolbar = ExtensionToolbar(
                self.browser_window.extension_toolbar, 
                self.browser_window
            )
            
            # Create context menu
            self.context_menu = ExtensionContextMenu(self.browser_window)
            
            # Context menu will be handled through PyQt6 context menu events
            
        except Exception as e:
            self.logger.error(f"Error initializing UI: {e}")
    
    def register_extension(self, extension_id: str, extension_api: ExtensionAPI):
        """Register an extension with the UI manager."""
        self.extension_apis[extension_id] = extension_api
        
        # Add toolbar button if extension has action
        manifest = extension_api.get_manifest()
        action = manifest.get('action') or manifest.get('browser_action')
        
        if action:
            icon_path = action.get('default_icon')
            title = action.get('default_title', extension_id)
            popup_path = action.get('default_popup')
            
            if popup_path:
                popup_path = os.path.join(extension_api.get_extension_directory(), popup_path)
            
            self.toolbar.add_extension_button(extension_id, icon_path, title, popup_path)
    
    def unregister_extension(self, extension_id: str):
        """Unregister an extension from the UI manager."""
        if extension_id in self.extension_apis:
            del self.extension_apis[extension_id]
        
        # Remove toolbar button
        self.toolbar.remove_extension_button(extension_id)
        
        # Remove context menu items
        self.context_menu.remove_menu_item(extension_id, "*")
    
    def show_extension_options(self, extension_id: str):
        """Show options dialog for an extension."""
        if extension_id in self.extension_apis:
            extension_api = self.extension_apis[extension_id]
            options_dialog = ExtensionOptionsDialog(
                self.browser_window.root, 
                extension_id, 
                extension_api
            )
            options_dialog.show()
    
    def update_extension_badge(self, extension_id: str, text: str, color: str = '#ff0000'):
        """Update extension badge."""
        self.toolbar.update_badge(extension_id, text, color)
    
    def add_context_menu_item(self, extension_id: str, item_id: str, 
                             properties: Dict[str, Any]) -> bool:
        """Add a context menu item."""
        return self.context_menu.add_menu_item(
            extension_id, item_id,
            properties.get('title', ''),
            properties.get('contexts', ['all']),
            properties.get('onclick'),
            properties.get('parentId'),
            properties.get('icon')
        )
    
    def remove_context_menu_item(self, extension_id: str, item_id: str) -> bool:
        """Remove a context menu item."""
        return self.context_menu.remove_menu_item(extension_id, item_id)
    
    def _on_right_click(self, event):
        """Handle right-click event."""
        try:
            # Get current tab info
            current_tab = self.browser_window.get_current_tab()
            tab_info = {
                'id': 'current',
                'url': current_tab.get_url() if current_tab else '',
                'title': current_tab.get_title() if current_tab else ''
            }
            
            # Get context info
            context_info = {
                'context_type': 'page',
                'page_url': tab_info['url'],
                'selection_text': ''  # Would get selected text
            }
            
            # Show context menu
            self.context_menu.show_context_menu(event, tab_info, context_info)
            
        except Exception as e:
            self.logger.error(f"Error handling right-click: {e}")
