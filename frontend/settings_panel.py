"""
Settings Panel

This module contains the settings panel for configuring browser
preferences, themes, security options, and other settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import logging
from typing import Dict, Any, Optional
import yaml
import os


class SettingsWindow:
    """Settings window for browser configuration."""
    
    def __init__(self, parent, config: Dict[str, Any], main_window):
        self.parent = parent
        self.config = config.copy()  # Work on a copy
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
        # Create settings window
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")
        
        # Setup settings UI
        self.setup_settings()
        
        # Store original config for comparison
        self.original_config = config.copy()
    
    def setup_settings(self):
        """Setup the settings UI."""
        # Create notebook for different setting categories
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # General settings
        self.setup_general_settings()
        
        # Security settings
        self.setup_security_settings()
        
        # UI settings
        self.setup_ui_settings()
        
        # Network settings
        self.setup_network_settings()
        
        # AI settings
        self.setup_ai_settings()
        
        # Buttons
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, text="Save", command=self.save_settings
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame, text="Reset", command=self.reset_settings
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame, text="Cancel", command=self.cancel
        ).pack(side="right", padx=5)
    
    def setup_general_settings(self):
        """Setup general browser settings."""
        general_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(general_frame, text="General")
        
        # Homepage
        homepage_frame = ctk.CTkFrame(general_frame)
        homepage_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(homepage_frame, text="Homepage:").pack(side="left")
        self.homepage_var = tk.StringVar(
            value=self.config.get('browser', {}).get('default_homepage', 'https://www.google.com')
        )
        self.homepage_entry = ctk.CTkEntry(homepage_frame, textvariable=self.homepage_var, width=400)
        self.homepage_entry.pack(side="right", fill="x", expand=True)
        
        # Restore session
        session_frame = ctk.CTkFrame(general_frame)
        session_frame.pack(fill="x", padx=10, pady=5)
        
        self.restore_session_var = tk.BooleanVar(
            value=self.config.get('browser', {}).get('restore_last_session', False)
        )
        ctk.CTkCheckBox(
            session_frame, text="Restore last session on startup", 
            variable=self.restore_session_var
        ).pack(side="left")
        
        # JavaScript
        js_frame = ctk.CTkFrame(general_frame)
        js_frame.pack(fill="x", padx=10, pady=5)
        
        self.enable_js_var = tk.BooleanVar(
            value=self.config.get('browser', {}).get('enable_javascript', True)
        )
        ctk.CTkCheckBox(
            js_frame, text="Enable JavaScript", variable=self.enable_js_var
        ).pack(side="left")
        
        # Cookies
        cookies_frame = ctk.CTkFrame(general_frame)
        cookies_frame.pack(fill="x", padx=10, pady=5)
        
        self.enable_cookies_var = tk.BooleanVar(
            value=self.config.get('browser', {}).get('enable_cookies', True)
        )
        ctk.CTkCheckBox(
            cookies_frame, text="Enable Cookies", variable=self.enable_cookies_var
        ).pack(side="left")
        
        # Plugins
        plugins_frame = ctk.CTkFrame(general_frame)
        plugins_frame.pack(fill="x", padx=10, pady=5)
        
        self.enable_plugins_var = tk.BooleanVar(
            value=self.config.get('browser', {}).get('enable_plugins', True)
        )
        ctk.CTkCheckBox(
            plugins_frame, text="Enable Plugins", variable=self.enable_plugins_var
        ).pack(side="left")
        
        # Default zoom
        zoom_frame = ctk.CTkFrame(general_frame)
        zoom_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(zoom_frame, text="Default Zoom:").pack(side="left")
        self.zoom_var = tk.StringVar(
            value=str(self.config.get('browser', {}).get('default_zoom', 1.0))
        )
        self.zoom_combo = ctk.CTkComboBox(
            zoom_frame, variable=self.zoom_var, values=["0.5", "0.75", "1.0", "1.25", "1.5", "2.0"]
        )
        self.zoom_combo.pack(side="right")
    
    def setup_security_settings(self):
        """Setup security and privacy settings."""
        security_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(security_frame, text="Security")
        
        # Ad blocker
        ad_block_frame = ctk.CTkFrame(security_frame)
        ad_block_frame.pack(fill="x", padx=10, pady=10)
        
        self.enable_ad_blocker_var = tk.BooleanVar(
            value=self.config.get('security', {}).get('enable_ad_blocker', True)
        )
        ctk.CTkCheckBox(
            ad_block_frame, text="Enable Ad Blocker", variable=self.enable_ad_blocker_var
        ).pack(side="left")
        
        # HTTPS enforcement
        https_frame = ctk.CTkFrame(security_frame)
        https_frame.pack(fill="x", padx=10, pady=5)
        
        self.enforce_https_var = tk.BooleanVar(
            value=self.config.get('security', {}).get('enforce_https', True)
        )
        ctk.CTkCheckBox(
            https_frame, text="Enforce HTTPS", variable=self.enforce_https_var
        ).pack(side="left")
        
        # Tracker blocking
        tracker_frame = ctk.CTkFrame(security_frame)
        tracker_frame.pack(fill="x", padx=10, pady=5)
        
        self.block_trackers_var = tk.BooleanVar(
            value=self.config.get('security', {}).get('block_trackers', True)
        )
        ctk.CTkCheckBox(
            tracker_frame, text="Block Trackers", variable=self.block_trackers_var
        ).pack(side="left")
        
        # Private browsing
        private_frame = ctk.CTkFrame(security_frame)
        private_frame.pack(fill="x", padx=10, pady=5)
        
        self.private_browsing_var = tk.BooleanVar(
            value=self.config.get('security', {}).get('enable_private_browsing', False)
        )
        ctk.CTkCheckBox(
            private_frame, text="Enable Private Browsing", variable=self.private_browsing_var
        ).pack(side="left")
        
        # Clear history on exit
        clear_history_frame = ctk.CTkFrame(security_frame)
        clear_history_frame.pack(fill="x", padx=10, pady=5)
        
        self.clear_history_var = tk.BooleanVar(
            value=self.config.get('security', {}).get('clear_history_on_exit', False)
        )
        ctk.CTkCheckBox(
            clear_history_frame, text="Clear History on Exit", variable=self.clear_history_var
        ).pack(side="left")
        
        # Block malicious domains
        malicious_frame = ctk.CTkFrame(security_frame)
        malicious_frame.pack(fill="x", padx=10, pady=5)
        
        self.block_malicious_var = tk.BooleanVar(
            value=self.config.get('security', {}).get('block_malicious_domains', True)
        )
        ctk.CTkCheckBox(
            malicious_frame, text="Block Malicious Domains", variable=self.block_malicious_var
        ).pack(side="left")
    
    def setup_ui_settings(self):
        """Setup user interface settings."""
        ui_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(ui_frame, text="Appearance")
        
        # Theme
        theme_frame = ctk.CTkFrame(ui_frame)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left")
        self.theme_var = tk.StringVar(
            value=self.config.get('browser', {}).get('theme', 'dark')
        )
        self.theme_combo = ctk.CTkComboBox(
            theme_frame, variable=self.theme_var, values=["dark", "light", "system"]
        )
        self.theme_combo.pack(side="right")
        
        # Window size
        size_frame = ctk.CTkFrame(ui_frame)
        size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(size_frame, text="Window Size:").pack(side="left")
        
        size_subframe = ctk.CTkFrame(size_frame)
        size_subframe.pack(side="right")
        
        ctk.CTkLabel(size_subframe, text="Width:").pack(side="left")
        self.window_width_var = tk.StringVar(
            value=str(self.config.get('ui', {}).get('window_width', 1200))
        )
        self.width_entry = ctk.CTkEntry(size_subframe, textvariable=self.window_width_var, width=60)
        self.width_entry.pack(side="left", padx=2)
        
        ctk.CTkLabel(size_subframe, text="Height:").pack(side="left", padx=(10, 0))
        self.window_height_var = tk.StringVar(
            value=str(self.config.get('ui', {}).get('window_height', 800))
        )
        self.height_entry = ctk.CTkEntry(size_subframe, textvariable=self.window_height_var, width=60)
        self.height_entry.pack(side="left", padx=2)
        
        # Tab position
        tab_frame = ctk.CTkFrame(ui_frame)
        tab_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(tab_frame, text="Tab Position:").pack(side="left")
        self.tab_position_var = tk.StringVar(
            value=self.config.get('ui', {}).get('tab_position', 'top')
        )
        self.tab_combo = ctk.CTkComboBox(
            tab_frame, variable=self.tab_position_var, values=["top", "bottom", "left", "right"]
        )
        self.tab_combo.pack(side="right")
        
        # Show bookmarks bar
        bookmarks_bar_frame = ctk.CTkFrame(ui_frame)
        bookmarks_bar_frame.pack(fill="x", padx=10, pady=5)
        
        self.show_bookmarks_bar_var = tk.BooleanVar(
            value=self.config.get('ui', {}).get('show_bookmarks_bar', True)
        )
        ctk.CTkCheckBox(
            bookmarks_bar_frame, text="Show Bookmarks Bar", variable=self.show_bookmarks_bar_var
        ).pack(side="left")
        
        # Show status bar
        status_bar_frame = ctk.CTkFrame(ui_frame)
        status_bar_frame.pack(fill="x", padx=10, pady=5)
        
        self.show_status_bar_var = tk.BooleanVar(
            value=self.config.get('ui', {}).get('show_status_bar', True)
        )
        ctk.CTkCheckBox(
            status_bar_frame, text="Show Status Bar", variable=self.show_status_bar_var
        ).pack(side="left")
        
        # Animations
        animations_frame = ctk.CTkFrame(ui_frame)
        animations_frame.pack(fill="x", padx=10, pady=5)
        
        self.animations_var = tk.BooleanVar(
            value=self.config.get('ui', {}).get('animations_enabled', True)
        )
        ctk.CTkCheckBox(
            animations_frame, text="Enable Animations", variable=self.animations_var
        ).pack(side="left")
    
    def setup_network_settings(self):
        """Setup network settings."""
        network_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(network_frame, text="Network")
        
        # User agent
        ua_frame = ctk.CTkFrame(network_frame)
        ua_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ua_frame, text="User Agent:").pack(side="left")
        self.user_agent_var = tk.StringVar(
            value=self.config.get('network', {}).get('user_agent', 'AdvancedWebBrowser/1.0')
        )
        self.user_agent_entry = ctk.CTkEntry(ua_frame, textvariable=self.user_agent_var, width=400)
        self.user_agent_entry.pack(side="right", fill="x", expand=True)
        
        # Timeout
        timeout_frame = ctk.CTkFrame(network_frame)
        timeout_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(timeout_frame, text="Request Timeout (seconds):").pack(side="left")
        self.timeout_var = tk.StringVar(
            value=str(self.config.get('network', {}).get('timeout', 30))
        )
        self.timeout_entry = ctk.CTkEntry(timeout_frame, textvariable=self.timeout_var, width=100)
        self.timeout_entry.pack(side="right")
        
        # Max concurrent requests
        concurrent_frame = ctk.CTkFrame(network_frame)
        concurrent_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(concurrent_frame, text="Max Concurrent Requests:").pack(side="left")
        self.concurrent_var = tk.StringVar(
            value=str(self.config.get('network', {}).get('max_concurrent_requests', 10))
        )
        self.concurrent_entry = ctk.CTkEntry(concurrent_frame, textvariable=self.concurrent_var, width=100)
        self.concurrent_entry.pack(side="right")
        
        # Proxy settings
        proxy_frame = ctk.CTkFrame(network_frame)
        proxy_frame.pack(fill="x", padx=10, pady=5)
        
        self.proxy_enabled_var = tk.BooleanVar(
            value=self.config.get('network', {}).get('proxy_enabled', False)
        )
        ctk.CTkCheckBox(
            proxy_frame, text="Enable Proxy", variable=self.proxy_enabled_var,
            command=self.toggle_proxy_fields
        ).pack(side="left")
        
        # Proxy fields (initially disabled)
        self.proxy_host_frame = ctk.CTkFrame(network_frame)
        self.proxy_host_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.proxy_host_frame, text="Proxy Host:").pack(side="left")
        self.proxy_host_var = tk.StringVar(
            value=self.config.get('network', {}).get('proxy_host', '')
        )
        self.proxy_host_entry = ctk.CTkEntry(self.proxy_host_frame, textvariable=self.proxy_host_var)
        self.proxy_host_entry.pack(side="right", fill="x", expand=True)
        
        self.proxy_port_frame = ctk.CTkFrame(network_frame)
        self.proxy_port_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.proxy_port_frame, text="Proxy Port:").pack(side="left")
        self.proxy_port_var = tk.StringVar(
            value=str(self.config.get('network', {}).get('proxy_port', ''))
        )
        self.proxy_port_entry = ctk.CTkEntry(self.proxy_port_frame, textvariable=self.proxy_port_var)
        self.proxy_port_entry.pack(side="right")
        
        # Initially disable proxy fields
        self.toggle_proxy_fields()
    
    def setup_ai_settings(self):
        """Setup AI and suggestions settings."""
        ai_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(ai_frame, text="AI Features")
        
        # Enable suggestions
        suggestions_frame = ctk.CTkFrame(ai_frame)
        suggestions_frame.pack(fill="x", padx=10, pady=10)
        
        self.enable_suggestions_var = tk.BooleanVar(
            value=self.config.get('ai', {}).get('enable_suggestions', True)
        )
        ctk.CTkCheckBox(
            suggestions_frame, text="Enable AI Suggestions", variable=self.enable_suggestions_var
        ).pack(side="left")
        
        # Suggestion provider
        provider_frame = ctk.CTkFrame(ai_frame)
        provider_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(provider_frame, text="Suggestion Provider:").pack(side="left")
        self.suggestion_provider_var = tk.StringVar(
            value=self.config.get('ai', {}).get('suggestion_provider', 'local')
        )
        self.provider_combo = ctk.CTkComboBox(
            provider_frame, variable=self.suggestion_provider_var, 
            values=["local", "openai", "google"]
        )
        self.provider_combo.pack(side="right")
        
        # Max suggestions
        max_suggestions_frame = ctk.CTkFrame(ai_frame)
        max_suggestions_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(max_suggestions_frame, text="Max Suggestions:").pack(side="left")
        self.max_suggestions_var = tk.StringVar(
            value=str(self.config.get('ai', {}).get('max_suggestions', 5))
        )
        self.max_suggestions_entry = ctk.CTkEntry(max_suggestions_frame, textvariable=self.max_suggestions_var, width=100)
        self.max_suggestions_entry.pack(side="right")
        
        # Cache suggestions
        cache_suggestions_frame = ctk.CTkFrame(ai_frame)
        cache_suggestions_frame.pack(fill="x", padx=10, pady=5)
        
        self.cache_suggestions_var = tk.BooleanVar(
            value=self.config.get('ai', {}).get('cache_suggestions', True)
        )
        ctk.CTkCheckBox(
            cache_suggestions_frame, text="Cache Suggestions", variable=self.cache_suggestions_var
        ).pack(side="left")
        
        # Learning enabled
        learning_frame = ctk.CTkFrame(ai_frame)
        learning_frame.pack(fill="x", padx=10, pady=5)
        
        self.learning_enabled_var = tk.BooleanVar(
            value=self.config.get('ai', {}).get('learning_enabled', True)
        )
        ctk.CTkCheckBox(
            learning_frame, text="Enable Learning", variable=self.learning_enabled_var
        ).pack(side="left")
    
    def toggle_proxy_fields(self):
        """Toggle proxy field states."""
        enabled = self.proxy_enabled_var.get()
        
        state = "normal" if enabled else "disabled"
        self.proxy_host_entry.configure(state=state)
        self.proxy_port_entry.configure(state=state)
    
    def save_settings(self):
        """Save settings to config file."""
        try:
            # Update config with new values
            self.config['browser']['default_homepage'] = self.homepage_var.get()
            self.config['browser']['restore_last_session'] = self.restore_session_var.get()
            self.config['browser']['enable_javascript'] = self.enable_js_var.get()
            self.config['browser']['enable_cookies'] = self.enable_cookies_var.get()
            self.config['browser']['enable_plugins'] = self.enable_plugins_var.get()
            self.config['browser']['default_zoom'] = float(self.zoom_var.get())
            self.config['browser']['theme'] = self.theme_var.get()
            
            self.config['security']['enable_ad_blocker'] = self.enable_ad_blocker_var.get()
            self.config['security']['enforce_https'] = self.enforce_https_var.get()
            self.config['security']['block_trackers'] = self.block_trackers_var.get()
            self.config['security']['enable_private_browsing'] = self.private_browsing_var.get()
            self.config['security']['clear_history_on_exit'] = self.clear_history_var.get()
            self.config['security']['block_malicious_domains'] = self.block_malicious_var.get()
            
            self.config['ui']['window_width'] = int(self.window_width_var.get())
            self.config['ui']['window_height'] = int(self.window_height_var.get())
            self.config['ui']['tab_position'] = self.tab_position_var.get()
            self.config['ui']['show_bookmarks_bar'] = self.show_bookmarks_bar_var.get()
            self.config['ui']['show_status_bar'] = self.show_status_bar_var.get()
            self.config['ui']['animations_enabled'] = self.animations_var.get()
            
            self.config['network']['user_agent'] = self.user_agent_var.get()
            self.config['network']['timeout'] = int(self.timeout_var.get())
            self.config['network']['max_concurrent_requests'] = int(self.concurrent_var.get())
            self.config['network']['proxy_enabled'] = self.proxy_enabled_var.get()
            self.config['network']['proxy_host'] = self.proxy_host_var.get()
            self.config['network']['proxy_port'] = self.proxy_port_var.get()
            
            self.config['ai']['enable_suggestions'] = self.enable_suggestions_var.get()
            self.config['ai']['suggestion_provider'] = self.suggestion_provider_var.get()
            self.config['ai']['max_suggestions'] = int(self.max_suggestions_var.get())
            self.config['ai']['cache_suggestions'] = self.cache_suggestions_var.get()
            self.config['ai']['learning_enabled'] = self.learning_enabled_var.get()
            
            # Save to file
            with open('config.yaml', 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            # Apply some settings immediately
            self.apply_immediate_settings()
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.window.destroy()
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def apply_immediate_settings(self):
        """Apply settings that take effect immediately."""
        # Update theme
        if self.theme_var.get() != self.original_config.get('browser', {}).get('theme'):
            # Apply theme change
            if self.theme_var.get() == 'dark':
                ctk.set_appearance_mode('dark')
            elif self.theme_var.get() == 'light':
                ctk.set_appearance_mode('light')
            else:
                ctk.set_appearance_mode('system')
        
        # Update window size if changed
        current_width = self.main_window.root.winfo_width()
        current_height = self.main_window.root.winfo_height()
        new_width = int(self.window_width_var.get())
        new_height = int(self.window_height_var.get())
        
        if current_width != new_width or current_height != new_height:
            self.main_window.root.geometry(f"{new_width}x{new_height}")
    
    def reset_settings(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            # Load default settings
            default_config = {
                'browser': {
                    'default_homepage': 'https://www.google.com',
                    'theme': 'dark',
                    'enable_javascript': True,
                    'enable_cookies': True,
                    'enable_plugins': True,
                    'default_zoom': 1.0,
                    'restore_last_session': False
                },
                'security': {
                    'enable_ad_blocker': True,
                    'enforce_https': True,
                    'block_trackers': True,
                    'enable_private_browsing': False,
                    'clear_history_on_exit': False,
                    'block_malicious_domains': True
                },
                'ui': {
                    'window_width': 1200,
                    'window_height': 800,
                    'tab_position': 'top',
                    'show_bookmarks_bar': True,
                    'show_status_bar': True,
                    'animations_enabled': True
                },
                'network': {
                    'user_agent': 'AdvancedWebBrowser/1.0',
                    'timeout': 30,
                    'max_concurrent_requests': 10,
                    'proxy_enabled': False,
                    'proxy_host': '',
                    'proxy_port': ''
                },
                'ai': {
                    'enable_suggestions': True,
                    'suggestion_provider': 'local',
                    'max_suggestions': 5,
                    'cache_suggestions': True,
                    'learning_enabled': True
                }
            }
            
            self.config = default_config
            self.update_ui_from_config()
    
    def update_ui_from_config(self):
        """Update UI elements from config values."""
        # Update all variables
        self.homepage_var.set(self.config.get('browser', {}).get('default_homepage', ''))
        self.restore_session_var.set(self.config.get('browser', {}).get('restore_last_session', False))
        self.enable_js_var.set(self.config.get('browser', {}).get('enable_javascript', True))
        self.enable_cookies_var.set(self.config.get('browser', {}).get('enable_cookies', True))
        self.enable_plugins_var.set(self.config.get('browser', {}).get('enable_plugins', True))
        self.zoom_var.set(str(self.config.get('browser', {}).get('default_zoom', 1.0)))
        self.theme_var.set(self.config.get('browser', {}).get('theme', 'dark'))
        
        self.enable_ad_blocker_var.set(self.config.get('security', {}).get('enable_ad_blocker', True))
        self.enforce_https_var.set(self.config.get('security', {}).get('enforce_https', True))
        self.block_trackers_var.set(self.config.get('security', {}).get('block_trackers', True))
        self.private_browsing_var.set(self.config.get('security', {}).get('enable_private_browsing', False))
        self.clear_history_var.set(self.config.get('security', {}).get('clear_history_on_exit', False))
        self.block_malicious_var.set(self.config.get('security', {}).get('block_malicious_domains', True))
        
        self.window_width_var.set(str(self.config.get('ui', {}).get('window_width', 1200)))
        self.window_height_var.set(str(self.config.get('ui', {}).get('window_height', 800)))
        self.tab_position_var.set(self.config.get('ui', {}).get('tab_position', 'top'))
        self.show_bookmarks_bar_var.set(self.config.get('ui', {}).get('show_bookmarks_bar', True))
        self.show_status_bar_var.set(self.config.get('ui', {}).get('show_status_bar', True))
        self.animations_var.set(self.config.get('ui', {}).get('animations_enabled', True))
        
        self.user_agent_var.set(self.config.get('network', {}).get('user_agent', ''))
        self.timeout_var.set(str(self.config.get('network', {}).get('timeout', 30)))
        self.concurrent_var.set(str(self.config.get('network', {}).get('max_concurrent_requests', 10)))
        self.proxy_enabled_var.set(self.config.get('network', {}).get('proxy_enabled', False))
        self.proxy_host_var.set(self.config.get('network', {}).get('proxy_host', ''))
        self.proxy_port_var.set(str(self.config.get('network', {}).get('proxy_port', '')))
        
        self.enable_suggestions_var.set(self.config.get('ai', {}).get('enable_suggestions', True))
        self.suggestion_provider_var.set(self.config.get('ai', {}).get('suggestion_provider', 'local'))
        self.max_suggestions_var.set(str(self.config.get('ai', {}).get('max_suggestions', 5)))
        self.cache_suggestions_var.set(self.config.get('ai', {}).get('cache_suggestions', True))
        self.learning_enabled_var.set(self.config.get('ai', {}).get('learning_enabled', True))
        
        self.toggle_proxy_fields()
    
    def cancel(self):
        """Cancel settings changes."""
        self.window.destroy()
    
    def run(self):
        """Run the settings window."""
        self.window.mainloop()
