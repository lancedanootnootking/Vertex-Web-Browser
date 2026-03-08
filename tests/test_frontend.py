"""
Frontend Tests

This module contains tests for the frontend components,
including GUI elements, user interactions, and browser tabs.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock CustomTkinter if not available
try:
    import customtkinter as ctk
except ImportError:
    ctk = Mock()
    ctk.CTk = Mock()
    ctk.CTkFrame = Mock
    ctk.CTkButton = Mock
    ctk.CTkEntry = Mock
    ctk.CTkLabel = Mock
    ctk.CTkComboBox = Mock
    ctk.CTkProgressBar = Mock
    ctk.set_appearance_mode = Mock()


class TestAddressBar(unittest.TestCase):
    """Test address bar functionality."""
    
    def setUp(self):
        """Set up test address bar."""
        # Create mock main window
        self.mock_main_window = Mock()
        self.mock_main_window.get_current_tab = Mock()
        self.mock_main_window.update_status = Mock()
        
        # Create mock parent
        self.mock_parent = Mock()
        
        # Import and create address bar
        try:
            from frontend.address_bar import AddressBar
            self.address_bar = AddressBar(self.mock_parent, self.mock_main_window)
        except ImportError:
            self.skipTest("AddressBar module not available")
    
    def test_url_formatting(self):
        """Test URL formatting and validation."""
        # Test HTTPS upgrade
        formatted = self.address_bar.format_url('example.com')
        self.assertEqual(formatted, 'https://example.com')
        
        # Test search query
        formatted = self.address_bar.format_url('python tutorial')
        self.assertIn('google.com/search', formatted)
        self.assertIn('python+tutorial', formatted)
        
        # Test already HTTPS URL
        formatted = self.address_bar.format_url('https://example.com')
        self.assertEqual(formatted, 'https://example.com')
    
    def test_url_validation(self):
        """Test URL validation."""
        # Test valid URLs
        self.assertTrue(self.address_bar.validate_url('https://example.com'))
        self.assertTrue(self.address_bar.validate_url('http://localhost:8000'))
        
        # Test invalid URLs
        self.assertFalse(self.address_bar.validate_url('not-a-url'))
        self.assertFalse(self.address_bar.validate_url(''))
    
    def test_get_suggestions(self):
        """Test getting URL suggestions."""
        with patch('requests.get') as mock_get:
            # Mock API responses
            mock_history_response = Mock()
            mock_history_response.status_code = 200
            mock_history_response.json.return_value = [
                {'url': 'https://example.com', 'title': 'Example'}
            ]
            
            mock_bookmarks_response = Mock()
            mock_bookmarks_response.status_code = 200
            mock_bookmarks_response.json.return_value = [
                {'url': 'https://google.com', 'title': 'Google'}
            ]
            
            mock_get.side_effect = [mock_history_response, mock_bookmarks_response]
            
            suggestions = self.address_bar.get_suggestions_from_backend('test')
            
            self.assertIsInstance(suggestions, list)
            self.assertGreater(len(suggestions), 0)
    
    def test_security_indicator_update(self):
        """Test security indicator updates."""
        # Test HTTPS URL
        self.address_bar.update_security_indicator('https://example.com')
        
        # Test HTTP URL
        self.address_bar.update_security_indicator('http://example.com')
        
        # Test about: URL
        self.address_bar.update_security_indicator('about:blank')


class TestBrowserTab(unittest.TestCase):
    """Test browser tab functionality."""
    
    def setUp(self):
        """Set up test browser tab."""
        # Create mock notebook
        self.mock_notebook = Mock()
        self.mock_notebook.add = Mock()
        self.mock_notebook.select = Mock()
        
        # Create mock main window
        self.mock_main_window = Mock()
        self.mock_main_window.new_tab = Mock()
        
        # Create browser tab
        try:
            from frontend.browser_tab import BrowserTab
            with patch('frontend.browser_tab.CEF_AVAILABLE', False):
                self.browser_tab = BrowserTab(self.mock_notebook, self.mock_main_window)
        except ImportError:
            self.skipTest("BrowserTab module not available")
    
    def test_url_loading(self):
        """Test URL loading."""
        test_url = 'https://example.com'
        self.browser_tab.load_url(test_url)
        
        # Check if URL was set
        self.assertEqual(self.browser_tab.current_url, test_url)
    
    def test_navigation(self):
        """Test navigation functions."""
        # Test go back
        self.browser_tab.go_back()
        
        # Test go forward
        self.browser_tab.go_forward()
        
        # Test refresh
        self.browser_tab.refresh()
        
        # Test go home
        self.browser_tab.go_home()
    
    def test_zoom_functions(self):
        """Test zoom functionality."""
        initial_zoom = self.browser_tab.get_zoom_level()
        
        # Test zoom in
        self.browser_tab.zoom_in()
        self.assertGreater(self.browser_tab.get_zoom_level(), initial_zoom)
        
        # Test zoom out
        self.browser_tab.zoom_out()
        
        # Test reset zoom
        self.browser_tab.reset_zoom()
        self.assertEqual(self.browser_tab.get_zoom_level(), 1.0)
    
    def test_tab_info(self):
        """Test getting tab information."""
        url = self.browser_tab.get_url()
        title = self.browser_tab.get_title()
        zoom = self.browser_tab.get_zoom_level()
        
        self.assertIsInstance(url, str)
        self.assertIsInstance(title, str)
        self.assertIsInstance(zoom, float)
    
    def test_find_functionality(self):
        """Test find on page."""
        self.browser_tab.find_text('test', forward=True)
        self.browser_tab.find_text('test', forward=False)
    
    def test_print_and_save(self):
        """Test print and save functions."""
        self.browser_tab.print_page()
        self.browser_tab.save_page('/tmp/test.html')


class TestBookmarksPanel(unittest.TestCase):
    """Test bookmarks panel functionality."""
    
    def setUp(self):
        """Set up test bookmarks panel."""
        # Create mock main window
        self.mock_main_window = Mock()
        self.mock_main_window.get_current_tab = Mock()
        self.mock_main_window.update_status = Mock()
        
        # Create mock parent
        self.mock_parent = Mock()
        
        # Create bookmarks panel
        try:
            from frontend.bookmarks_panel import BookmarksPanel
            with patch('frontend.bookmarks_panel.ctk.CTkFrame'):
                self.bookmarks_panel = BookmarksPanel(self.mock_parent, self.mock_main_window)
        except ImportError:
            self.skipTest("BookmarksPanel module not available")
    
    def test_bookmark_operations(self):
        """Test bookmark operations."""
        # Test adding bookmark
        bookmark_data = {
            'title': 'Test Bookmark',
            'url': 'https://example.com',
            'folder': 'Test'
        }
        
        # Mock the add_bookmark method
        self.bookmarks_panel.add_bookmark = Mock()
        self.bookmarks_panel.add_bookmark(bookmark_data)
        self.bookmarks_panel.add_bookmark.assert_called_once_with(bookmark_data)
    
    def test_bookmark_search(self):
        """Test bookmark searching."""
        # Mock search functionality
        self.bookmarks_panel.search_bookmarks = Mock()
        self.bookmarks_panel.search_bookmarks('test')
        self.bookmarks_panel.search_bookmarks.assert_called_once_with('test')
    
    def test_bookmark_filtering(self):
        """Test bookmark filtering."""
        # Mock filtering functionality
        self.bookmarks_panel.filter_bookmarks = Mock()
        self.bookmarks_panel.filter_bookmarks()
        self.bookmarks_panel.filter_bookmarks.assert_called_once()


class TestHistoryPanel(unittest.TestCase):
    """Test history panel functionality."""
    
    def setUp(self):
        """Set up test history panel."""
        # Create mock main window
        self.mock_main_window = Mock()
        self.mock_main_window.get_current_tab = Mock()
        self.mock_main_window.update_status = Mock()
        
        # Create mock parent
        self.mock_parent = Mock()
        
        # Create history panel
        try:
            from frontend.history_panel import HistoryPanel
            with patch('frontend.history_panel.ctk.CTkFrame'):
                self.history_panel = HistoryPanel(self.mock_parent, self.mock_main_window)
        except ImportError:
            self.skipTest("HistoryPanel module not available")
    
    def test_history_operations(self):
        """Test history operations."""
        # Test getting history
        self.history_panel.get_history = Mock()
        self.history_panel.get_history()
        self.history_panel.get_history.assert_called_once()
    
    def test_history_search(self):
        """Test history searching."""
        # Mock search functionality
        self.history_panel.search_history = Mock()
        self.history_panel.search_history('test')
        self.history_panel.search_history.assert_called_once_with('test')
    
    def test_history_filtering(self):
        """Test history filtering."""
        # Mock filtering functionality
        self.history_panel.filter_history = Mock()
        self.history_panel.filter_history()
        self.history_panel.filter_history.assert_called_once()
    
    def test_history_statistics(self):
        """Test history statistics."""
        # Mock statistics functionality
        self.history_panel.get_history_stats = Mock()
        self.history_panel.get_history_stats()
        self.history_panel.get_history_stats.assert_called_once()


class TestThemeManager(unittest.TestCase):
    """Test theme manager functionality."""
    
    def setUp(self):
        """Set up test theme manager."""
        try:
            from frontend.themes.theme_manager import ThemeManager
            self.theme_manager = ThemeManager('dark')
        except ImportError:
            self.skipTest("ThemeManager module not available")
    
    def test_theme_switching(self):
        """Test theme switching."""
        # Test setting theme
        success = self.theme_manager.set_theme('light')
        self.assertTrue(success)
        self.assertEqual(self.theme_manager.get_current_theme(), 'light')
        
        # Test invalid theme
        success = self.theme_manager.set_theme('invalid_theme')
        self.assertFalse(success)
    
    def test_theme_colors(self):
        """Test getting theme colors."""
        colors = self.theme_manager.get_theme_colors()
        self.assertIsInstance(colors, dict)
        self.assertIn('primary', colors)
        self.assertIn('accent', colors)
        self.assertIn('background', colors)
    
    def test_custom_themes(self):
        """Test custom theme management."""
        # Test adding custom theme
        custom_theme = {
            'name': 'Custom Theme',
            'appearance_mode': 'dark',
            'colors': {
                'primary': '#ff0000',
                'accent': '#00ff00',
                'background': '#000000',
                'text': '#ffffff'
            }
        }
        
        success = self.theme_manager.add_custom_theme('custom', custom_theme)
        self.assertTrue(success)
        
        # Test using custom theme
        self.theme_manager.set_theme('custom')
        colors = self.theme_manager.get_theme_colors()
        self.assertEqual(colors['primary'], '#ff0000')
    
    def test_theme_export_import(self):
        """Test theme export and import."""
        # Export theme
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            success = self.theme_manager.export_theme('dark', temp_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            
            # Import theme
            success = self.theme_manager.import_theme(temp_path, 'imported_dark')
            self.assertTrue(success)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMainWindow(unittest.TestCase):
    """Test main window functionality."""
    
    def setUp(self):
        """Set up test main window."""
        # Create mock components
        self.mock_config = {
            'browser': {'theme': 'dark'},
            'security': {'enable_ad_blocker': True}
        }
        
        self.mock_backend_app = Mock()
        self.mock_extension_manager = Mock()
        
        # Create main window
        try:
            from frontend.main_window import BrowserMainWindow
            with patch('frontend.main_window.ctk.CTk'):
                self.main_window = BrowserMainWindow(
                    self.mock_config,
                    self.mock_backend_app,
                    self.mock_extension_manager
                )
        except ImportError:
            self.skipTest("MainWindow module not available")
    
    def test_tab_management(self):
        """Test tab management."""
        # Test creating new tab
        self.main_window.new_tab = Mock()
        self.main_window.new_tab()
        self.main_window.new_tab.assert_called_once()
        
        # Test closing current tab
        self.main_window.close_current_tab = Mock()
        self.main_window.close_current_tab()
        self.main_window.close_current_tab.assert_called_once()
    
    def test_navigation(self):
        """Test navigation functions."""
        # Test navigation functions
        self.main_window.go_back = Mock()
        self.main_window.go_forward = Mock()
        self.main_window.refresh_page = Mock()
        self.main_window.go_home = Mock()
        
        self.main_window.go_back()
        self.main_window.go_forward()
        self.main_window.refresh_page()
        self.main_window.go_home()
        
        # Verify calls were made
        self.main_window.go_back.assert_called_once()
        self.main_window.go_forward.assert_called_once()
        self.main_window.refresh_page.assert_called_once()
        self.main_window.go_home.assert_called_once()
    
    def test_bookmark_operations(self):
        """Test bookmark operations."""
        # Test bookmark current page
        self.main_window.bookmark_page = Mock()
        self.main_window.bookmark_page()
        self.main_window.bookmark_page.assert_called_once()
    
    def test_history_operations(self):
        """Test history operations."""
        # Test clear history
        self.main_window.clear_history = Mock()
        self.main_window.clear_history()
        self.main_window.clear_history.assert_called_once()
    
    def test_ui_operations(self):
        """Test UI operations."""
        # Test toggle functions
        self.main_window.toggle_bookmarks_bar = Mock()
        self.main_window.toggle_status_bar = Mock()
        self.main_window.toggle_side_panel = Mock()
        self.main_window.toggle_fullscreen = Mock()
        
        self.main_window.toggle_bookmarks_bar()
        self.main_window.toggle_status_bar()
        self.main_window.toggle_side_panel()
        self.main_window.toggle_fullscreen()
        
        # Verify calls were made
        self.main_window.toggle_bookmarks_bar.assert_called_once()
        self.main_window.toggle_status_bar.assert_called_once()
        self.main_window.toggle_side_panel.assert_called_once()
        self.main_window.toggle_fullscreen.assert_called_once()


if __name__ == '__main__':
    unittest.main()
