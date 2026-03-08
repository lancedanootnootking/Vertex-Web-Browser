"""
HTTPS Enforcer

This module provides HTTPS enforcement functionality to ensure
secure connections and prevent mixed content issues.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import requests
import ssl
import socket
from datetime import datetime, timedelta


class HTTPSEnforcer:
    """HTTPS enforcement service for secure browsing."""
    
    def __init__(self, enabled: bool = True, allow_http_localhost: bool = True):
        self.enabled = enabled
        self.allow_http_localhost = allow_http_localhost
        self.logger = logging.getLogger(__name__)
        
        # HTTPS upgrade rules
        self.upgrade_rules: Dict[str, str] = {}
        self.exempt_domains: set[str] = set()
        
        # HSTS preload list (simplified)
        self.hsts_domains: set[str] = {
            'google.com', 'gmail.com', 'facebook.com', 'twitter.com',
            'github.com', 'stackoverflow.com', 'wikipedia.org',
            'reddit.com', 'youtube.com', 'amazon.com', 'microsoft.com'
        }
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'upgraded_requests': 0,
            'blocked_requests': 0,
            'certificate_errors': 0,
            'mixed_content_blocked': 0
        }
        
        # Load default rules
        self.load_default_rules()
    
    def load_default_rules(self):
        """Load default HTTPS upgrade rules."""
        # Common sites that support HTTPS
        upgrade_rules = {
            'http://example.com': 'https://example.com',
            'http://www.example.com': 'https://www.example.com',
            # Add more rules as needed
        }
        
        self.upgrade_rules.update(upgrade_rules)
        
        # Exempt domains (must use HTTP)
        exempt_domains = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'
        ]
        
        self.exempt_domains.update(exempt_domains)
        
        self.logger.info(f"Loaded {len(self.upgrade_rules)} upgrade rules and {len(self.exempt_domains)} exempt domains")
    
    def should_upgrade_to_https(self, url: str) -> Tuple[bool, str, str]:
        """Check if URL should be upgraded to HTTPS."""
        if not self.enabled:
            return False, url, "HTTPS enforcement disabled"
        
        self.stats['total_requests'] += 1
        
        try:
            parsed_url = urlparse(url)
            
            # Already HTTPS
            if parsed_url.scheme == 'https':
                return False, url, "Already HTTPS"
            
            # Not HTTP
            if parsed_url.scheme != 'http':
                return False, url, "Not HTTP scheme"
            
            domain = parsed_url.netloc.lower()
            
            # Check exempt domains
            if self.is_exempt_domain(domain):
                return False, url, "Exempt domain"
            
            # Check HSTS preload list
            if self.is_hsts_domain(domain):
                https_url = url.replace('http://', 'https://', 1)
                self.stats['upgraded_requests'] += 1
                return True, https_url, "HSTS domain"
            
            # Check upgrade rules
            if url in self.upgrade_rules:
                https_url = self.upgrade_rules[url]
                self.stats['upgraded_requests'] += 1
                return True, https_url, "Upgrade rule"
            
            # Check if HTTPS is available
            if self.is_https_available(domain):
                https_url = url.replace('http://', 'https://', 1)
                self.stats['upgraded_requests'] += 1
                return True, https_url, "HTTPS available"
            
        except Exception as e:
            self.logger.error(f"Error checking HTTPS upgrade for {url}: {e}")
        
        return False, url, "No upgrade needed"
    
    def is_exempt_domain(self, domain: str) -> bool:
        """Check if domain is exempt from HTTPS enforcement."""
        # Check exact match
        if domain in self.exempt_domains:
            return True
        
        # Check localhost patterns
        if self.allow_http_localhost:
            if (domain.startswith('localhost') or 
                domain.startswith('127.0.0.1') or
                domain.startswith('0.0.0.0') or
                domain.startswith('::1') or
                domain.endswith('.localhost') or
                domain.endswith('.local')):
                return True
        
        return False
    
    def is_hsts_domain(self, domain: str) -> bool:
        """Check if domain is in HSTS preload list."""
        # Check exact match
        if domain in self.hsts_domains:
            return True
        
        # Check subdomains
        for hsts_domain in self.hsts_domains:
            if domain == hsts_domain or domain.endswith('.' + hsts_domain):
                return True
        
        return False
    
    def is_https_available(self, domain: str, timeout: int = 5) -> bool:
        """Check if HTTPS is available for a domain."""
        try:
            # Try to establish HTTPS connection
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Skip certificate verification for availability check
            
            with socket.create_connection((domain, 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    return True
                    
        except Exception as e:
            self.logger.debug(f"HTTPS not available for {domain}: {e}")
            return False
    
    def check_mixed_content(self, page_url: str, resource_url: str) -> Tuple[bool, str]:
        """Check for mixed content (HTTP resources on HTTPS pages)."""
        try:
            page_parsed = urlparse(page_url)
            resource_parsed = urlparse(resource_url)
            
            # Only check if main page is HTTPS
            if page_parsed.scheme != 'https':
                return False, "Main page not HTTPS"
            
            # Check if resource is HTTP
            if resource_parsed.scheme == 'http':
                self.stats['mixed_content_blocked'] += 1
                return True, "Mixed content: HTTP resource on HTTPS page"
            
        except Exception as e:
            self.logger.error(f"Error checking mixed content: {e}")
        
        return False, "No mixed content"
    
    def validate_certificate(self, url: str) -> Dict[str, Any]:
        """Validate SSL certificate for HTTPS URL."""
        result = {
            'valid': False,
            'error': None,
            'certificate_info': {},
            'validation_details': {}
        }
        
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme != 'https':
                result['error'] = 'Not HTTPS URL'
                return result
            
            domain = parsed_url.netloc
            
            # Get certificate
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    result['valid'] = True
                    result['certificate_info'] = {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'serial_number': cert['serialNumber'],
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'subject_alt_name': cert.get('subjectAltName', [])
                    }
                    
                    # Additional validation
                    result['validation_details'] = self.validate_certificate_details(cert)
        
        except ssl.SSLCertVerificationError as e:
            result['error'] = f"Certificate verification failed: {e}"
            self.stats['certificate_errors'] += 1
        
        except ssl.SSLError as e:
            result['error'] = f"SSL error: {e}"
            self.stats['certificate_errors'] += 1
        
        except Exception as e:
            result['error'] = f"Connection error: {e}"
        
        return result
    
    def validate_certificate_details(self, cert: dict) -> Dict[str, Any]:
        """Validate certificate details."""
        details = {
            'hostname_match': True,
            'not_expired': True,
            'self_signed': False,
            'trusted_chain': True
        }
        
        try:
            # Check expiration
            from datetime import datetime
            import dateutil.parser
            
            not_after = dateutil.parser.parse(cert['notAfter'])
            if not_after < datetime.now():
                details['not_expired'] = False
        
        except:
            details['not_expired'] = False
        
        # Check if self-signed
        subject = dict(x[0] for x in cert['subject'])
        issuer = dict(x[0] for x in cert['issuer'])
        
        if subject == issuer:
            details['self_signed'] = True
            details['trusted_chain'] = False
        
        return details
    
    def add_upgrade_rule(self, http_url: str, https_url: str):
        """Add an HTTPS upgrade rule."""
        self.upgrade_rules[http_url] = https_url
        self.logger.info(f"Added upgrade rule: {http_url} -> {https_url}")
    
    def remove_upgrade_rule(self, http_url: str):
        """Remove an HTTPS upgrade rule."""
        if http_url in self.upgrade_rules:
            del self.upgrade_rules[http_url]
            self.logger.info(f"Removed upgrade rule: {http_url}")
    
    def add_exempt_domain(self, domain: str):
        """Add a domain exempt from HTTPS enforcement."""
        self.exempt_domains.add(domain.lower())
        self.logger.info(f"Added exempt domain: {domain}")
    
    def remove_exempt_domain(self, domain: str):
        """Remove an exempt domain."""
        self.exempt_domains.discard(domain.lower())
        self.logger.info(f"Removed exempt domain: {domain}")
    
    def add_hsts_domain(self, domain: str):
        """Add a domain to HSTS preload list."""
        self.hsts_domains.add(domain.lower())
        self.logger.info(f"Added HSTS domain: {domain}")
    
    def remove_hsts_domain(self, domain: str):
        """Remove a domain from HSTS preload list."""
        self.hsts_domains.discard(domain.lower())
        self.logger.info(f"Removed HSTS domain: {domain}")
    
    def get_security_headers(self, url: str) -> Dict[str, str]:
        """Get recommended security headers for HTTPS URLs."""
        headers = {}
        
        try:
            parsed_url = urlparse(url)
            
            if parsed_url.scheme == 'https':
                headers.update({
                    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'DENY',
                    'X-XSS-Protection': '1; mode=block',
                    'Referrer-Policy': 'strict-origin-when-cross-origin',
                    'Content-Security-Policy': "default-src 'self'; upgrade-insecure-requests"
                })
        
        except Exception as e:
            self.logger.error(f"Error generating security headers: {e}")
        
        return headers
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get HTTPS enforcement statistics."""
        total_requests = self.stats['total_requests']
        upgraded_requests = self.stats['upgraded_requests']
        
        upgrade_rate = (upgraded_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'enabled': self.enabled,
            'total_requests': total_requests,
            'upgraded_requests': upgraded_requests,
            'blocked_requests': self.stats['blocked_requests'],
            'upgrade_rate_percentage': round(upgrade_rate, 2),
            'certificate_errors': self.stats['certificate_errors'],
            'mixed_content_blocked': self.stats['mixed_content_blocked'],
            'upgrade_rules_count': len(self.upgrade_rules),
            'exempt_domains_count': len(self.exempt_domains),
            'hsts_domains_count': len(self.hsts_domains)
        }
    
    def test_url_security(self, url: str) -> Dict[str, Any]:
        """Test URL security and provide recommendations."""
        result = {
            'url': url,
            'secure': False,
            'upgraded': False,
            'original_url': url,
            'final_url': url,
            'recommendations': [],
            'certificate_valid': None,
            'mixed_content_risk': False
        }
        
        try:
            # Check if upgrade is needed
            should_upgrade, upgraded_url, reason = self.should_upgrade_to_https(url)
            
            if should_upgrade:
                result['upgraded'] = True
                result['final_url'] = upgraded_url
                result['recommendations'].append(f"Upgraded to HTTPS: {reason}")
            
            # Check if final URL is secure
            final_url = result['final_url']
            parsed_url = urlparse(final_url)
            
            if parsed_url.scheme == 'https':
                result['secure'] = True
                
                # Validate certificate
                cert_result = self.validate_certificate(final_url)
                result['certificate_valid'] = cert_result['valid']
                
                if not cert_result['valid']:
                    result['secure'] = False
                    result['recommendations'].append(f"Certificate issue: {cert_result['error']}")
                else:
                    result['recommendations'].append("Valid SSL certificate")
            
            else:
                result['recommendations'].append("Consider using HTTPS for better security")
        
        except Exception as e:
            result['recommendations'].append(f"Error checking security: {e}")
        
        return result
    
    def enable(self):
        """Enable HTTPS enforcement."""
        self.enabled = True
        self.logger.info("HTTPS enforcement enabled")
    
    def disable(self):
        """Disable HTTPS enforcement."""
        self.enabled = False
        self.logger.info("HTTPS enforcement disabled")
    
    def reset_statistics(self):
        """Reset enforcement statistics."""
        self.stats = {
            'total_requests': 0,
            'upgraded_requests': 0,
            'blocked_requests': 0,
            'certificate_errors': 0,
            'mixed_content_blocked': 0
        }
        self.logger.info("Reset HTTPS enforcement statistics")
    
    def export_rules(self, file_path: str) -> bool:
        """Export HTTPS rules to file."""
        try:
            import json
            
            rules_data = {
                'upgrade_rules': self.upgrade_rules,
                'exempt_domains': list(self.exempt_domains),
                'hsts_domains': list(self.hsts_domains),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            self.logger.info(f"Exported HTTPS rules to {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting HTTPS rules: {e}")
            return False
    
    def import_rules(self, file_path: str) -> bool:
        """Import HTTPS rules from file."""
        try:
            import json
            
            with open(file_path, 'r') as f:
                rules_data = json.load(f)
            
            # Import upgrade rules
            if 'upgrade_rules' in rules_data:
                self.upgrade_rules.update(rules_data['upgrade_rules'])
            
            # Import exempt domains
            if 'exempt_domains' in rules_data:
                self.exempt_domains.update(rules_data['exempt_domains'])
            
            # Import HSTS domains
            if 'hsts_domains' in rules_data:
                self.hsts_domains.update(rules_data['hsts_domains'])
            
            self.logger.info(f"Imported HTTPS rules from {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error importing HTTPS rules: {e}")
            return False
