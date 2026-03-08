# Extension Development Guide

This guide explains how to create extensions for the Advanced Web Browser.

## Overview

Extensions allow developers to add custom functionality to the browser. Extensions are Python modules that can interact with browser features through the Extension API.

## Extension Structure

An extension is a directory containing:

```
my_extension/
├── manifest.json          # Extension metadata
├── main.py               # Main extension code
├── icon.png              # Extension icon (optional)
├── README.md             # Documentation (optional)
└── resources/            # Additional resources (optional)
    ├── styles.css
    └── scripts.js
```

## Manifest File

The `manifest.json` file defines extension metadata:

```json
{
  "id": "my-extension",
  "name": "My Extension",
  "version": "1.0.0",
  "description": "A sample browser extension",
  "author": "Your Name",
  "main": "main.py",
  "permissions": [
    "bookmarks",
    "history",
    "notifications",
    "ui",
    "network"
  ],
  "auto_enable": true,
  "min_browser_version": "1.0.0"
}
```

### Manifest Fields

- `id`: Unique identifier for the extension
- `name`: Display name
- `version`: Extension version
- `description`: Brief description
- `author`: Extension author
- `main`: Main script file (default: "main.py")
- `permissions`: Required permissions
- `auto_enable`: Whether to auto-enable on install
- `min_browser_version`: Minimum browser version

## Permissions

Extensions must request permissions to access browser features:

### Available Permissions

- `bookmarks`: Access and modify bookmarks
- `history`: Access and modify browsing history
- `settings`: Read and write browser settings
- `notifications`: Show notifications to user
- `ui`: Modify browser interface
- `network`: Make HTTP requests
- `security`: Access security features
- `storage`: Store extension data
- `external`: Open external applications

## Extension API

Extensions interact with the browser through the Extension API class.

### Basic Extension Template

```python
# main.py
import logging

def initialize(api):
    """Called when extension is loaded."""
    logging.info(f"Extension initialized: {api.get_extension_info()['name']}")
    
    # Register event handlers
    api.register_event_handler('tab_loaded', on_tab_loaded)
    api.register_event_handler('url_changed', on_url_changed)

def enable(api):
    """Called when extension is enabled."""
    logging.info("Extension enabled")
    
    # Add toolbar button
    api.add_toolbar_button(
        "my_button", 
        "My Action", 
        on_button_click
    )

def disable(api):
    """Called when extension is disabled."""
    logging.info("Extension disabled")
    
    # Remove toolbar button
    api.remove_toolbar_button("my_button")

def cleanup(api):
    """Called when extension is unloaded."""
    logging.info("Extension cleaned up")

def on_event(event_name, api, *args, **kwargs):
    """Generic event handler."""
    logging.info(f"Event: {event_name}")

def on_tab_loaded(api, tab_info):
    """Called when a tab finishes loading."""
    url = tab_info.get('url', '')
    logging.info(f"Tab loaded: {url}")

def on_url_changed(api, url):
    """Called when URL changes."""
    logging.info(f"URL changed: {url}")

def on_button_click(api):
    """Toolbar button click handler."""
    api.show_notification("My Extension", "Button clicked!")
```

## API Methods

### Tab Management

```python
# Create new tab
tab_id = api.create_tab("https://example.com")

# Get current tab
current_tab = api.get_current_tab()

# Navigate tab
api.navigate_tab(tab_id, "https://newsite.com")

# Close tab
api.close_tab(tab_id)
```

### Bookmarks

```python
# Add bookmark
api.add_bookmark("Example", "https://example.com", "Sites")

# Get bookmarks
bookmarks = api.get_bookmarks("Sites")

# Delete bookmark
api.delete_bookmark(bookmark_id)
```

### History

```python
# Get history
history = api.get_history(limit=50)

# Add history entry
api.add_history_entry("https://example.com", "Example")

# Clear history
api.clear_history()
```

### Settings

```python
# Get preference
theme = api.get_preference("browser.theme")

# Set preference
api.set_preference("browser.theme", "dark")
```

### UI Operations

```python
# Show notification
api.show_notification("Title", "Message", 5000)

# Show dialog
api.show_dialog("Title", "Message", "info")

# Add toolbar button
api.add_toolbar_button("button_id", "Button Text", callback_function)

# Remove toolbar button
api.remove_toolbar_button("button_id")
```

### Network Requests

```python
# Make GET request
response = api.make_request("https://api.example.com/data")

# Make POST request
response = api.make_request(
    "https://api.example.com/data",
    method="POST",
    data={"key": "value"}
)
```

### Storage

```python
# Set storage item
api.set_storage_item("my_key", "my_value")

# Get storage item
value = api.get_storage_item("my_key")

# Get all storage data
data = api.get_storage_data()

# Set all storage data
api.set_storage_data({"key": "value"})
```

### Security

```python
# Check URL security
security_info = api.check_url_security("https://example.com")
```

### Utilities

```python
# Log message
api.log("info", "Extension message")

# Get extension info
info = api.get_extension_info()

# Get browser info
browser_info = api.get_browser_info()

# Get current time
timestamp = api.get_current_time()

# Open external URL
api.open_external("https://example.com")
```

## Event System

Extensions can register handlers for browser events:

### Available Events

- `tab_loaded`: Tab finished loading
- `tab_closed`: Tab was closed
- `url_changed`: URL changed in tab
- `bookmark_added`: Bookmark was added
- `bookmark_removed`: Bookmark was removed
- `history_added`: History entry added
- `history_cleared`: History was cleared
- `preference_changed`: Preference was changed
- `extension_enabled`: Extension was enabled
- `extension_disabled`: Extension was disabled

### Event Registration

```python
def initialize(api):
    # Register event handlers
    api.register_event_handler('tab_loaded', on_tab_loaded)
    api.register_event_handler('url_changed', on_url_changed)

def on_tab_loaded(api, tab_info):
    url = tab_info.get('url', '')
    # Handle tab loaded event

def on_url_changed(api, url):
    # Handle URL changed event
```

## Extension Examples

### Simple URL Shortener Extension

```python
# main.py
import requests
import logging

def initialize(api):
    api.register_event_handler('url_changed', on_url_changed)

def on_url_changed(api, url):
    # Check if URL is long and could be shortened
    if len(url) > 50 and not url.startswith('https://bit.ly'):
        try:
            # Call URL shortening service
            short_url = shorten_url(url)
            if short_url:
                api.show_notification("URL Shortened", f"Shortened: {short_url}")
        except Exception as e:
            api.log("error", f"Error shortening URL: {e}")

def shorten_url(long_url):
    # Implement URL shortening logic
    # This is a placeholder - integrate with actual service
    return f"https://bit.ly/placeholder"
```

### Theme Switcher Extension

```python
# main.py

def enable(api):
    api.add_toolbar_button("theme_switch", "Switch Theme", switch_theme)

def disable(api):
    api.remove_toolbar_button("theme_switch")

def switch_theme(api):
    current_theme = api.get_preference("browser.theme")
    new_theme = "light" if current_theme == "dark" else "dark"
    api.set_preference("browser.theme", new_theme)
    api.show_notification("Theme Changed", f"Theme switched to {new_theme}")
```

### Password Generator Extension

```python
# main.py
import random
import string

def enable(api):
    api.add_toolbar_button("password_gen", "Generate Password", generate_password)

def disable(api):
    api.remove_toolbar_button("password_gen")

def generate_password(api):
    password = generate_random_password()
    api.show_notification("Password Generated", f"New password: {password}")
    
    # Copy to clipboard (if supported)
    try:
        import pyperclip
        pyperclip.copy(password)
        api.show_notification("Copied", "Password copied to clipboard")
    except ImportError:
        pass

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))
```

## Installation

### Manual Installation

1. Create extension directory with manifest and main files
2. Copy to `user_extensions/` directory
3. Restart browser or use extension manager to reload

### Programmatic Installation

```python
from extensions.manager import ExtensionManager

manager = ExtensionManager(config)
success = manager.install_extension("/path/to/extension.zip")
```

## Testing

### Unit Testing

```python
# test_my_extension.py
import unittest
from unittest.mock import Mock
from main import initialize, enable, disable

class TestMyExtension(unittest.TestCase):
    def setUp(self):
        self.api = Mock()
        initialize(self.api)
    
    def test_enable(self):
        enable(self.api)
        self.api.add_toolbar_button.assert_called()
    
    def test_disable(self):
        disable(self.api)
        self.api.remove_toolbar_button.assert_called()

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

Test the extension with the actual browser:

1. Install the extension
2. Test all functionality manually
3. Check browser logs for errors
4. Verify permissions are properly enforced

## Best Practices

### Security

1. **Validate Input**: Always validate user input
2. **Use HTTPS**: Use HTTPS for network requests
3. **Sanitize Data**: Sanitize data before storage or display
4. **Principle of Least Privilege**: Request only necessary permissions

### Performance

1. **Async Operations**: Use async operations for network requests
2. **Caching**: Cache frequently used data
3. **Resource Management**: Clean up resources properly
4. **Error Handling**: Handle errors gracefully

### User Experience

1. **Clear Messages**: Use clear, concise notification messages
2. **Progress Indicators**: Show progress for long operations
3. **Settings**: Provide configurable settings
4. **Documentation**: Include clear documentation

## Debugging

### Logging

Use the API logging method:

```python
api.log("info", "Information message")
api.log("warning", "Warning message")
api.log("error", "Error message")
```

### Error Handling

```python
try:
    # Extension code
    result = some_operation()
except Exception as e:
    api.log("error", f"Operation failed: {e}")
    api.show_notification("Error", "Operation failed")
```

### Browser Logs

Check browser logs for extension errors:

1. Enable debug logging in browser settings
2. Monitor console output
3. Check extension manager for error messages

## Publishing

### Extension Package

Create a distributable package:

```bash
# Create zip package
zip -r my_extension.zip my_extension/
```

### Distribution Methods

1. **Direct Download**: Provide download link
2. **Extension Store**: Submit to browser extension store
3. **Package Manager**: Publish to package manager

### Version Management

Use semantic versioning:

- `1.0.0`: Major release
- `1.1.0`: Minor release with new features
- `1.1.1`: Patch release with bug fixes

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check manifest permissions
2. **Import Errors**: Verify Python dependencies
3. **API Not Available**: Ensure browser is running
4. **Extension Not Loading**: Check manifest syntax

### Debug Steps

1. Check extension logs
2. Verify manifest syntax
3. Test API methods individually
4. Check browser compatibility

## Resources

- [Extension API Reference](api.md)
- [Browser Architecture](architecture.md)
- [Sample Extensions](../examples/extensions/)
- [Community Forum](https://github.com/advanced-browser/forum)

## Support

For extension development support:

1. Check the documentation
2. Search existing issues
3. Create new issue with details
4. Join the developer community
