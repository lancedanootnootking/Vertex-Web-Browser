#!/usr/bin/env python3.12
"""
Advanced Ad Blocker System for Vertex Browser

Comprehensive ad and tracker blocking with rule management, 
whitelisting, statistics, and real-time filtering.
Supports EasyList, EasyPrivacy, and custom filter rules.
"""

import re
import json
import gzip
import threading
import time
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import sqlite3
import weakref
import asyncio
from urllib.parse import urlparse

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit,
                             QFrame, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                             QProgressBar, QMessageBox, QDialog, QDialogButtonBox,
                             QFormLayout, QScrollArea, QSplitter, QMenu, QToolBar,
                             QToolButton, QFileDialog, QStatusBar, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QObject, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QKeySequence, QPalette

from frontend.themes.modern_theme import theme, style_manager, ui_components


class FilterType(Enum):
    """Filter rule types."""
    URL_BLOCK = "url_block"
    URL_WHITELIST = "url_whitelist"
    ELEMENT_HIDE = "element_hide"
    ELEMENT_HIDE_EXCEPTION = "element_hide_exception"
    CSS_INJECT = "css_inject"
    SCRIPT_INJECT = "script_inject"
    GENERATE_HIDE = "generate_hide"
    GENERATE_HIDE_EXCEPTION = "generate_hide_exception"


class RuleOption(Enum):
    """Rule options."""
    THIRD_PARTY = "third-party"
    FIRST_PARTY = "first-party"
    SCRIPT = "script"
    IMAGE = "image"
    STYLESHEET = "stylesheet"
    OBJECT = "object"
    OBJECT_SUBREQUEST = "object_subrequest"
    SUBDOCUMENT = "subdocument"
    XMLHTTPREQUEST = "xmlhttprequest"
    WEBSOCKET = "websocket"
    PING = "ping"
    MEDIA = "media"
    FONT = "font"
    POPUP = "popup"
    GENERICBLOCK = "genericblock"
    GENERICHIDE = "generichide"
    DOCUMENT = "document"
    ELEMHIDE = "elemhide"
    OTHER = "other"
    MATCH_CASE = "match-case"
    CSP = "csp"
    REPLACE = "replace"


@dataclass
class FilterRule:
    """Filter rule data structure."""
    id: str
    text: str
    type: FilterType
    options: Set[RuleOption]
    domains: Dict[str, bool]  # domain -> include/exclude
    selector: str = ""
    css_content: str = ""
    script_content: str = ""
    csp_directive: str = ""
    replace_content: str = ""
    enabled: bool = True
    hit_count: int = 0
    last_hit: Optional[datetime] = None
    source: str = "custom"
    priority: int = 0
    
    def __post_init__(self):
        if isinstance(self.options, list):
            self.options = set(self.options)


class BlockStatistics:
    """Blocking statistics."""
    
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.allowed_requests = 0
        self.blocked_by_type = {}
        self.blocked_by_domain = {}
        self.blocked_by_rule = {}
        self.start_time = datetime.now()
        self.session_stats = {
            'ads_blocked': 0,
            'trackers_blocked': 0,
            'malware_blocked': 0,
            'social_blocked': 0,
            'annoyances_blocked': 0
        }
    
    def record_request(self, url: str, blocked: bool, rule: FilterRule = None, request_type: str = "other"):
        """Record a request."""
        self.total_requests += 1
        
        if blocked:
            self.blocked_requests += 1
            
            # By type
            self.blocked_by_type[request_type] = self.blocked_by_type.get(request_type, 0) + 1
            
            # By domain
            domain = urlparse(url).netloc
            self.blocked_by_domain[domain] = self.blocked_by_domain.get(domain, 0) + 1
            
            # By rule
            if rule:
                self.blocked_by_rule[rule.id] = self.blocked_by_rule.get(rule.id, 0) + 1
                rule.hit_count += 1
                rule.last_hit = datetime.now()
            
            # Session stats
            if request_type in ["script", "image", "subdocument"]:
                self.session_stats['ads_blocked'] += 1
            elif "tracker" in url.lower() or "analytics" in url.lower():
                self.session_stats['trackers_blocked'] += 1
            elif "malware" in url.lower() or "virus" in url.lower():
                self.session_stats['malware_blocked'] += 1
            elif "facebook" in url.lower() or "twitter" in url.lower():
                self.session_stats['social_blocked'] += 1
            else:
                self.session_stats['annoyances_blocked'] += 1
        else:
            self.allowed_requests += 1
    
    def get_block_rate(self) -> float:
        """Get blocking rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_requests / self.total_requests) * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary."""
        runtime = datetime.now() - self.start_time
        
        return {
            'total_requests': self.total_requests,
            'blocked_requests': self.blocked_requests,
            'allowed_requests': self.allowed_requests,
            'block_rate': self.get_block_rate(),
            'runtime_hours': runtime.total_seconds() / 3600,
            'blocked_per_hour': self.blocked_requests / max(runtime.total_seconds() / 3600, 1),
            'top_blocked_domains': sorted(self.blocked_by_domain.items(), 
                                        key=lambda x: x[1], reverse=True)[:10],
            'top_blocked_types': sorted(self.blocked_by_type.items(), 
                                       key=lambda x: x[1], reverse=True),
            'session_stats': self.session_stats
        }


class RuleParser:
    """Parser for filter rules."""
    
    @staticmethod
    def parse_rule(rule_text: str) -> FilterRule:
        """Parse a filter rule."""
        rule_text = rule_text.strip()
        
        # Skip comments and empty lines
        if not rule_text or rule_text.startswith('!') or rule_text.startswith('#'):
            return None
        
        # Element hiding rules
        if rule_text.startswith('##'):
            return RuleParser._parse_element_hide(rule_text, FilterType.ELEMENT_HIDE)
        elif rule_text.startswith('#@#'):
            return RuleParser._parse_element_hide(rule_text, FilterType.ELEMENT_HIDE_EXCEPTION)
        elif rule_text.startswith('#?#'):
            return RuleParser._parse_element_hide(rule_text, FilterType.GENERATE_HIDE)
        elif rule_text.startswith('#@?#'):
            return RuleParser._parse_element_hide(rule_text, FilterType.GENERATE_HIDE_EXCEPTION)
        
        # URL blocking rules
        else:
            return RuleParser._parse_url_block(rule_text)
    
    @staticmethod
    def _parse_url_block(rule_text: str) -> FilterRule:
        """Parse URL blocking rule."""
        options = set()
        domains = {}
        selector = ""
        css_content = ""
        script_content = ""
        csp_directive = ""
        replace_content = ""
        
        # Check for exception
        is_exception = rule_text.startswith('@@')
        if is_exception:
            rule_type = FilterType.URL_WHITELIST
            rule_text = rule_text[2:]
        else:
            rule_type = FilterType.URL_BLOCK
        
        # Split rule and options
        parts = rule_text.split('$')
        pattern = parts[0]
        options_text = parts[1] if len(parts) > 1 else ""
        
        # Parse options
        if options_text:
            for option in options_text.split(','):
                option = option.strip()
                
                # Domain options
                if option.startswith('domain='):
                    domain_list = option[7:].split('|')
                    for domain in domain_list:
                        if domain.startswith('~'):
                            domains[domain[1:]] = False
                        else:
                            domains[domain] = True
                
                # Special options
                elif option in [opt.value for opt in RuleOption]:
                    options.add(RuleOption(option))
                
                # CSP directive
                elif option.startswith('csp='):
                    csp_directive = option[4:]
                    options.add(RuleOption.CSP)
                
                # Replace option
                elif option.startswith('replace='):
                    replace_content = option[8:]
                    options.add(RuleOption.REPLACE)
        
        # Generate rule ID
        rule_id = hashlib.md5(rule_text.encode()).hexdigest()[:16]
        
        return FilterRule(
            id=rule_id,
            text=rule_text,
            type=rule_type,
            options=options,
            domains=domains,
            selector=selector,
            css_content=css_content,
            script_content=script_content,
            csp_directive=csp_directive,
            replace_content=replace_content
        )
    
    @staticmethod
    def _parse_element_hide(rule_text: str, rule_type: FilterType) -> FilterRule:
        """Parse element hiding rule."""
        domains = {}
        selector = ""
        
        # Remove prefix
        if rule_type == FilterType.ELEMENT_HIDE:
            selector = rule_text[2:]
        elif rule_type == FilterType.ELEMENT_HIDE_EXCEPTION:
            selector = rule_text[3:]
        elif rule_type == FilterType.GENERATE_HIDE:
            selector = rule_text[3:]
        elif rule_type == FilterType.GENERATE_HIDE_EXCEPTION:
            selector = rule_text[4:]
        
        # Check for domain restrictions
        if '#' in selector:
            parts = selector.split('#')
            if len(parts) >= 2 and parts[0]:
                # Domain restrictions
                domain_list = parts[0].split(',')
                for domain in domain_list:
                    if domain.startswith('~'):
                        domains[domain[1:]] = False
                    else:
                        domains[domain] = True
                selector = '#'.join(parts[1:])
        
        # Generate rule ID
        rule_id = hashlib.md5(rule_text.encode()).hexdigest()[:16]
        
        return FilterRule(
            id=rule_id,
            text=rule_text,
            type=rule_type,
            options=set(),
            domains=domains,
            selector=selector
        )


class FilterList:
    """Filter list management."""
    
    def __init__(self, name: str, url: str = "", path: Path = None):
        self.name = name
        self.url = url
        self.path = path
        self.rules = []
        self.last_updated = None
        self.version = ""
        self.title = ""
        self.homepage = ""
        self.enabled = True
        self.metadata = {}
        
        if path and path.exists():
            self.load_from_file()
    
    def load_from_file(self):
        """Load rules from file."""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.parse_content(content)
            self.last_updated = datetime.now()
            
        except Exception as e:
            logging.error(f"Failed to load filter list {self.name}: {e}")
    
    def parse_content(self, content: str):
        """Parse filter list content."""
        lines = content.split('\n')
        self.rules = []
        
        for line in lines:
            rule = RuleParser.parse_rule(line)
            if rule:
                rule.source = self.name
                self.rules.append(rule)
    
    def update_from_url(self):
        """Update filter list from URL."""
        if not self.url:
            return False
        
        try:
            # Download content
            req = urllib.request.Request(self.url)
            req.add_header('User-Agent', 'Vertex Ad Blocker')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
            
            # Handle gzip compression
            if response.info().get('Content-Encoding') == 'gzip':
                content = gzip.decompress(content).decode('utf-8')
            else:
                content = content.decode('utf-8')
            
            # Parse content
            self.parse_content(content)
            
            # Save to file
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            self.last_updated = datetime.now()
            return True
            
        except Exception as e:
            logging.error(f"Failed to update filter list {self.name}: {e}")
            return False
    
    def get_enabled_rules(self) -> List[FilterRule]:
        """Get enabled rules."""
        return [rule for rule in self.rules if rule.enabled]


class AdBlockEngine:
    """Main ad blocking engine."""
    
    def __init__(self):
        self.filter_lists = {}
        self.url_block_rules = []
        self.url_whitelist_rules = []
        self.element_hide_rules = []
        self.element_hide_exceptions = []
        self.generate_hide_rules = []
        self.generate_hide_exceptions = []
        self.statistics = BlockStatistics()
        self.whitelist_domains = set()
        self.whitelist_pages = set()
        self.custom_css = ""
        self.custom_js = ""
        
        # Initialize default filter lists
        self._init_default_lists()
        
        # Load rules
        self.load_all_rules()
    
    def _init_default_lists(self):
        """Initialize default filter lists."""
        filter_dir = Path.home() / '.vertex_adblock'
        filter_dir.mkdir(exist_ok=True)
        
        # EasyList
        easylist = FilterList(
            "EasyList",
            "https://easylist.to/easylist/easylist.txt",
            filter_dir / "easylist.txt"
        )
        self.filter_lists["EasyList"] = easylist
        
        # EasyPrivacy
        easyprivacy = FilterList(
            "EasyPrivacy", 
            "https://easylist.to/easylist/easyprivacy.txt",
            filter_dir / "easyprivacy.txt"
        )
        self.filter_lists["EasyPrivacy"] = easyprivacy
        
        # Custom rules
        custom_list = FilterList(
            "Custom",
            path=filter_dir / "custom.txt"
        )
        self.filter_lists["Custom"] = custom_list
    
    def load_all_rules(self):
        """Load all rules from filter lists."""
        self.url_block_rules = []
        self.url_whitelist_rules = []
        self.element_hide_rules = []
        self.element_hide_exceptions = []
        self.generate_hide_rules = []
        self.generate_hide_exceptions = []
        
        for filter_list in self.filter_lists.values():
            if filter_list.enabled:
                rules = filter_list.get_enabled_rules()
                for rule in rules:
                    self._add_rule_to_collection(rule)
    
    def _add_rule_to_collection(self, rule: FilterRule):
        """Add rule to appropriate collection."""
        if rule.type == FilterType.URL_BLOCK:
            self.url_block_rules.append(rule)
        elif rule.type == FilterType.URL_WHITELIST:
            self.url_whitelist_rules.append(rule)
        elif rule.type == FilterType.ELEMENT_HIDE:
            self.element_hide_rules.append(rule)
        elif rule.type == FilterType.ELEMENT_HIDE_EXCEPTION:
            self.element_hide_exceptions.append(rule)
        elif rule.type == FilterType.GENERATE_HIDE:
            self.generate_hide_rules.append(rule)
        elif rule_type == FilterType.GENERATE_HIDE_EXCEPTION:
            self.generate_hide_exceptions.append(rule)
    
    def should_block_request(self, url: str, request_type: str = "other", 
                           source_url: str = "", referrer: str = "") -> Tuple[bool, Optional[FilterRule]]:
        """Check if request should be blocked."""
        # Check whitelist first
        if self._is_whitelisted(url, request_type, source_url):
            self.statistics.record_request(url, False, None, request_type)
            return False, None
        
        # Check whitelist rules
        for rule in self.url_whitelist_rules:
            if self._rule_matches_request(rule, url, request_type, source_url):
                self.statistics.record_request(url, False, rule, request_type)
                return False, rule
        
        # Check block rules
        for rule in self.url_block_rules:
            if self._rule_matches_request(rule, url, request_type, source_url):
                self.statistics.record_request(url, True, rule, request_type)
                return True, rule
        
        # Default: allow
        self.statistics.record_request(url, False, None, request_type)
        return False, None
    
    def _is_whitelisted(self, url: str, request_type: str, source_url: str) -> bool:
        """Check if URL is whitelisted."""
        # Check domain whitelist
        domain = urlparse(url).netloc
        if domain in self.whitelist_domains:
            return True
        
        # Check page whitelist
        if source_url:
            source_domain = urlparse(source_url).netloc
            if source_domain in self.whitelist_pages:
                return True
        
        return False
    
    def _rule_matches_request(self, rule: FilterRule, url: str, request_type: str, source_url: str) -> bool:
        """Check if rule matches request."""
        # Check domain restrictions
        if rule.domains:
            source_domain = urlparse(source_url).netloc if source_url else ""
            domain_match = False
            
            for domain, include in rule.domains.items():
                if domain in source_domain or source_domain.endswith('.' + domain):
                    if include:
                        domain_match = True
                    else:
                        return False
            
            if not domain_match:
                return False
        
        # Check URL pattern
        if not self._url_matches_pattern(url, rule.text):
            return False
        
        # Check options
        source_domain = urlparse(source_url).netloc if source_url else ""
        request_domain = urlparse(url).netloc
        
        for option in rule.options:
            if option == RuleOption.THIRD_PARTY:
                if source_domain == request_domain or request_domain.endswith('.' + source_domain):
                    return False
            elif option == RuleOption.FIRST_PARTY:
                if source_domain != request_domain and not request_domain.endswith('.' + source_domain):
                    return False
            elif option == RuleOption.SCRIPT and request_type != "script":
                return False
            elif option == RuleOption.IMAGE and request_type != "image":
                return False
            elif option == RuleOption.STYLESHEET and request_type != "stylesheet":
                return False
            elif option == RuleOption.SUBDOCUMENT and request_type != "subdocument":
                return False
            elif option == RuleOption.XMLHTTPREQUEST and request_type != "xmlhttprequest":
                return False
            elif option == RuleOption.WEBSOCKET and request_type != "websocket":
                return False
            elif option == RuleOption.MEDIA and request_type != "media":
                return False
            elif option == RuleOption.FONT and request_type != "font":
                return False
        
        return True
    
    def _url_matches_pattern(self, url: str, pattern: str) -> bool:
        """Check if URL matches pattern."""
        # Remove options and exceptions
        pattern = pattern.split('$')[0]
        pattern = pattern.replace('@@', '')
        
        # Wildcard matching
        if '*' in pattern:
            # Convert to regex
            regex_pattern = pattern.replace('*', '.*')
            regex_pattern = re.escape(regex_pattern).replace(r'\.*', '.*')
            regex_pattern = f'^{regex_pattern}$'
            return re.match(regex_pattern, url) is not None
        
        # Exact match or starts with
        if pattern.startswith('||'):
            # Domain anchor
            domain = pattern[2:]
            url_domain = urlparse(url).netloc
            return url_domain == domain or url_domain.endswith('.' + domain)
        elif pattern.startswith('|'):
            # Start anchor
            return url.startswith(pattern[1:])
        elif pattern.endswith('|'):
            # End anchor
            return url.endswith(pattern[:-1])
        else:
            # Contains
            return pattern in url
    
    def get_element_hiding_rules(self, url: str) -> List[str]:
        """Get element hiding rules for URL."""
        domain = urlparse(url).netloc
        selectors = []
        
        # Check exceptions first
        exceptions = []
        for rule in self.element_hide_exceptions:
            if self._domain_matches_rule(domain, rule.domains):
                exceptions.append(rule.selector)
        
        # Add rules that aren't excepted
        for rule in self.element_hide_rules:
            if self._domain_matches_rule(domain, rule.domains):
                if rule.selector not in exceptions:
                    selectors.append(rule.selector)
        
        # Add generate hide rules
        for rule in self.generate_hide_rules:
            if self._domain_matches_rule(domain, rule.domains):
                selectors.append(rule.selector)
        
        return selectors
    
    def _domain_matches_rule(self, domain: str, rule_domains: Dict[str, bool]) -> bool:
        """Check if domain matches rule domain restrictions."""
        if not rule_domains:
            return True
        
        for rule_domain, include in rule_domains.items():
            if domain == rule_domain or domain.endswith('.' + rule_domain):
                return include
        
        return False
    
    def get_custom_css(self) -> str:
        """Get custom CSS for injection."""
        css = self.custom_css
        
        # Add CSS from rules
        for rule in self.url_block_rules:
            if rule.css_content and RuleOption.CSP in rule.options:
                css += f"\n{rule.css_content}"
        
        return css
    
    def get_custom_js(self) -> str:
        """Get custom JavaScript for injection."""
        return self.custom_js
    
    def add_whitelist_domain(self, domain: str):
        """Add domain to whitelist."""
        self.whitelist_domains.add(domain)
    
    def remove_whitelist_domain(self, domain: str):
        """Remove domain from whitelist."""
        self.whitelist_domains.discard(domain)
    
    def add_whitelist_page(self, page: str):
        """Add page to whitelist."""
        self.whitelist_pages.add(page)
    
    def remove_whitelist_page(self, page: str):
        """Remove page from whitelist."""
        self.whitelist_pages.discard(page)
    
    def add_custom_rule(self, rule_text: str) -> bool:
        """Add custom rule."""
        rule = RuleParser.parse_rule(rule_text)
        if rule:
            rule.source = "Custom"
            custom_list = self.filter_lists["Custom"]
            custom_list.rules.append(rule)
            self._add_rule_to_collection(rule)
            return True
        return False
    
    def remove_custom_rule(self, rule_id: str) -> bool:
        """Remove custom rule."""
        custom_list = self.filter_lists["Custom"]
        for i, rule in enumerate(custom_list.rules):
            if rule.id == rule_id:
                custom_list.rules.pop(i)
                self.load_all_rules()
                return True
        return False
    
    def update_filter_lists(self) -> Dict[str, bool]:
        """Update all filter lists."""
        results = {}
        
        for name, filter_list in self.filter_lists.items():
            if filter_list.url:
                success = filter_list.update_from_url()
                results[name] = success
        
        # Reload rules
        self.load_all_rules()
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get blocking statistics."""
        return self.statistics.get_summary()
    
    def reset_statistics(self):
        """Reset statistics."""
        self.statistics = BlockStatistics()


class AdBlockRequestInterceptor(QObject):
    """Intercepts web requests for ad blocking."""
    
    request_blocked = pyqtSignal(str, str)  # url, rule_id
    
    def __init__(self, engine: AdBlockEngine):
        super().__init__()
        self.engine = engine
    
    def intercept_request(self, url: str, request_type: str = "other", 
                         source_url: str = "") -> bool:
        """Intercept and block request if needed."""
        blocked, rule = self.engine.should_block_request(url, request_type, source_url)
        
        if blocked and rule:
            self.request_blocked.emit(url, rule.id)
        
        return blocked


class AdBlockDatabase:
    """Database for ad blocker settings and statistics."""
    
    def __init__(self):
        self.db_path = Path.home() / '.vertex_adblock.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filter_lists (
                name TEXT PRIMARY KEY,
                url TEXT,
                path TEXT,
                enabled INTEGER,
                last_updated TEXT,
                version TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_rules (
                id TEXT PRIMARY KEY,
                text TEXT,
                enabled INTEGER,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                date TEXT PRIMARY KEY,
                total_requests INTEGER,
                blocked_requests INTEGER,
                blocked_domains TEXT,
                blocked_types TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,  -- domain, page
                value TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_filter_list(self, filter_list: FilterList):
        """Save filter list to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO filter_lists 
            (name, url, path, enabled, last_updated, version)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            filter_list.name,
            filter_list.url,
            str(filter_list.path) if filter_list.path else "",
            int(filter_list.enabled),
            filter_list.last_updated.isoformat() if filter_list.last_updated else "",
            filter_list.version
        ))
        
        conn.commit()
        conn.close()
    
    def save_custom_rule(self, rule: FilterRule):
        """Save custom rule to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO custom_rules 
            (id, text, enabled, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            rule.id,
            rule.text,
            int(rule.enabled),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def delete_custom_rule(self, rule_id: str):
        """Delete custom rule from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM custom_rules WHERE id = ?', (rule_id,))
        
        conn.commit()
        conn.close()
    
    def save_statistics(self, stats: Dict[str, Any]):
        """Save daily statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT OR REPLACE INTO statistics 
            (date, total_requests, blocked_requests, blocked_domains, blocked_types)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            today,
            stats['total_requests'],
            stats['blocked_requests'],
            json.dumps(stats['blocked_by_domain']),
            json.dumps(stats['blocked_by_type'])
        ))
        
        conn.commit()
        conn.close()
    
    def load_whitelist(self) -> Dict[str, Set[str]]:
        """Load whitelist from database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT type, value FROM whitelist')
        rows = cursor.fetchall()
        
        whitelist = {'domain': set(), 'page': set()}
        for row_type, value in rows:
            if row_type in whitelist:
                whitelist[row_type].add(value)
        
        conn.close()
        return whitelist
    
    def save_whitelist(self, whitelist: Dict[str, Set[str]]):
        """Save whitelist to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Clear existing
        cursor.execute('DELETE FROM whitelist')
        
        # Insert new
        for whitelist_type, values in whitelist.items():
            for value in values:
                cursor.execute('''
                    INSERT INTO whitelist (type, value, created_at)
                    VALUES (?, ?, ?)
                ''', (whitelist_type, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()


def show_ad_block_settings(parent=None):
    """Show ad blocker settings dialog."""
    from .ad_block_ui import AdBlockSettingsDialog
    dialog = AdBlockSettingsDialog(parent)
    dialog.show()
    return dialog
