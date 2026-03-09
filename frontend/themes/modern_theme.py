#!/usr/bin/env python3.12
"""
Modern Blue/Grey Theme System for Vertex Browser

Comprehensive theme system with modern blue and grey color palette,
CSS styling, animations, and visual effects.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPalette, QFont, QFontDatabase, QPainter, QBrush, QLinearGradient
import json
from pathlib import Path
from typing import Dict, Any, Tuple


class ModernTheme:
    """Modern blue and grey theme system for Vertex Browser."""
    
    def __init__(self):
        # Color palette - Modern Blue and Grey
        self.colors = {
            # Primary blues
            'primary_blue': '#2196F3',
            'primary_blue_dark': '#1976D2',
            'primary_blue_light': '#BBDEFB',
            'accent_blue': '#03A9F4',
            'accent_blue_dark': '#0288D1',
            
            # Secondary blues
            'secondary_blue': '#42A5F5',
            'secondary_blue_dark': '#1E88E5',
            'secondary_blue_light': '#90CAF9',
            
            # Greys
            'background_grey': '#121212',
            'surface_grey': '#1E1E1E',
            'card_grey': '#2D2D30',
            'hover_grey': '#3E3E42',
            'border_grey': '#4A4A4A',
            'text_primary': '#FFFFFF',
            'text_secondary': '#B3B3B3',
            'text_disabled': '#666666',
            'divider_grey': '#404040',
            
            # Status colors
            'success_green': '#4CAF50',
            'warning_yellow': '#FF9800',
            'error_red': '#F44336',
            'info_blue': '#2196F3',
            
            # Special colors
            'shadow_color': '#000000',
            'highlight_color': '#3F51B5',
            'gradient_start': '#1A237E',
            'gradient_end': '#3949AB',
            
            # Tab colors
            'tab_active': '#2D2D30',
            'tab_inactive': '#1E1E1E',
            'tab_hover': '#3E3E42',
            
            # Button colors
            'button_primary': '#2196F3',
            'button_primary_hover': '#1976D2',
            'button_secondary': '#424242',
            'button_secondary_hover': '#616161',
            
            # Input colors
            'input_background': '#2D2D30',
            'input_border': '#4A4A4A',
            'input_focus': '#2196F3',
        }
        
        # Typography
        self.fonts = {
            'primary': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'monospace': 'JetBrains Mono, "Cascadia Code", "Fira Code", Consolas, monospace',
            'heading': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        }
        
        # Font sizes
        self.font_sizes = {
            'xs': 10,
            'sm': 12,
            'base': 14,
            'lg': 16,
            'xl': 18,
            '2xl': 24,
            '3xl': 30,
            '4xl': 36,
        }
        
        # Spacing
        self.spacing = {
            'xs': 4,
            'sm': 8,
            'md': 16,
            'lg': 24,
            'xl': 32,
            '2xl': 48,
            '3xl': 64,
        }
        
        # Border radius
        self.border_radius = {
            'sm': 4,
            'md': 8,
            'lg': 12,
            'xl': 16,
            'full': 9999,
        }
        
        # Shadows
        self.shadows = {
            'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        }
        
        # Animations
        self.animations = {
            'fast': '150ms ease-in-out',
            'normal': '250ms ease-in-out',
            'slow': '350ms ease-in-out',
        }
        
        # Z-index layers
        self.z_index = {
            'dropdown': 1000,
            'sticky': 1020,
            'fixed': 1030,
            'modal_backdrop': 1040,
            'modal': 1050,
            'popover': 1060,
            'tooltip': 1070,
            'toast': 1080,
        }

    def apply_theme(self, app: QApplication) -> None:
        """Apply the theme to the PyQt application."""
        palette = QPalette()
        
        # Set colors for different UI elements
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors['background_grey']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors['surface_grey']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors['card_grey']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.colors['primary_blue']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors['button_secondary']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors['text_primary']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(self.colors['accent_blue']))
        palette.setColor(QPalette.ColorRole.Link, QColor(self.colors['accent_blue']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors['primary_blue']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.colors['text_primary']))
        
        app.setPalette(palette)
        
        # Set application font
        font = QFont(self.fonts['primary'])
        font.setPointSize(self.font_sizes['base'])
        app.setFont(font)

    def get_color(self, name: str) -> str:
        """Get a color by name."""
        return self.colors.get(name, '#000000')
    
    def get_font_size(self, size: str) -> int:
        """Get font size by name."""
        return self.font_sizes.get(size, 14)
    
    def get_spacing(self, size: str) -> int:
        """Get spacing value by name."""
        return self.spacing.get(size, 8)
    
    def get_border_radius(self, size: str) -> int:
        """Get border radius by name."""
        return self.border_radius.get(size, 8)


class StyleSheetManager:
    """Manages CSS stylesheets for PyQt widgets."""
    
    def __init__(self, theme: ModernTheme):
        self.theme = theme
        self.stylesheets = {}
        self.generate_stylesheets()
    
    def generate_stylesheets(self):
        """Generate all CSS stylesheets."""
        self.stylesheets['main_window'] = self.get_main_window_style()
        self.stylesheets['toolbar'] = self.get_toolbar_style()
        self.stylesheets['tab_widget'] = self.get_tab_widget_style()
        self.stylesheets['address_bar'] = self.get_address_bar_style()
        self.stylesheets['button'] = self.get_button_style()
        self.stylesheets['menu'] = self.get_menu_style()
        self.stylesheets['status_bar'] = self.get_status_bar_style()
        self.stylesheets['scroll_area'] = self.get_scroll_area_style()
        self.stylesheets['list_widget'] = self.get_list_widget_style()
        self.stylesheets['tree_widget'] = self.get_tree_widget_style()
        self.stylesheets['table_widget'] = self.get_table_widget_style()
        self.stylesheets['progress_bar'] = self.get_progress_bar_style()
        self.stylesheets['slider'] = self.get_slider_style()
        self.stylesheets['checkbox'] = self.get_checkbox_style()
        self.stylesheets['radio_button'] = self.get_radio_button_style()
        self.stylesheets['group_box'] = self.get_group_box_style()
        self.stylesheets['tab_bar'] = self.get_tab_bar_style()
        self.stylesheets['combo_box'] = self.get_combo_box_style()
        self.stylesheets['spin_box'] = self.get_spin_box_style()
        self.stylesheets['double_spin_box'] = self.get_double_spin_box_style()
        self.stylesheets['text_edit'] = self.get_text_edit_style()
        self.stylesheets['plain_text_edit'] = self.get_plain_text_edit_style()
        self.stylesheets['label'] = self.get_label_style()
        self.stylesheets['frame'] = self.get_frame_style()
        self.stylesheets['widget'] = self.get_widget_style()
        self.stylesheets['dialog'] = self.get_dialog_style()
        self.stylesheets['message_box'] = self.get_message_box_style()
        self.stylesheets['tooltip'] = self.get_tooltip_style()
    
    def get_main_window_style(self) -> str:
        """Get main window stylesheet."""
        return f"""
        QMainWindow {{
            background-color: {self.theme.get_color('background_grey')};
            color: {self.theme.get_color('text_primary')};
            border: none;
        }}
        """
    
    def get_toolbar_style(self) -> str:
        """Get toolbar stylesheet."""
        return f"""
        QToolBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.theme.get_color('surface_grey')},
                stop:1 {self.theme.get_color('card_grey')});
            border: none;
            border-bottom: 1px solid {self.theme.get_color('divider_grey')};
            spacing: {self.theme.get_spacing('sm')}px;
            padding: {self.theme.get_spacing('sm')}px;
        }}
        
        QToolBar::handle {{
            background-color: {self.theme.get_color('border_grey')};
            width: 8px;
            border-radius: {self.theme.get_border_radius('sm')}px;
        }}
        
        QToolBar::handle:hover {{
            background-color: {self.theme.get_color('hover_grey')};
        }}
        """
    
    def get_tab_widget_style(self) -> str:
        """Get tab widget stylesheet."""
        return f"""
        QTabWidget::pane {{
            border: 1px solid {self.theme.get_color('divider_grey')};
            background-color: {self.theme.get_color('surface_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
        }}
        
        QTabWidget::tab-bar {{
            alignment: center;
        }}
        
        QTabBar::tab {{
            background-color: {self.theme.get_color('tab_inactive')};
            color: {self.theme.get_color('text_secondary')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-bottom: none;
            border-radius: {self.theme.get_border_radius('md')}px {self.theme.get_border_radius('md')}px 0 0;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('lg')}px;
            margin-right: 2px;
            font-weight: 500;
        }}
        
        QTabBar::tab:hover {{
            background-color: {self.theme.get_color('tab_hover')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.theme.get_color('tab_active')};
            color: {self.theme.get_color('text_primary')};
            border-bottom: 2px solid {self.theme.get_color('primary_blue')};
        }}
        
        QTabBar::close-button {{
            image: none;
            subcontrol-position: right;
            margin: 2px;
            padding: 2px;
        }}
        
        QTabBar::close-button:hover {{
            background-color: {self.theme.get_color('error_red')};
            border-radius: {self.theme.get_border_radius('sm')}px;
        }}
        """
    
    def get_address_bar_style(self) -> str:
        """Get address bar stylesheet."""
        return f"""
        QLineEdit {{
            background-color: {self.theme.get_color('input_background')};
            border: 2px solid {self.theme.get_color('input_border')};
            border-radius: {self.theme.get_border_radius('lg')}px;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            color: {self.theme.get_color('text_primary')};
            font-size: {self.theme.get_font_size('base')}px;
            selection-background-color: {self.theme.get_color('primary_blue')};
        }}
        
        QLineEdit:focus {{
            border-color: {self.theme.get_color('input_focus')};
            background-color: {self.theme.get_color('surface_grey')};
        }}
        
        QLineEdit:hover {{
            border-color: {self.theme.get_color('hover_grey')};
        }}
        """
    
    def get_button_style(self) -> str:
        """Get button stylesheet."""
        return f"""
        QPushButton {{
            background-color: {self.theme.get_color('button_secondary')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            font-weight: 500;
            font-size: {self.theme.get_font_size('base')}px;
        }}
        
        QPushButton:hover {{
            background-color: {self.theme.get_color('button_secondary_hover')};
            border-color: {self.theme.get_color('primary_blue')};
        }}
        
        QPushButton:pressed {{
            background-color: {self.theme.get_color('primary_blue_dark')};
        }}
        
        QPushButton:disabled {{
            background-color: {self.theme.get_color('text_disabled')};
            color: {self.theme.get_color('text_secondary')};
            border-color: {self.theme.get_color('divider_grey')};
        }}
        
        /* Primary button style */
        QPushButton[class="primary"] {{
            background-color: {self.theme.get_color('button_primary')};
            border-color: {self.theme.get_color('button_primary')};
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: {self.theme.get_color('button_primary_hover')};
            border-color: {self.theme.get_color('button_primary_hover')};
        }}
        
        /* Tool button style */
        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px;
            color: {self.theme.get_color('text_secondary')};
        }}
        
        QToolButton:hover {{
            background-color: {self.theme.get_color('hover_grey')};
            border-color: {self.theme.get_color('border_grey')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QToolButton:pressed {{
            background-color: {self.theme.get_color('primary_blue')};
            color: {self.theme.get_color('text_primary')};
        }}
        """
    
    def get_menu_style(self) -> str:
        """Get menu stylesheet."""
        return f"""
        QMenuBar {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border-bottom: 1px solid {self.theme.get_color('divider_grey')};
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            border-radius: {self.theme.get_border_radius('sm')}px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.theme.get_color('hover_grey')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QMenu {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('xs')}px;
        }}
        
        QMenu::item {{
            background-color: transparent;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            border-radius: {self.theme.get_border_radius('sm')}px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.theme.get_color('hover_grey')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {self.theme.get_color('divider_grey')};
            margin: {self.theme.get_spacing('xs')}px {self.theme.get_spacing('md')}px;
        }}
        """
    
    def get_status_bar_style(self) -> str:
        """Get status bar stylesheet."""
        return f"""
        QStatusBar {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_secondary')};
            border-top: 1px solid {self.theme.get_color('divider_grey')};
            font-size: {self.theme.get_font_size('sm')}px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        """
    
    def get_scroll_area_style(self) -> str:
        """Get scroll area stylesheet."""
        return f"""
        QScrollArea {{
            background-color: {self.theme.get_color('surface_grey')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
        }}
        
        QScrollBar:vertical {{
            background-color: {self.theme.get_color('surface_grey')};
            width: 12px;
            border-radius: {self.theme.get_border_radius('md')}px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {self.theme.get_color('surface_grey')};
            height: 12px;
            border-radius: {self.theme.get_border_radius('md')}px;
            margin: 0;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        """
    
    def get_list_widget_style(self) -> str:
        """Get list widget stylesheet."""
        return f"""
        QListWidget {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            outline: none;
            padding: {self.theme.get_spacing('xs')}px;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: none;
            padding: {self.theme.get_spacing('sm')}px;
            border-radius: {self.theme.get_border_radius('sm')}px;
            margin: 1px;
        }}
        
        QListWidget::item:hover {{
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QListWidget::item:selected {{
            background-color: {self.theme.get_color('primary_blue')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QListWidget::item:selected:!active {{
            background-color: {self.theme.get_color('primary_blue_dark')};
        }}
        """
    
    def get_tree_widget_style(self) -> str:
        """Get tree widget stylesheet."""
        return f"""
        QTreeWidget {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            outline: none;
            header-background-color: {self.theme.get_color('card_grey')};
        }}
        
        QTreeWidget::item {{
            background-color: transparent;
            border: none;
            padding: {self.theme.get_spacing('sm')}px;
            border-radius: {self.theme.get_border_radius('sm')}px;
            margin: 1px;
        }}
        
        QTreeWidget::item:hover {{
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {self.theme.get_color('primary_blue')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QTreeWidget::item:selected:!active {{
            background-color: {self.theme.get_color('primary_blue_dark')};
        }}
        
        QTreeWidget::header {{
            background-color: {self.theme.get_color('card_grey')};
            border: none;
            border-radius: {self.theme.get_border_radius('md')}px {self.theme.get_border_radius('md')}px 0 0;
            padding: {self.theme.get_spacing('sm')}px;
        }}
        
        QTreeWidget::header::section {{
            background-color: {self.theme.get_color('card_grey')};
            color: {self.theme.get_color('text_primary')};
            border: none;
            border-right: 1px solid {self.theme.get_color('divider_grey')};
            padding: {self.theme.get_spacing('sm')}px;
            font-weight: 600;
        }}
        
        QTreeWidget::header::section:last {{
            border-right: none;
        }}
        """
    
    def get_table_widget_style(self) -> str:
        """Get table widget stylesheet."""
        return f"""
        QTableWidget {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            outline: none;
            gridline-color: {self.theme.get_color('divider_grey')};
        }}
        
        QTableWidget::item {{
            background-color: {self.theme.get_color('surface_grey')};
            border: none;
            padding: {self.theme.get_spacing('sm')}px;
        }}
        
        QTableWidget::item:hover {{
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QTableWidget::item:selected {{
            background-color: {self.theme.get_color('primary_blue')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QTableWidget::item:selected:!active {{
            background-color: {self.theme.get_color('primary_blue_dark')};
        }}
        
        QTableWidget::header {{
            background-color: {self.theme.get_color('card_grey')};
            border: none;
            border-radius: {self.theme.get_border_radius('md')}px {self.theme.get_border_radius('md')}px 0 0;
            padding: {self.theme.get_spacing('sm')}px;
        }}
        
        QTableWidget::header::section {{
            background-color: {self.theme.get_color('card_grey')};
            color: {self.theme.get_color('text_primary')};
            border: none;
            border-right: 1px solid {self.theme.get_color('divider_grey')};
            padding: {self.theme.get_spacing('sm')}px;
            font-weight: 600;
        }}
        
        QTableWidget::header::section:last {{
            border-right: none;
        }}
        """
    
    def get_progress_bar_style(self) -> str:
        """Get progress bar stylesheet."""
        return f"""
        QProgressBar {{
            background-color: {self.theme.get_color('input_background')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            text-align: center;
            color: {self.theme.get_color('text_primary')};
            font-weight: 500;
        }}
        
        QProgressBar::chunk {{
            background-color: {self.theme.get_color('primary_blue')};
            border-radius: {self.theme.get_border_radius('md')}px;
            margin: 1px;
        }}
        
        QProgressBar::chunk:disabled {{
            background-color: {self.theme.get_color('text_disabled')};
        }}
        """
    
    def get_slider_style(self) -> str:
        """Get slider stylesheet."""
        return f"""
        QSlider::groove:horizontal {{
            background-color: {self.theme.get_color('input_background')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            height: 8px;
            margin: 2px 0;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {self.theme.get_color('primary_blue')};
            border: 2px solid {self.theme.get_color('text_primary')};
            border-radius: {self.theme.get_border_radius('lg')}px;
            width: 18px;
            margin: -8px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {self.theme.get_color('accent_blue')};
        }}
        
        QSlider::groove:vertical {{
            background-color: {self.theme.get_color('input_background')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            width: 8px;
            margin: 0 2px;
        }}
        
        QSlider::handle:vertical {{
            background-color: {self.theme.get_color('primary_blue')};
            border: 2px solid {self.theme.get_color('text_primary')};
            border-radius: {self.theme.get_border_radius('lg')}px;
            height: 18px;
            margin: 0 -8px;
        }}
        
        QSlider::handle:vertical:hover {{
            background-color: {self.theme.get_color('accent_blue')};
        }}
        """
    
    def get_checkbox_style(self) -> str:
        """Get checkbox stylesheet."""
        return f"""
        QCheckBox {{
            color: {self.theme.get_color('text_primary')};
            spacing: {self.theme.get_spacing('sm')}px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('sm')}px;
            background-color: {self.theme.get_color('input_background')};
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {self.theme.get_color('primary_blue')};
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {self.theme.get_color('primary_blue')};
            border-color: {self.theme.get_color('primary_blue')};
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEgNUw0IDhMOSAzIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
        }}
        
        QCheckBox::indicator:checked:hover {{
            background-color: {self.theme.get_color('primary_blue_hover')};
        }}
        
        QCheckBox::indicator:disabled {{
            background-color: {self.theme.get_color('text_disabled')};
            border-color: {self.theme.get_color('text_disabled')};
        }}
        """
    
    def get_radio_button_style(self) -> str:
        """Get radio button stylesheet."""
        return f"""
        QRadioButton {{
            color: {self.theme.get_color('text_primary')};
            spacing: {self.theme.get_spacing('sm')}px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('full')}px;
            background-color: {self.theme.get_color('input_background')};
        }}
        
        QRadioButton::indicator:hover {{
            border-color: {self.theme.get_color('primary_blue')};
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {self.theme.get_color('primary_blue')};
            border-color: {self.theme.get_color('primary_blue')};
        }}
        
        QRadioButton::indicator:checked:hover {{
            background-color: {self.theme.get_color('primary_blue_hover')};
        }}
        
        QRadioButton::indicator:disabled {{
            background-color: {self.theme.get_color('text_disabled')};
            border-color: {self.theme.get_color('text_disabled')};
        }}
        """
    
    def get_group_box_style(self) -> str:
        """Get group box stylesheet."""
        return f"""
        QGroupBox {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            font-weight: 600;
            padding-top: {self.theme.get_spacing('lg')}px;
            margin-top: {self.theme.get_spacing('sm')}px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {self.theme.get_spacing('md')}px;
            padding: 0 {self.theme.get_spacing('sm')}px 0 {self.theme.get_spacing('sm')}px;
            background-color: {self.theme.get_color('surface_grey')};
        }}
        """
    
    def get_tab_bar_style(self) -> str:
        """Get tab bar stylesheet."""
        return f"""
        QTabBar::tab {{
            background-color: {self.theme.get_color('tab_inactive')};
            color: {self.theme.get_color('text_secondary')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-bottom: none;
            border-radius: {self.theme.get_border_radius('md')}px {self.theme.get_border_radius('md')}px 0 0;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('lg')}px;
            margin-right: 2px;
            font-weight: 500;
        }}
        
        QTabBar::tab:hover {{
            background-color: {self.theme.get_color('tab_hover')};
            color: {self.theme.get_color('text_primary')};
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.theme.get_color('tab_active')};
            color: {self.theme.get_color('text_primary')};
            border-bottom: 2px solid {self.theme.get_color('primary_blue')};
        }}
        """
    
    def get_combo_box_style(self) -> str:
        """Get combo box stylesheet."""
        return f"""
        QComboBox {{
            background-color: {self.theme.get_color('input_background')};
            border: 2px solid {self.theme.get_color('input_border')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            color: {self.theme.get_color('text_primary')};
            font-size: {self.theme.get_font_size('base')}px;
        }}
        
        QComboBox:hover {{
            border-color: {self.theme.get_color('hover_grey')};
        }}
        
        QComboBox:focus {{
            border-color: {self.theme.get_color('input_focus')};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;
            border-left: 1px solid {self.theme.get_color('border_grey')};
            border-radius: 0 {self.theme.get_border_radius('md')}px {self.theme.get_border_radius('md')}px 0;
            background-color: {self.theme.get_color('hover_grey')};
        }}
        
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0ie2NvbG9yfSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg);
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            selection-background-color: {self.theme.get_color('primary_blue')};
        }}
        """
    
    def get_spin_box_style(self) -> str:
        """Get spin box stylesheet."""
        return f"""
        QSpinBox {{
            background-color: {self.theme.get_color('input_background')};
            border: 2px solid {self.theme.get_color('input_border')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            color: {self.theme.get_color('text_primary')};
            font-size: {self.theme.get_font_size('base')}px;
        }}
        
        QSpinBox:hover {{
            border-color: {self.theme.get_color('hover_grey')};
        }}
        
        QSpinBox:focus {{
            border-color: {self.theme.get_color('input_focus')};
        }}
        
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {self.theme.get_color('hover_grey')};
            border: none;
            width: 20px;
        }}
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {self.theme.get_color('primary_blue')};
        }}
        """
    
    def get_double_spin_box_style(self) -> str:
        """Get double spin box stylesheet."""
        return self.get_spin_box_style()
    
    def get_text_edit_style(self) -> str:
        """Get text edit stylesheet."""
        return f"""
        QTextEdit {{
            background-color: {self.theme.get_color('input_background')};
            color: {self.theme.get_color('text_primary')};
            border: 2px solid {self.theme.get_color('input_border')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px;
            font-size: {self.theme.get_font_size('base')}px;
            selection-background-color: {self.theme.get_color('primary_blue')};
        }}
        
        QTextEdit:focus {{
            border-color: {self.theme.get_color('input_focus')};
            background-color: {self.theme.get_color('surface_grey')};
        }}
        
        QTextEdit:hover {{
            border-color: {self.theme.get_color('hover_grey')};
        }}
        """
    
    def get_plain_text_edit_style(self) -> str:
        """Get plain text edit stylesheet."""
        return f"""
        QPlainTextEdit {{
            background-color: {self.theme.get_color('input_background')};
            color: {self.theme.get_color('text_primary')};
            border: 2px solid {self.theme.get_color('input_border')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px;
            font-size: {self.theme.get_font_size('base')}px;
            selection-background-color: {self.theme.get_color('primary_blue')};
        }}
        
        QPlainTextEdit:focus {{
            border-color: {self.theme.get_color('input_focus')};
            background-color: {self.theme.get_color('surface_grey')};
        }}
        
        QPlainTextEdit:hover {{
            border-color: {self.theme.get_color('hover_grey')};
        }}
        """
    
    def get_label_style(self) -> str:
        """Get label stylesheet."""
        return f"""
        QLabel {{
            color: {self.theme.get_color('text_primary')};
            background-color: transparent;
            font-size: {self.theme.get_font_size('base')}px;
        }}
        
        QLabel[class="heading"] {{
            font-size: {self.theme.get_font_size('xl')}px;
            font-weight: 600;
            color: {self.theme.get_color('text_primary')};
        }}
        
        QLabel[class="subheading"] {{
            font-size: {self.theme.get_font_size('lg')}px;
            font-weight: 500;
            color: {self.theme.get_color('text_secondary')};
        }}
        
        QLabel[class="caption"] {{
            font-size: {self.theme.get_font_size('sm')}px;
            color: {self.theme.get_color('text_secondary')};
        }}
        
        QLabel[class="disabled"] {{
            color: {self.theme.get_color('text_disabled')};
        }}
        """
    
    def get_frame_style(self) -> str:
        """Get frame stylesheet."""
        return f"""
        QFrame {{
            background-color: {self.theme.get_color('surface_grey')};
            border: 1px solid {self.theme.get_color('divider_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
        }}
        
        QFrame[class="card"] {{
            background-color: {self.theme.get_color('card_grey')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('lg')}px;
        }}
        
        QFrame[class="separator"] {{
            background-color: {self.theme.get_color('divider_grey')};
            border: none;
            border-radius: 0;
        }}
        """
    
    def get_widget_style(self) -> str:
        """Get general widget stylesheet."""
        return f"""
        QWidget {{
            background-color: {self.theme.get_color('background_grey')};
            color: {self.theme.get_color('text_primary')};
            font-family: {self.theme.fonts['primary']};
        }}
        """
    
    def get_dialog_style(self) -> str:
        """Get dialog stylesheet."""
        return f"""
        QDialog {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('lg')}px;
        }}
        """
    
    def get_message_box_style(self) -> str:
        """Get message box stylesheet."""
        return f"""
        QMessageBox {{
            background-color: {self.theme.get_color('surface_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('lg')}px;
        }}
        
        QMessageBox QLabel {{
            color: {self.theme.get_color('text_primary')};
        }}
        
        QMessageBox QPushButton {{
            background-color: {self.theme.get_color('button_primary')};
            color: {self.theme.get_color('text_primary')};
            border: none;
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            font-weight: 500;
        }}
        
        QMessageBox QPushButton:hover {{
            background-color: {self.theme.get_color('button_primary_hover')};
        }}
        """
    
    def get_tooltip_style(self) -> str:
        """Get tooltip stylesheet."""
        return f"""
        QToolTip {{
            background-color: {self.theme.get_color('card_grey')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border_grey')};
            border-radius: {self.theme.get_border_radius('md')}px;
            padding: {self.theme.get_spacing('sm')}px {self.theme.get_spacing('md')}px;
            font-size: {self.theme.get_font_size('sm')}px;
        }}
        """
    
    def get_stylesheet(self, widget_type: str) -> str:
        """Get stylesheet for a specific widget type."""
        return self.stylesheets.get(widget_type, '')
    
    def apply_stylesheet(self, widget, widget_type: str):
        """Apply stylesheet to a widget."""
        widget.setStyleSheet(self.get_stylesheet(widget_type))


class AnimationManager:
    """Manages UI animations and transitions."""
    
    def __init__(self, theme: ModernTheme):
        self.theme = theme
        self.animations = {}
    
    def fade_in(self, widget, duration: int = 250):
        """Create fade-in animation."""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation
    
    def fade_out(self, widget, duration: int = 250):
        """Create fade-out animation."""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        return animation
    
    def slide_in_left(self, widget, duration: int = 300):
        """Create slide-in from left animation."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = widget.geometry()
        start_rect.moveLeft(-widget.width())
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation
    
    def slide_in_right(self, widget, duration: int = 300):
        """Create slide-in from right animation."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = widget.geometry()
        start_rect.moveLeft(widget.parent().width() if widget.parent() else 1920)
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation
    
    def slide_in_top(self, widget, duration: int = 300):
        """Create slide-in from top animation."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = widget.geometry()
        start_rect.moveTop(-widget.height())
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation
    
    def slide_in_bottom(self, widget, duration: int = 300):
        """Create slide-in from bottom animation."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = widget.geometry()
        start_rect.moveTop(widget.parent().height() if widget.parent() else 1080)
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation
    
    def scale_in(self, widget, duration: int = 250):
        """Create scale-in animation."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = widget.geometry()
        center_x = start_rect.center().x()
        center_y = start_rect.center().y()
        
        # Calculate scaled rect
        start_rect.setWidth(0)
        start_rect.setHeight(0)
        start_rect.moveCenter(center_x, center_y)
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation
    
    def bounce(self, widget, duration: int = 500):
        """Create bounce animation."""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        original_rect = widget.geometry()
        
        # Create bounce effect
        animation.setStartValue(original_rect)
        animation.setEndValue(original_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutElastic)
        return animation


class ModernUIComponents:
    """Collection of modern UI components with blue/grey theme."""
    
    def __init__(self, theme: ModernTheme, style_manager: StyleSheetManager):
        self.theme = theme
        self.style_manager = style_manager
    
    def create_modern_button(self, text: str, button_type: str = "secondary", parent=None) -> 'QPushButton':
        """Create a modern styled button."""
        from PyQt6.QtWidgets import QPushButton
        
        button = QPushButton(text, parent)
        button.setProperty("class", button_type)
        self.style_manager.apply_stylesheet(button, "button")
        
        # Set minimum size for better appearance
        button.setMinimumHeight(36)
        button.setMinimumWidth(80)
        
        return button
    
    def create_modern_card(self, parent=None) -> 'QFrame':
        """Create a modern card frame."""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout
        
        card = QFrame(parent)
        card.setProperty("class", "card")
        self.style_manager.apply_stylesheet(card, "frame")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            self.theme.get_spacing('md'),
            self.theme.get_spacing('md'),
            self.theme.get_spacing('md'),
            self.theme.get_spacing('md')
        )
        
        return card
    
    def create_modern_separator(self, orientation: str = "horizontal", parent=None) -> 'QFrame':
        """Create a modern separator."""
        from PyQt6.QtWidgets import QFrame
        
        separator = QFrame(parent)
        separator.setProperty("class", "separator")
        
        if orientation == "horizontal":
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setMaximumHeight(1)
        else:
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setMaximumWidth(1)
        
        self.style_manager.apply_stylesheet(separator, "frame")
        return separator
    
    def create_modern_label(self, text: str, label_type: str = "normal", parent=None) -> 'QLabel':
        """Create a modern styled label."""
        from PyQt6.QtWidgets import QLabel
        
        label = QLabel(text, parent)
        label.setProperty("class", label_type)
        self.style_manager.apply_stylesheet(label, "label")
        
        return label
    
    def create_modern_progress_bar(self, parent=None) -> 'QProgressBar':
        """Create a modern progress bar."""
        from PyQt6.QtWidgets import QProgressBar
        
        progress = QProgressBar(parent)
        progress.setTextVisible(True)
        progress.setMinimumHeight(20)
        self.style_manager.apply_stylesheet(progress, "progress_bar")
        
        return progress
    
    def create_modern_slider(self, orientation: str = "horizontal", parent=None) -> 'QSlider':
        """Create a modern slider."""
        from PyQt6.QtWidgets import QSlider
        from PyQt6.QtCore import Qt
        
        slider = QSlider()
        if orientation == "horizontal":
            slider.setOrientation(Qt.Orientation.Horizontal)
        else:
            slider.setOrientation(Qt.Orientation.Vertical)
        
        self.style_manager.apply_stylesheet(slider, "slider")
        return slider


# Global theme instance
theme = ModernTheme()
style_manager = StyleSheetManager(theme)
animation_manager = AnimationManager(theme)
ui_components = ModernUIComponents(theme, style_manager)
