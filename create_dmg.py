#!/usr/bin/env python3.12
"""
Create DMG distribution for Vertex Browser
"""

import os
import subprocess
from pathlib import Path

def create_dmg():
    """Create DMG file for distribution."""
    
    project_dir = Path(__file__).parent
    app_name = "Vertex Browser"
    app_path = project_dir / f"{app_name}.app"
    dmg_name = f"{app_name}-1.0.0"
    dmg_path = project_dir / f"{dmg_name}.dmg"
    
    if not app_path.exists():
        print(f"❌ App bundle not found: {app_path}")
        return False
    
    print(f"Creating DMG: {dmg_name}.dmg")
    
    # Remove existing DMG
    if dmg_path.exists():
        os.remove(dmg_path)
    
    # Create DMG using hdiutil
    try:
        # Create temporary DMG
        temp_dmg = project_dir / "temp.dmg"
        subprocess.run([
            "hdiutil", "create",
            "-size", "1g",
            "-fs", "HFS+",
            "-volname", app_name,
            str(temp_dmg)
        ], check=True)
        
        # Mount the DMG
        mount_result = subprocess.run([
            "hdiutil", "attach", str(temp_dmg)
        ], capture_output=True, text=True)
        
        if mount_result.returncode != 0:
            print(f"❌ Failed to mount DMG: {mount_result.stderr}")
            return False
        
        # Get mount point
        mount_output = mount_result.stdout
        mount_line = [line for line in mount_output.split('\n') if '/Volumes/' in line][0]
        mount_point = mount_line.split()[-1]
        
        # Copy app to DMG
        subprocess.run([
            "cp", "-R", str(app_path), mount_point
        ], check=True)
        
        # Create Applications symlink
        subprocess.run([
            "ln", "-s", "/Applications", f"{mount_point}/Applications"
        ], check=True)
        
        # Unmount DMG
        subprocess.run([
            "hdiutil", "detach", mount_point
        ], check=True)
        
        # Convert to compressed DMG
        subprocess.run([
            "hdiutil", "convert", str(temp_dmg),
            "-format", "UDZO",
            "-o", str(dmg_path)
        ], check=True)
        
        # Remove temporary DMG
        os.remove(temp_dmg)
        
        # Get DMG size
        dmg_size = os.path.getsize(dmg_path) / (1024 * 1024)
        
        print(f"✅ DMG created successfully!")
        print(f"📦 Location: {dmg_path}")
        print(f"📊 Size: {dmg_size:.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating DMG: {e}")
        return False

if __name__ == "__main__":
    if create_dmg():
        print("\n🎉 DMG packaging completed!")
        print("You can now distribute the DMG file to users.")
