"""
Search Integration

This module provides search engine integration with multiple providers,
including Google, Bing, DuckDuckGo, and custom search engines.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import requests
import json
from urllib.parse import urlencode, quote
from datetime import datetime
import re


class SearchEngine:
    """Base class for search engines."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform search query."""
        raise NotImplementedError
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get search suggestions."""
        raise NotImplementedError


class GoogleSearch(SearchEngine):
    """Google search engine integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Google", config)
        self.api_key = config.get('api_key', '')
        self.search_engine_id = config.get('search_engine_id', '')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.suggestions_url = "https://suggestqueries.google.com/complete/search"
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform Google search."""
        results = []
        
        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(limit, 10)
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    result = {
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'display_url': item.get('displayLink', ''),
                        'source': 'Google',
                        'rank': len(results) + 1
                    }
                    results.append(result)
            
            else:
                self.logger.error(f"Google search API error: {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"Error performing Google search: {e}")
        
        return results
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get Google search suggestions."""
        suggestions = []
        
        try:
            params = {
                'client': 'firefox',
                'q': query
            }
            
            response = requests.get(self.suggestions_url, params=params, timeout=5)
            
            if response.status_code == 200:
                # Google returns JSONP format, need to parse
                text = response.text
                # Extract suggestions from JSONP response
                if text.startswith('window.google.ac.h('):
                    json_str = text[19:-1]  # Remove wrapper
                    data = json.loads(json_str)
                    if len(data) > 1:
                        suggestions = data[1]
        
        except Exception as e:
            self.logger.error(f"Error getting Google suggestions: {e}")
        
        return suggestions


class BingSearch(SearchEngine):
    """Bing search engine integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Bing", config)
        self.api_key = config.get('api_key', '')
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        self.suggestions_url = "https://api.bing.microsoft.com/v7.0/suggestions"
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform Bing search."""
        results = []
        
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            
            params = {
                'q': query,
                'count': min(limit, 50),
                'offset': 0,
                'mkt': 'en-US'
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('webPages', {}).get('value', []):
                    result = {
                        'title': item.get('name', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('snippet', ''),
                        'display_url': item.get('displayUrl', ''),
                        'source': 'Bing',
                        'rank': len(results) + 1
                    }
                    results.append(result)
            
            else:
                self.logger.error(f"Bing search API error: {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"Error performing Bing search: {e}")
        
        return results
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get Bing search suggestions."""
        suggestions = []
        
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            
            params = {
                'q': query,
                'mkt': 'en-US'
            }
            
            response = requests.get(self.suggestions_url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                for suggestion in data.get('suggestionGroups', [{}])[0].get('searchSuggestions', []):
                    suggestions.append(suggestion.get('displayText', ''))
        
        except Exception as e:
            self.logger.error(f"Error getting Bing suggestions: {e}")
        
        return suggestions


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search engine integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("DuckDuckGo", config)
        self.base_url = "https://duckduckgo.com/html/"
        self.instant_answers_url = "https://api.duckduckgo.com/"
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform DuckDuckGo search."""
        results = []
        
        try:
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse HTML results (simplified)
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result divs
                result_divs = soup.find_all('div', class_='result')
                
                for div in result_divs[:limit]:
                    title_tag = div.find('a', class_='result__a')
                    snippet_tag = div.find('a', class_='result__snippet')
                    
                    if title_tag:
                        result = {
                            'title': title_tag.get_text(strip=True),
                            'url': title_tag.get('href', ''),
                            'snippet': snippet_tag.get_text(strip=True) if snippet_tag else '',
                            'display_url': title_tag.get('href', ''),
                            'source': 'DuckDuckGo',
                            'rank': len(results) + 1
                        }
                        results.append(result)
            
        except Exception as e:
            self.logger.error(f"Error performing DuckDuckGo search: {e}")
        
        return results
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get DuckDuckGo search suggestions."""
        suggestions = []
        
        try:
            params = {
                'q': query,
                'format': 'json',
                'pretty': '1'
            }
            
            response = requests.get(self.instant_answers_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract related topics as suggestions
                for topic in data.get('RelatedTopics', []):
                    text = topic.get('Text', '')
                    if text and query.lower() not in text.lower():
                        suggestions.append(text)
        
        except Exception as e:
            self.logger.error(f"Error getting DuckDuckGo suggestions: {e}")
        
        return suggestions


class SearchIntegration:
    """Main search integration service."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize search engines
        self.search_engines: Dict[str, SearchEngine] = {}
        self.default_engine = config.get('default_engine', 'google')
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'searches_by_engine': {},
            'popular_queries': {},
            'last_search': None
        }
        
        # Initialize search engines
        self.initialize_search_engines()
    
    def initialize_search_engines(self):
        """Initialize available search engines."""
        search_config = self.config.get('search_engines', {})
        
        # Initialize Google
        if 'google' in search_config:
            self.search_engines['google'] = GoogleSearch(search_config['google'])
        
        # Initialize Bing
        if 'bing' in search_config:
            self.search_engines['bing'] = BingSearch(search_config['bing'])
        
        # Initialize DuckDuckGo (no API key required)
        self.search_engines['duckduckgo'] = DuckDuckGoSearch(search_config.get('duckduckgo', {}))
        
        # Initialize statistics
        for engine_name in self.search_engines:
            self.stats['searches_by_engine'][engine_name] = 0
        
        self.logger.info(f"Initialized {len(self.search_engines)} search engines")
    
    def search(self, query: str, engine: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform search query."""
        if not query.strip():
            return []
        
        # Determine which engine to use
        if engine is None:
            engine = self.default_engine
        
        if engine not in self.search_engines:
            self.logger.warning(f"Search engine '{engine}' not available, using default")
            engine = self.default_engine
        
        # Perform search
        search_engine = self.search_engines[engine]
        results = search_engine.search(query, limit)
        
        # Update statistics
        self.stats['total_searches'] += 1
        self.stats['searches_by_engine'][engine] = self.stats['searches_by_engine'].get(engine, 0) + 1
        self.stats['popular_queries'][query.lower()] = self.stats['popular_queries'].get(query.lower(), 0) + 1
        self.stats['last_search'] = datetime.now().isoformat()
        
        self.logger.info(f"Search performed: '{query}' using {engine} - {len(results)} results")
        
        return results
    
    def get_suggestions(self, query: str, engine: str = None) -> List[str]:
        """Get search suggestions."""
        if not query.strip():
            return []
        
        # Determine which engine to use
        if engine is None:
            engine = self.default_engine
        
        if engine not in self.search_engines:
            engine = self.default_engine
        
        # Get suggestions
        search_engine = self.search_engines[engine]
        suggestions = search_engine.get_suggestions(query)
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    def multi_engine_search(self, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple engines."""
        results = {}
        
        for engine_name, search_engine in self.search_engines.items():
            try:
                engine_results = search_engine.search(query, limit)
                results[engine_name] = engine_results
            except Exception as e:
                self.logger.error(f"Error with {engine_name} search: {e}")
                results[engine_name] = []
        
        return results
    
    def get_search_url(self, query: str, engine: str = None) -> str:
        """Get direct search URL for query."""
        if engine is None:
            engine = self.default_engine
        
        if engine == 'google':
            return f"https://www.google.com/search?q={quote(query)}"
        elif engine == 'bing':
            return f"https://www.bing.com/search?q={quote(query)}"
        elif engine == 'duckduckgo':
            return f"https://duckduckgo.com/?q={quote(query)}"
        else:
            return f"https://www.google.com/search?q={quote(query)}"
    
    def parse_search_query(self, url: str) -> Optional[str]:
        """Parse search query from URL."""
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(url)
            
            if 'google.com' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                return query_params.get('q', [''])[0]
            elif 'bing.com' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                return query_params.get('q', [''])[0]
            elif 'duckduckgo.com' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                return query_params.get('q', [''])[0]
        
        except Exception as e:
            self.logger.error(f"Error parsing search query: {e}")
        
        return None
    
    def is_search_url(self, url: str) -> bool:
        """Check if URL is a search results page."""
        search_domains = [
            'google.com/search',
            'bing.com/search',
            'duckduckgo.com/',
            'yahoo.com/search',
            'baidu.com/s'
        ]
        
        return any(domain in url.lower() for domain in search_domains)
    
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get search history from backend."""
        try:
            # Get history entries that are search URLs
            response = requests.get('http://127.0.0.1:5000/api/history', params={'limit': limit}, timeout=5)
            
            if response.status_code == 200:
                history = response.json()
                search_history = []
                
                for entry in history:
                    url = entry.get('url', '')
                    if self.is_search_url(url):
                        query = self.parse_search_query(url)
                        if query:
                            search_history.append({
                                'query': query,
                                'url': url,
                                'title': entry.get('title', ''),
                                'last_visited': entry.get('last_visited', ''),
                                'visit_count': entry.get('visit_count', 1)
                            })
                
                return search_history
        
        except Exception as e:
            self.logger.error(f"Error getting search history: {e}")
        
        return []
    
    def get_popular_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular search queries."""
        queries = self.stats.get('popular_queries', {})
        
        # Sort by frequency
        sorted_queries = sorted(queries.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_queries[:limit]
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            'total_searches': self.stats['total_searches'],
            'searches_by_engine': self.stats['searches_by_engine'],
            'popular_queries': self.get_popular_queries(5),
            'available_engines': list(self.search_engines.keys()),
            'default_engine': self.default_engine,
            'last_search': self.stats.get('last_search')
        }
    
    def set_default_engine(self, engine: str) -> bool:
        """Set default search engine."""
        if engine in self.search_engines:
            self.default_engine = engine
            self.logger.info(f"Default search engine set to: {engine}")
            return True
        else:
            self.logger.warning(f"Search engine '{engine}' not available")
            return False
    
    def add_custom_engine(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a custom search engine."""
        try:
            # Create custom search engine
            class CustomSearch(SearchEngine):
                def __init__(self, name, config):
                    super().__init__(name, config)
                    self.search_url = config.get('search_url', '')
                    self.suggestions_url = config.get('suggestions_url', '')
                
                def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
                    # Implement custom search logic
                    return []
                
                def get_suggestions(self, query: str) -> List[str]:
                    # Implement custom suggestions logic
                    return []
            
            custom_engine = CustomSearch(name, config)
            self.search_engines[name] = custom_engine
            
            # Initialize statistics
            self.stats['searches_by_engine'][name] = 0
            
            self.logger.info(f"Added custom search engine: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding custom search engine: {e}")
            return False
    
    def remove_engine(self, engine: str) -> bool:
        """Remove a search engine."""
        if engine in self.search_engines:
            del self.search_engines[engine]
            
            if engine in self.stats['searches_by_engine']:
                del self.stats['searches_by_engine'][engine]
            
            if self.default_engine == engine:
                self.default_engine = list(self.search_engines.keys())[0] if self.search_engines else 'google'
            
            self.logger.info(f"Removed search engine: {engine}")
            return True
        
        return False
    
    def reset_statistics(self):
        """Reset search statistics."""
        self.stats = {
            'total_searches': 0,
            'searches_by_engine': {engine: 0 for engine in self.search_engines},
            'popular_queries': {},
            'last_search': None
        }
        
        self.logger.info("Reset search statistics")
    
    def export_search_data(self, file_path: str) -> bool:
        """Export search data for analysis."""
        try:
            data = {
                'statistics': self.stats,
                'search_history': self.get_search_history(100),
                'available_engines': list(self.search_engines.keys()),
                'default_engine': self.default_engine,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Exported search data to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting search data: {e}")
            return False
    
    def get_search_suggestions_with_metadata(self, query: str, engine: str = None) -> List[Dict[str, Any]]:
        """Get search suggestions with metadata."""
        suggestions = self.get_suggestions(query, engine)
        
        # Add metadata
        suggestions_with_metadata = []
        for i, suggestion in enumerate(suggestions):
            suggestions_with_metadata.append({
                'text': suggestion,
                'rank': i + 1,
                'engine': engine or self.default_engine,
                'query': query,
                'timestamp': datetime.now().isoformat()
            })
        
        return suggestions_with_metadata
