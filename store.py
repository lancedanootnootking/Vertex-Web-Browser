#!/usr/bin/env python3
"""
Extension Store System

Comprehensive extension store with search, installation, updates,
and community features.
"""

import os
import json
import requests
import hashlib
import tempfile
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from urllib.parse import urljoin, urlparse
import zipfile
import shutil


class StoreCategory(Enum):
    """Extension store categories."""
    PRODUCTIVITY = "productivity"
    SOCIAL = "social"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    DEVELOPER = "developer"
    EDUCATION = "education"
    SHOPPING = "shopping"
    TOOLS = "tools"
    APPEARANCE = "appearance"
    PRIVACY = "privacy"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    PHOTOS = "photos"
    MUSIC = "music"
    VIDEOS = "videos"
    GAMES = "games"
    SPORTS = "sports"
    FINANCE = "finance"
    BUSINESS = "business"
    WEATHER = "weather"
    FOOD = "food"
    HEALTH = "health"
    TRAVEL = "travel"
    LIFESTYLE = "lifestyle"
    ART = "art"
    BOOKS = "books"
    REFERENCE = "reference"
    UTILITIES = "utilities"


class ExtensionStatus(Enum):
    """Extension status in store."""
    PUBLISHED = "published"
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    FEATURED = "featured"
    TRENDING = "trending"
    POPULAR = "popular"


class SortOrder(Enum):
    """Sort orders for search results."""
    RELEVANCE = "relevance"
    NAME = "name"
    RATING = "rating"
    DOWNLOADS = "downloads"
    UPDATED = "updated"
    CREATED = "created"
    PRICE = "price"


@dataclass
class StoreExtension:
    """Extension information from store."""
    id: str
    name: str
    short_name: str
    description: str
    full_description: str
    version: str
    author: Dict[str, Any]
    homepage_url: str
    support_url: str
    category: StoreCategory
    tags: List[str]
    status: ExtensionStatus
    featured: bool
    trending: bool
    
    # Statistics
    downloads: int
    weekly_downloads: int
    rating: float
    rating_count: int
    reviews: List[Dict[str, Any]]
    
    # Media
    screenshots: List[Dict[str, str]]
    icons: Dict[str, str]
    videos: List[Dict[str, str]]
    
    # Technical details
    manifest_version: int
    permissions: List[str]
    host_permissions: List[str]
    content_scripts: List[Dict[str, Any]]
    background_scripts: List[Dict[str, Any]]
    web_accessible_resources: List[Dict[str, Any]]
    
    # Store metadata
    created_at: datetime
    updated_at: datetime
    published_at: datetime
    size: int
    download_url: str
    checksum: str
    minimum_browser_version: str
    maximum_browser_version: Optional[str]
    
    # Pricing
    price: float = 0.0
    currency: str = "USD"
    free: bool = True
    
    # Compatibility
    compatible_platforms: List[str] = field(default_factory=list)
    
    # Security
    verified: bool = False
    signature_verified: bool = False
    security_scan_passed: bool = True
    
    # Localization
    available_locales: List[str] = field(default_factory=list)
    default_locale: str = "en"


@dataclass
class StoreReview:
    """Review for an extension."""
    id: str
    extension_id: str
    user_id: str
    username: str
    rating: int
    title: str
    content: str
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    version: str
    verified_purchase: bool = False
    developer_reply: Optional[Dict[str, Any]] = None


@dataclass
class SearchQuery:
    """Search query parameters."""
    query: str = ""
    category: Optional[StoreCategory] = None
    tags: List[str] = field(default_factory=list)
    status: List[ExtensionStatus] = field(default_factory=lambda: [ExtensionStatus.PUBLISHED])
    sort: SortOrder = SortOrder.RELEVANCE
    order: str = "desc"  # asc, desc
    min_rating: float = 0.0
    max_price: Optional[float] = None
    verified_only: bool = False
    featured_only: bool = False
    limit: int = 20
    offset: int = 0


@dataclass
class SearchResults:
    """Search results from store."""
    extensions: List[StoreExtension]
    total_count: int
    has_more: bool
    query: SearchQuery
    search_time: float
    suggestions: List[str] = field(default_factory=list)


class ExtensionStore:
    """Main extension store client."""
    
    def __init__(self, store_url: str = "https://extensions.browser.com/api/v1"):
        self.store_url = store_url
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Browser-Extension-Store/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Cache
        self.cache_dir = Path.home() / ".browser_extension_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_expiry = timedelta(hours=1)
        
        # Download tracking
        self.download_dir = Path.home() / "Downloads" / "Extensions"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Background update checker
        self.update_thread = None
        self.update_callbacks: List[Callable] = []
        
        # User preferences
        self.preferences_file = self.cache_dir / "store_preferences.json"
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading preferences: {e}")
        
        return {
            'auto_update': True,
            'update_check_interval': 24,  # hours
            'preferred_categories': [],
            'ignored_extensions': [],
            'installed_extensions': {},
            'favorite_extensions': []
        }
    
    def _save_preferences(self):
        """Save user preferences."""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")
    
    def search(self, query: SearchQuery) -> SearchResults:
        """Search for extensions."""
        start_time = time.time()
        
        try:
            # Build request parameters
            params = {
                'q': query.query,
                'limit': query.limit,
                'offset': query.offset,
                'sort': query.sort.value,
                'order': query.order,
                'min_rating': query.min_rating
            }
            
            if query.category:
                params['category'] = query.category.value
            
            if query.tags:
                params['tags'] = ','.join(query.tags)
            
            if query.status:
                params['status'] = ','.join([s.value for s in query.status])
            
            if query.max_price is not None:
                params['max_price'] = query.max_price
            
            if query.verified_only:
                params['verified'] = True
            
            if query.featured_only:
                params['featured'] = True
            
            # Make request
            response = self.session.get(
                urljoin(self.store_url, "/extensions/search"),
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse extensions
            extensions = []
            for ext_data in data.get('extensions', []):
                extensions.append(self._parse_store_extension(ext_data))
            
            # Create results
            results = SearchResults(
                extensions=extensions,
                total_count=data.get('total_count', 0),
                has_more=data.get('has_more', False),
                query=query,
                search_time=time.time() - start_time,
                suggestions=data.get('suggestions', [])
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching extensions: {e}")
            return SearchResults(
                extensions=[],
                total_count=0,
                has_more=False,
                query=query,
                search_time=time.time() - start_time
            )
    
    def get_extension(self, extension_id: str) -> Optional[StoreExtension]:
        """Get detailed information about an extension."""
        try:
            # Check cache first
            cache_file = self.cache_dir / f"extension_{extension_id}.json"
            if cache_file.exists():
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - cache_time < self.cache_expiry:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    return self._parse_store_extension(data)
            
            # Fetch from store
            response = self.session.get(
                urljoin(self.store_url, f"/extensions/{extension_id}"),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            extension = self._parse_store_extension(data)
            
            # Cache result
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return extension
            
        except Exception as e:
            self.logger.error(f"Error getting extension {extension_id}: {e}")
            return None
    
    def get_reviews(self, extension_id: str, limit: int = 20, 
                   offset: int = 0, sort: str = "newest") -> List[StoreReview]:
        """Get reviews for an extension."""
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'sort': sort
            }
            
            response = self.session.get(
                urljoin(self.store_url, f"/extensions/{extension_id}/reviews"),
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            reviews = []
            
            for review_data in data.get('reviews', []):
                reviews.append(self._parse_store_review(review_data))
            
            return reviews
            
        except Exception as e:
            self.logger.error(f"Error getting reviews for {extension_id}: {e}")
            return []
    
    def get_featured(self, limit: int = 10) -> List[StoreExtension]:
        """Get featured extensions."""
        query = SearchQuery(
            featured_only=True,
            limit=limit,
            sort=SortOrder.RATING
        )
        results = self.search(query)
        return results.extensions
    
    def get_trending(self, limit: int = 10) -> List[StoreExtension]:
        """Get trending extensions."""
        query = SearchQuery(
            trending_only=True,
            limit=limit,
            sort=SortOrder.DOWNLOADS
        )
        results = self.search(query)
        return results.extensions
    
    def get_popular(self, category: Optional[StoreCategory] = None, 
                   limit: int = 10) -> List[StoreExtension]:
        """Get popular extensions."""
        query = SearchQuery(
            category=category,
            limit=limit,
            sort=SortOrder.DOWNLOADS
        )
        results = self.search(query)
        return results.extensions
    
    def get_categories(self) -> Dict[StoreCategory, Dict[str, Any]]:
        """Get available categories with counts."""
        try:
            response = self.session.get(
                urljoin(self.store_url, "/categories"),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            categories = {}
            
            for cat_data in data.get('categories', []):
                category = StoreCategory(cat_data['id'])
                categories[category] = {
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'extension_count': cat_data['extension_count'],
                    'icon': cat_data.get('icon')
                }
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            return {}
    
    def download_extension(self, extension_id: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """Download an extension."""
        try:
            # Get extension info
            extension = self.get_extension(extension_id)
            if not extension:
                return False, "Extension not found"
            
            # Determine download URL
            if version:
                download_url = urljoin(self.store_url, f"/extensions/{extension_id}/download/{version}")
            else:
                download_url = extension.download_url
            
            # Download file
            response = self.session.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            content_disposition = response.headers.get('content-disposition', '')
            filename = f"{extension.id}-{extension.version}.crx"
            
            if 'filename=' in content_disposition:
                filename = re.search(r'filename="?([^"]+)"?', content_disposition).group(1)
            
            download_path = self.download_dir / filename
            
            # Download with progress tracking
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            # Verify checksum
            if extension.checksum:
                file_hash = self._calculate_file_hash(download_path)
                if file_hash != extension.checksum:
                    download_path.unlink()
                    return False, "Checksum verification failed"
            
            # Update preferences
            self.preferences['installed_extensions'][extension_id] = {
                'version': extension.version,
                'installed_at': datetime.now().isoformat(),
                'download_path': str(download_path)
            }
            self._save_preferences()
            
            self.logger.info(f"Downloaded extension {extension_id} to {download_path}")
            return True, str(download_path)
            
        except Exception as e:
            error_msg = f"Error downloading extension {extension_id}: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def install_extension(self, extension_id: str, version: Optional[str] = None, 
                         auto_enable: bool = True) -> Tuple[bool, str]:
        """Download and install an extension."""
        # Download extension
        success, result = self.download_extension(extension_id, version)
        if not success:
            return False, result
        
        download_path = result
        
        # Install using loader
        try:
            from .loader import ExtensionLoader
            # This would be injected or passed in
            # loader = ExtensionLoader(browser_instance)
            # return loader.install_extension(download_path, auto_enable)
            
            # For now, just return the download path
            return True, f"Extension downloaded to {download_path}. Manual installation required."
            
        except Exception as e:
            error_msg = f"Error installing extension: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def check_updates(self) -> List[Dict[str, Any]]:
        """Check for updates to installed extensions."""
        updates = []
        
        for extension_id, info in self.preferences['installed_extensions'].items():
            try:
                # Get latest version from store
                extension = self.get_extension(extension_id)
                if not extension:
                    continue
                
                # Compare versions
                if self._is_newer_version(extension.version, info['version']):
                    updates.append({
                        'extension_id': extension_id,
                        'name': extension.name,
                        'current_version': info['version'],
                        'latest_version': extension.version,
                        'size': extension.size,
                        'release_notes': extension.full_description,
                        'download_url': extension.download_url
                    })
            
            except Exception as e:
                self.logger.error(f"Error checking updates for {extension_id}: {e}")
        
        return updates
    
    def update_extension(self, extension_id: str) -> Tuple[bool, str]:
        """Update an extension."""
        try:
            # Get current info
            if extension_id not in self.preferences['installed_extensions']:
                return False, "Extension not installed"
            
            current_info = self.preferences['installed_extensions'][extension_id]
            
            # Download latest version
            success, result = self.download_extension(extension_id)
            if not success:
                return False, result
            
            # Update installation
            self.preferences['installed_extensions'][extension_id].update({
                'version': self.get_extension(extension_id).version,
                'updated_at': datetime.now().isoformat(),
                'download_path': result
            })
            self._save_preferences()
            
            return True, f"Extension {extension_id} updated successfully"
            
        except Exception as e:
            error_msg = f"Error updating extension {extension_id}: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def submit_review(self, extension_id: str, rating: int, title: str, 
                     content: str) -> Tuple[bool, str]:
        """Submit a review for an extension."""
        try:
            data = {
                'extension_id': extension_id,
                'rating': rating,
                'title': title,
                'content': content
            }
            
            response = self.session.post(
                urljoin(self.store_url, f"/extensions/{extension_id}/reviews"),
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            return True, "Review submitted successfully"
            
        except Exception as e:
            error_msg = f"Error submitting review: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def report_extension(self, extension_id: str, reason: str, 
                         description: str) -> Tuple[bool, str]:
        """Report an extension for policy violation."""
        try:
            data = {
                'extension_id': extension_id,
                'reason': reason,
                'description': description
            }
            
            response = self.session.post(
                urljoin(self.store_url, f"/extensions/{extension_id}/report"),
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            return True, "Extension reported successfully"
            
        except Exception as e:
            error_msg = f"Error reporting extension: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _parse_store_extension(self, data: Dict[str, Any]) -> StoreExtension:
        """Parse extension data from store."""
        return StoreExtension(
            id=data['id'],
            name=data['name'],
            short_name=data.get('short_name', ''),
            description=data['description'],
            full_description=data.get('full_description', ''),
            version=data['version'],
            author=data['author'],
            homepage_url=data.get('homepage_url', ''),
            support_url=data.get('support_url', ''),
            category=StoreCategory(data['category']),
            tags=data.get('tags', []),
            status=ExtensionStatus(data['status']),
            featured=data.get('featured', False),
            trending=data.get('trending', False),
            downloads=data.get('downloads', 0),
            weekly_downloads=data.get('weekly_downloads', 0),
            rating=data.get('rating', 0.0),
            rating_count=data.get('rating_count', 0),
            reviews=[self._parse_store_review(r) for r in data.get('reviews', [])],
            screenshots=data.get('screenshots', []),
            icons=data.get('icons', {}),
            videos=data.get('videos', []),
            manifest_version=data.get('manifest_version', 2),
            permissions=data.get('permissions', []),
            host_permissions=data.get('host_permissions', []),
            content_scripts=data.get('content_scripts', []),
            background_scripts=data.get('background_scripts', []),
            web_accessible_resources=data.get('web_accessible_resources', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            published_at=datetime.fromisoformat(data['published_at']),
            size=data.get('size', 0),
            download_url=data['download_url'],
            checksum=data.get('checksum', ''),
            minimum_browser_version=data.get('minimum_browser_version', '1.0.0'),
            maximum_browser_version=data.get('maximum_browser_version'),
            price=data.get('price', 0.0),
            currency=data.get('currency', 'USD'),
            free=data.get('free', True),
            compatible_platforms=data.get('compatible_platforms', []),
            verified=data.get('verified', False),
            signature_verified=data.get('signature_verified', False),
            security_scan_passed=data.get('security_scan_passed', True),
            available_locales=data.get('available_locales', []),
            default_locale=data.get('default_locale', 'en')
        )
    
    def _parse_store_review(self, data: Dict[str, Any]) -> StoreReview:
        """Parse review data from store."""
        return StoreReview(
            id=data['id'],
            extension_id=data['extension_id'],
            user_id=data['user_id'],
            username=data['username'],
            rating=data['rating'],
            title=data['title'],
            content=data['content'],
            helpful_count=data.get('helpful_count', 0),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            version=data['version'],
            verified_purchase=data.get('verified_purchase', False),
            developer_reply=data.get('developer_reply')
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Compare version strings."""
        try:
            def version_tuple(v):
                return tuple(map(int, (v.split("."))))
            
            return version_tuple(new_version) > version_tuple(current_version)
        except:
            return new_version != current_version
    
    def start_update_checker(self):
        """Start background update checker."""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.update_thread = threading.Thread(target=self._update_checker_loop, daemon=True)
        self.update_thread.start()
    
    def stop_update_checker(self):
        """Stop background update checker."""
        self.update_thread = None
    
    def _update_checker_loop(self):
        """Background update checker loop."""
        while True:
            try:
                if self.preferences.get('auto_update', True):
                    updates = self.check_updates()
                    
                    if updates:
                        for callback in self.update_callbacks:
                            try:
                                callback(updates)
                            except Exception as e:
                                self.logger.error(f"Error in update callback: {e}")
                
                # Sleep for configured interval
                interval = self.preferences.get('update_check_interval', 24) * 3600
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in update checker: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def add_update_callback(self, callback: Callable):
        """Add callback for update notifications."""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable):
        """Remove update callback."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
