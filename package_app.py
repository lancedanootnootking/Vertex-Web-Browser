#!/usr/bin/env python3.12
"""
Package Vertex Browser as macOS .app bundle

Creates a proper macOS application bundle with all dependencies.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import plistlib
import json

def create_app_bundle():
    """Create macOS .app bundle for Vertex Browser."""
    
    # Get current directory
    project_dir = Path(__file__).parent
    app_name = "Vertex Browser"
    app_id = "com.vertex.browser"
    
    # Create .app structure
    app_dir = project_dir / f"{app_name}.app"
    contents_dir = app_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    frameworks_dir = contents_dir / "Frameworks"
    
    print(f"Creating {app_name}.app bundle...")
    
    # Remove existing app if it exists
    if app_dir.exists():
        shutil.rmtree(app_dir)
    
    # Create directory structure
    for directory in [contents_dir, macos_dir, resources_dir, frameworks_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create Info.plist
    info_plist = {
        "CFBundleDisplayName": app_name,
        "CFBundleExecutable": "Vertex Browser",
        "CFBundleIconFile": "Vertex Browser.icns",
        "CFBundleIdentifier": app_id,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": app_name,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeExtensions": ["html", "htm"],
                "CFBundleTypeName": "HTML Document",
                "CFBundleTypeRole": "Viewer"
            },
            {
                "CFBundleTypeExtensions": ["url"],
                "CFBundleTypeName": "Web Location",
                "CFBundleTypeRole": "Viewer"
            }
        ],
        "LSMinimumSystemVersion": "10.15.0",
        "NSHighResolutionCapable": True,
        "NSSupportsAutomaticGraphicsSwitching": True,
        "CFBundleLocalizations": ["en"]
    }
    
    info_plist_path = contents_dir / "Info.plist"
    with open(info_plist_path, "wb") as f:
        plistlib.dump(info_plist, f)
    
    print(f"✓ Created Info.plist")
    
    # Copy icon if it exists
    icon_source = project_dir / "Vertex Browser.icns"
    if icon_source.exists():
        shutil.copy2(icon_source, resources_dir / "Vertex Browser.icns")
        print(f"✓ Copied application icon")
    else:
        print(f"⚠ Icon file not found: {icon_source}")
    
    # Create main executable script
    main_script = macos_dir / "Vertex Browser"
    main_script_content = f'''#!/bin/bash
# Vertex Browser launcher script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
CONTENTS_DIR="$SCRIPT_DIR/../Resources"

# Set Python path
export PYTHONPATH="$CONTENTS_DIR"

# Change to resources directory
cd "$CONTENTS_DIR"

# Run the browser
exec python3 main.py "$@"
'''
    
    with open(main_script, "w") as f:
        f.write(main_script_content)
    
    # Make executable
    main_script.chmod(0o755)
    print(f"✓ Created main executable")
    
    # Copy all Python files to Resources
    python_files = list(project_dir.glob("*.py"))
    for py_file in python_files:
        shutil.copy2(py_file, resources_dir)
    
    # Copy directories
    directories_to_copy = ["frontend", "backend", "extensions", "security", "dev_tools", "docs"]
    for directory in directories_to_copy:
        src_dir = project_dir / directory
        if src_dir.exists():
            dst_dir = resources_dir / directory
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            print(f"✓ Copied {directory} directory")
    
    # Copy requirements.txt if it exists
    requirements_file = project_dir / "requirements.txt"
    if requirements_file.exists():
        shutil.copy2(requirements_file, resources_dir)
        print(f"✓ Copied requirements.txt")
    
    # Copy other assets
    asset_files = ["Vertex Browser.png", "Vertex_Browser-removebg-preview.png"]
    for asset_file in asset_files:
        src = project_dir / asset_file
        if src.exists():
            shutil.copy2(src, resources_dir)
            print(f"✓ Copied {asset_file}")
    
    # Install dependencies in Resources
    print("Installing dependencies...")
    try:
        subprocess.run([
            "pip3", "install", 
            "-r", str(resources_dir / "requirements.txt"),
            "--target", str(resources_dir / "lib")
        ], check=True, capture_output=True)
        print("✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Could not install dependencies: {e}")
    
    # Create PkgInfo
    pkg_info_path = contents_dir / "PkgInfo"
    with open(pkg_info_path, "w") as f:
        f.write("APPL????")
    
    print(f"✓ Created PkgInfo")
    
    # Calculate app size
    def get_directory_size(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    app_size = get_directory_size(app_dir)
    app_size_mb = app_size / (1024 * 1024)
    
    print(f"\n🎉 {app_name}.app created successfully!")
    print(f"📍 Location: {app_dir}")
    print(f"📊 Size: {app_size_mb:.1f} MB")
    print(f"\nTo run the app:")
    print(f"   open '{app_dir}'")
    print(f"   or double-click {app_name}.app in Finder")
    
    return app_dir

if __name__ == "__main__":
    try:
        app_path = create_app_bundle()
        print(f"\n✅ Packaging completed successfully!")
        print(f"📦 App bundle ready at: {app_path}")
    except Exception as e:
        print(f"❌ Error creating app bundle: {e}")
        sys.exit(1)
