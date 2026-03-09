"""
Security Tests

This module contains tests for the security features,
including ad-blocking, HTTPS enforcement, and privacy protection.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.ad_blocker import AdBlocker
from security.https_enforcer import HTTPSEnforcer
from security.privacy_mode import PrivacyMode


class TestAdBlocker(unittest.TestCase):
    """Test ad-blocking functionality."""
    
    def setUp(self):
        """Set up test ad blocker."""
        self.ad_blocker = AdBlocker(enabled=True)
    
    def test_domain_blocking(self):
        """Test domain-based blocking."""
        # Test blocked domains
        self.assertTrue(self.ad_blocker.is_domain_blocked('doubleclick.net'))
        self.assertTrue(self.ad_blocker.is_domain_blocked('googleadservices.com'))
        
        # Test allowed domains
        self.assertFalse(self.ad_blocker.is_domain_blocked('example.com'))
        self.assertFalse(self.ad_blocker.is_domain_blocked('github.com'))
    
    def test_request_blocking(self):
        """Test request blocking."""
        # Test ad requests
        blocked = self.ad_blocker.should_block_request('https://doubleclick.net/ad')
        self.assertTrue(blocked)
        
        # Test tracker requests
        blocked = self.ad_blocker.should_block_request('https://google-analytics.com/collect')
        self.assertTrue(blocked)
        
        # Test safe requests
        blocked = self.ad_blocker.should_block_request('https://example.com/page')
        self.assertFalse(blocked)
    
    def test_pattern_matching(self):
        """Test pattern-based blocking."""
        # Test ad patterns
        blocked = self.ad_blocker.should_block_request('https://example.com/ads/banner.jpg')
        self.assertTrue(blocked)
        
        blocked = self.ad_blocker.should_block_request('https://example.com/popup.html')
        self.assertTrue(blocked)
    
    def test_custom_patterns(self):
        """Test custom blocking patterns."""
        # Add custom pattern
        success = self.ad_blocker.add_custom_pattern(r'.*/custom/ads/.*')
        self.assertTrue(success)
        
        # Test custom pattern
        blocked = self.ad_blocker.should_block_request('https://example.com/custom/ads/image.jpg')
        self.assertTrue(blocked)
    
    def test_domain_management(self):
        """Test domain allowlist/blocklist management."""
        # Add domain to blocklist
        self.ad_blocker.add_domain_to_blocklist('ads.example.com')
        self.assertTrue(self.ad_blocker.is_domain_blocked('ads.example.com'))
        
        # Remove domain from blocklist
        self.ad_blocker.remove_domain_from_blocklist('ads.example.com')
        self.assertFalse(self.ad_blocker.is_domain_blocked('ads.example.com'))
        
        # Add domain to allowlist
        self.ad_blocker.add_domain_to_allowlist('safe.example.com')
        # Note: Allowlist functionality would need to be implemented
    
    def test_statistics(self):
        """Test ad-blocking statistics."""
        # Generate some blocked requests
        self.ad_blocker.should_block_request('https://doubleclick.net/ad')
        self.ad_blocker.should_block_request('https://google-analytics.com/collect')
        self.ad_blocker.should_block_request('https://example.com/page')
        
        # Get statistics
        stats = self.ad_blocker.get_statistics()
        
        self.assertIn('total_requests', stats)
        self.assertIn('blocked_requests', stats)
        self.assertIn('block_rate_percentage', stats)
        self.assertGreater(stats['blocked_requests'], 0)
    
    def test_cache_operations(self):
        """Test cache operations."""
        # Test cache clearing
        self.ad_blocker.clear_cache()
        
        # Verify cache is empty
        self.assertEqual(len(self.ad_blocker.blocked_cache), 0)
    
    def test_enable_disable(self):
        """Test enabling/disabling ad blocker."""
        # Test disabling
        self.ad_blocker.disable()
        blocked = self.ad_blocker.should_block_request('https://doubleclick.net/ad')
        self.assertFalse(blocked)
        
        # Test enabling
        self.ad_blocker.enable()
        blocked = self.ad_blocker.should_block_request('https://doubleclick.net/ad')
        self.assertTrue(blocked)
    
    def test_url_testing(self):
        """Test URL testing functionality."""
        # Test blocked URL
        result = self.ad_blocker.test_url('https://doubleclick.net/ad')
        self.assertTrue(result['blocked'])
        self.assertIn('reason', result)
        
        # Test safe URL
        result = self.ad_blocker.test_url('https://example.com')
        self.assertFalse(result['blocked'])


class TestHTTPSEnforcer(unittest.TestCase):
    """Test HTTPS enforcement functionality."""
    
    def setUp(self):
        """Set up test HTTPS enforcer."""
        self.https_enforcer = HTTPSEnforcer(enabled=True)
    
    def test_https_upgrade(self):
        """Test HTTPS URL upgrading."""
        # Test HTTP to HTTPS upgrade
        should_upgrade, upgraded_url, reason = self.https_enforcer.should_upgrade_to_https('http://example.com')
        self.assertTrue(should_upgrade)
        self.assertEqual(upgraded_url, 'https://example.com')
        
        # Test already HTTPS URL
        should_upgrade, upgraded_url, reason = self.https_enforcer.should_upgrade_to_https('https://example.com')
        self.assertFalse(should_upgrade)
        self.assertEqual(upgraded_url, 'https://example.com')
    
    def test_exempt_domains(self):
        """Test exempt domain handling."""
        # Test localhost exemption
        should_upgrade, _, _ = self.https_enforcer.should_upgrade_to_https('http://localhost:8000')
        self.assertFalse(should_upgrade)
        
        # Test 127.0.0.1 exemption
        should_upgrade, _, _ = self.https_enforcer.should_upgrade_to_https('http://127.0.0.1:8000')
        self.assertFalse(should_upgrade)
    
    def test_hsts_domains(self):
        """Test HSTS preload list."""
        # Test HSTS domain
        should_upgrade, upgraded_url, reason = self.https_enforcer.should_upgrade_to_https('http://google.com')
        self.assertTrue(should_upgrade)
        self.assertEqual(upgraded_url, 'https://google.com')
        self.assertEqual(reason, 'HSTS domain')
    
    def test_https_availability(self):
        """Test HTTPS availability checking."""
        # Mock HTTPS availability check
        with patch('socket.create_connection') as mock_connect:
            mock_connect.return_value = Mock()
            mock_sock = Mock()
            mock_context = Mock()
            mock_context.wrap_socket.return_value = mock_sock
            mock_connect.return_value.__enter__.return_value = mock_sock
            
            available = self.https_enforcer.is_https_available('example.com')
            self.assertTrue(available)
    
    def test_mixed_content_detection(self):
        """Test mixed content detection."""
        # Test mixed content
        is_mixed, reason = self.https_enforcer.check_mixed_content(
            'https://example.com',
            'http://example.com/script.js'
        )
        self.assertTrue(is_mixed)
        self.assertIn('Mixed content', reason)
        
        # Test secure content
        is_mixed, reason = self.https_enforcer.check_mixed_content(
            'https://example.com',
            'https://example.com/script.js'
        )
        self.assertFalse(is_mixed)
    
    def test_certificate_validation(self):
        """Test SSL certificate validation."""
        # Mock certificate validation
        with patch('socket.create_connection') as mock_connect:
            mock_connect.return_value = Mock()
            mock_sock = Mock()
            mock_context = Mock()
            mock_context.wrap_socket.return_value = mock_sock
            mock_sock.getpeercert.return_value = {
                'subject': [('commonName', 'example.com')],
                'issuer': [('commonName', 'CA')],
                'version': 2,
                'serialNumber': '123456',
                'notBefore': 'Jan  1 12:00:00 2023 GMT',
                'notAfter': 'Jan  1 12:00:00 2024 GMT'
            }
            mock_connect.return_value.__enter__.return_value = mock_sock
            
            result = self.https_enforcer.validate_certificate('https://example.com')
            self.assertTrue(result['valid'])
    
    def test_security_headers(self):
        """Test security header generation."""
        headers = self.https_enforcer.get_security_headers('https://example.com')
        
        self.assertIn('Strict-Transport-Security', headers)
        self.assertIn('X-Content-Type-Options', headers)
        self.assertIn('X-Frame-Options', headers)
        self.assertIn('Content-Security-Policy', headers)
    
    def test_upgrade_rules(self):
        """Test HTTPS upgrade rules."""
        # Add upgrade rule
        self.https_enforcer.add_upgrade_rule('http://old-site.com', 'https://new-site.com')
        
        # Test upgrade rule
        should_upgrade, upgraded_url, reason = self.https_enforcer.should_upgrade_to_https('http://old-site.com')
        self.assertTrue(should_upgrade)
        self.assertEqual(upgraded_url, 'https://new-site.com')
        self.assertEqual(reason, 'Upgrade rule')
    
    def test_url_security_testing(self):
        """Test URL security testing."""
        # Test HTTP URL
        result = self.https_enforcer.test_url_security('http://example.com')
        self.assertIn('secure', result)
        self.assertIn('upgraded', result)
        self.assertIn('recommendations', result)
        
        # Test HTTPS URL
        result = self.https_enforcer.test_url_security('https://example.com')
        self.assertTrue(result['secure'])
        self.assertFalse(result['upgraded'])
    
    def test_statistics(self):
        """Test HTTPS enforcement statistics."""
        # Generate some statistics
        self.https_enforcer.should_upgrade_to_https('http://example.com')
        self.https_enforcer.should_upgrade_to_https('https://example.com')
        
        stats = self.https_enforcer.get_statistics()
        
        self.assertIn('total_requests', stats)
        self.assertIn('upgraded_requests', stats)
        self.assertIn('upgrade_rate_percentage', stats)
    
    def test_enable_disable(self):
        """Test enabling/disabling HTTPS enforcement."""
        # Test disabling
        self.https_enforcer.disable()
        should_upgrade, _, _ = self.https_enforcer.should_upgrade_to_https('http://example.com')
        self.assertFalse(should_upgrade)
        
        # Test enabling
        self.https_enforcer.enable()
        should_upgrade, _, _ = self.https_enforcer.should_upgrade_to_https('http://example.com')
        self.assertTrue(should_upgrade)


class TestPrivacyMode(unittest.TestCase):
    """Test private browsing functionality."""
    
    def setUp(self):
        """Set up test privacy mode."""
        self.privacy_mode = PrivacyMode(enabled=False)
    
    def test_private_mode_enable_disable(self):
        """Test enabling/disabling private mode."""
        # Test enabling
        session_id = self.privacy_mode.enable_private_mode()
        self.assertIsNotNone(session_id)
        self.assertTrue(self.privacy_mode.enabled)
        self.assertIn(session_id, self.privacy_mode.private_sessions)
        
        # Test disabling
        success = self.privacy_mode.disable_private_mode(session_id)
        self.assertTrue(success)
        self.assertFalse(self.privacy_mode.enabled)
    
    def test_request_blocking(self):
        """Test request blocking in private mode."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        # Test tracking request blocking
        blocked = self.privacy_mode.should_block_request(
            'https://google-analytics.com/collect',
            'script',
            session_id
        )
        self.assertTrue(blocked)
        
        # Test cookie request blocking
        blocked = self.privacy_mode.should_block_request(
            'https://example.com/cookie',
            'SET_COOKIE',
            session_id
        )
        self.assertTrue(blocked)
        
        # Test storage request blocking
        blocked = self.privacy_mode.should_block_request(
            'https://example.com/storage',
            'WEB_STORAGE',
            session_id
        )
        self.assertTrue(blocked)
    
    def test_data_storage_blocking(self):
        """Test data storage blocking."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        # Test history blocking
        should_store = self.privacy_mode.should_store_data('history', session_id)
        self.assertFalse(should_store)
        
        # Test cache blocking
        should_store = self.privacy_mode.should_store_data('cache', session_id)
        self.assertFalse(should_store)
        
        # Test cookie blocking
        should_store = self.privacy_mode.should_store_data('cookies', session_id)
        self.assertFalse(should_store)
    
    def test_privacy_headers(self):
        """Test privacy-enhanced headers."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        headers = self.privacy_mode.get_privacy_headers('https://example.com')
        
        self.assertIn('DNT', headers)
        self.assertIn('Sec-GPC', headers)
        self.assertEqual(headers['DNT'], '1')
        self.assertEqual(headers['Sec-GPC'], '1')
    
    def test_user_agent_sanitization(self):
        """Test user agent sanitization."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        sanitized_ua = self.privacy_mode.sanitize_user_agent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        self.assertIn('Mozilla/5.0', sanitized_ua)
        # Should remove specific version info
    
    def test_privacy_report(self):
        """Test privacy report generation."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        # Generate some activity
        self.privacy_mode.should_block_request('https://google-analytics.com/collect', 'script', session_id)
        
        report = self.privacy_mode.get_privacy_report(session_id)
        
        self.assertIn('enabled', report)
        self.assertIn('session_id', report)
        self.assertIn('statistics', report)
        self.assertIn('settings', report)
        self.assertIn('recommendations', report)
    
    def test_privacy_score(self):
        """Test privacy score calculation."""
        score_data = self.privacy_mode.get_privacy_score('https://example.com')
        
        self.assertIn('score', score_data)
        self.assertIn('rating', score_data)
        self.assertIn('issues', score_data)
        self.assertIn('recommendations', score_data)
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(score_data['score'], 0)
        self.assertLessEqual(score_data['score'], 100)
    
    def test_settings_management(self):
        """Test privacy settings management."""
        # Test updating settings
        self.privacy_mode.update_setting('disable_cookies', False)
        self.assertFalse(self.privacy_mode.get_setting('disable_cookies'))
        
        # Test getting all settings
        all_settings = self.privacy_mode.get_all_settings()
        self.assertIsInstance(all_settings, dict)
        self.assertIn('disable_cookies', all_settings)
    
    def test_session_management(self):
        """Test private session management."""
        # Create multiple sessions
        session1 = self.privacy_mode.create_private_session()
        session2 = self.privacy_mode.create_private_session()
        
        self.assertEqual(len(self.privacy_mode.private_sessions), 2)
        self.assertIn(session1, self.privacy_mode.private_sessions)
        self.assertIn(session2, self.privacy_mode.private_sessions)
        
        # Test session checking
        self.assertTrue(self.privacy_mode.is_private_session(session1))
        self.assertFalse(self.privacy_mode.is_private_session('invalid_session'))
        
        # Test getting active sessions
        active_sessions = self.privacy_mode.get_active_sessions()
        self.assertEqual(len(active_sessions), 2)
    
    def test_statistics(self):
        """Test privacy mode statistics."""
        # Enable private mode and generate activity
        session_id = self.privacy_mode.enable_private_mode()
        self.privacy_mode.should_block_request('https://google-analytics.com/collect', 'script', session_id)
        
        stats = self.privacy_mode.get_statistics()
        
        self.assertIn('enabled', stats)
        self.assertIn('active_sessions', stats)
        self.assertIn('requests_blocked', stats)
        self.assertIn('tracking_attempts_blocked', stats)
    
    def test_data_cleanup(self):
        """Test private data cleanup."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        # Add some data
        self.privacy_mode.private_data[session_id] = {'test': 'data'}
        
        # Clear data
        self.privacy_mode.clear_private_data(session_id)
        
        # Verify data is cleared
        self.assertNotIn(session_id, self.privacy_mode.private_data)
    
    def test_temporary_directories(self):
        """Test temporary directory management."""
        # Enable private mode
        session_id = self.privacy_mode.enable_private_mode()
        
        # Verify temp directory is created
        self.assertIsNotNone(self.privacy_mode.temp_dir)
        self.assertTrue(os.path.exists(self.privacy_mode.temp_dir))
        
        # Disable private mode
        self.privacy_mode.disable_private_mode(session_id)
        
        # Verify temp directory is cleaned up
        self.assertIsNone(self.privacy_mode.temp_dir)


if __name__ == '__main__':
    unittest.main()
