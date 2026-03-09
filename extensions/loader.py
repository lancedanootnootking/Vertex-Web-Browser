#!/usr/bin/env python3
"""
Extension Loader System

Comprehensive extension loading system with support for multiple formats,
dependency management, and lifecycle management.
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
import importlib.util
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Callable, Set
from pathlib import Path
from datetime import datetime
import logging
import hashlib
import traceback
from dataclasses import dataclass, field
from enum import Enum

from .manifest import ManifestParser, ManifestVersion
from .security import SecurityManager, SecurityLevel, SandboxedEnvironment


class LoadState(Enum):
    """Extension loading states."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ENABLING = "enabling"
    ENABLED = "enabled"
    DISABLING = "disabling"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADING = "unloading"


class ExtensionFormat(Enum):
    """Supported extension formats."""
    DIRECTORY = "directory"
    ZIP_PACKAGE = "zip_package"
    CRX_PACKAGE = "crx_package"
    XPI_PACKAGE = "xpi_package"


@dataclass
class ExtensionMetadata:
    """Metadata for an extension."""
    id: str
    name: str
    version: str
    description: str
    author: str
    homepage_url: str
    manifest_version: int
    permissions: List[str]
    host_permissions: List[str]
    content_scripts: List[Dict[str, Any]]
    background_scripts: List[Dict[str, Any]]
    web_accessible_resources: List[Dict[str, Any]]
    action: Optional[Dict[str, Any]]
    icons: Dict[str, str]
    default_locale: str
    locales: Dict[str, str]
    incognito: str
    offline_enabled: bool
    short_name: str
    theme: Optional[Dict[str, Any]]
    developer: Optional[Dict[str, Any]]
    minimum_browser_version: str
    requirements: Dict[str, Any]
    
    # Runtime metadata
    install_date: datetime
    update_date: datetime
    last_used: Optional[datetime]
    usage_count: int = 0
    load_time: float = 0.0
    file_size: int = 0
    checksum: str = ""
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    
    # State
    load_state: LoadState = LoadState.UNLOADED
    enabled: bool = False
    auto_update: bool = True
    allow_in_incognito: bool = False
    
    # Security
    security_level: SecurityLevel = SecurityLevel.UNVERIFIED
    security_verified: bool = False
    signature_verified: bool = False


@dataclass
class LoadError:
    """Represents a loading error."""
    timestamp: datetime
    error_type: str
    error_message: str
    traceback: str
    recoverable: bool = True


class DependencyResolver:
    """Resolves and manages extension dependencies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_graph: Dict[str, Set[str]] = {}
    
    def add_dependency(self, extension_id: str, dependencies: List[str]):
        """Add dependencies for an extension."""
        self.dependency_graph[extension_id] = set(dependencies)
        
        # Update reverse graph
        for dep in dependencies:
            if dep not in self.reverse_graph:
                self.reverse_graph[dep] = set()
            self.reverse_graph[dep].add(extension_id)
    
    def resolve_dependencies(self, extension_id: str) -> Tuple[List[str], List[str]]:
        """Resolve dependencies for an extension.
        
        Returns:
            Tuple of (load_order, missing_dependencies)
        """
        visited = set()
        visiting = set()
        load_order = []
        missing = []
        
        def visit(ext_id: str):
            if ext_id in visiting:
                # Circular dependency detected
                self.logger.warning(f"Circular dependency detected involving {ext_id}")
                return
            
            if ext_id in visited:
                return
            
            visiting.add(ext_id)
            
            # Check if dependency exists
            if ext_id not in self.dependency_graph:
                missing.append(ext_id)
                visiting.remove(ext_id)
                return
            
            # Visit dependencies first
            for dep in self.dependency_graph[ext_id]:
                visit(dep)
            
            visiting.remove(ext_id)
            visited.add(ext_id)
            load_order.append(ext_id)
        
        visit(extension_id)
        return load_order, missing
    
    def get_dependents(self, extension_id: str) -> List[str]:
        """Get all extensions that depend on this extension."""
        return list(self.reverse_graph.get(extension_id, set()))
    
    def check_conflicts(self, extension_id: str, new_dependencies: List[str]) -> List[str]:
        """Check for potential conflicts with existing dependencies."""
        conflicts = []
        
        # Check if new dependencies conflict with existing ones
        for dep in new_dependencies:
            if dep in self.reverse_graph:
                # Another extension depends on this dependency
                conflicts.extend(self.reverse_graph[dep])
        
        return conflicts


class ExtensionLoader:
    """Main extension loader."""
    
    def __init__(self, browser_instance):
        self.browser = browser_instance
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.manifest_parser = ManifestParser()
        self.security_manager = SecurityManager()
        self.dependency_resolver = DependencyResolver()
        
        # Extension storage
        self.extensions: Dict[str, ExtensionMetadata] = {}
        self.extension_paths: Dict[str, str] = {}
        self.extension_modules: Dict[str, Any] = {}
        self.extension_sandboxes: Dict[str, SandboxedEnvironment] = {}
        
        # Load state
        self.loading_extensions: Set[str] = set()
        self.enabling_extensions: Set[str] = set()
        self.load_errors: Dict[str, List[LoadError]] = {}
        
        # Configuration
        self.extensions_dir = Path.home() / ".browser_extensions"
        self.temp_dir = Path(tempfile.gettempdir()) / "browser_extensions_temp"
        
        # Ensure directories exist
        self.extensions_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Load installed extensions
        self._load_installed_extensions()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'extension_loaded': [],
            'extension_enabled': [],
            'extension_disabled': [],
            'extension_unloaded': [],
            'load_error': [],
            'security_event': []
        }
    
    def _load_installed_extensions(self):
        """Load all installed extensions from disk."""
        self.logger.info("Loading installed extensions...")
        
        for item in self.extensions_dir.iterdir():
            if item.is_dir():
                self._load_extension_from_directory(str(item))
            elif item.suffix in ['.zip', '.crx', '.xpi']:
                self._load_extension_from_package(str(item))
    
    def install_extension(self, source_path: str, auto_enable: bool = True) -> Tuple[bool, str]:
        """Install an extension from a source path."""
        try:
            # Determine format
            extension_format = self._detect_format(source_path)
            
            # Extract/load extension
            if extension_format == ExtensionFormat.DIRECTORY:
                extension_path = source_path
            else:
                extension_path = self._extract_package(source_path)
            
            # Parse manifest
            manifest_path = os.path.join(extension_path, "manifest.json")
            if not os.path.exists(manifest_path):
                return False, "manifest.json not found"
            
            manifest = self.manifest_parser.parse(manifest_path)
            if not manifest:
                return False, "Invalid manifest"
            
            extension_id = manifest['id']
            
            # Check if already installed
            if extension_id in self.extensions:
                return False, f"Extension {extension_id} is already installed"
            
            # Security verification
            is_secure, security_level = self.security_manager.verify_extension(extension_path, manifest)
            if not is_secure:
                return False, f"Security verification failed: {security_level}"
            
            # Install to extensions directory
            install_path = self.extensions_dir / extension_id
            if extension_format == ExtensionFormat.DIRECTORY:
                shutil.copytree(extension_path, install_path)
            else:
                shutil.move(extension_path, install_path)
            
            # Load metadata
            metadata = self._create_metadata(manifest, install_path)
            metadata.security_level = security_level
            metadata.security_verified = True
            
            # Store extension
            self.extensions[extension_id] = metadata
            self.extension_paths[extension_id] = str(install_path)
            
            # Resolve dependencies
            dependencies = manifest.get('dependencies', [])
            self.dependency_resolver.add_dependency(extension_id, dependencies)
            
            # Check dependencies
            load_order, missing = self.dependency_resolver.resolve_dependencies(extension_id)
            if missing:
                self.logger.warning(f"Missing dependencies for {extension_id}: {missing}")
            
            # Auto-enable if requested
            if auto_enable:
                self.enable_extension(extension_id)
            
            self.logger.info(f"Successfully installed extension: {extension_id}")
            return True, f"Extension {extension_id} installed successfully"
            
        except Exception as e:
            error_msg = f"Failed to install extension: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def uninstall_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Uninstall an extension."""
        try:
            if extension_id not in self.extensions:
                return False, f"Extension {extension_id} is not installed"
            
            # Disable first
            if self.extensions[extension_id].enabled:
                self.disable_extension(extension_id)
            
            # Check dependents
            dependents = self.dependency_resolver.get_dependents(extension_id)
            if dependents:
                return False, f"Cannot uninstall {extension_id}: required by {dependents}"
            
            # Remove files
            install_path = self.extension_paths.get(extension_id)
            if install_path and os.path.exists(install_path):
                shutil.rmtree(install_path)
            
            # Remove from storage
            del self.extensions[extension_id]
            del self.extension_paths[extension_id]
            
            if extension_id in self.extension_modules:
                del self.extension_modules[extension_id]
            
            if extension_id in self.extension_sandboxes:
                self.extension_sandboxes[extension_id].cleanup()
                del self.extension_sandboxes[extension_id]
            
            # Remove from dependency graph
            if extension_id in self.dependency_resolver.dependency_graph:
                del self.dependency_resolver.dependency_graph[extension_id]
            
            for dep, dependents in self.dependency_resolver.reverse_graph.items():
                dependents.discard(extension_id)
            
            self.logger.info(f"Successfully uninstalled extension: {extension_id}")
            return True, f"Extension {extension_id} uninstalled successfully"
            
        except Exception as e:
            error_msg = f"Failed to uninstall extension: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def enable_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Enable an extension."""
        try:
            if extension_id not in self.extensions:
                return False, f"Extension {extension_id} is not installed"
            
            if self.extensions[extension_id].enabled:
                return True, f"Extension {extension_id} is already enabled"
            
            if extension_id in self.enabling_extensions:
                return False, f"Extension {extension_id} is already being enabled"
            
            self.enabling_extensions.add(extension_id)
            self.extensions[extension_id].load_state = LoadState.ENABLING
            
            # Resolve and load dependencies
            load_order, missing = self.dependency_resolver.resolve_dependencies(extension_id)
            
            # Load dependencies first
            for dep_id in load_order:
                if dep_id != extension_id:
                    success, _ = self.load_extension(dep_id)
                    if not success:
                        self.enabling_extensions.remove(extension_id)
                        return False, f"Failed to load dependency: {dep_id}"
            
            # Load the extension
            success, error = self.load_extension(extension_id)
            if not success:
                self.enabling_extensions.remove(extension_id)
                return False, error
            
            # Create sandbox
            sandbox = self.security_manager.create_sandbox(extension_id)
            if sandbox:
                self.extension_sandboxes[extension_id] = sandbox
            
            # Initialize extension
            if extension_id in self.extension_modules:
                module = self.extension_modules[extension_id]
                if hasattr(module, 'on_enabled'):
                    try:
                        if sandbox:
                            module.on_enabled(sandbox.api)
                        else:
                            module.on_enabled(self._create_api_for_extension(extension_id))
                    except Exception as e:
                        self.logger.error(f"Error in extension on_enabled: {e}")
            
            # Update state
            self.extensions[extension_id].enabled = True
            self.extensions[extension_id].load_state = LoadState.ENABLED
            self.extensions[extension_id].last_used = datetime.now()
            self.enabling_extensions.remove(extension_id)
            
            # Fire event
            self._fire_event('extension_enabled', extension_id)
            
            self.logger.info(f"Successfully enabled extension: {extension_id}")
            return True, f"Extension {extension_id} enabled successfully"
            
        except Exception as e:
            if extension_id in self.enabling_extensions:
                self.enabling_extensions.remove(extension_id)
            
            error_msg = f"Failed to enable extension: {e}"
            self.logger.error(error_msg)
            self._add_load_error(extension_id, "enable_error", error_msg, traceback.format_exc())
            return False, error_msg
    
    def disable_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Disable an extension."""
        try:
            if extension_id not in self.extensions:
                return False, f"Extension {extension_id} is not installed"
            
            if not self.extensions[extension_id].enabled:
                return True, f"Extension {extension_id} is already disabled"
            
            if extension_id in self.enabling_extensions:
                return False, f"Cannot disable extension {extension_id}: currently being enabled"
            
            self.extensions[extension_id].load_state = LoadState.DISABLING
            
            # Call extension cleanup
            if extension_id in self.extension_modules:
                module = self.extension_modules[extension_id]
                if hasattr(module, 'on_disabled'):
                    try:
                        if extension_id in self.extension_sandboxes:
                            module.on_disabled(self.extension_sandboxes[extension_id].api)
                        else:
                            module.on_disabled(self._create_api_for_extension(extension_id))
                    except Exception as e:
                        self.logger.error(f"Error in extension on_disabled: {e}")
            
            # Cleanup sandbox
            if extension_id in self.extension_sandboxes:
                self.extension_sandboxes[extension_id].cleanup()
                del self.extension_sandboxes[extension_id]
            
            # Update state
            self.extensions[extension_id].enabled = False
            self.extensions[extension_id].load_state = LoadState.DISABLED
            
            # Fire event
            self._fire_event('extension_disabled', extension_id)
            
            self.logger.info(f"Successfully disabled extension: {extension_id}")
            return True, f"Extension {extension_id} disabled successfully"
            
        except Exception as e:
            error_msg = f"Failed to disable extension: {e}"
            self.logger.error(error_msg)
            self._add_load_error(extension_id, "disable_error", error_msg, traceback.format_exc())
            return False, error_msg
    
    def load_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Load an extension module."""
        try:
            if extension_id not in self.extensions:
                return False, f"Extension {extension_id} is not installed"
            
            if extension_id in self.extension_modules:
                return True, f"Extension {extension_id} is already loaded"
            
            if extension_id in self.loading_extensions:
                return False, f"Extension {extension_id} is already being loaded"
            
            self.loading_extensions.add(extension_id)
            self.extensions[extension_id].load_state = LoadState.LOADING
            
            start_time = time.time()
            
            extension_path = self.extension_paths[extension_id]
            manifest_path = os.path.join(extension_path, "manifest.json")
            
            # Load manifest
            manifest = self.manifest_parser.parse(manifest_path)
            if not manifest:
                self.loading_extensions.remove(extension_id)
                return False, "Failed to parse manifest"
            
            # Find main script
            main_script = manifest.get('main', 'main.py')
            main_path = os.path.join(extension_path, main_script)
            
            if not os.path.exists(main_path):
                self.loading_extensions.remove(extension_id)
                return False, f"Main script not found: {main_script}"
            
            # Load module
            spec = importlib.util.spec_from_file_location(extension_id, main_path)
            module = importlib.util.module_from_spec(spec)
            
            # Set up module environment
            module.__extension_id__ = extension_id
            module.__extension_path__ = extension_path
            module.__manifest__ = manifest
            
            # Execute module
            spec.loader.exec_module(module)
            
            # Store module
            self.extension_modules[extension_id] = module
            
            # Update metadata
            self.extensions[extension_id].load_time = time.time() - start_time
            self.extensions[extension_id].load_state = LoadState.LOADED
            
            # Initialize extension
            if hasattr(module, 'initialize'):
                try:
                    api = self._create_api_for_extension(extension_id)
                    module.initialize(api)
                except Exception as e:
                    self.logger.error(f"Error in extension initialize: {e}")
                    self._add_load_error(extension_id, "initialize_error", str(e), traceback.format_exc())
            
            # Fire event
            self._fire_event('extension_loaded', extension_id)
            
            self.loading_extensions.remove(extension_id)
            self.logger.info(f"Successfully loaded extension: {extension_id}")
            return True, f"Extension {extension_id} loaded successfully"
            
        except Exception as e:
            if extension_id in self.loading_extensions:
                self.loading_extensions.remove(extension_id)
            
            error_msg = f"Failed to load extension: {e}"
            self.logger.error(error_msg)
            self._add_load_error(extension_id, "load_error", error_msg, traceback.format_exc())
            return False, error_msg
    
    def unload_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Unload an extension."""
        try:
            if extension_id not in self.extensions:
                return False, f"Extension {extension_id} is not installed"
            
            if extension_id not in self.extension_modules:
                return True, f"Extension {extension_id} is not loaded"
            
            # Disable first
            if self.extensions[extension_id].enabled:
                self.disable_extension(extension_id)
            
            self.extensions[extension_id].load_state = LoadState.UNLOADING
            
            # Call cleanup
            module = self.extension_modules[extension_id]
            if hasattr(module, 'cleanup'):
                try:
                    module.cleanup()
                except Exception as e:
                    self.logger.error(f"Error in extension cleanup: {e}")
            
            # Remove module
            del self.extension_modules[extension_id]
            
            # Update state
            self.extensions[extension_id].load_state = LoadState.UNLOADED
            
            # Fire event
            self._fire_event('extension_unloaded', extension_id)
            
            self.logger.info(f"Successfully unloaded extension: {extension_id}")
            return True, f"Extension {extension_id} unloaded successfully"
            
        except Exception as e:
            error_msg = f"Failed to unload extension: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _detect_format(self, source_path: str) -> ExtensionFormat:
        """Detect the format of an extension package."""
        if os.path.isdir(source_path):
            return ExtensionFormat.DIRECTORY
        
        suffix = Path(source_path).suffix.lower()
        if suffix == '.zip':
            return ExtensionFormat.ZIP_PACKAGE
        elif suffix == '.crx':
            return ExtensionFormat.CRX_PACKAGE
        elif suffix == '.xpi':
            return ExtensionFormat.XPI_PACKAGE
        
        raise ValueError(f"Unsupported extension format: {suffix}")
    
    def _extract_package(self, package_path: str) -> str:
        """Extract an extension package to a temporary directory."""
        temp_dir = self.temp_dir / f"extract_{int(time.time())}"
        temp_dir.mkdir(exist_ok=True)
        
        if package_path.endswith('.crx'):
            # CRX format has a header
            with open(package_path, 'rb') as f:
                # Skip CRX header (first 16 bytes)
                f.seek(16)
                zip_data = f.read()
            
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                zf.extractall(temp_dir)
        else:
            # Standard ZIP
            with zipfile.ZipFile(package_path) as zf:
                zf.extractall(temp_dir)
        
        return str(temp_dir)
    
    def _load_extension_from_directory(self, directory_path: str):
        """Load extension from a directory."""
        try:
            manifest_path = os.path.join(directory_path, "manifest.json")
            if not os.path.exists(manifest_path):
                return
            
            manifest = self.manifest_parser.parse(manifest_path)
            if not manifest:
                return
            
            extension_id = manifest['id']
            
            # Create metadata
            metadata = self._create_metadata(manifest, Path(directory_path))
            
            # Store extension
            self.extensions[extension_id] = metadata
            self.extension_paths[extension_id] = directory_path
            
            # Add to dependency graph
            dependencies = manifest.get('dependencies', [])
            self.dependency_resolver.add_dependency(extension_id, dependencies)
            
        except Exception as e:
            self.logger.error(f"Error loading extension from {directory_path}: {e}")
    
    def _load_extension_from_package(self, package_path: str):
        """Load extension from a package file."""
        try:
            extension_path = self._extract_package(package_path)
            self._load_extension_from_directory(extension_path)
        except Exception as e:
            self.logger.error(f"Error loading extension package {package_path}: {e}")
    
    def _create_metadata(self, manifest: Dict[str, Any], extension_path: Path) -> ExtensionMetadata:
        """Create extension metadata from manifest."""
        # Calculate file size and checksum
        file_size = sum(f.stat().st_size for f in extension_path.rglob('*') if f.is_file())
        checksum = self._calculate_checksum(extension_path)
        
        return ExtensionMetadata(
            id=manifest['id'],
            name=manifest.get('name', ''),
            version=manifest.get('version', '1.0.0'),
            description=manifest.get('description', ''),
            author=manifest.get('author', ''),
            homepage_url=manifest.get('homepage_url', ''),
            manifest_version=manifest.get('manifest_version', 2),
            permissions=manifest.get('permissions', []),
            host_permissions=manifest.get('host_permissions', []),
            content_scripts=manifest.get('content_scripts', []),
            background_scripts=[manifest.get('background', {})],
            web_accessible_resources=manifest.get('web_accessible_resources', []),
            action=manifest.get('action') or manifest.get('browser_action'),
            icons=manifest.get('icons', {}),
            default_locale=manifest.get('default_locale', 'en'),
            locales=manifest.get('locales', {}),
            incognito=manifest.get('incognito', 'spanning'),
            offline_enabled=manifest.get('offline_enabled', True),
            short_name=manifest.get('short_name', ''),
            theme=manifest.get('theme'),
            developer=manifest.get('developer'),
            minimum_browser_version=manifest.get('minimum_browser_version', '1.0.0'),
            requirements=manifest.get('requirements', {}),
            install_date=datetime.now(),
            update_date=datetime.now(),
            file_size=file_size,
            checksum=checksum,
            dependencies=manifest.get('dependencies', []),
            optional_dependencies=manifest.get('optional_dependencies', [])
        )
    
    def _calculate_checksum(self, extension_path: Path) -> str:
        """Calculate checksum for extension files."""
        hash_sha256 = hashlib.sha256()
        
        for file_path in sorted(extension_path.rglob('*')):
            if file_path.is_file() and not file_path.name.startswith('.'):
                with open(file_path, 'rb') as f:
                    hash_sha256.update(f.read())
        
        return hash_sha256.hexdigest()
    
    def _create_api_for_extension(self, extension_id: str):
        """Create API instance for an extension."""
        from .api import ExtensionAPI
        
        # Import here to avoid circular imports
        api = ExtensionAPI(self.extensions[extension_id])
        api.set_browser_window(self.browser)
        return api
    
    def _add_load_error(self, extension_id: str, error_type: str, error_message: str, traceback_str: str):
        """Add a load error for an extension."""
        if extension_id not in self.load_errors:
            self.load_errors[extension_id] = []
        
        error = LoadError(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            traceback=traceback_str
        )
        
        self.load_errors[extension_id].append(error)
        
        # Update extension state
        if extension_id in self.extensions:
            self.extensions[extension_id].load_state = LoadState.ERROR
        
        # Fire event
        self._fire_event('load_error', extension_id, error)
    
    def _fire_event(self, event_name: str, *args):
        """Fire an event to all handlers."""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    handler(*args)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_name}: {e}")
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """Add an event handler."""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    def get_extension_info(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an extension."""
        if extension_id not in self.extensions:
            return None
        
        metadata = self.extensions[extension_id]
        errors = self.load_errors.get(extension_id, [])
        security_report = self.security_manager.get_security_report(extension_id)
        
        return {
            'metadata': {
                'id': metadata.id,
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'homepage_url': metadata.homepage_url,
                'install_date': metadata.install_date.isoformat(),
                'update_date': metadata.update_date.isoformat(),
                'last_used': metadata.last_used.isoformat() if metadata.last_used else None,
                'usage_count': metadata.usage_count,
                'load_time': metadata.load_time,
                'file_size': metadata.file_size,
                'checksum': metadata.checksum,
                'enabled': metadata.enabled,
                'load_state': metadata.load_state.value,
                'auto_update': metadata.auto_update,
                'allow_in_incognito': metadata.allow_in_incognito,
                'dependencies': metadata.dependencies,
                'optional_dependencies': metadata.optional_dependencies
            },
            'manifest': {
                'permissions': metadata.permissions,
                'host_permissions': metadata.host_permissions,
                'content_scripts': metadata.content_scripts,
                'background_scripts': metadata.background_scripts,
                'web_accessible_resources': metadata.web_accessible_resources,
                'action': metadata.action,
                'icons': metadata.icons
            },
            'errors': [
                {
                    'timestamp': error.timestamp.isoformat(),
                    'type': error.error_type,
                    'message': error.error_message,
                    'traceback': error.traceback,
                    'recoverable': error.recoverable
                }
                for error in errors[-10:]  # Last 10 errors
            ],
            'security': security_report,
            'dependents': self.dependency_resolver.get_dependents(extension_id)
        }
    
    def list_extensions(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List all extensions."""
        extensions = []
        
        for extension_id, metadata in self.extensions.items():
            if enabled_only and not metadata.enabled:
                continue
            
            extensions.append({
                'id': extension_id,
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'enabled': metadata.enabled,
                'load_state': metadata.load_state.value,
                'security_level': metadata.security_level.value,
                'install_date': metadata.install_date.isoformat(),
                'last_used': metadata.last_used.isoformat() if metadata.last_used else None
            })
        
        return extensions
    
    def update_extension(self, extension_id: str, new_source_path: str) -> Tuple[bool, str]:
        """Update an extension."""
        try:
            if extension_id not in self.extensions:
                return False, f"Extension {extension_id} is not installed"
            
            # Disable extension
            was_enabled = self.extensions[extension_id].enabled
            if was_enabled:
                self.disable_extension(extension_id)
            
            # Unload extension
            self.unload_extension(extension_id)
            
            # Install new version
            success, message = self.install_extension(new_source_path, auto_enable=False)
            if not success:
                return False, f"Failed to install update: {message}"
            
            # Re-enable if it was enabled
            if was_enabled:
                self.enable_extension(extension_id)
            
            return True, f"Extension {extension_id} updated successfully"
            
        except Exception as e:
            error_msg = f"Failed to update extension: {e}"
            self.logger.error(error_msg)
            return False, error_msg
