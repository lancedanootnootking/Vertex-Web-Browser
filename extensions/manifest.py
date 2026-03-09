#!/usr/bin/env python3
"""
Extension Manifest System

Comprehensive manifest validation and management for browser extensions.
Supports multiple manifest formats and provides extensive validation.
"""

import json
import os
import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime
import logging
from dataclasses import dataclass, field
from enum import Enum


class ManifestVersion(Enum):
    """Supported manifest versions."""
    V2 = "2.0"
    V3 = "3.0"


class PermissionLevel(Enum):
    """Permission levels for extensions."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Permission:
    """Represents a permission with metadata."""
    name: str
    level: PermissionLevel
    description: str
    required: bool = False
    dangerous: bool = False
    api_methods: List[str] = field(default_factory=list)


@dataclass
class ContentScript:
    """Represents a content script configuration."""
    matches: List[str]
    js_files: List[str] = field(default_factory=list)
    css_files: List[str] = field(default_factory=list)
    run_at: str = "document_idle"  # document_start, document_end, document_idle
    all_frames: bool = False
    match_about_blank: bool = False
    exclude_matches: List[str] = field(default_factory=list)


@dataclass
class BackgroundScript:
    """Represents a background script configuration."""
    scripts: List[str] = field(default_factory=list)
    service_worker: Optional[str] = None
    persistent: bool = True


@dataclass
class WebResource:
    """Represents a web accessible resource."""
    resources: List[str]
    matches: List[str] = field(default_factory=list)
    use_dynamic_url: bool = False


@dataclass
class Action:
    """Represents browser action configuration."""
    default_title: str = ""
    default_icon: Optional[str] = None
    default_popup: Optional[str] = None
    default_badge_text: str = ""
    default_badge_color: str = "#000000"


class ManifestValidator:
    """Validates extension manifests against specifications."""
    
    # Predefined permissions with their metadata
    PERMISSIONS = {
        "activeTab": Permission(
            "activeTab", PermissionLevel.LOW,
            "Access the currently active tab when the user invokes the extension"
        ),
        "storage": Permission(
            "storage", PermissionLevel.LOW,
            "Store and retrieve data for the extension"
        ),
        "tabs": Permission(
            "tabs", PermissionLevel.MEDIUM,
            "Access browser tabs", 
            api_methods=["create_tab", "get_current_tab", "navigate_tab", "close_tab"]
        ),
        "bookmarks": Permission(
            "bookmarks", PermissionLevel.MEDIUM,
            "Access and manage bookmarks",
            api_methods=["add_bookmark", "get_bookmarks", "remove_bookmark"]
        ),
        "history": Permission(
            "history", PermissionLevel.MEDIUM,
            "Access browser history",
            api_methods=["get_history", "clear_history"]
        ),
        "downloads": Permission(
            "downloads", PermissionLevel.MEDIUM,
            "Manage downloads",
            api_methods=["add_download", "pause_download", "resume_download"]
        ),
        "cookies": Permission(
            "cookies", PermissionLevel.HIGH,
            "Access browser cookies",
            dangerous=True
        ),
        "webNavigation": Permission(
            "webNavigation", PermissionLevel.MEDIUM,
            "Access navigation events",
            api_methods=["on_navigation", "get_navigation_info"]
        ),
        "webRequest": Permission(
            "webRequest", PermissionLevel.HIGH,
            "Intercept and modify web requests",
            dangerous=True
        ),
        "webRequestBlocking": Permission(
            "webRequestBlocking", PermissionLevel.CRITICAL,
            "Block web requests",
            dangerous=True
        ),
        "scripting": Permission(
            "scripting", PermissionLevel.HIGH,
            "Execute scripts on web pages",
            dangerous=True
        ),
        "notifications": Permission(
            "notifications", PermissionLevel.MEDIUM,
            "Show desktop notifications"
        ),
        "geolocation": Permission(
            "geolocation", PermissionLevel.HIGH,
            "Access user's location",
            dangerous=True
        ),
        "camera": Permission(
            "camera", PermissionLevel.CRITICAL,
            "Access camera",
            dangerous=True
        ),
        "microphone": Permission(
            "microphone", PermissionLevel.CRITICAL,
            "Access microphone",
            dangerous=True
        ),
        "host_permissions": Permission(
            "host_permissions", PermissionLevel.HIGH,
            "Access to specific websites",
            dangerous=True
        ),
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.warnings = []
    
    def validate(self, manifest_data: Dict[str, Any], manifest_path: str) -> Tuple[bool, List[str], List[str]]:
        """Validate a manifest file."""
        self.errors = []
        self.warnings = []
        
        # Basic structure validation
        self._validate_basic_structure(manifest_data)
        
        # Validate manifest version
        self._validate_manifest_version(manifest_data)
        
        # Validate identification fields
        self._validate_identification(manifest_data)
        
        # Validate permissions
        self._validate_permissions(manifest_data)
        
        # Validate content scripts
        self._validate_content_scripts(manifest_data, manifest_path)
        
        # Validate background scripts
        self._validate_background_scripts(manifest_data, manifest_path)
        
        # Validate web accessible resources
        self._validate_web_resources(manifest_data, manifest_path)
        
        # Validate action configuration
        self._validate_action(manifest_data, manifest_path)
        
        # Validate icons
        self._validate_icons(manifest_data, manifest_path)
        
        # Validate localization
        self._validate_localization(manifest_data, manifest_path)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_basic_structure(self, manifest: Dict[str, Any]):
        """Validate basic manifest structure."""
        if not isinstance(manifest, dict):
            self.errors.append("Manifest must be a JSON object")
            return
        
        required_fields = ["name", "version", "manifest_version"]
        for field in required_fields:
            if field not in manifest:
                self.errors.append(f"Required field missing: {field}")
        
        # Check for unknown fields
        known_fields = {
            "name", "version", "manifest_version", "description", "author",
            "homepage_url", "permissions", "host_permissions", "optional_permissions",
            "content_scripts", "background", "web_accessible_resources", "action",
            "page_action", "browser_action", "icons", "default_locale", "locales",
            "incognito", "offline_enabled", "short_name", "theme", "developer",
            "minimum_chrome_version", "minimum_browser_version", "requirements"
        }
        
        unknown_fields = set(manifest.keys()) - known_fields
        for field in unknown_fields:
            self.warnings.append(f"Unknown field: {field}")
    
    def _validate_manifest_version(self, manifest: Dict[str, Any]):
        """Validate manifest version."""
        version = manifest.get("manifest_version")
        if version not in [2, 3, "2.0", "3.0"]:
            self.errors.append("manifest_version must be 2 or 3")
        
        # Check for deprecated features based on version
        if version == 3:
            if "browser_action" in manifest or "page_action" in manifest:
                self.errors.append("browser_action and page_action are deprecated in manifest v3, use 'action' instead")
            if "background" in manifest and "persistent" in manifest["background"]:
                self.warnings.append("'persistent' is ignored in manifest v3")
    
    def _validate_identification(self, manifest: Dict[str, Any]):
        """Validate extension identification fields."""
        # Name validation
        name = manifest.get("name", "")
        if not name or not isinstance(name, str):
            self.errors.append("Extension name is required and must be a string")
        elif len(name) > 45:
            self.errors.append("Extension name must be 45 characters or less")
        elif not re.match(r'^[a-zA-Z0-9._-]+$', name):
            self.warnings.append("Extension name should contain only alphanumeric characters, dots, hyphens, and underscores")
        
        # Version validation
        version = manifest.get("version", "")
        if not version or not isinstance(version, str):
            self.errors.append("Extension version is required and must be a string")
        elif not re.match(r'^\d+(\.\d+)*$', version):
            self.errors.append("Version must follow semantic versioning (e.g., 1.0.0)")
        
        # ID validation (if present)
        extension_id = manifest.get("id", "")
        if extension_id:
            if not re.match(r'^[a-z0-9]{32}$', extension_id):
                self.errors.append("Extension ID must be a 32-character lowercase hexadecimal string")
        
        # Author validation
        author = manifest.get("author", "")
        if author and isinstance(author, str) and len(author) > 100:
            self.warnings.append("Author name should be 100 characters or less")
        
        # Homepage URL validation
        homepage = manifest.get("homepage_url", "")
        if homepage:
            if not self._is_valid_url(homepage):
                self.errors.append("homepage_url must be a valid URL")
    
    def _validate_permissions(self, manifest: Dict[str, Any]):
        """Validate permissions."""
        permissions = manifest.get("permissions", [])
        if not isinstance(permissions, list):
            self.errors.append("permissions must be an array")
            return
        
        dangerous_permissions = []
        for permission in permissions:
            if not isinstance(permission, str):
                self.errors.append(f"Permission must be a string: {permission}")
                continue
            
            # Check if permission is known
            if permission not in self.PERMISSIONS and not permission.startswith("chrome://") and not permission.startswith("moz-extension://"):
                self.warnings.append(f"Unknown permission: {permission}")
            elif permission in self.PERMISSIONS:
                perm_info = self.PERMISSIONS[permission]
                if perm_info.dangerous:
                    dangerous_permissions.append(permission)
        
        # Warn about dangerous permissions
        if dangerous_permissions:
            self.warnings.append(f"Extension requests dangerous permissions: {', '.join(dangerous_permissions)}")
        
        # Validate host permissions
        host_permissions = manifest.get("host_permissions", [])
        if not isinstance(host_permissions, list):
            self.errors.append("host_permissions must be an array")
            return
        
        for host in host_permissions:
            if not self._is_valid_host_permission(host):
                self.errors.append(f"Invalid host permission: {host}")
        
        # Validate optional permissions
        optional_permissions = manifest.get("optional_permissions", [])
        if not isinstance(optional_permissions, list):
            self.errors.append("optional_permissions must be an array")
            return
        
        for permission in optional_permissions:
            if permission not in self.PERMISSIONS and not self._is_valid_host_permission(permission):
                self.warnings.append(f"Unknown optional permission: {permission}")
    
    def _validate_content_scripts(self, manifest: Dict[str, Any], manifest_path: str):
        """Validate content scripts."""
        content_scripts = manifest.get("content_scripts", [])
        if not isinstance(content_scripts, list):
            self.errors.append("content_scripts must be an array")
            return
        
        extension_dir = os.path.dirname(manifest_path)
        
        for i, script in enumerate(content_scripts):
            if not isinstance(script, dict):
                self.errors.append(f"Content script {i} must be an object")
                continue
            
            # Validate matches
            matches = script.get("matches", [])
            if not matches:
                self.errors.append(f"Content script {i} must specify matches")
            elif not isinstance(matches, list):
                self.errors.append(f"Content script {i} matches must be an array")
            else:
                for match in matches:
                    if not self._is_valid_match_pattern(match):
                        self.errors.append(f"Invalid match pattern in content script {i}: {match}")
            
            # Validate JS files
            js_files = script.get("js", [])
            if js_files and not isinstance(js_files, list):
                self.errors.append(f"Content script {i} js must be an array")
            else:
                for js_file in js_files:
                    if not os.path.exists(os.path.join(extension_dir, js_file)):
                        self.errors.append(f"JS file not found in content script {i}: {js_file}")
            
            # Validate CSS files
            css_files = script.get("css", [])
            if css_files and not isinstance(css_files, list):
                self.errors.append(f"Content script {i} css must be an array")
            else:
                for css_file in css_files:
                    if not os.path.exists(os.path.join(extension_dir, css_file)):
                        self.errors.append(f"CSS file not found in content script {i}: {css_file}")
            
            # Validate run_at
            run_at = script.get("run_at", "document_idle")
            if run_at not in ["document_start", "document_end", "document_idle"]:
                self.errors.append(f"Invalid run_at in content script {i}: {run_at}")
            
            # Validate all_frames
            all_frames = script.get("all_frames", False)
            if not isinstance(all_frames, bool):
                self.errors.append(f"all_frames in content script {i} must be a boolean")
    
    def _validate_background_scripts(self, manifest: Dict[str, Any], manifest_path: str):
        """Validate background scripts."""
        background = manifest.get("background")
        if not background:
            return
        
        if not isinstance(background, dict):
            self.errors.append("background must be an object")
            return
        
        extension_dir = os.path.dirname(manifest_path)
        manifest_version = manifest.get("manifest_version", 2)
        
        if manifest_version == 2:
            # V2 uses scripts array
            scripts = background.get("scripts", [])
            if not isinstance(scripts, list):
                self.errors.append("background.scripts must be an array")
                return
            
            for script in scripts:
                if not os.path.exists(os.path.join(extension_dir, script)):
                    self.errors.append(f"Background script not found: {script}")
        else:
            # V3 uses service_worker
            service_worker = background.get("service_worker")
            if service_worker and not os.path.exists(os.path.join(extension_dir, service_worker)):
                self.errors.append(f"Service worker not found: {service_worker}")
    
    def _validate_web_resources(self, manifest: Dict[str, Any], manifest_path: str):
        """Validate web accessible resources."""
        web_resources = manifest.get("web_accessible_resources", [])
        if not web_resources:
            return
        
        manifest_version = manifest.get("manifest_version", 2)
        extension_dir = os.path.dirname(manifest_path)
        
        if manifest_version == 2:
            # V2 format: array of strings
            if not isinstance(web_resources, list):
                self.errors.append("web_accessible_resources must be an array in manifest v2")
                return
            
            for resource in web_resources:
                if not isinstance(resource, str):
                    self.errors.append(f"Web accessible resource must be a string: {resource}")
                elif not os.path.exists(os.path.join(extension_dir, resource)):
                    self.warnings.append(f"Web accessible resource not found: {resource}")
        else:
            # V3 format: array of objects
            if not isinstance(web_resources, list):
                self.errors.append("web_accessible_resources must be an array in manifest v3")
                return
            
            for i, resource in enumerate(web_resources):
                if not isinstance(resource, dict):
                    self.errors.append(f"Web accessible resource {i} must be an object")
                    continue
                
                resources = resource.get("resources", [])
                if not isinstance(resources, list):
                    self.errors.append(f"Web accessible resource {i}.resources must be an array")
                    continue
                
                for res in resources:
                    if not os.path.exists(os.path.join(extension_dir, res)):
                        self.warnings.append(f"Web accessible resource not found: {res}")
    
    def _validate_action(self, manifest: Dict[str, Any], manifest_path: str):
        """Validate browser/page action."""
        manifest_version = manifest.get("manifest_version", 2)
        
        if manifest_version == 3:
            action = manifest.get("action")
            if not action:
                return
            
            if not isinstance(action, dict):
                self.errors.append("action must be an object")
                return
        else:
            # V2 uses browser_action or page_action
            browser_action = manifest.get("browser_action")
            page_action = manifest.get("page_action")
            
            for action_name, action in [("browser_action", browser_action), ("page_action", page_action)]:
                if action and not isinstance(action, dict):
                    self.errors.append(f"{action_name} must be an object")
                    continue
        
        extension_dir = os.path.dirname(manifest_path)
        
        # Validate popup files
        if manifest_version == 3:
            popup = manifest.get("action", {}).get("default_popup")
        else:
            popup = manifest.get("browser_action", {}).get("default_popup")
        
        if popup and not os.path.exists(os.path.join(extension_dir, popup)):
            self.errors.append(f"Popup file not found: {popup}")
    
    def _validate_icons(self, manifest: Dict[str, Any], manifest_path: str):
        """Validate extension icons."""
        icons = manifest.get("icons")
        if not icons:
            self.warnings.append("No icons specified")
            return
        
        if not isinstance(icons, dict):
            self.errors.append("icons must be an object")
            return
        
        extension_dir = os.path.dirname(manifest_path)
        
        for size, icon_path in icons.items():
            if not isinstance(size, str) or not size.isdigit():
                self.errors.append(f"Icon size must be a numeric string: {size}")
                continue
            
            if not os.path.exists(os.path.join(extension_dir, icon_path)):
                self.errors.append(f"Icon file not found: {icon_path}")
    
    def _validate_localization(self, manifest: Dict[str, Any], manifest_path: str):
        """Validate localization settings."""
        default_locale = manifest.get("default_locale")
        if default_locale:
            if not isinstance(default_locale, str):
                self.errors.append("default_locale must be a string")
            elif not re.match(r'^[a-z]{2}(_[A-Z]{2})?$', default_locale):
                self.warnings.append(f"Unusual locale format: {default_locale}")
        
        locales = manifest.get("locales", {})
        if locales and not isinstance(locales, dict):
            self.errors.append("locales must be an object")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _is_valid_host_permission(self, host: str) -> bool:
        """Check if a host permission pattern is valid."""
        # Basic validation for host patterns
        if host.startswith("chrome://") or host.startswith("moz-extension://"):
            return True
        
        # URL patterns
        patterns = [
            r'^https?://\*?\.?[^/]+$',  # http://example.com or https://*.example.com
            r'^https?://\*/$',  # http://*/
            r'^<all_urls>$',  # All URLs
        ]
        
        return any(re.match(pattern, host) for pattern in patterns)
    
    def _is_valid_match_pattern(self, pattern: str) -> bool:
        """Check if a match pattern is valid."""
        # Match pattern validation
        patterns = [
            r'^https?://\*?\.?[^/]+/.*$',  # http://example.com/*
            r'^https?://\*/.*$',  # http://*/*
            r'^file:///.+$',  # file:///*
        ]
        
        return any(re.match(pattern, pattern) for pattern in patterns)


class ManifestParser:
    """Parses and processes extension manifests."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = ManifestValidator()
    
    def parse(self, manifest_path: str) -> Optional[Dict[str, Any]]:
        """Parse a manifest file."""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Validate the manifest
            is_valid, errors, warnings = self.validator.validate(manifest_data, manifest_path)
            
            if not is_valid:
                self.logger.error(f"Manifest validation failed: {errors}")
                return None
            
            if warnings:
                self.logger.warning(f"Manifest warnings: {warnings}")
            
            # Process and normalize the manifest
            return self._process_manifest(manifest_data, manifest_path)
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in manifest: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing manifest: {e}")
            return None
    
    def _process_manifest(self, manifest: Dict[str, Any], manifest_path: str) -> Dict[str, Any]:
        """Process and normalize manifest data."""
        processed = manifest.copy()
        
        # Normalize manifest version
        version = processed.get("manifest_version", 2)
        if isinstance(version, str):
            processed["manifest_version"] = int(version.split('.')[0])
        
        # Generate extension ID if not present
        if "id" not in processed:
            processed["id"] = self._generate_extension_id(processed, manifest_path)
        
        # Set default values
        processed.setdefault("description", "")
        processed.setdefault("author", "")
        processed.setdefault("homepage_url", "")
        processed.setdefault("permissions", [])
        processed.setdefault("host_permissions", [])
        processed.setdefault("content_scripts", [])
        processed.setdefault("web_accessible_resources", [])
        
        # Process content scripts
        processed["content_scripts"] = [
            self._process_content_script(script) for script in processed["content_scripts"]
        ]
        
        # Process background scripts
        if "background" in processed:
            processed["background"] = self._process_background_script(processed["background"])
        
        # Process web accessible resources
        if processed["web_accessible_resources"]:
            processed["web_accessible_resources"] = self._process_web_resources(
                processed["web_accessible_resources"], processed["manifest_version"]
            )
        
        # Process action
        if "action" in processed:
            processed["action"] = self._process_action(processed["action"])
        elif "browser_action" in processed:
            processed["browser_action"] = self._process_action(processed["browser_action"])
        elif "page_action" in processed:
            processed["page_action"] = self._process_action(processed["page_action"])
        
        return processed
    
    def _generate_extension_id(self, manifest: Dict[str, Any], manifest_path: str) -> str:
        """Generate a unique extension ID."""
        # Use name, version, and path to create a hash
        identifier = f"{manifest.get('name', '')}{manifest.get('version', '')}{manifest_path}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:32]
    
    def _process_content_script(self, script: Dict[str, Any]) -> ContentScript:
        """Process a content script configuration."""
        return ContentScript(
            matches=script.get("matches", []),
            js_files=script.get("js", []),
            css_files=script.get("css", []),
            run_at=script.get("run_at", "document_idle"),
            all_frames=script.get("all_frames", False),
            match_about_blank=script.get("match_about_blank", False),
            exclude_matches=script.get("exclude_matches", [])
        )
    
    def _process_background_script(self, background: Dict[str, Any]) -> BackgroundScript:
        """Process a background script configuration."""
        manifest_version = background.get("manifest_version", 2)
        
        if manifest_version == 2:
            return BackgroundScript(
                scripts=background.get("scripts", []),
                persistent=background.get("persistent", True)
            )
        else:
            return BackgroundScript(
                service_worker=background.get("service_worker"),
                persistent=False  # V3 background scripts are never persistent
            )
    
    def _process_web_resources(self, resources: List[Any], manifest_version: int) -> List[WebResource]:
        """Process web accessible resources."""
        processed = []
        
        if manifest_version == 2:
            # V2: array of strings
            for resource in resources:
                if isinstance(resource, str):
                    processed.append(WebResource(resources=[resource]))
        else:
            # V3: array of objects
            for resource in resources:
                if isinstance(resource, dict):
                    processed.append(WebResource(
                        resources=resource.get("resources", []),
                        matches=resource.get("matches", []),
                        use_dynamic_url=resource.get("use_dynamic_url", False)
                    ))
        
        return processed
    
    def _process_action(self, action: Dict[str, Any]) -> Action:
        """Process an action configuration."""
        return Action(
            default_title=action.get("default_title", ""),
            default_icon=action.get("default_icon"),
            default_popup=action.get("default_popup"),
            default_badge_text=action.get("default_badge_text", ""),
            default_badge_color=action.get("default_badge_color", "#000000")
        )
