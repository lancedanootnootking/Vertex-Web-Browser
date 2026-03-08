"""
Privacy Mode

This module provides private browsing functionality to ensure
no browsing data is stored locally and enhance user privacy.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import tempfile
import os
import shutil
from urllib.parse import urlparse


class PrivacyMode:
    """Private browsing mode for enhanced privacy."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        # Private browsing state
        self.private_sessions: List[str] = []
        self.private_data: Dict[str, Any] = {}
        
        # Temporary storage for private session
        self.temp_dir = None
        self.private_cache_dir = None
        
        # Privacy settings
        self.settings = {
            'disable_cookies': True,
            'disable_history': True,
            'disable_cache': True,
            'disable_form_data': True,
            'disable_passwords': True,
            'disable_downloads_history': True,
            'disable_web_storage': True,
            'disable_location_services': True,
            'disable_camera_microphone': True,
            'disable_notifications': True,
            'clear_on_exit': True,
            'isolate_sessions': True
        }
        
        # Statistics
        self.stats = {
            'private_sessions_started': 0,
            'private_sessions_ended': 0,
            'requests_blocked': 0,
            'data_cleared': 0,
            'tracking_attempts_blocked': 0
        }
    
    def enable_private_mode(self) -> str:
        """Enable private browsing mode."""
        if self.enabled:
            self.logger.warning("Private mode already enabled")
            return None
        
        self.enabled = True
        session_id = self.create_private_session()
        self.private_sessions.append(session_id)
        
        # Create temporary directories
        self.setup_temp_directories()
        
        # Apply privacy settings
        self.apply_privacy_settings()
        
        self.stats['private_sessions_started'] += 1
        self.logger.info(f"Private browsing mode enabled - Session: {session_id}")
        
        return session_id
    
    def disable_private_mode(self, session_id: str = None) -> bool:
        """Disable private browsing mode."""
        if not self.enabled:
            self.logger.warning("Private mode not enabled")
            return False
        
        # Clear private data
        self.clear_private_data(session_id)
        
        # Remove temporary directories
        self.cleanup_temp_directories()
        
        # Remove session
        if session_id and session_id in self.private_sessions:
            self.private_sessions.remove(session_id)
        else:
            self.private_sessions.clear()
        
        self.enabled = False
        self.stats['private_sessions_ended'] += 1
        self.logger.info("Private browsing mode disabled")
        
        return True
    
    def create_private_session(self) -> str:
        """Create a new private session."""
        import uuid
        session_id = str(uuid.uuid4())
        
        self.private_data[session_id] = {
            'created_at': datetime.now(),
            'requests_blocked': 0,
            'tracking_blocked': 0,
            'cookies_blocked': 0,
            'cache_size': 0
        }
        
        return session_id
    
    def setup_temp_directories(self):
        """Setup temporary directories for private browsing."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="browser_private_")
            
            # Create cache directory
            self.private_cache_dir = os.path.join(self.temp_dir, "cache")
            os.makedirs(self.private_cache_dir, exist_ok=True)
            
            self.logger.info(f"Created private temp directory: {self.temp_dir}")
            
        except Exception as e:
            self.logger.error(f"Error creating temp directories: {e}")
    
    def cleanup_temp_directories(self):
        """Cleanup temporary directories."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"Cleaned up private temp directory: {self.temp_dir}")
            
            self.temp_dir = None
            self.private_cache_dir = None
            
        except Exception as e:
            self.logger.error(f"Error cleaning up temp directories: {e}")
    
    def apply_privacy_settings(self):
        """Apply privacy settings to the browser."""
        # This would integrate with the browser's settings
        # For now, we'll just log what would be applied
        
        settings_applied = []
        
        for setting, value in self.settings.items():
            if value:
                settings_applied.append(setting)
        
        self.logger.info(f"Applied privacy settings: {', '.join(settings_applied)}")
    
    def should_block_request(self, url: str, request_type: str = "GET", 
                           session_id: str = None) -> bool:
        """Check if a request should be blocked in private mode."""
        if not self.enabled:
            return False
        
        blocked = False
        reason = None
        
        # Block tracking and analytics
        if self.is_tracking_request(url, request_type):
            blocked = True
            reason = "Tracking request"
            self.stats['tracking_attempts_blocked'] += 1
        
        # Block cookies
        if request_type.upper() in ["COOKIE", "SET_COOKIE"]:
            if self.settings.get('disable_cookies', True):
                blocked = True
                reason = "Cookie request"
        
        # Block storage requests
        if request_type.upper() in ["WEB_STORAGE", "INDEXED_DB", "LOCAL_STORAGE"]:
            if self.settings.get('disable_web_storage', True):
                blocked = True
                reason = "Storage request"
        
        # Block location services
        if request_type.upper() == "GEOLOCATION":
            if self.settings.get('disable_location_services', True):
                blocked = True
                reason = "Location request"
        
        # Block camera/microphone
        if request_type.upper() in ["CAMERA", "MICROPHONE"]:
            if self.settings.get('disable_camera_microphone', True):
                blocked = True
                reason = "Media request"
        
        # Block notifications
        if request_type.upper() == "NOTIFICATION":
            if self.settings.get('disable_notifications', True):
                blocked = True
                reason = "Notification request"
        
        if blocked:
            self.stats['requests_blocked'] += 1
            if session_id and session_id in self.private_data:
                self.private_data[session_id]['requests_blocked'] += 1
            
            self.logger.debug(f"Blocked private mode request: {url} - {reason}")
        
        return blocked
    
    def is_tracking_request(self, url: str, request_type: str) -> bool:
        """Check if request is for tracking/analytics."""
        tracking_indicators = [
            'google-analytics', 'googletagmanager', 'doubleclick',
            'facebook.com/tr', 'connect.facebook.net', 'scorecardresearch',
            'quantserve', 'addthis', 'sharethis', 'disqus'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in tracking_indicators)
    
    def should_store_data(self, data_type: str, session_id: str = None) -> bool:
        """Check if data should be stored in private mode."""
        if not self.enabled:
            return True
        
        # Check specific data types
        storage_rules = {
            'history': self.settings.get('disable_history', True),
            'cache': self.settings.get('disable_cache', True),
            'cookies': self.settings.get('disable_cookies', True),
            'form_data': self.settings.get('disable_form_data', True),
            'passwords': self.settings.get('disable_passwords', True),
            'downloads': self.settings.get('disable_downloads_history', True),
            'web_storage': self.settings.get('disable_web_storage', True)
        }
        
        should_block = storage_rules.get(data_type, False)
        
        if should_block:
            self.logger.debug(f"Blocked data storage in private mode: {data_type}")
        
        return not should_block
    
    def clear_private_data(self, session_id: str = None):
        """Clear private browsing data."""
        try:
            cleared_items = 0
            
            if session_id and session_id in self.private_data:
                # Clear specific session data
                del self.private_data[session_id]
                cleared_items += 1
            else:
                # Clear all private data
                cleared_items = len(self.private_data)
                self.private_data.clear()
            
            # Clear temporary directories
            self.cleanup_temp_directories()
            
            self.stats['data_cleared'] += cleared_items
            self.logger.info(f"Cleared private data: {cleared_items} items")
            
        except Exception as e:
            self.logger.error(f"Error clearing private data: {e}")
    
    def get_private_headers(self, url: str) -> Dict[str, str]:
        """Get privacy-enhanced headers for requests."""
        headers = {}
        
        if not self.enabled:
            return headers
        
        # Add privacy headers
        headers.update({
            'DNT': '1',  # Do Not Track
            'Sec-GPC': '1',  # Global Privacy Control
            'Accept-Language': 'en-US,en;q=0.9',  # Limit language info
            'Accept-Encoding': 'gzip, deflate',  # Standard compression only
        })
        
        # Remove tracking headers
        privacy_headers_to_remove = [
            'X-Forwarded-For',
            'X-Real-IP',
            'Referer',  # Can be set to empty or minimal
            'From'
        ]
        
        # Set minimal referer for privacy
        parsed_url = urlparse(url)
        if parsed_url.scheme and parsed_url.netloc:
            headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        return headers
    
    def sanitize_user_agent(self, user_agent: str) -> str:
        """Sanitize user agent for privacy."""
        if not self.enabled:
            return user_agent
        
        # Return a generic user agent that doesn't reveal specific browser/version info
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def get_privacy_report(self, session_id: str = None) -> Dict[str, Any]:
        """Get privacy report for private browsing session."""
        report = {
            'enabled': self.enabled,
            'session_id': session_id,
            'session_data': None,
            'statistics': self.stats.copy(),
            'settings': self.settings.copy(),
            'recommendations': []
        }
        
        if session_id and session_id in self.private_data:
            report['session_data'] = self.private_data[session_id].copy()
        
        # Add recommendations
        if self.stats['tracking_attempts_blocked'] > 0:
            report['recommendations'].append(f"Blocked {self.stats['tracking_attempts_blocked']} tracking attempts")
        
        if self.stats['requests_blocked'] > 0:
            report['recommendations'].append(f"Blocked {self.stats['requests_blocked']} privacy-invasive requests")
        
        return report
    
    def update_setting(self, setting: str, value: bool):
        """Update a privacy setting."""
        if setting in self.settings:
            self.settings[setting] = value
            self.logger.info(f"Updated privacy setting {setting}: {value}")
        else:
            self.logger.warning(f"Unknown privacy setting: {setting}")
    
    def get_setting(self, setting: str) -> bool:
        """Get a privacy setting value."""
        return self.settings.get(setting, False)
    
    def get_all_settings(self) -> Dict[str, bool]:
        """Get all privacy settings."""
        return self.settings.copy()
    
    def reset_settings(self):
        """Reset privacy settings to defaults."""
        self.settings = {
            'disable_cookies': True,
            'disable_history': True,
            'disable_cache': True,
            'disable_form_data': True,
            'disable_passwords': True,
            'disable_downloads_history': True,
            'disable_web_storage': True,
            'disable_location_services': True,
            'disable_camera_microphone': True,
            'disable_notifications': True,
            'clear_on_exit': True,
            'isolate_sessions': True
        }
        
        self.logger.info("Reset privacy settings to defaults")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get private browsing statistics."""
        return {
            'enabled': self.enabled,
            'active_sessions': len(self.private_sessions),
            'private_sessions_started': self.stats['private_sessions_started'],
            'private_sessions_ended': self.stats['private_sessions_ended'],
            'requests_blocked': self.stats['requests_blocked'],
            'tracking_attempts_blocked': self.stats['tracking_attempts_blocked'],
            'data_cleared': self.stats['data_cleared'],
            'current_settings': self.settings.copy()
        }
    
    def reset_statistics(self):
        """Reset private browsing statistics."""
        self.stats = {
            'private_sessions_started': 0,
            'private_sessions_ended': 0,
            'requests_blocked': 0,
            'data_cleared': 0,
            'tracking_attempts_blocked': 0
        }
        
        self.logger.info("Reset private browsing statistics")
    
    def export_privacy_log(self, file_path: str, session_id: str = None) -> bool:
        """Export privacy log for analysis."""
        try:
            import json
            
            log_data = {
                'exported_at': datetime.now().isoformat(),
                'privacy_mode_enabled': self.enabled,
                'statistics': self.stats,
                'settings': self.settings,
                'sessions': {}
            }
            
            # Include session data
            sessions_to_export = [session_id] if session_id else self.private_sessions
            
            for sid in sessions_to_export:
                if sid in self.private_data:
                    log_data['sessions'][sid] = self.private_data[sid]
            
            with open(file_path, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported privacy log to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting privacy log: {e}")
            return False
    
    def is_private_session(self, session_id: str) -> bool:
        """Check if a session is a private session."""
        return session_id in self.private_sessions
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active private sessions."""
        return self.private_sessions.copy()
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired private sessions."""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self.private_data.items():
                created_at = session_data.get('created_at', current_time)
                age = current_time - created_at
                
                if age > timedelta(hours=max_age_hours):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.private_data[session_id]
                if session_id in self.private_sessions:
                    self.private_sessions.remove(session_id)
            
            if expired_sessions:
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired private sessions")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
    
    def get_privacy_score(self, url: str) -> Dict[str, Any]:
        """Get privacy score for a website."""
        score = 100  # Start with perfect score
        issues = []
        
        if not self.enabled:
            issues.append("Private mode not enabled")
            score -= 50
        
        # Check URL for privacy concerns
        parsed_url = urlparse(url)
        
        # Check for tracking domains
        tracking_domains = [
            'google-analytics', 'facebook.com/tr', 'doubleclick.net'
        ]
        
        for domain in tracking_domains:
            if domain in parsed_url.netloc.lower():
                issues.append(f"Tracking domain detected: {domain}")
                score -= 20
        
        # Check for HTTP
        if parsed_url.scheme != 'https':
            issues.append("Not using HTTPS")
            score -= 15
        
        # Determine rating
        if score >= 90:
            rating = "Excellent"
        elif score >= 70:
            rating = "Good"
        elif score >= 50:
            rating = "Fair"
        elif score >= 30:
            rating = "Poor"
        else:
            rating = "Very Poor"
        
        return {
            'score': score,
            'rating': rating,
            'issues': issues,
            'recommendations': [
                "Enable private browsing",
                "Use HTTPS when possible",
                "Avoid sites with known trackers"
            ]
        }
