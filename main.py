#!/usr/bin/env python3
"""
Advanced Web Browser - Main Entry Point

This is the main entry point for the Advanced Web Browser application.
It starts the working search browser with full functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the browser application."""
    print("🚀 Starting Advanced Web Browser...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the working browser by executing it as a script
    try:
        import subprocess
        result = subprocess.run([sys.executable, "browser.py"], cwd=project_root)
        if result.returncode != 0:
            print("❌ Browser exited with error")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Browser not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting browser: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
