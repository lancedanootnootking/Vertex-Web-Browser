"""
Security Service

This module handles security features including URL validation,
malicious domain detection, and security policy enforcement.
"""

import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Optional
import logging
from urllib.parse import urlparse

class SecurityService:
    """Service for managing security features."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Security settings
        self.enable_ad_blocker = config.get('enable_ad_blocker', True)
        self.enforce_https = config.get('enforce_https', True)
        self.block_trackers = config.get('block_trackers', True)
        self.block_malicious_domains = config.get('block_malicious_domains', True)
        
        # Initialize blocklists
        self.ad_blocklist = self._load_ad_blocklist()
        self.tracker_blocklist = self._load_tracker_blocklist()
        self.malicious_blocklist = self._load_malicious_blocklist()
        
        # Cache for blocklist updates
        self.last_blocklist_update = datetime.now()
        self.blocklist_update_interval = timedelta(hours=24)
    
    def is_url_safe(self, url: str) -> bool:
        """Check if a URL is safe to visit."""
        try:
            parsed_url = urlparse(url)
            
            # Basic URL validation
            if not self._is_valid_url_structure(parsed_url):
                return False
            
            # Check against blocklists
            if self._is_blocked_domain(parsed_url.netloc):
                return False
            
            # HTTPS enforcement
            if self.enforce_https and parsed_url.scheme != 'https':
                # Allow HTTP for localhost and development
                if not (parsed_url.netloc.startswith('localhost') or 
                       parsed_url.netloc.startswith('127.0.0.1')):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking URL safety for {url}: {e}")
            return False
    
    def should_block_request(self, url: str, resource_type: str = None) -> bool:
        """Check if a request should be blocked based on security policies."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Ad blocking
            if self.enable_ad_blocker and self._is_ad_domain(domain):
                self.logger.debug(f"Blocked ad request: {url}")
                return True
            
            # Tracker blocking
            if self.block_trackers and self._is_tracker_domain(domain):
                self.logger.debug(f"Blocked tracker request: {url}")
                return True
            
            # Malicious domain blocking
            if self.block_malicious_domains and self._is_malicious_domain(domain):
                self.logger.warning(f"Blocked malicious domain request: {url}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking request blocking for {url}: {e}")
            return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers for responses."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize and normalize a URL."""
        try:
            parsed_url = urlparse(url)
            
            # Remove tracking parameters
            cleaned_query = self._remove_tracking_params(parsed_url.query)
            
            # Rebuild URL
            cleaned_url = parsed_url._replace(query=cleaned_query).geturl()
            
            # Force HTTPS if enabled and appropriate
            if (self.enforce_https and 
                parsed_url.scheme == 'http' and 
                not (parsed_url.netloc.startswith('localhost') or 
                     parsed_url.netloc.startswith('127.0.0.1'))):
                cleaned_url = cleaned_url.replace('http://', 'https://', 1)
            
            return cleaned_url
            
        except Exception as e:
            self.logger.error(f"Error sanitizing URL {url}: {e}")
            return url
    
    def get_blocklist(self) -> Dict[str, List[str]]:
        """Get current blocklists."""
        return {
            'ads': list(self.ad_blocklist),
            'trackers': list(self.tracker_blocklist),
            'malicious': list(self.malicious_blocklist)
        }
    
    def update_blocklists(self) -> bool:
        """Update blocklists from external sources."""
        try:
            # This is a placeholder for external blocklist updates
            # In practice, you'd fetch from sources like:
            # - EasyList for ads
            # - Disconnect.me for trackers
            # - PhishTank for malicious domains
            
            self.logger.info("Blocklists updated (placeholder implementation)")
            self.last_blocklist_update = datetime.now()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating blocklists: {e}")
            return False
    
    def _is_valid_url_structure(self, parsed_url) -> bool:
        """Check if URL has a valid structure."""
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
        
        if parsed_url.scheme not in ['http', 'https']:
            return False
        
        # Check for suspicious patterns
        if '..' in parsed_url.path:
            return False
        
        return True
    
    def _is_blocked_domain(self, domain: str) -> bool:
        """Check if domain is in any blocklist."""
        return (self._is_ad_domain(domain) or 
                self._is_tracker_domain(domain) or 
                self._is_malicious_domain(domain))
    
    def _is_ad_domain(self, domain: str) -> bool:
        """Check if domain is known for ads."""
        domain_lower = domain.lower()
        
        # Check against ad blocklist
        for blocked in self.ad_blocklist:
            if blocked in domain_lower or domain_lower.endswith(blocked):
                return True
        
        # Common ad patterns
        ad_patterns = [
            'doubleclick', 'googleads', 'googlesyndication', 'googletag',
            'amazon-adsystem', 'facebook.com/tr', 'google-analytics',
            'adsystem', 'adnxs', 'advertising', 'adservice'
        ]
        
        return any(pattern in domain_lower for pattern in ad_patterns)
    
    def _is_tracker_domain(self, domain: str) -> bool:
        """Check if domain is known for tracking."""
        domain_lower = domain.lower()
        
        # Check against tracker blocklist
        for blocked in self.tracker_blocklist:
            if blocked in domain_lower or domain_lower.endswith(blocked):
                return True
        
        # Common tracker patterns
        tracker_patterns = [
            'google-analytics', 'googletagmanager', 'facebook.com/tr',
            'connect.facebook.net', 'googleadservices', 'doubleclick',
            'amazon-adsystem', 'scorecardresearch', 'quantserve',
            'addthis', 'sharethis', 'disqus'
        ]
        
        return any(pattern in domain_lower for pattern in tracker_patterns)
    
    def _is_malicious_domain(self, domain: str) -> bool:
        """Check if domain is known to be malicious."""
        domain_lower = domain.lower()
        
        # Check against malicious blocklist
        for blocked in self.malicious_blocklist:
            if blocked in domain_lower or domain_lower.endswith(blocked):
                return True
        
        # Suspicious patterns
        suspicious_patterns = [
            # These would be populated from actual threat intelligence
            'malware-example', 'phishing-example'
        ]
        
        return any(pattern in domain_lower for pattern in suspicious_patterns)
    
    def _remove_tracking_params(self, query: str) -> str:
        """Remove tracking parameters from URL query."""
        if not query:
            return query
        
        # Common tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'campaign',
            'clickid', 'ad_id', 'creative_id'
        }
        
        # Parse and clean query parameters
        params = []
        for param in query.split('&'):
            if '=' in param:
                key = param.split('=')[0]
                if key not in tracking_params:
                    params.append(param)
        
        return '&'.join(params)
    
    def _load_ad_blocklist(self) -> Set[str]:
        """Load ad blocking list."""
        # This is a simplified ad blocklist
        # In practice, you'd load from sources like EasyList
        return {
            'doubleclick.net', 'googleadservices.com', 'googlesyndication.com',
            'googletagmanager.com', 'google-analytics.com', 'googletagservices.com',
            'amazon-adsystem.com', 'facebook.com/tr', 'connect.facebook.net',
            'adnxs.com', 'adsystem.com', 'advertising.com', 'adservice.com'
        }
    
    def _load_tracker_blocklist(self) -> Set[str]:
        """Load tracker blocking list."""
        # This is a simplified tracker blocklist
        # In practice, you'd load from sources like Disconnect.me
        return {
            'google-analytics.com', 'googletagmanager.com', 'facebook.com/tr',
            'connect.facebook.net', 'googleadservices.com', 'doubleclick.net',
            'scorecardresearch.com', 'quantserve.com', 'addthis.com',
            'sharethis.com', 'disqus.com', 'gravatar.com'
        }
    
    def _load_malicious_blocklist(self) -> Set[str]:
        """Load malicious domain blocklist."""
        # This is a placeholder for malicious domains
        # In practice, you'd load from threat intelligence sources
        return {
            # Example malicious domains (these are fake examples)
            'malware-example.com', 'phishing-example.net',
            'scam-example.org', 'trojan-example.info'
        }
    
    def get_security_report(self, url: str) -> Dict[str, Any]:
        """Get a security report for a URL."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            report = {
                'url': url,
                'domain': domain,
                'is_safe': self.is_url_safe(url),
                'warnings': [],
                'recommendations': []
            }
            
            # Check various security aspects
            if parsed_url.scheme != 'https':
                report['warnings'].append('HTTP connection - not encrypted')
                report['recommendations'].append('Use HTTPS when possible')
            
            if self._is_ad_domain(domain):
                report['warnings'].append('Domain known for advertising')
            
            if self._is_tracker_domain(domain):
                report['warnings'].append('Domain known for tracking')
                report['recommendations'].append('Consider using privacy protection')
            
            if self._is_malicious_domain(domain):
                report['warnings'].append('Domain flagged as potentially malicious')
                report['recommendations'].append('Avoid visiting this site')
            
            # Check for suspicious URL patterns
            if self._has_suspicious_patterns(url):
                report['warnings'].append('URL contains suspicious patterns')
                report['recommendations'].append('Verify the legitimacy of this site')
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating security report for {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    def _has_suspicious_patterns(self, url: str) -> bool:
        """Check for suspicious patterns in URL."""
        suspicious_patterns = [
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'[a-z0-9]{20,}',  # Long random strings
            r'bit\.ly|tinyurl\.com|t\.co',  # URL shorteners
            r'paypal.*secure.*login',  # Phishing patterns
            r'microsoft.*security.*alert'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def get_privacy_score(self, url: str) -> Dict[str, Any]:
        """Get a privacy score for a website."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            score = 100  # Start with perfect score
            issues = []
            
            # HTTPS check
            if parsed_url.scheme != 'https':
                score -= 30
                issues.append('No HTTPS encryption')
            
            # Tracker check
            if self._is_tracker_domain(domain):
                score -= 25
                issues.append('Known tracking domain')
            
            # Ad check
            if self._is_ad_domain(domain):
                score -= 15
                issues.append('Known advertising domain')
            
            # Length and complexity check
            if len(url) > 200:
                score -= 10
                issues.append('Unusually long URL')
            
            # Determine rating
            if score >= 80:
                rating = 'Excellent'
            elif score >= 60:
                rating = 'Good'
            elif score >= 40:
                rating = 'Fair'
            elif score >= 20:
                rating = 'Poor'
            else:
                rating = 'Very Poor'
            
            return {
                'url': url,
                'score': score,
                'rating': rating,
                'issues': issues,
                'recommendations': self._get_privacy_recommendations(issues)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating privacy score for {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    def _get_privacy_recommendations(self, issues: List[str]) -> List[str]:
        """Get privacy recommendations based on issues."""
        recommendations = []
        
        if 'No HTTPS encryption' in issues:
            recommendations.append('Look for HTTPS version of the site')
        
        if 'Known tracking domain' in issues:
            recommendations.append('Use privacy protection tools')
            recommendations.append('Consider alternative services')
        
        if 'Known advertising domain' in issues:
            recommendations.append('Use ad blockers')
        
        if 'Unusually long URL' in issues:
            recommendations.append('Verify the site is legitimate')
            recommendations.append('Be cautious with personal information')
        
        return recommendations
