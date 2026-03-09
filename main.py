#!/usr/bin/env python3.12
"""
Advanced Web Browser - Main Entry Point

Launches the advanced browser with tabs, navigation, and full features.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point."""
    print("Starting Vertex...")
    
    # Set Qt attribute before creating QApplication
    from PyQt6.QtCore import Qt
    Qt.AA_ShareOpenGLContexts = True
    
    # Import QtWebEngineWidgets before QApplication
    import PyQt6.QtWebEngineWidgets
    
    # Create QApplication with required attributes for QtWebEngine
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Import and run the browser
    from browser import AdvancedBrowser
    
    try:
        # Create and show browser
        browser = AdvancedBrowser()
        browser.show()
        
        print("Vertex ready!")
        return app.exec()
    except KeyboardInterrupt:
        print("\nShutting down browser...")
    except Exception as e:
        print(f"Browser error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
