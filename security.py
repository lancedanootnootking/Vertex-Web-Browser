#!/usr/bin/env python3
"""
Extension Security System

Comprehensive security framework for browser extensions including
sandboxing, permission management, and security policies.
"""

import os
import json
import hashlib
import time
import threading
import subprocess
import tempfile
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import uuid


class SecurityLevel(Enum):
    """Security levels for extensions."""
    TRUSTED = "trusted"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


class ThreatType(Enum):
    """Types of security threats."""
    MALWARE = "malware"
    PHISHING = "phishing"
    DATA_THEFT = "data_theft"
    PRIVACY_VIOLATION = "privacy_violation"
    RESOURCE_ABUSE = "resource_abuse"
    CODE_INJECTION = "code_injection"
    PERMISSION_ESCALATION = "permission_escalation"


@dataclass
class SecurityEvent:
    """Represents a security event."""
    id: str
    extension_id: str
    event_type: str
    severity: str  # low, medium, high, critical
    description: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class ExtensionSignature:
    """Digital signature for an extension."""
    signature: str
    public_key: str
    algorithm: str = "SHA256"
    timestamp: datetime = field(default_factory=datetime.now)
    verified: bool = False
    signer: Optional[str] = None


@dataclass
class SecurityPolicy:
    """Security policy for extension execution."""
    allowed_domains: Set[str] = field(default_factory=set)
    blocked_domains: Set[str] = field(default_factory=set)
    max_memory_usage: int = 100 * 1024 * 1024  # 100MB
    max_cpu_time: int = 30  # seconds
    allowed_apis: Set[str] = field(default_factory=set)
    blocked_apis: Set[str] = field(default_factory=set)
    require_user_approval: bool = True
    sandbox_level: str = "strict"  # strict, moderate, permissive


class SandboxedEnvironment:
    """Sandboxed environment for extension execution."""
    
    def __init__(self, extension_id: str, policy: SecurityPolicy):
        self.extension_id = extension_id
        self.policy = policy
        self.logger = logging.getLogger(__name__)
        self.temp_dir = None
        self.process = None
        self.resource_monitor = None
        self.active = False
        
    def create_sandbox(self) -> bool:
        """Create a sandboxed environment."""
        try:
            # Create temporary directory for extension
            self.temp_dir = tempfile.mkdtemp(prefix=f"ext_sandbox_{self.extension_id}_")
            
            # Set up resource limits
            self._setup_resource_limits()
            
            # Create isolated Python environment
            self._setup_isolated_environment()
            
            self.active = True
            self.logger.info(f"Sandbox created for extension {self.extension_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create sandbox for {self.extension_id}: {e}")
            self.cleanup()
            return False
    
    def _setup_resource_limits(self):
        """Setup resource limits for the sandbox."""
        # This would integrate with system resource limits
        # For now, we'll simulate with monitoring
        self.resource_monitor = ResourceMonitor(self.extension_id, self.policy)
        self.resource_monitor.start()
    
    def _setup_isolated_environment(self):
        """Setup isolated Python environment."""
        # Create restricted environment
        # In a real implementation, this would use containers or similar
        pass
    
    def execute_code(self, code: str, context: Dict[str, Any] = None) -> Any:
        """Execute code in the sandbox."""
        if not self.active:
            raise RuntimeError("Sandbox is not active")
        
        # Check code for security violations
        if not self._validate_code(code):
            raise SecurityError("Code contains security violations")
        
        try:
            # Execute in restricted environment
            return self._safe_execute(code, context or {})
        except Exception as e:
            self.logger.error(f"Error executing code in sandbox: {e}")
            raise
    
    def _validate_code(self, code: str) -> bool:
        """Validate code for security violations."""
        # Check for dangerous imports
        dangerous_imports = [
            'os.system', 'subprocess', 'eval', 'exec', 'compile',
            '__import__', 'open', 'file', 'input', 'raw_input'
        ]
        
        for dangerous in dangerous_imports:
            if dangerous in code:
                self.logger.warning(f"Dangerous import detected: {dangerous}")
                return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'__.*__',  # Magic methods
            r'globals\(\)',  # Access to globals
            r'locals\(\)',  # Access to locals
            r'vars\(\)',  # Access to variables
            r'dir\(\)',  # Directory inspection
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, code):
                self.logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
        
        return True
    
    def _safe_execute(self, code: str, context: Dict[str, Any]) -> Any:
        """Safely execute code with restrictions."""
        # Create restricted globals
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'min': min,
                'max': max,
                'sum': sum,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
            }
        }
        
        # Add safe context
        safe_globals.update(context)
        
        # Execute code
        exec(code, safe_globals)
        return safe_globals
    
    def cleanup(self):
        """Clean up sandbox resources."""
        if self.resource_monitor:
            self.resource_monitor.stop()
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
        
        self.active = False
        self.logger.info(f"Sandbox cleaned up for extension {self.extension_id}")


class ResourceMonitor:
    """Monitor resource usage for extensions."""
    
    def __init__(self, extension_id: str, policy: SecurityPolicy):
        self.extension_id = extension_id
        self.policy = policy
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.monitor_thread = None
        self.stats = {
            'memory_usage': 0,
            'cpu_time': 0,
            'network_requests': 0,
            'file_accesses': 0,
            'start_time': None
        }
    
    def start(self):
        """Start monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.stats['start_time'] = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Monitor memory usage
                self._check_memory_usage()
                
                # Monitor CPU time
                self._check_cpu_time()
                
                # Check for policy violations
                self._check_policy_violations()
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                self.logger.error(f"Error in resource monitor: {e}")
    
    def _check_memory_usage(self):
        """Check memory usage."""
        # In a real implementation, this would use system APIs
        # For now, we'll simulate
        pass
    
    def _check_cpu_time(self):
        """Check CPU time usage."""
        # In a real implementation, this would use system APIs
        # For now, we'll simulate
        pass
    
    def _check_policy_violations(self):
        """Check for policy violations."""
        if self.stats['memory_usage'] > self.policy.max_memory_usage:
            self.logger.warning(f"Extension {self.extension_id} exceeded memory limit")
        
        if self.stats['cpu_time'] > self.policy.max_cpu_time:
            self.logger.warning(f"Extension {self.extension_id} exceeded CPU time limit")


class SecurityManager:
    """Main security manager for extensions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_events: List[SecurityEvent] = []
        self.extension_policies: Dict[str, SecurityPolicy] = {}
        self.extension_signatures: Dict[str, ExtensionSignature] = {}
        self.blocked_extensions: Set[str] = set()
        self.trusted_signers: Set[str] = set()
        self.threat_database = ThreatDatabase()
        self.sandboxes: Dict[str, SandboxedEnvironment] = {}
        
        # Load security configuration
        self._load_security_config()
        
        # Start background security monitoring
        self.monitoring_thread = threading.Thread(target=self._security_monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _load_security_config(self):
        """Load security configuration."""
        # Load trusted signers
        self.trusted_signers = {
            "browser_store",
            "verified_developer",
            "official_partner"
        }
        
        # Load blocked extensions
        self.blocked_extensions = set()
        
        # Load threat database
        self.threat_database.load()
    
    def verify_extension(self, extension_path: str, manifest: Dict[str, Any]) -> Tuple[bool, SecurityLevel]:
        """Verify an extension's security."""
        extension_id = manifest.get('id', '')
        
        # Check against threat database
        if self.threat_database.is_threat(extension_id):
            self._log_security_event(
                extension_id,
                "threat_detected",
                "high",
                f"Extension {extension_id} found in threat database"
            )
            return False, SecurityLevel.BLOCKED
        
        # Verify digital signature
        signature_valid = self._verify_signature(extension_path, manifest)
        
        # Analyze code for threats
        code_analysis = self._analyze_extension_code(extension_path, manifest)
        
        # Check permissions
        permission_risk = self._assess_permission_risk(manifest.get('permissions', []))
        
        # Determine security level
        security_level = self._calculate_security_level(
            signature_valid, code_analysis, permission_risk
        )
        
        # Create security policy
        policy = self._create_security_policy(manifest, security_level)
        self.extension_policies[extension_id] = policy
        
        return security_level != SecurityLevel.BLOCKED, security_level
    
    def _verify_signature(self, extension_path: str, manifest: Dict[str, Any]) -> bool:
        """Verify extension's digital signature."""
        signature_file = os.path.join(extension_path, "signature.json")
        
        if not os.path.exists(signature_file):
            self.logger.warning(f"No signature file found for extension")
            return False
        
        try:
            with open(signature_file, 'r') as f:
                signature_data = json.load(f)
            
            signature = ExtensionSignature(
                signature=signature_data.get('signature', ''),
                public_key=signature_data.get('public_key', ''),
                algorithm=signature_data.get('algorithm', 'SHA256'),
                signer=signature_data.get('signer')
            )
            
            # Verify signature (simplified)
            # In a real implementation, this would use cryptographic verification
            signature.verified = self._cryptographic_verify(extension_path, signature)
            
            if signature.verified and signature.signer in self.trusted_signers:
                self.extension_signatures[manifest['id']] = signature
                return True
            
        except Exception as e:
            self.logger.error(f"Error verifying signature: {e}")
        
        return False
    
    def _cryptographic_verify(self, extension_path: str, signature: ExtensionSignature) -> bool:
        """Perform cryptographic verification."""
        # In a real implementation, this would use proper cryptographic verification
        # For now, we'll simulate basic verification
        try:
            # Calculate hash of extension files
            extension_hash = self._calculate_extension_hash(extension_path)
            
            # Verify hash against signature (simplified)
            expected_hash = hashlib.sha256(signature.signature.encode()).hexdigest()
            return extension_hash == expected_hash
            
        except Exception as e:
            self.logger.error(f"Cryptographic verification failed: {e}")
            return False
    
    def _calculate_extension_hash(self, extension_path: str) -> str:
        """Calculate hash of all extension files."""
        hash_sha256 = hashlib.sha256()
        
        for root, dirs, files in os.walk(extension_path):
            # Skip hidden files and directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in sorted(files):
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        hash_sha256.update(f.read())
                except Exception as e:
                    self.logger.warning(f"Could not hash file {file_path}: {e}")
        
        return hash_sha256.hexdigest()
    
    def _analyze_extension_code(self, extension_path: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze extension code for security threats."""
        analysis = {
            'threats_found': [],
            'suspicious_patterns': [],
            'risk_score': 0
        }
        
        # Analyze main script
        main_script = manifest.get('main', 'main.py')
        main_path = os.path.join(extension_path, main_script)
        
        if os.path.exists(main_path):
            analysis.update(self._analyze_file(main_path))
        
        # Analyze content scripts
        for script in manifest.get('content_scripts', []):
            for js_file in script.get('js', []):
                js_path = os.path.join(extension_path, js_file)
                if os.path.exists(js_path):
                    file_analysis = self._analyze_file(js_path)
                    analysis['threats_found'].extend(file_analysis['threats_found'])
                    analysis['suspicious_patterns'].extend(file_analysis['suspicious_patterns'])
                    analysis['risk_score'] += file_analysis['risk_score']
        
        # Analyze background scripts
        if 'background' in manifest:
            background = manifest['background']
            if 'scripts' in background:
                for script_file in background['scripts']:
                    script_path = os.path.join(extension_path, script_file)
                    if os.path.exists(script_path):
                        file_analysis = self._analyze_file(script_path)
                        analysis['threats_found'].extend(file_analysis['threats_found'])
                        analysis['suspicious_patterns'].extend(file_analysis['suspicious_patterns'])
                        analysis['risk_score'] += file_analysis['risk_score']
            elif 'service_worker' in background:
                worker_path = os.path.join(extension_path, background['service_worker'])
                if os.path.exists(worker_path):
                    file_analysis = self._analyze_file(worker_path)
                    analysis['threats_found'].extend(file_analysis['threats_found'])
                    analysis['suspicious_patterns'].extend(file_analysis['suspicious_patterns'])
                    analysis['risk_score'] += file_analysis['risk_score']
        
        return analysis
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file for security threats."""
        analysis = {
            'threats_found': [],
            'suspicious_patterns': [],
            'risk_score': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for dangerous patterns
            dangerous_patterns = {
                r'eval\s*\(': ThreatType.CODE_INJECTION,
                r'exec\s*\(': ThreatType.CODE_INJECTION,
                r'__import__\s*\(': ThreatType.PERMISSION_ESCALATION,
                r'subprocess\.': ThreatType.PERMISSION_ESCALATION,
                r'os\.system': ThreatType.PERMISSION_ESCALATION,
                r'open\s*\([^)]*["\']w': ThreatType.DATA_THEFT,
                r'urllib\.request\.urlopen': ThreatType.DATA_THEFT,
                r'requests\.': ThreatType.DATA_THEFT,
                r'socket\.': ThreatType.DATA_THEFT,
                r'base64\.decode': ThreatType.MALWARE,
                r'marshal\.loads': ThreatType.MALWARE,
                r'pickle\.loads': ThreatType.MALWARE,
            }
            
            for pattern, threat_type in dangerous_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    analysis['threats_found'].append({
                        'type': threat_type,
                        'pattern': pattern,
                        'file': file_path
                    })
                    analysis['risk_score'] += 10
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'document\.cookie',
                r'localStorage\.',
                r'sessionStorage\.',
                r'window\.location\.href',
                r'window\.open\s*\(',
                r'alert\s*\(',
                r'confirm\s*\(',
                r'prompt\s*\(',
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    analysis['suspicious_patterns'].append({
                        'pattern': pattern,
                        'file': file_path
                    })
                    analysis['risk_score'] += 5
            
            # Check for obfuscated code
            if self._is_obfuscated(content):
                analysis['threats_found'].append({
                    'type': ThreatType.MALWARE,
                    'pattern': 'obfuscated_code',
                    'file': file_path
                })
                analysis['risk_score'] += 20
        
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
        
        return analysis
    
    def _is_obfuscated(self, content: str) -> bool:
        """Check if code is obfuscated."""
        # Simple heuristic for obfuscation detection
        lines = content.split('\n')
        
        # Check for very long lines
        long_lines = [line for line in lines if len(line) > 200]
        if len(long_lines) > len(lines) * 0.1:
            return True
        
        # Check for high density of special characters
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / len(content)
        if special_char_ratio > 0.3:
            return True
        
        # Check for lack of whitespace
        whitespace_ratio = content.count(' ') / len(content)
        if whitespace_ratio < 0.05:
            return True
        
        return False
    
    def _assess_permission_risk(self, permissions: List[str]) -> int:
        """Assess the risk level of requested permissions."""
        risk_scores = {
            'activeTab': 1,
            'storage': 1,
            'tabs': 3,
            'bookmarks': 3,
            'history': 3,
            'downloads': 3,
            'cookies': 5,
            'webNavigation': 3,
            'webRequest': 5,
            'webRequestBlocking': 8,
            'scripting': 7,
            'notifications': 3,
            'geolocation': 6,
            'camera': 9,
            'microphone': 9,
            'host_permissions': 6,
        }
        
        total_risk = 0
        for permission in permissions:
            total_risk += risk_scores.get(permission, 2)  # Default risk for unknown permissions
        
        return total_risk
    
    def _calculate_security_level(self, signature_valid: bool, code_analysis: Dict[str, Any], permission_risk: int) -> SecurityLevel:
        """Calculate overall security level."""
        risk_score = code_analysis['risk_score'] + permission_risk
        
        if code_analysis['threats_found']:
            return SecurityLevel.BLOCKED
        
        if risk_score > 50:
            return SecurityLevel.SUSPICIOUS
        
        if risk_score > 20:
            return SecurityLevel.UNVERIFIED
        
        if signature_valid and risk_score < 10:
            return SecurityLevel.VERIFIED
        
        if risk_score < 15:
            return SecurityLevel.TRUSTED
        
        return SecurityLevel.UNVERIFIED
    
    def _create_security_policy(self, manifest: Dict[str, Any], security_level: SecurityLevel) -> SecurityPolicy:
        """Create security policy based on security level."""
        permissions = manifest.get('permissions', [])
        
        # Base policy configuration
        policy_configs = {
            SecurityLevel.TRUSTED: {
                'max_memory_usage': 200 * 1024 * 1024,  # 200MB
                'max_cpu_time': 60,  # 1 minute
                'sandbox_level': 'moderate',
                'require_user_approval': False
            },
            SecurityLevel.VERIFIED: {
                'max_memory_usage': 150 * 1024 * 1024,  # 150MB
                'max_cpu_time': 45,  # 45 seconds
                'sandbox_level': 'moderate',
                'require_user_approval': False
            },
            SecurityLevel.UNVERIFIED: {
                'max_memory_usage': 100 * 1024 * 1024,  # 100MB
                'max_cpu_time': 30,  # 30 seconds
                'sandbox_level': 'strict',
                'require_user_approval': True
            },
            SecurityLevel.SUSPICIOUS: {
                'max_memory_usage': 50 * 1024 * 1024,  # 50MB
                'max_cpu_time': 15,  # 15 seconds
                'sandbox_level': 'strict',
                'require_user_approval': True
            }
        }
        
        config = policy_configs.get(security_level, policy_configs[SecurityLevel.UNVERIFIED])
        
        # Create policy
        policy = SecurityPolicy(
            max_memory_usage=config['max_memory_usage'],
            max_cpu_time=config['max_cpu_time'],
            sandbox_level=config['sandbox_level'],
            require_user_approval=config['require_user_approval']
        )
        
        # Set allowed APIs based on permissions
        api_mapping = {
            'tabs': ['create_tab', 'get_current_tab', 'navigate_tab', 'close_tab'],
            'bookmarks': ['add_bookmark', 'get_bookmarks', 'remove_bookmark'],
            'history': ['get_history', 'clear_history'],
            'downloads': ['add_download', 'pause_download', 'resume_download'],
            'storage': ['get_storage', 'set_storage', 'remove_storage'],
            'notifications': ['show_notification'],
        }
        
        for permission in permissions:
            if permission in api_mapping:
                policy.allowed_apis.update(api_mapping[permission])
        
        return policy
    
    def create_sandbox(self, extension_id: str) -> Optional[SandboxedEnvironment]:
        """Create a sandbox for an extension."""
        if extension_id not in self.extension_policies:
            self.logger.error(f"No security policy found for extension {extension_id}")
            return None
        
        policy = self.extension_policies[extension_id]
        sandbox = SandboxedEnvironment(extension_id, policy)
        
        if sandbox.create_sandbox():
            self.sandboxes[extension_id] = sandbox
            return sandbox
        
        return None
    
    def get_sandbox(self, extension_id: str) -> Optional[SandboxedEnvironment]:
        """Get sandbox for an extension."""
        return self.sandboxes.get(extension_id)
    
    def _log_security_event(self, extension_id: str, event_type: str, severity: str, description: str, data: Dict[str, Any] = None):
        """Log a security event."""
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            extension_id=extension_id,
            event_type=event_type,
            severity=severity,
            description=description,
            timestamp=datetime.now(),
            data=data or {}
        )
        
        self.security_events.append(event)
        self.logger.warning(f"Security event: {description}")
    
    def _security_monitor_loop(self):
        """Background security monitoring loop."""
        while True:
            try:
                # Monitor active sandboxes
                for extension_id, sandbox in list(self.sandboxes.items()):
                    if not sandbox.active:
                        del self.sandboxes[extension_id]
                        continue
                    
                    # Check for security violations
                    if sandbox.resource_monitor:
                        stats = sandbox.resource_monitor.stats
                        
                        if stats['memory_usage'] > sandbox.policy.max_memory_usage:
                            self._log_security_event(
                                extension_id,
                                "memory_violation",
                                "medium",
                                f"Extension exceeded memory limit: {stats['memory_usage']}"
                            )
                        
                        if stats['cpu_time'] > sandbox.policy.max_cpu_time:
                            self._log_security_event(
                                extension_id,
                                "cpu_violation",
                                "medium",
                                f"Extension exceeded CPU time limit: {stats['cpu_time']}"
                            )
                
                # Clean up old security events
                self._cleanup_old_events()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in security monitor: {e}")
    
    def _cleanup_old_events(self):
        """Clean up old security events."""
        cutoff_date = datetime.now() - timedelta(days=30)
        self.security_events = [
            event for event in self.security_events 
            if event.timestamp > cutoff_date
        ]
    
    def get_security_report(self, extension_id: str) -> Dict[str, Any]:
        """Get security report for an extension."""
        events = [e for e in self.security_events if e.extension_id == extension_id]
        policy = self.extension_policies.get(extension_id)
        signature = self.extension_signatures.get(extension_id)
        
        return {
            'extension_id': extension_id,
            'security_level': self._get_extension_security_level(extension_id),
            'events': [
                {
                    'type': e.event_type,
                    'severity': e.severity,
                    'description': e.description,
                    'timestamp': e.timestamp.isoformat(),
                    'resolved': e.resolved
                }
                for e in events[-50:]  # Last 50 events
            ],
            'policy': {
                'max_memory_usage': policy.max_memory_usage if policy else None,
                'max_cpu_time': policy.max_cpu_time if policy else None,
                'sandbox_level': policy.sandbox_level if policy else None,
                'allowed_apis': list(policy.allowed_apis) if policy else []
            },
            'signature': {
                'verified': signature.verified if signature else False,
                'signer': signature.signer if signature else None,
                'timestamp': signature.timestamp.isoformat() if signature else None
            }
        }
    
    def _get_extension_security_level(self, extension_id: str) -> str:
        """Get security level for an extension."""
        if extension_id in self.blocked_extensions:
            return SecurityLevel.BLOCKED.value
        
        if extension_id in self.extension_signatures:
            signature = self.extension_signatures[extension_id]
            if signature.verified and signature.signer in self.trusted_signers:
                return SecurityLevel.VERIFIED.value
        
        return SecurityLevel.UNVERIFIED.value


class ThreatDatabase:
    """Database of known malicious extensions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.threats: Dict[str, Dict[str, Any]] = {}
        self.last_updated = None
    
    def load(self):
        """Load threat database."""
        # In a real implementation, this would load from a remote server
        # For now, we'll use a small built-in database
        self.threats = {
            "malicious_extension_1": {
                "type": "malware",
                "description": "Steals user data",
                "detected": "2024-01-01"
            },
            "phishing_extension_2": {
                "type": "phishing",
                "description": "Redirects to phishing sites",
                "detected": "2024-01-15"
            }
        }
        self.last_updated = datetime.now()
    
    def is_threat(self, extension_id: str) -> bool:
        """Check if extension is a known threat."""
        return extension_id in self.threats
    
    def add_threat(self, extension_id: str, threat_info: Dict[str, Any]):
        """Add a new threat to the database."""
        self.threats[extension_id] = threat_info
        self.last_updated = datetime.now()
        self.logger.info(f"Added threat to database: {extension_id}")


class SecurityError(Exception):
    """Security-related exception."""
    pass
