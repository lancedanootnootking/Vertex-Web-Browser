"""
Theme Manager

This module manages browser themes, including switching between
dark, light, and custom themes.
"""

import logging
from typing import Dict, Any, Optional
import os
import json


class ThemeManager:
    """Manages browser themes and appearance settings."""
    
    def __init__(self, current_theme: str = "dark"):
        self.current_theme = current_theme
        self.logger = logging.getLogger(__name__)
        
        # Available themes
        self.themes = {
            "dark": {
                "name": "Dark",
                "appearance_mode": "dark",
                "colors": {
                    "primary": "#1a1a1a",
                    "secondary": "#2d2d2d",
                    "accent": "#0078d7",
                    "text": "#ffffff",
                    "text_secondary": "#cccccc",
                    "background": "#000000",
                    "surface": "#1e1e1e",
                    "border": "#404040",
                    "success": "#107c10",
                    "warning": "#ff8c00",
                    "error": "#d13438"
                }
            },
            "light": {
                "name": "Light",
                "appearance_mode": "light",
                "colors": {
                    "primary": "#ffffff",
                    "secondary": "#f3f2f1",
                    "accent": "#0078d7",
                    "text": "#000000",
                    "text_secondary": "#605e5c",
                    "background": "#ffffff",
                    "surface": "#faf9f8",
                    "border": "#d2d0ce",
                    "success": "#107c10",
                    "warning": "#ff8c00",
                    "error": "#d13438"
                }
            },
            "blue": {
                "name": "Blue",
                "appearance_mode": "dark",
                "colors": {
                    "primary": "#0f2c59",
                    "secondary": "#1e3a8a",
                    "accent": "#3b82f6",
                    "text": "#ffffff",
                    "text_secondary": "#cbd5e1",
                    "background": "#020617",
                    "surface": "#0f172a",
                    "border": "#334155",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                }
            },
            "green": {
                "name": "Green",
                "appearance_mode": "dark",
                "colors": {
                    "primary": "#14532d",
                    "secondary": "#166534",
                    "accent": "#22c55e",
                    "text": "#ffffff",
                    "text_secondary": "#bbf7d0",
                    "background": "#052e16",
                    "surface": "#022c22",
                    "border": "#15803d",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                }
            }
        }
        
        # Load custom themes
        self.load_custom_themes()
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.current_theme
    
    def get_theme_info(self, theme_name: str = None) -> Dict[str, Any]:
        """Get theme information."""
        if theme_name is None:
            theme_name = self.current_theme
        
        return self.themes.get(theme_name, self.themes["dark"])
    
    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """Get theme colors."""
        theme_info = self.get_theme_info(theme_name)
        return theme_info.get("colors", {})
    
    def get_appearance_mode(self, theme_name: str = None) -> str:
        """Get appearance mode for theme."""
        theme_info = self.get_theme_info(theme_name)
        return theme_info.get("appearance_mode", "dark")
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.logger.info(f"Theme changed to: {theme_name}")
            return True
        else:
            self.logger.warning(f"Theme not found: {theme_name}")
            return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get list of available themes."""
        return {name: theme["name"] for name, theme in self.themes.items()}
    
    def add_custom_theme(self, theme_name: str, theme_data: Dict[str, Any]) -> bool:
        """Add a custom theme."""
        try:
            # Validate theme data
            required_keys = ["name", "appearance_mode", "colors"]
            for key in required_keys:
                if key not in theme_data:
                    self.logger.error(f"Custom theme missing required key: {key}")
                    return False
            
            # Add theme
            self.themes[theme_name] = theme_data
            
            # Save custom theme to file
            self.save_custom_theme(theme_name, theme_data)
            
            self.logger.info(f"Added custom theme: {theme_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding custom theme: {e}")
            return False
    
    def remove_custom_theme(self, theme_name: str) -> bool:
        """Remove a custom theme."""
        if theme_name in ["dark", "light"]:
            self.logger.warning("Cannot remove built-in themes")
            return False
        
        if theme_name in self.themes:
            del self.themes[theme_name]
            
            # Remove custom theme file
            theme_file = f"themes/{theme_name}.json"
            if os.path.exists(theme_file):
                os.remove(theme_file)
            
            self.logger.info(f"Removed custom theme: {theme_name}")
            return True
        
        return False
    
    def load_custom_themes(self):
        """Load custom themes from files."""
        themes_dir = "themes"
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)
            return
        
        try:
            for filename in os.listdir(themes_dir):
                if filename.endswith(".json"):
                    theme_name = filename[:-5]  # Remove .json extension
                    
                    with open(os.path.join(themes_dir, filename), 'r') as f:
                        theme_data = json.load(f)
                    
                    self.themes[theme_name] = theme_data
                    self.logger.info(f"Loaded custom theme: {theme_name}")
                    
        except Exception as e:
            self.logger.error(f"Error loading custom themes: {e}")
    
    def save_custom_theme(self, theme_name: str, theme_data: Dict[str, Any]):
        """Save a custom theme to file."""
        themes_dir = "themes"
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)
        
        try:
            theme_file = os.path.join(themes_dir, f"{theme_name}.json")
            with open(theme_file, 'w') as f:
                json.dump(theme_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving custom theme {theme_name}: {e}")
    
    def create_theme_from_colors(self, theme_name: str, colors: Dict[str, str], 
                                appearance_mode: str = "dark") -> Dict[str, Any]:
        """Create a theme from color definitions."""
        # Default color values
        default_colors = self.themes["dark"]["colors"]
        
        # Merge with provided colors
        merged_colors = default_colors.copy()
        merged_colors.update(colors)
        
        theme_data = {
            "name": theme_name.replace("_", " ").title(),
            "appearance_mode": appearance_mode,
            "colors": merged_colors
        }
        
        return theme_data
    
    def get_color(self, color_name: str, theme_name: str = None) -> str:
        """Get a specific color from the theme."""
        colors = self.get_theme_colors(theme_name)
        return colors.get(color_name, "#000000")
    
    def get_contrast_color(self, background_color: str) -> str:
        """Get a contrasting text color for a background color."""
        # Simple luminance calculation
        try:
            # Remove # and convert to RGB
            hex_color = background_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Calculate luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Return black or white based on luminance
            return "#000000" if luminance > 0.5 else "#ffffff"
            
        except:
            return "#000000"
    
    def export_theme(self, theme_name: str, file_path: str) -> bool:
        """Export a theme to a file."""
        try:
            if theme_name not in self.themes:
                return False
            
            theme_data = self.themes[theme_name]
            
            with open(file_path, 'w') as f:
                json.dump(theme_data, f, indent=2)
            
            self.logger.info(f"Exported theme {theme_name} to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting theme {theme_name}: {e}")
            return False
    
    def import_theme(self, file_path: str, theme_name: str = None) -> bool:
        """Import a theme from a file."""
        try:
            with open(file_path, 'r') as f:
                theme_data = json.load(f)
            
            # Use filename as theme name if not provided
            if theme_name is None:
                theme_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Validate theme data
            required_keys = ["name", "appearance_mode", "colors"]
            for key in required_keys:
                if key not in theme_data:
                    self.logger.error(f"Imported theme missing required key: {key}")
                    return False
            
            # Add theme
            self.themes[theme_name] = theme_data
            
            # Save as custom theme
            self.save_custom_theme(theme_name, theme_data)
            
            self.logger.info(f"Imported theme: {theme_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing theme from {file_path}: {e}")
            return False
    
    def get_theme_preview(self, theme_name: str) -> Dict[str, str]:
        """Get theme preview colors for UI display."""
        colors = self.get_theme_colors(theme_name)
        
        return {
            "primary": colors.get("primary", "#000000"),
            "secondary": colors.get("secondary", "#000000"),
            "accent": colors.get("accent", "#000000"),
            "text": colors.get("text", "#000000"),
            "background": colors.get("background", "#000000"),
            "surface": colors.get("surface", "#000000")
        }
    
    def validate_theme_data(self, theme_data: Dict[str, Any]) -> bool:
        """Validate theme data structure."""
        required_keys = ["name", "appearance_mode", "colors"]
        
        # Check required keys
        for key in required_keys:
            if key not in theme_data:
                return False
        
        # Check colors
        colors = theme_data["colors"]
        required_colors = ["primary", "accent", "text", "background"]
        
        for color in required_colors:
            if color not in colors:
                return False
        
        # Validate color format (simple hex check)
        for color_name, color_value in colors.items():
            if not isinstance(color_value, str) or not color_value.startswith("#"):
                return False
        
        return True
    
    def get_theme_statistics(self) -> Dict[str, Any]:
        """Get statistics about available themes."""
        total_themes = len(self.themes)
        builtin_themes = len(["dark", "light"])
        custom_themes = total_themes - builtin_themes
        
        appearance_modes = {}
        for theme in self.themes.values():
            mode = theme.get("appearance_mode", "unknown")
            appearance_modes[mode] = appearance_modes.get(mode, 0) + 1
        
        return {
            "total_themes": total_themes,
            "builtin_themes": builtin_themes,
            "custom_themes": custom_themes,
            "appearance_modes": appearance_modes,
            "current_theme": self.current_theme
        }
