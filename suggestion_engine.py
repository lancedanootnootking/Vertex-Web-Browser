"""
AI Suggestion Engine

This module provides AI-powered website suggestions based on
browsing history, user preferences, and machine learning.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import pickle
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re
from collections import defaultdict, Counter


class SuggestionEngine:
    """AI-powered suggestion engine for website recommendations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enabled = config.get('enable_suggestions', True)
        self.provider = config.get('suggestion_provider', 'local')
        self.max_suggestions = config.get('max_suggestions', 5)
        self.cache_suggestions = config.get('cache_suggestions', True)
        self.learning_enabled = config.get('learning_enabled', True)
        
        # Data storage
        self.user_profile: Dict[str, Any] = {}
        self.browsing_patterns: Dict[str, Any] = {}
        self.suggestion_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Model data
        self.category_model: Dict[str, List[str]] = {}
        self.domain_popularity: Dict[str, float] = {}
        self.user_interests: Dict[str, float] = {}
        
        # Statistics
        self.stats = {
            'suggestions_generated': 0,
            'suggestions_accepted': 0,
            'accuracy_score': 0.0,
            'last_updated': datetime.now()
        }
        
        # Initialize models
        self.load_models()
        self.initialize_categories()
    
    def initialize_categories(self):
        """Initialize website categories for classification."""
        self.category_model = {
            'news': [
                'cnn.com', 'bbc.com', 'reuters.com', 'nytimes.com', 'washingtonpost.com',
                'theguardian.com', 'wsj.com', 'nbcnews.com', 'abcnews.go.com', 'cbsnews.com'
            ],
            'social': [
                'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'reddit.com',
                'tiktok.com', 'snapchat.com', 'pinterest.com', 'tumblr.com', 'discord.com'
            ],
            'entertainment': [
                'youtube.com', 'netflix.com', 'hulu.com', 'amazon.com/video', 'disneyplus.com',
                'spotify.com', 'twitch.tv', 'imdb.com', 'rottentomatoes.com', 'metacritic.com'
            ],
            'shopping': [
                'amazon.com', 'ebay.com', 'etsy.com', 'shopify.com', 'walmart.com',
                'target.com', 'bestbuy.com', 'home depot.com', 'lowes.com', 'costco.com'
            ],
            'technology': [
                'github.com', 'stackoverflow.com', 'medium.com', 'dev.to', 'hackernews.ycombinator.com',
                'techcrunch.com', 'wired.com', 'arstechnica.com', 'theverge.com', 'engadget.com'
            ],
            'education': [
                'coursera.org', 'edx.org', 'khanacademy.org', 'udemy.com', 'pluralsight.com',
                'wikipedia.org', 'mit.edu', 'stanford.edu', 'harvard.edu', 'berkeley.edu'
            ],
            'sports': [
                'espn.com', 'nfl.com', 'nba.com', 'mlb.com', 'nhl.com',
                'fifa.com', 'olympics.com', 'cbs.sports.com', 'foxsports.com', 'bleacherreport.com'
            ],
            'finance': [
                'yahoo.com/finance', 'bloomberg.com', 'reuters.com/business', 'marketwatch.com',
                'cnbc.com', 'fool.com', 'morningstar.com', 'zacks.com', 'seekingalpha.com'
            ],
            'health': [
                'webmd.com', 'mayoclinic.org', 'nih.gov', 'cdc.gov', 'healthline.com',
                'medicalnewstoday.com', 'medscape.com', 'everydayhealth.com', 'healthgrades.com'
            ],
            'travel': [
                'booking.com', 'expedia.com', 'airbnb.com', 'tripadvisor.com', 'kayak.com',
                'hotels.com', 'priceline.com', 'orbitz.com', 'travelocity.com', 'airbnb.com'
            ]
        }
        
        self.logger.info(f"Initialized {len(self.category_model)} website categories")
    
    def load_models(self):
        """Load pre-trained models and data."""
        try:
            # Load domain popularity data (simplified)
            self.domain_popularity = {
                'google.com': 0.95,
                'youtube.com': 0.92,
                'facebook.com': 0.90,
                'amazon.com': 0.88,
                'twitter.com': 0.85,
                'instagram.com': 0.83,
                'linkedin.com': 0.80,
                'reddit.com': 0.78,
                'wikipedia.org': 0.75,
                'netflix.com': 0.73
            }
            
            # Load user profile if exists
            profile_file = "user_profile.pkl"
            if os.path.exists(profile_file):
                with open(profile_file, 'rb') as f:
                    self.user_profile = pickle.load(f)
            
            self.logger.info("Loaded AI models and data")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            self.initialize_default_profile()
    
    def initialize_default_profile(self):
        """Initialize default user profile."""
        self.user_profile = {
            'interests': {},
            'frequent_categories': {},
            'time_patterns': {},
            'preferred_domains': {},
            'created_at': datetime.now(),
            'last_updated': datetime.now()
        }
    
    def get_suggestions(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions based on query and context."""
        if not self.enabled:
            return []
        
        self.stats['suggestions_generated'] += 1
        
        try:
            # Check cache first
            cache_key = self.generate_cache_key(query, context)
            if self.cache_suggestions and cache_key in self.suggestion_cache:
                return self.suggestion_cache[cache_key]
            
            suggestions = []
            
            # Generate suggestions based on provider
            if self.provider == 'local':
                suggestions = self.get_local_suggestions(query, context)
            elif self.provider == 'openai':
                suggestions = self.get_openai_suggestions(query, context)
            elif self.provider == 'google':
                suggestions = self.get_google_suggestions(query, context)
            else:
                suggestions = self.get_local_suggestions(query, context)
            
            # Rank and filter suggestions
            ranked_suggestions = self.rank_suggestions(suggestions, query, context)
            
            # Limit to max suggestions
            final_suggestions = ranked_suggestions[:self.max_suggestions]
            
            # Cache results
            if self.cache_suggestions:
                self.suggestion_cache[cache_key] = final_suggestions
            
            return final_suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return []
    
    def get_local_suggestions(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate suggestions using local AI models."""
        suggestions = []
        
        # Extract keywords from query
        keywords = self.extract_keywords(query)
        
        # Get suggestions from different sources
        suggestions.extend(self.get_history_suggestions(keywords, context))
        suggestions.extend(self.get_category_suggestions(keywords, context))
        suggestions.extend(self.get_popularity_suggestions(keywords, context))
        suggestions.extend(self.get_pattern_suggestions(keywords, context))
        
        return suggestions
    
    def get_openai_suggestions(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate suggestions using OpenAI API."""
        # Placeholder for OpenAI integration
        # In production, this would call OpenAI's API
        
        suggestions = []
        
        try:
            # This would be the actual OpenAI API call
            # For now, return fallback local suggestions
            suggestions = self.get_local_suggestions(query, context)
            
        except Exception as e:
            self.logger.error(f"Error with OpenAI suggestions: {e}")
            suggestions = self.get_local_suggestions(query, context)
        
        return suggestions
    
    def get_google_suggestions(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate suggestions using Google Search API."""
        # Placeholder for Google Search API integration
        
        suggestions = []
        
        try:
            # This would be the actual Google Search API call
            # For now, return fallback local suggestions
            suggestions = self.get_local_suggestions(query, context)
            
        except Exception as e:
            self.logger.error(f"Error with Google suggestions: {e}")
            suggestions = self.get_local_suggestions(query, context)
        
        return suggestions
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def get_history_suggestions(self, keywords: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions based on browsing history."""
        suggestions = []
        
        try:
            # Get recent history from backend
            import requests
            response = requests.get('http://127.0.0.1:5000/api/history', params={'limit': 50}, timeout=5)
            
            if response.status_code == 200:
                history = response.json()
                
                # Find related history entries
                for entry in history:
                    title = entry.get('title', '').lower()
                    url = entry.get('url', '')
                    
                    # Check if keywords match
                    if any(keyword in title for keyword in keywords):
                        score = self.calculate_relevance_score(keywords, title, entry)
                        
                        suggestions.append({
                            'type': 'history',
                            'title': entry.get('title', 'Untitled'),
                            'url': url,
                            'score': score,
                            'reason': 'Based on your browsing history',
                            'favicon': entry.get('favicon', ''),
                            'visit_count': entry.get('visit_count', 1)
                        })
        
        except Exception as e:
            self.logger.error(f"Error getting history suggestions: {e}")
        
        return suggestions
    
    def get_category_suggestions(self, keywords: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions based on website categories."""
        suggestions = []
        
        # Find matching categories
        matching_categories = []
        for category, domains in self.category_model.items():
            if any(keyword in category for keyword in keywords):
                matching_categories.append(category)
        
        # Get popular sites from matching categories
        for category in matching_categories:
            domains = self.category_model[category]
            
            for domain in domains[:5]:  # Top 5 from each category
                score = self.calculate_category_score(category, domain, keywords)
                
                suggestions.append({
                    'type': 'category',
                    'title': f"{category.title()} - {domain}",
                    'url': f"https://{domain}",
                    'score': score,
                    'reason': f'Popular {category} site',
                    'category': category,
                    'favicon': f"https://{domain}/favicon.ico"
                })
        
        return suggestions
    
    def get_popularity_suggestions(self, keywords: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions based on domain popularity."""
        suggestions = []
        
        # Sort domains by popularity
        sorted_domains = sorted(self.domain_popularity.items(), key=lambda x: x[1], reverse=True)
        
        for domain, popularity in sorted_domains[:10]:
            # Check if domain relates to keywords
            domain_keywords = domain.replace('.com', '').replace('.org', '').replace('.net', '').split('.')
            
            if any(keyword in ' '.join(domain_keywords) for keyword in keywords):
                suggestions.append({
                    'type': 'popularity',
                    'title': domain,
                    'url': f"https://{domain}",
                    'score': popularity,
                    'reason': 'Popular website',
                    'popularity': popularity,
                    'favicon': f"https://{domain}/favicon.ico"
                })
        
        return suggestions
    
    def get_pattern_suggestions(self, keywords: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions based on user browsing patterns."""
        suggestions = []
        
        if not self.learning_enabled:
            return suggestions
        
        # Analyze user patterns
        user_interests = self.user_profile.get('interests', {})
        frequent_categories = self.user_profile.get('frequent_categories', {})
        
        # Suggest based on user interests
        for interest, score in user_interests.items():
            if any(keyword in interest for keyword in keywords):
                suggestions.append({
                    'type': 'pattern',
                    'title': f"Explore {interest}",
                    'url': f"https://www.google.com/search?q={interest}",
                    'score': score * 0.8,
                    'reason': 'Based on your interests',
                    'interest': interest
                })
        
        return suggestions
    
    def calculate_relevance_score(self, keywords: List[str], text: str, entry: Dict[str, Any]) -> float:
        """Calculate relevance score for a suggestion."""
        score = 0.0
        
        # Keyword matching
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                score += 1.0
        
        # Visit count bonus
        visit_count = entry.get('visit_count', 1)
        score += min(visit_count / 10.0, 1.0)  # Cap at 1.0
        
        # Recency bonus
        last_visited = entry.get('last_visited')
        if last_visited:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_visited.replace('Z', '+00:00'))
                days_ago = (datetime.now() - dt).days
                score += max(0, 1.0 - days_ago / 30.0)  # Decay over 30 days
            except:
                pass
        
        return score
    
    def calculate_category_score(self, category: str, domain: str, keywords: List[str]) -> float:
        """Calculate score for category-based suggestions."""
        score = 0.5  # Base score
        
        # Category relevance
        if any(keyword in category for keyword in keywords):
            score += 0.3
        
        # Domain popularity
        score += self.domain_popularity.get(domain, 0.0) * 0.2
        
        return score
    
    def rank_suggestions(self, suggestions: List[Dict[str, Any]], query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank suggestions by relevance and quality."""
        # Remove duplicates
        seen_urls = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            url = suggestion.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_suggestions.append(suggestion)
        
        # Sort by score
        ranked = sorted(unique_suggestions, key=lambda x: x.get('score', 0), reverse=True)
        
        # Add ranking metadata
        for i, suggestion in enumerate(ranked):
            suggestion['rank'] = i + 1
            suggestion['confidence'] = min(suggestion.get('score', 0) / 2.0, 1.0)
        
        return ranked
    
    def generate_cache_key(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate cache key for suggestions."""
        import hashlib
        
        key_data = query.lower()
        if context:
            key_data += json.dumps(context, sort_keys=True)
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def learn_from_interaction(self, suggestion: Dict[str, Any], accepted: bool):
        """Learn from user interaction with suggestions."""
        if not self.learning_enabled:
            return
        
        try:
            # Update user interests
            title = suggestion.get('title', '')
            category = suggestion.get('category', '')
            
            if category:
                interests = self.user_profile.get('interests', {})
                current_score = interests.get(category, 0.0)
                
                if accepted:
                    interests[category] = min(current_score + 0.1, 1.0)
                    self.stats['suggestions_accepted'] += 1
                else:
                    interests[category] = max(current_score - 0.05, 0.0)
                
                self.user_profile['interests'] = interests
            
            # Update accuracy score
            total_suggestions = self.stats['suggestions_generated']
            accepted_suggestions = self.stats['suggestions_accepted']
            
            if total_suggestions > 0:
                self.stats['accuracy_score'] = accepted_suggestions / total_suggestions
            
            # Save updated profile
            self.save_user_profile()
            
        except Exception as e:
            self.logger.error(f"Error learning from interaction: {e}")
    
    def save_user_profile(self):
        """Save user profile to disk."""
        try:
            self.user_profile['last_updated'] = datetime.now()
            
            with open("user_profile.pkl", 'wb') as f:
                pickle.dump(self.user_profile, f)
            
        except Exception as e:
            self.logger.error(f"Error saving user profile: {e}")
    
    def update_browsing_patterns(self, history_data: List[Dict[str, Any]]):
        """Update browsing patterns from history data."""
        if not self.learning_enabled:
            return
        
        try:
            # Analyze time patterns
            time_patterns = defaultdict(int)
            category_patterns = defaultdict(int)
            domain_patterns = defaultdict(int)
            
            for entry in history_data:
                # Extract time pattern
                last_visited = entry.get('last_visited')
                if last_visited:
                    try:
                        dt = datetime.fromisoformat(last_visited.replace('Z', '+00:00'))
                        hour = dt.hour
                        time_patterns[hour] += 1
                    except:
                        pass
                
                # Extract category and domain patterns
                url = entry.get('url', '')
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                if domain:
                    domain_patterns[domain] += 1
                    
                    # Find category
                    for category, domains in self.category_model.items():
                        if any(d in domain for d in domains):
                            category_patterns[category] += 1
                            break
            
            # Update user profile
            self.user_profile['time_patterns'] = dict(time_patterns)
            self.user_profile['frequent_categories'] = dict(category_patterns)
            self.user_profile['preferred_domains'] = dict(domain_patterns)
            
            self.save_user_profile()
            
        except Exception as e:
            self.logger.error(f"Error updating browsing patterns: {e}")
    
    def get_personalized_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on user profile."""
        recommendations = []
        
        if not self.learning_enabled:
            return recommendations
        
        try:
            interests = self.user_profile.get('interests', {})
            frequent_categories = self.user_profile.get('frequent_categories', {})
            
            # Generate recommendations based on interests
            for interest, score in sorted(interests.items(), key=lambda x: x[1], reverse=True):
                if len(recommendations) >= limit:
                    break
                
                # Find related websites
                related_sites = self.find_related_sites(interest)
                
                for site in related_sites[:3]:  # Top 3 per interest
                    if len(recommendations) >= limit:
                        break
                    
                    recommendations.append({
                        'type': 'personalized',
                        'title': site['title'],
                        'url': site['url'],
                        'score': score * 0.9,
                        'reason': f'Based on your interest in {interest}',
                        'interest': interest
                    })
        
        except Exception as e:
            self.logger.error(f"Error getting personalized recommendations: {e}")
        
        return recommendations
    
    def find_related_sites(self, interest: str) -> List[Dict[str, Any]]:
        """Find sites related to a specific interest."""
        related_sites = []
        
        # Search in categories
        for category, domains in self.category_model.items():
            if interest.lower() in category.lower():
                for domain in domains[:5]:
                    related_sites.append({
                        'title': f"{category.title()} - {domain}",
                        'url': f"https://{domain}",
                        'category': category
                    })
        
        return related_sites
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get suggestion engine statistics."""
        return {
            'enabled': self.enabled,
            'provider': self.provider,
            'suggestions_generated': self.stats['suggestions_generated'],
            'suggestions_accepted': self.stats['suggestions_accepted'],
            'accuracy_score': round(self.stats['accuracy_score'], 3),
            'cache_size': len(self.suggestion_cache),
            'categories_count': len(self.category_model),
            'learning_enabled': self.learning_enabled,
            'user_interests_count': len(self.user_profile.get('interests', {})),
            'last_updated': self.stats['last_updated'].isoformat()
        }
    
    def clear_cache(self):
        """Clear suggestion cache."""
        self.suggestion_cache.clear()
        self.logger.info("Cleared suggestion cache")
    
    def reset_learning(self):
        """Reset learning data."""
        self.initialize_default_profile()
        self.save_user_profile()
        self.logger.info("Reset learning data")
    
    def export_model_data(self, file_path: str) -> bool:
        """Export model data for analysis."""
        try:
            data = {
                'user_profile': self.user_profile,
                'category_model': self.category_model,
                'domain_popularity': self.domain_popularity,
                'statistics': self.stats,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Exported model data to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting model data: {e}")
            return False
    
    def import_model_data(self, file_path: str) -> bool:
        """Import model data from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if 'user_profile' in data:
                self.user_profile = data['user_profile']
            
            if 'category_model' in data:
                self.category_model = data['category_model']
            
            if 'domain_popularity' in data:
                self.domain_popularity = data['domain_popularity']
            
            if 'statistics' in data:
                self.stats.update(data['statistics'])
            
            self.save_user_profile()
            self.logger.info(f"Imported model data from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing model data: {e}")
            return False
