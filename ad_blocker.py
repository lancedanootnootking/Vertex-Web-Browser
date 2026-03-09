"""
Ad Blocker

This module provides ad-blocking functionality using filter lists
and pattern matching to block advertising content.
"""

import re
import logging
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse
import requests
from datetime import datetime, timedelta


class AdBlocker:
    """Ad-blocking service using filter lists and pattern matching."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        # Blocklists
        self.blocklist_patterns: List[re.Pattern] = []
        self.blocklist_domains: Set[str] = set()
        self.allowlist_domains: Set[str] = set()
        
        # Cache for blocked URLs
        self.blocked_cache: Dict[str, bool] = {}
        self.cache_size_limit = 10000
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'blocked_domains': set(),
            'last_update': datetime.now()
        }
        
        # Load default blocklists
        self.load_default_blocklists()
    
    def load_default_blocklists(self):
        """Load default ad-blocking patterns."""
        # Default blocking patterns (simplified version of common filters)
        default_patterns = [
            # Common ad patterns
            r'.*/ads/.*',
            r'.*/adserver/.*',
            r'.*/advertisement/.*',
            r'.*/banner/.*',
            r'.*/popup/.*',
            r'.*/sponsor/.*',
            r'.*/affiliate/.*',
            
            # File extensions commonly used for ads
            r'.*\.(gif|jpg|jpeg|png|swf).*\?(width|height|size)=.*',
            
            # URL parameters
            r'.*[?&](ad|banner|campaign|click|creative)=.*',
            
            # Common ad networks
            r'.*doubleclick\.net/.*',
            r'.*googleadservices\.com/.*',
            r'.*googlesyndication\.com/.*',
            r'.*googletagmanager\.com/.*',
            r'.*google-analytics\.com/.*',
            r'.*amazon-adsystem\.com/.*',
            r'.*facebook\.com/tr.*',
            r'.*connect\.facebook\.net/.*',
            r'.*adnxs\.com/.*',
            r'.*adsystem\.com/.*',
            r'.*advertising\.com/.*',
            r'.*adservice\.com/.*',
        ]
        
        # Compile patterns
        for pattern in default_patterns:
            try:
                self.blocklist_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern: {pattern} - {e}")
        
        # Default blocked domains
        default_domains = [
            'doubleclick.net',
            'googleadservices.com',
            'googlesyndication.com',
            'googletagmanager.com',
            'google-analytics.com',
            'amazon-adsystem.com',
            'facebook.com',
            'connect.facebook.net',
            'adnxs.com',
            'adsystem.com',
            'advertising.com',
            'adservice.com',
            'scorecardresearch.com',
            'quantserve.com',
            'addthis.com',
            'sharethis.com',
            'disqus.com',
            'gravatar.com'
        ]
        
        self.blocklist_domains.update(default_domains)
        
        self.logger.info(f"Loaded {len(self.blocklist_patterns)} blocking patterns and {len(self.blocklist_domains)} blocked domains")
    
    def should_block_request(self, url: str, request_type: str = "GET", 
                           referrer: str = None) -> bool:
        """Check if a request should be blocked."""
        if not self.enabled:
            return False
        
        self.stats['total_requests'] += 1
        
        # Check cache first
        if url in self.blocked_cache:
            should_block = self.blocked_cache[url]
            if should_block:
                self.stats['blocked_requests'] += 1
            return should_block
        
        # Parse URL
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            path = parsed_url.path.lower()
            query = parsed_url.query.lower()
            
        except Exception as e:
            self.logger.error(f"Error parsing URL {url}: {e}")
            return False
        
        # Check domain blocklist
        if self.is_domain_blocked(domain):
            self.block_request(url, domain)
            return True
        
        # Check pattern matching
        for pattern in self.blocklist_patterns:
            if pattern.search(url.lower()):
                self.block_request(url, domain)
                return True
        
        # Check specific content types
        if request_type.upper() in ["SCRIPT", "IFRAME"]:
            if self.is_advertising_script(url, path, query):
                self.block_request(url, domain)
                return True
        
        # Check referrer for ad contexts
        if referrer and self.is_ad_context(referrer):
            if self.is_ad_related_resource(url):
                self.block_request(url, domain)
                return True
        
        # Cache result
        self.cache_result(url, False)
        return False
    
    def is_domain_blocked(self, domain: str) -> bool:
        """Check if a domain is in the blocklist."""
        # Check exact match
        if domain in self.blocklist_domains:
            return True
        
        # Check subdomains
        for blocked_domain in self.blocklist_domains:
            if domain == blocked_domain or domain.endswith('.' + blocked_domain):
                return True
        
        return False
    
    def is_advertising_script(self, url: str, path: str, query: str) -> bool:
        """Check if a script is advertising-related."""
        ad_keywords = [
            'ad', 'ads', 'advertisement', 'banner', 'popup', 'sponsor',
            'affiliate', 'tracking', 'analytics', 'doubleclick', 'adsense'
        ]
        
        # Check URL path
        for keyword in ad_keywords:
            if keyword in path or keyword in query:
                return True
        
        # Check file patterns
        if any(pattern in url.lower() for pattern in ['/ad/', '/ads/', '/banner']):
            return True
        
        return False
    
    def is_ad_context(self, referrer: str) -> bool:
        """Check if referrer indicates an advertising context."""
        try:
            parsed_referrer = urlparse(referrer)
            domain = parsed_referrer.netloc.lower()
            
            # Check if referrer is an ad network
            ad_networks = [
                'doubleclick.net', 'googleadservices.com', 'facebook.com/tr',
                'adnxs.com', 'adsystem.com'
            ]
            
            for network in ad_networks:
                if network in domain:
                    return True
            
        except:
            pass
        
        return False
    
    def is_ad_related_resource(self, url: str) -> bool:
        """Check if a resource is ad-related."""
        ad_indicators = [
            'adserver', 'adnetwork', 'adtech', 'advertising',
            'clicktrack', 'impression', 'viewtrack'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in ad_indicators)
    
    def block_request(self, url: str, domain: str):
        """Record a blocked request."""
        self.stats['blocked_requests'] += 1
        self.stats['blocked_domains'].add(domain)
        self.cache_result(url, True)
        
        self.logger.debug(f"Blocked ad request: {url}")
    
    def cache_result(self, url: str, blocked: bool):
        """Cache blocking result."""
        # Limit cache size
        if len(self.blocked_cache) >= self.cache_size_limit:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self.blocked_cache.keys())[:1000]
            for key in keys_to_remove:
                del self.blocked_cache[key]
        
        self.blocked_cache[url] = blocked
    
    def add_domain_to_blocklist(self, domain: str):
        """Add a domain to the blocklist."""
        self.blocklist_domains.add(domain.lower())
        self.logger.info(f"Added domain to blocklist: {domain}")
    
    def remove_domain_from_blocklist(self, domain: str):
        """Remove a domain from the blocklist."""
        self.blocklist_domains.discard(domain.lower())
        self.logger.info(f"Removed domain from blocklist: {domain}")
    
    def add_domain_to_allowlist(self, domain: str):
        """Add a domain to the allowlist (never blocked)."""
        self.allowlist_domains.add(domain.lower())
        self.logger.info(f"Added domain to allowlist: {domain}")
    
    def remove_domain_from_allowlist(self, domain: str):
        """Remove a domain from the allowlist."""
        self.allowlist_domains.discard(domain.lower())
        self.logger.info(f"Removed domain from allowlist: {domain}")
    
    def add_custom_pattern(self, pattern: str) -> bool:
        """Add a custom blocking pattern."""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            self.blocklist_patterns.append(compiled_pattern)
            self.logger.info(f"Added custom pattern: {pattern}")
            return True
        except re.error as e:
            self.logger.error(f"Invalid custom pattern: {pattern} - {e}")
            return False
    
    def remove_pattern(self, pattern: str) -> bool:
        """Remove a blocking pattern."""
        for i, compiled_pattern in enumerate(self.blocklist_patterns):
            if compiled_pattern.pattern == pattern:
                del self.blocklist_patterns[i]
                self.logger.info(f"Removed pattern: {pattern}")
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ad-blocking statistics."""
        total_requests = self.stats['total_requests']
        blocked_requests = self.stats['blocked_requests']
        
        block_rate = (blocked_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'enabled': self.enabled,
            'total_requests': total_requests,
            'blocked_requests': blocked_requests,
            'block_rate_percentage': round(block_rate, 2),
            'blocked_domains_count': len(self.stats['blocked_domains']),
            'blocked_domains': list(self.stats['blocked_domains'])[:10],  # Top 10
            'patterns_count': len(self.blocklist_patterns),
            'domains_count': len(self.blocklist_domains),
            'cache_size': len(self.blocked_cache),
            'last_update': self.stats['last_update'].isoformat()
        }
    
    def update_blocklists(self, sources: List[str] = None) -> bool:
        """Update blocklists from external sources."""
        if sources is None:
            # Default sources (these would be real blocklist URLs in production)
            sources = [
                "https://easylist.to/easylist/easylist.txt",
                "https://easylist.to/easylist/easyprivacy.txt"
            ]
        
        try:
            updated_patterns = 0
            updated_domains = 0
            
            for source_url in sources:
                try:
                    response = requests.get(source_url, timeout=30)
                    if response.status_code == 200:
                        # Parse blocklist (simplified)
                        lines = response.text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            
                            # Skip comments and empty lines
                            if not line or line.startswith('!') or line.startswith('#'):
                                continue
                            
                            # Parse filter rule (simplified)
                            if line.startswith('||'):
                                # Domain rule
                                domain = line[2:].replace('^', '').split('/')[0]
                                if domain:
                                    self.blocklist_domains.add(domain.lower())
                                    updated_domains += 1
                            
                            elif line.startswith('/') and line.endswith('/'):
                                # Regex rule
                                pattern = line[1:-1]
                                if self.add_custom_pattern(pattern):
                                    updated_patterns += 1
                
                except Exception as e:
                    self.logger.error(f"Error updating from {source_url}: {e}")
                    continue
            
            self.stats['last_update'] = datetime.now()
            self.logger.info(f"Updated blocklists: {updated_domains} domains, {updated_patterns} patterns")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating blocklists: {e}")
            return False
    
    def export_blocklist(self, file_path: str) -> bool:
        """Export current blocklist to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Ad Blocker Export\n")
                f.write(f"# Exported: {datetime.now().isoformat()}\n\n")
                
                f.write("# Blocked Domains\n")
                for domain in sorted(self.blocklist_domains):
                    f.write(f"||{domain}^\n")
                
                f.write("\n# Custom Patterns\n")
                for pattern in self.blocklist_patterns:
                    f.write(f"/{pattern.pattern}/\n")
            
            self.logger.info(f"Exported blocklist to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting blocklist: {e}")
            return False
    
    def import_blocklist(self, file_path: str) -> bool:
        """Import blocklist from file."""
        try:
            imported_domains = 0
            imported_patterns = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('!') or line.startswith('#'):
                        continue
                    
                    # Parse domain rule
                    if line.startswith('||'):
                        domain = line[2:].replace('^', '').split('/')[0]
                        if domain:
                            self.blocklist_domains.add(domain.lower())
                            imported_domains += 1
                    
                    # Parse regex rule
                    elif line.startswith('/') and line.endswith('/'):
                        pattern = line[1:-1]
                        if self.add_custom_pattern(pattern):
                            imported_patterns += 1
            
            self.logger.info(f"Imported blocklist: {imported_domains} domains, {imported_patterns} patterns")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing blocklist: {e}")
            return False
    
    def clear_cache(self):
        """Clear the blocking cache."""
        self.blocked_cache.clear()
        self.logger.info("Cleared ad-blocker cache")
    
    def reset_statistics(self):
        """Reset blocking statistics."""
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'blocked_domains': set(),
            'last_update': datetime.now()
        }
        self.logger.info("Reset ad-blocker statistics")
    
    def enable(self):
        """Enable ad-blocking."""
        self.enabled = True
        self.logger.info("Ad-blocker enabled")
    
    def disable(self):
        """Disable ad-blocking."""
        self.enabled = False
        self.logger.info("Ad-blocker disabled")
    
    def get_blocked_domains(self) -> List[str]:
        """Get list of blocked domains."""
        return sorted(list(self.blocklist_domains))
    
    def get_blocked_patterns(self) -> List[str]:
        """Get list of blocking patterns."""
        return [pattern.pattern for pattern in self.blocklist_patterns]
    
    def test_url(self, url: str) -> Dict[str, Any]:
        """Test if a URL would be blocked."""
        result = {
            'url': url,
            'blocked': False,
            'reason': None,
            'matched_pattern': None,
            'blocked_domain': None
        }
        
        if not self.enabled:
            result['reason'] = 'Ad-blocker disabled'
            return result
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check domain
            if self.is_domain_blocked(domain):
                result['blocked'] = True
                result['reason'] = 'Domain blocked'
                result['blocked_domain'] = domain
                return result
            
            # Check patterns
            for pattern in self.blocklist_patterns:
                if pattern.search(url.lower()):
                    result['blocked'] = True
                    result['reason'] = 'Pattern matched'
                    result['matched_pattern'] = pattern.pattern
                    return result
        
        except Exception as e:
            result['reason'] = f'Error: {e}'
        
        return result
