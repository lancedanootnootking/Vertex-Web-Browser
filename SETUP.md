# Setup Instructions

This guide provides detailed instructions for setting up and running the Advanced Web Browser.

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM
- **Storage**: 500MB free space
- **Network**: Internet connection for web browsing

### Recommended Requirements

- **Operating System**: Windows 11, macOS 12, or Linux (Ubuntu 20.04+)
- **Python**: 3.10 or higher
- **Memory**: 8GB RAM
- **Storage**: 2GB free space
- **Graphics**: Hardware acceleration support

## Installation Steps

### 1. Prerequisites

#### Install Python

**Windows:**
1. Download Python from [python.org](https://python.org)
2. Run the installer and check "Add Python to PATH"
3. Verify installation:
```cmd
python --version
pip --version
```

**macOS:**
```bash
# Using Homebrew
brew install python3

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Install Git (Optional)

```bash
# Windows: Download from git-scm.com
# macOS: brew install git
# Linux: sudo apt install git
```

### 2. Clone or Download the Project

#### Option A: Clone with Git
```bash
git clone https://github.com/your-repo/advanced-web-browser.git
cd advanced-web-browser
```

#### Option B: Download ZIP
1. Download the project ZIP file
2. Extract to a directory
3. Navigate to the project directory

### 3. Create Virtual Environment

```bash
# Create virtual environment
python -m venv browser_env

# Activate virtual environment
# Windows:
browser_env\Scripts\activate

# macOS/Linux:
source browser_env/bin/activate
```

### 4. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# Initialize the database
python -m backend.database.init_db --init

# Create sample data (optional)
python -m backend.database.init_db --sample
```

### 6. Verify Installation

```bash
# Check database
python -m backend.database.init_db --info

# Test backend
python backend/app.py
```

## Running the Browser

### Development Mode

```bash
# Run with debug output
python main.py --debug
```

### Production Mode

```bash
# Run in production mode
python main.py --production
```

### Command Line Options

```bash
python main.py --help

# Options:
#   --config PATH     Configuration file path
#   --production     Run in production mode
#   --debug          Enable debug mode
```

## Configuration

### Configuration File

The browser uses `config.yaml` for configuration. A default file is created automatically.

### Key Settings

```yaml
browser:
  default_homepage: "https://www.google.com"
  theme: "dark"
  enable_javascript: true
  enable_cookies: true

security:
  enable_ad_blocker: true
  enforce_https: true
  block_trackers: true

ui:
  window_width: 1200
  window_height: 800
  show_bookmarks_bar: true
  show_status_bar: true
```

### Environment Variables

```bash
# Set configuration path
export BROWSER_CONFIG_PATH="/path/to/config.yaml"

# Set database path
export BROWSER_DB_PATH="/path/to/browser.db"

# Set log level
export BROWSER_LOG_LEVEL="INFO"
```

## Troubleshooting

### Common Issues

#### Python Not Found

**Problem**: `python: command not found`

**Solution**:
- Ensure Python is installed and in PATH
- Use `python3` instead of `python` on some systems
- Reinstall Python with PATH option enabled

#### Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'tkinter'`

**Solution**:
```bash
# Ubuntu/Debian:
sudo apt install python3-tk

# Fedora:
sudo dnf install python3-tkinter

# macOS: Tkinter comes with Python
# Windows: Reinstall Python with Tcl/Tk support
```

#### CEF Python Installation Issues

**Problem**: `cefpython3` installation fails

**Solution**:
```bash
# Install system dependencies
# Ubuntu/Debian:
sudo apt install libgtk-3-0 libgconf-2-4

# Try installing without wheel
pip install --no-use-wheel cefpython3

# Or install specific version
pip install cefpython3==66.0
```

#### Database Errors

**Problem**: Database initialization fails

**Solution**:
```bash
# Check database permissions
ls -la browser_data.db

# Recreate database
rm browser_data.db
python -m backend.database.init_db --init
```

#### Backend Connection Errors

**Problem**: Frontend cannot connect to backend

**Solution**:
1. Check if backend is running on port 5000
2. Verify firewall settings
3. Check for conflicting processes:
```bash
# Check port usage
netstat -an | grep 5000
lsof -i :5000
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
python main.py --debug
```

Check the log file:
```bash
tail -f browser.log
```

### Performance Issues

#### High Memory Usage

**Solution**:
1. Reduce cache size in configuration
2. Close unused tabs
3. Restart browser periodically

#### Slow Startup

**Solution**:
1. Disable unused extensions
2. Clear browser cache
3. Reduce history retention

## Platform-Specific Notes

### Windows

#### Antivirus Software

Some antivirus software may flag the browser as suspicious. Add an exception for the browser directory.

#### Windows Defender

Add the browser directory to Windows Defender exclusions.

#### PATH Issues

Ensure Python and pip are in system PATH.

### macOS

#### Security Settings

macOS may block the browser due to security settings:

```bash
# Allow app to run
xattr -d com.apple.quarantine main.py
```

#### Python Installation

Use Homebrew for easier Python management:
```bash
brew install python3
```

### Linux

#### Display Issues

Ensure X11 is properly configured for GUI applications.

#### Package Dependencies

Install required system packages:

```bash
# Ubuntu/Debian:
sudo apt install python3-tk python3-dev libffi-dev

# Fedora:
sudo dnf install python3-tkinter python3-devel libffi-devel

# Arch Linux:
sudo pacman -S tk python
```

#### Wayland Support

For Wayland users, ensure Tkinter Wayland support:
```bash
# Install required packages
sudo apt install python3-tk python3-pil python3-pil.imagetk
```

## Development Setup

### Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test
pytest tests/test_frontend.py
```

### Code Formatting

```bash
# Format code
black .

# Check style
flake8 .
```

### Database Development

```bash
# Create test database
cp browser_data.db browser_test.db

# Run database migrations
python -m backend.database.init_db --db browser_test.db --init
```

## Extension Development

### Extension Directory

Create extensions in the `user_extensions/` directory:

```bash
mkdir user_extensions/my_extension
cd user_extensions/my_extension
```

### Extension Template

```bash
# Create basic extension structure
mkdir -p user_extensions/my_extension
touch user_extensions/my_extension/manifest.json
touch user_extensions/my_extension/main.py
```

### Testing Extensions

```bash
# Install extension
python -c "
from extensions.manager import ExtensionManager
manager = ExtensionManager({})
manager.install_extension('user_extensions/my_extension')
"
```

## Performance Optimization

### Cache Configuration

```yaml
cache:
  enabled: true
  max_size_mb: 500
  cache_duration_hours: 24
  compress_cache: true
```

### Database Optimization

```bash
# Vacuum database
python -m backend.database.init_db --vacuum

# Check database info
python -m backend.database.init_db --info
```

### Memory Management

```yaml
browser:
  max_tabs: 50
  tab_unload_timeout: 300
```

## Security Configuration

### HTTPS Enforcement

```yaml
security:
  enforce_https: true
  block_malicious_domains: true
```

### Privacy Settings

```yaml
security:
  enable_private_browsing: false
  clear_history_on_exit: false
```

## Backup and Restore

### Backup Data

```bash
# Backup database
cp browser_data.db browser_data_backup.db

# Backup configuration
cp config.yaml config_backup.yaml

# Backup extensions
cp -r extensions/ extensions_backup/
```

### Restore Data

```bash
# Restore database
cp browser_data_backup.db browser_data.db

# Restore configuration
cp config_backup.yaml config.yaml
```

## Network Configuration

### Proxy Settings

```yaml
network:
  proxy_enabled: true
  proxy_host: "proxy.example.com"
  proxy_port: 8080
```

### DNS Settings

```yaml
network:
  dns_servers: ["8.8.8.8", "8.8.4.4"]
```

## Logging Configuration

### Log Levels

```yaml
logging:
  level: "INFO"
  file: "browser.log"
  max_size_mb: 10
  backup_count: 5
```

### Log Analysis

```bash
# View recent logs
tail -f browser.log

# Search for errors
grep "ERROR" browser.log
```

## Getting Help

### Documentation

- [API Documentation](docs/api.md)
- [Extension Development](docs/extensions.md)
- [Architecture Overview](docs/architecture.md)

### Community

- GitHub Issues: Report bugs and request features
- Discussion Forum: Community support
- Wiki: Additional documentation

### Support

For additional support:

1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with details
4. Include system information and error logs

## Updates and Maintenance

### Update Dependencies

```bash
# Update pip
pip install --upgrade pip

# Update packages
pip install --upgrade -r requirements.txt
```

### Database Maintenance

```bash
# Weekly maintenance
python -m backend.database.init_db --vacuum
python -m backend.database.init_db --info
```

### Extension Updates

```bash
# Update extensions
python main.py --update-extensions
```

## Uninstallation

### Remove Browser Files

```bash
# Remove application files
rm -rf /path/to/advanced-web-browser

# Remove user data
rm -rf ~/.config/advanced-web-browser
rm browser_data.db
rm browser.log
```

### Clean System

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf browser_env
```

This setup guide should help you get the Advanced Web Browser running on your system. If you encounter any issues, please refer to the troubleshooting section or create an issue on the project repository.
