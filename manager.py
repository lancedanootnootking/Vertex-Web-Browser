"""
Extension Manager

This module manages browser extensions, including loading,
unloading, and providing an API for extension functionality.
"""

import logging
import os
import json
import importlib.util
import sys
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import zipfile
import tempfile
import shutil
from pathlib import Path

from .api import ExtensionAPI


class Extension:
    """Represents a browser extension."""
    
    def __init__(self, manifest_path: str):
        self.logger = logging.getLogger(__name__)
        self.manifest_path = manifest_path
        self.extension_dir = os.path.dirname(manifest_path)
        
        # Load manifest
        self.manifest = self.load_manifest()
        
        # Extension properties
        self.id = self.manifest.get('id', '')
        self.name = self.manifest.get('name', 'Unknown Extension')
        self.version = self.manifest.get('version', '1.0.0')
        self.description = self.manifest.get('description', '')
        self.author = self.manifest.get('author', '')
        self.permissions = self.manifest.get('permissions', [])
        
        # Runtime state
        self.enabled = False
        self.loaded = False
        self.module = None
        self.api = None
        
        # Statistics
        self.stats = {
            'installed_at': datetime.now(),
            'enabled_at': None,
            'usage_count': 0,
            'errors': []
        }
    
    def load_manifest(self) -> Dict[str, Any]:
        """Load extension manifest."""
        try:
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading manifest {self.manifest_path}: {e}")
            return {}
    
    def load(self) -> bool:
        """Load the extension module."""
        if self.loaded:
            return True
        
        try:
            # Find main script
            main_script = self.manifest.get('main', 'main.py')
            main_path = os.path.join(self.extension_dir, main_script)
            
            if not os.path.exists(main_path):
                self.logger.error(f"Main script not found: {main_path}")
                return False
            
            # Load module
            spec = importlib.util.spec_from_file_location(self.id, main_path)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
            
            # Create API instance
            self.api = ExtensionAPI(self)
            
            # Initialize extension
            if hasattr(self.module, 'initialize'):
                self.module.initialize(self.api)
            
            self.loaded = True
            self.logger.info(f"Loaded extension: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading extension {self.name}: {e}")
            self.stats['errors'].append(str(e))
            return False
    
    def enable(self) -> bool:
        """Enable the extension."""
        if not self.loaded:
            if not self.load():
                return False
        
        try:
            # Call extension's enable method if exists
            if hasattr(self.module, 'enable'):
                self.module.enable(self.api)
            
            self.enabled = True
            self.stats['enabled_at'] = datetime.now()
            self.logger.info(f"Enabled extension: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling extension {self.name}: {e}")
            self.stats['errors'].append(str(e))
            return False
    
    def disable(self) -> bool:
        """Disable the extension."""
        if not self.enabled:
            return True
        
        try:
            # Call extension's disable method if exists
            if hasattr(self.module, 'disable'):
                self.module.disable(self.api)
            
            self.enabled = False
            self.logger.info(f"Disabled extension: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling extension {self.name}: {e}")
            self.stats['errors'].append(str(e))
            return False
    
    def unload(self) -> bool:
        """Unload the extension."""
        if self.enabled:
            self.disable()
        
        try:
            # Call extension's cleanup method if exists
            if hasattr(self.module, 'cleanup'):
                self.module.cleanup(self.api)
            
            self.loaded = False
            self.module = None
            self.api = None
            self.logger.info(f"Unloaded extension: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unloading extension {self.name}: {e}")
            self.stats['errors'].append(str(e))
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get extension information."""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'permissions': self.permissions,
            'enabled': self.enabled,
            'loaded': self.loaded,
            'stats': {
                'installed_at': self.stats['installed_at'].isoformat(),
                'enabled_at': self.stats['enabled_at'].isoformat() if self.stats['enabled_at'] else None,
                'usage_count': self.stats['usage_count'],
                'error_count': len(self.stats['errors'])
            }
        }
    
    def has_permission(self, permission: str) -> bool:
        """Check if extension has a specific permission."""
        return permission in self.permissions


class ExtensionManager:
    """Manages browser extensions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Extension storage
        self.extensions: Dict[str, Extension] = {}
        self.extension_dir = "extensions"
        self.user_extension_dir = "user_extensions"
        
        # Configuration
        self.enabled = config.get('enabled', True)
        self.auto_update = config.get('auto_update', True)
        self.allowed_extensions = config.get('allowed_extensions', [])
        self.blocked_extensions = config.get('blocked_extensions', [])
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            'total_extensions': 0,
            'enabled_extensions': 0,
            'disabled_extensions': 0,
            'blocked_extensions': 0,
            'total_errors': 0,
            'last_scan': None
        }
        
        # Initialize extension directories
        self.setup_directories()
        
        # Load extensions
        if self.enabled:
            self.load_extensions()
    
    def setup_directories(self):
        """Setup extension directories."""
        try:
            # Create extension directories
            os.makedirs(self.extension_dir, exist_ok=True)
            os.makedirs(self.user_extension_dir, exist_ok=True)
            
            self.logger.info("Extension directories setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up extension directories: {e}")
    
    def load_extensions(self):
        """Load all extensions from directories."""
        try:
            # Load from system extensions directory
            self.load_extensions_from_directory(self.extension_dir)
            
            # Load from user extensions directory
            self.load_extensions_from_directory(self.user_extension_dir)
            
            self.stats['last_scan'] = datetime.now().isoformat()
            self.update_statistics()
            
            self.logger.info(f"Loaded {len(self.extensions)} extensions")
            
        except Exception as e:
            self.logger.error(f"Error loading extensions: {e}")
    
    def load_extensions_from_directory(self, directory: str):
        """Load extensions from a specific directory."""
        if not os.path.exists(directory):
            return
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            # Check if it's an extension directory
            manifest_path = os.path.join(item_path, 'manifest.json')
            
            if os.path.isdir(item_path) and os.path.exists(manifest_path):
                try:
                    extension = Extension(manifest_path)
                    
                    # Check if extension is blocked
                    if extension.id in self.blocked_extensions:
                        self.logger.warning(f"Extension blocked: {extension.name}")
                        self.stats['blocked_extensions'] += 1
                        continue
                    
                    # Check if extension is allowed (if whitelist is enabled)
                    if self.allowed_extensions and extension.id not in self.allowed_extensions:
                        self.logger.warning(f"Extension not in allowlist: {extension.name}")
                        continue
                    
                    # Add extension
                    self.extensions[extension.id] = extension
                    self.stats['total_extensions'] += 1
                    
                    # Auto-enable if configured
                    if extension.manifest.get('auto_enable', False):
                        extension.enable()
                    
                except Exception as e:
                    self.logger.error(f"Error loading extension from {item_path}: {e}")
                    self.stats['total_errors'] += 1
    
    def install_extension(self, extension_file: str) -> bool:
        """Install extension from file."""
        try:
            # Check if file is a zip archive
            if extension_file.endswith('.zip'):
                return self.install_extension_from_zip(extension_file)
            
            # Check if file is a directory
            elif os.path.isdir(extension_file):
                return self.install_extension_from_directory(extension_file)
            
            else:
                self.logger.error(f"Unsupported extension file: {extension_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error installing extension: {e}")
            return False
    
    def install_extension_from_zip(self, zip_file: str) -> bool:
        """Install extension from zip file."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract zip file
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find extension directory
                extension_dir = None
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        manifest_path = os.path.join(item_path, 'manifest.json')
                        if os.path.exists(manifest_path):
                            extension_dir = item_path
                            break
                
                if not extension_dir:
                    self.logger.error("No valid extension found in zip file")
                    return False
                
                # Load extension to validate
                temp_extension = Extension(os.path.join(extension_dir, 'manifest.json'))
                
                # Check for conflicts
                if temp_extension.id in self.extensions:
                    self.logger.warning(f"Extension with ID {temp_extension.id} already exists")
                    return False
                
                # Copy to user extensions directory
                target_dir = os.path.join(self.user_extension_dir, temp_extension.id)
                shutil.copytree(extension_dir, target_dir)
                
                # Load extension
                extension = Extension(os.path.join(target_dir, 'manifest.json'))
                self.extensions[extension.id] = extension
                
                self.logger.info(f"Installed extension: {extension.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error installing extension from zip: {e}")
            return False
    
    def install_extension_from_directory(self, source_dir: str) -> bool:
        """Install extension from directory."""
        try:
            manifest_path = os.path.join(source_dir, 'manifest.json')
            
            if not os.path.exists(manifest_path):
                self.logger.error("No manifest.json found in extension directory")
                return False
            
            # Load extension to validate
            temp_extension = Extension(manifest_path)
            
            # Check for conflicts
            if temp_extension.id in self.extensions:
                self.logger.warning(f"Extension with ID {temp_extension.id} already exists")
                return False
            
            # Copy to user extensions directory
            target_dir = os.path.join(self.user_extension_dir, temp_extension.id)
            shutil.copytree(source_dir, target_dir)
            
            # Load extension
            extension = Extension(os.path.join(target_dir, 'manifest.json'))
            self.extensions[extension.id] = extension
            
            self.logger.info(f"Installed extension: {extension.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing extension from directory: {e}")
            return False
    
    def uninstall_extension(self, extension_id: str) -> bool:
        """Uninstall an extension."""
        if extension_id not in self.extensions:
            self.logger.warning(f"Extension not found: {extension_id}")
            return False
        
        try:
            extension = self.extensions[extension_id]
            
            # Unload extension
            extension.unload()
            
            # Remove extension directory
            if os.path.exists(extension.extension_dir):
                shutil.rmtree(extension.extension_dir)
            
            # Remove from extensions
            del self.extensions[extension_id]
            
            self.update_statistics()
            self.logger.info(f"Uninstalled extension: {extension.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error uninstalling extension: {e}")
            return False
    
    def enable_extension(self, extension_id: str) -> bool:
        """Enable an extension."""
        if extension_id not in self.extensions:
            self.logger.warning(f"Extension not found: {extension_id}")
            return False
        
        extension = self.extensions[extension_id]
        success = extension.enable()
        
        if success:
            self.update_statistics()
            self.trigger_event('extension_enabled', extension)
        
        return success
    
    def disable_extension(self, extension_id: str) -> bool:
        """Disable an extension."""
        if extension_id not in self.extensions:
            self.logger.warning(f"Extension not found: {extension_id}")
            return False
        
        extension = self.extensions[extension_id]
        success = extension.disable()
        
        if success:
            self.update_statistics()
            self.trigger_event('extension_disabled', extension)
        
        return success
    
    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get an extension by ID."""
        return self.extensions.get(extension_id)
    
    def get_all_extensions(self) -> List[Extension]:
        """Get all extensions."""
        return list(self.extensions.values())
    
    def get_enabled_extensions(self) -> List[Extension]:
        """Get all enabled extensions."""
        return [ext for ext in self.extensions.values() if ext.enabled]
    
    def get_extension_info(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Get extension information."""
        extension = self.get_extension(extension_id)
        return extension.get_info() if extension else None
    
    def get_all_extensions_info(self) -> List[Dict[str, Any]]:
        """Get information for all extensions."""
        return [ext.get_info() for ext in self.extensions.values()]
    
    def trigger_event(self, event_name: str, *args, **kwargs):
        """Trigger an event for all enabled extensions."""
        if not self.enabled:
            return
        
        try:
            # Call custom event handlers
            if event_name in self.event_handlers:
                for handler in self.event_handlers[event_name]:
                    try:
                        handler(*args, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Error in event handler: {e}")
            
            # Call extension event handlers
            for extension in self.get_enabled_extensions():
                if extension.module and hasattr(extension.module, 'on_event'):
                    try:
                        extension.module.on_event(event_name, extension.api, *args, **kwargs)
                        extension.stats['usage_count'] += 1
                    except Exception as e:
                        self.logger.error(f"Error in extension {extension.name} event handler: {e}")
                        extension.stats['errors'].append(str(e))
                        self.stats['total_errors'] += 1
        
        except Exception as e:
            self.logger.error(f"Error triggering event {event_name}: {e}")
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """Add a custom event handler."""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable):
        """Remove a custom event handler."""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    def update_statistics(self):
        """Update extension statistics."""
        self.stats['total_extensions'] = len(self.extensions)
        self.stats['enabled_extensions'] = len([ext for ext in self.extensions.values() if ext.enabled])
        self.stats['disabled_extensions'] = len([ext for ext in self.extensions.values() if not ext.enabled])
        
        # Count total errors
        self.stats['total_errors'] = sum(len(ext.stats['errors']) for ext in self.extensions.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get extension manager statistics."""
        self.update_statistics()
        
        return {
            'enabled': self.enabled,
            'total_extensions': self.stats['total_extensions'],
            'enabled_extensions': self.stats['enabled_extensions'],
            'disabled_extensions': self.stats['disabled_extensions'],
            'blocked_extensions': self.stats['blocked_extensions'],
            'total_errors': self.stats['total_errors'],
            'last_scan': self.stats['last_scan'],
            'extension_directory': self.extension_dir,
            'user_extension_directory': self.user_extension_dir
        }
    
    def scan_for_new_extensions(self) -> int:
        """Scan for new extensions."""
        old_count = len(self.extensions)
        self.load_extensions()
        new_count = len(self.extensions)
        
        return new_count - old_count
    
    def update_extensions(self) -> int:
        """Update all extensions (placeholder)."""
        if not self.auto_update:
            return 0
        
        updated_count = 0
        
        for extension in self.extensions.values():
            try:
                # Check for updates (placeholder implementation)
                if hasattr(extension.module, 'check_update'):
                    if extension.module.check_update(extension.api):
                        updated_count += 1
                        self.logger.info(f"Updated extension: {extension.name}")
            
            except Exception as e:
                self.logger.error(f"Error updating extension {extension.name}: {e}")
        
        return updated_count
    
    def export_extensions_config(self, file_path: str) -> bool:
        """Export extensions configuration."""
        try:
            config = {
                'enabled_extensions': [ext.id for ext in self.get_enabled_extensions()],
                'blocked_extensions': self.blocked_extensions,
                'allowed_extensions': self.allowed_extensions,
                'statistics': self.stats,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Exported extensions config to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting extensions config: {e}")
            return False
    
    def import_extensions_config(self, file_path: str) -> bool:
        """Import extensions configuration."""
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Apply configuration
            if 'enabled_extensions' in config:
                for ext_id in config['enabled_extensions']:
                    self.enable_extension(ext_id)
            
            if 'blocked_extensions' in config:
                self.blocked_extensions = config['blocked_extensions']
            
            if 'allowed_extensions' in config:
                self.allowed_extensions = config['allowed_extensions']
            
            self.logger.info(f"Imported extensions config from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing extensions config: {e}")
            return False
    
    def cleanup(self):
        """Cleanup extension manager."""
        try:
            # Unload all extensions
            for extension in self.extensions.values():
                extension.unload()
            
            self.extensions.clear()
            self.event_handlers.clear()
            
            self.logger.info("Extension manager cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def enable(self):
        """Enable extension manager."""
        self.enabled = True
        self.load_extensions()
        self.logger.info("Extension manager enabled")
    
    def disable(self):
        """Disable extension manager."""
        # Disable all extensions
        for extension in self.extensions.values():
            extension.disable()
        
        self.enabled = False
        self.logger.info("Extension manager disabled")
    
    def reset_statistics(self):
        """Reset extension statistics."""
        self.stats = {
            'total_extensions': len(self.extensions),
            'enabled_extensions': len([ext for ext in self.extensions.values() if ext.enabled]),
            'disabled_extensions': len([ext for ext in self.extensions.values() if not ext.enabled]),
            'blocked_extensions': self.stats['blocked_extensions'],
            'total_errors': 0,
            'last_scan': None
        }
        
        # Reset individual extension statistics
        for extension in self.extensions.values():
            extension.stats['usage_count'] = 0
            extension.stats['errors'] = []
        
        self.logger.info("Reset extension statistics")
