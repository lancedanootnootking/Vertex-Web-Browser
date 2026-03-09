# Vertex Browser

A comprehensive web browser built with Python and Tkinter, featuring advanced extension support, developer tools, and modern browsing capabilities.

## Features

### Core Browser Features
- **Tab Management**: Multi-tab browsing with intuitive navigation
- **Bookmarks**: Complete bookmark system with import/export
- **History**: Comprehensive browsing history tracking
- **Downloads**: Advanced download manager with pause/resume
- **Navigation**: Back, forward, refresh, home functionality
- **Search**: Find in page functionality

### Developer Tools
- **Console**: Interactive JavaScript console with command execution
- **Network Monitor**: HTTP request/response tracking and timing
- **Element Inspector**: DOM inspection with tag, class, and ID information
- **Storage Viewer**: Local storage, session storage, and cookies inspection
- **Command Support**: `console.log()`, `clear()`, `help()`, `document.title`, `window.location`

### Extension System
- **Comprehensive API**: Full browser functionality access for extensions
- **Security-First**: Sandboxing, code analysis, digital signatures
- **Developer-Friendly**: Rich hooks system and documentation
- **Store Integration**: Browse, search, and install extensions
- **Multi-Format Support**: Directory, ZIP, CRX, XPI packages
- **Performance Monitoring**: Resource usage and error tracking

### Security & SSL/TLS
- **Secure Context**: Configured SSL context with modern cipher suites
- **TLS 1.2+**: Minimum TLS version enforcement
- **Self-signed Support**: Development-friendly certificate handling
- **Security Logging**: SSL configuration status reporting

## Installation

### From Source
```bash
# Clone the repository
git clone <repository-url>
cd windsurf-project-6

# Install dependencies
pip3 install -r requirements.txt

# Run the browser
python3 main.py
```

### Using Packaged App

#### macOS
1. Download `VertexBrowser.app` from the `dist` folder
2. Double-click to launch
3. If you see a security warning, go to System Preferences > Security & Privacy and allow the app

#### Windows
```bash
# Package the application
python3 package_app.py

# Run the generated executable
dist/Vertex Browser.exe
```

#### Linux
```bash
# Package the application
python3 package_app.py

# Run the AppImage
./dist/vertexbrowser-1.0.0-x86_64.AppImage
```

## Usage

### Basic Browsing
1. **Navigate**: Enter URLs in the address bar
2. **Tabs**: Use the + button to create new tabs
3. **Bookmarks**: Add bookmarks via the Bookmarks menu or button
4. **History**: Access browsing history from the History menu

### Developer Tools
1. **Open DevTools**: Go to Tools > Developer Tools
2. **Console**: Execute JavaScript commands and view logs
3. **Network**: Monitor HTTP requests and responses
4. **Elements**: Inspect DOM structure
5. **Storage**: View and manage storage data

### Extensions
1. **Extension Manager**: Go to Tools > Extensions
2. **Install**: Load extensions from directories or packages
3. **Manage**: Enable/disable extensions and configure settings
4. **Develop**: Use the comprehensive extension API to create custom functionality

## Extension Development

### Creating Extensions
1. Create a directory with a `manifest.json` file
2. Add content scripts, background scripts, and resources
3. Install via the Extension Manager

### Example Extension Structure
```
my_extension/
├── manifest.json
├── background.js
├── content.js
├── popup.html
├── popup.js
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Extension API
The browser provides a comprehensive API for extensions:
- Tab management
- Bookmark management
- History access
- Download management
- Storage (local and sync)
- Notifications
- Context menus
- Message passing

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Operating System**: macOS 10.15+, Windows 10+, or modern Linux
- **Memory**: 512MB RAM
- **Storage**: 100MB available space

### Recommended Requirements
- **Python**: 3.9 or higher
- **Memory**: 1GB RAM or more
- **Storage**: 500MB available space

## Packaging

### Create Application Package
```bash
# Package for current platform
python3 package_app.py

# Package with installer
python3 package_app.py --installer
```

### Supported Platforms
- **macOS**: Creates `.app` bundle
- **Windows**: Creates `.exe` with PyInstaller
- **Linux**: Creates AppImage

## Architecture

The browser is built with a modular architecture:

- **Core Browser** (`browser.py`): Main browser functionality
- **Extension System** (`extensions/`): Comprehensive extension framework
- **Security** (`extensions/security.py`): Sandboxing and threat detection
- **Hooks** (`extensions/hooks.py`): Event system for extensions
- **API** (`extensions/api.py`): Extension API implementation
- **UI Manager** (`extensions/ui_manager.py`): Extension UI components
- **Store** (`extensions/store.py`): Extension store and installer

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Complete browser functionality
- Extension system with 5,000+ lines of code
- Developer tools integration
- SSL/TLS support
- Cross-platform packaging

## Support

For support and feature requests:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Join the community discussions

---

**Vertex Browser** - Advanced web browsing with extension support and developer tools.
