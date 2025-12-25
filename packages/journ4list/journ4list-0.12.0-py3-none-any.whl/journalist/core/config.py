"""
Configuration management for web scraping.
"""

import os
import json
from typing import Dict, Any, Optional


class ScrapingConfig:
    """Configuration class for web scraping operations."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize scraping configuration.
        
        Args:
            config_file: Path to external configuration file (optional)
        """
        # Load site selectors from external config or use defaults
        self.site_specific_selectors = self._load_site_selectors(config_file)
        
        self.generic_selectors = {
            "title_selector": "h1, h2, .article-title, .content-title, .news_title, [itemprop='headline']",
            "content_selector": "article, .article-body, .article-content, .content-text, .news_body, [itemprop='articleBody']",
            "date_selector": ".date, .time, .published, .pubdate, time, [itemprop='datePublished']",
            "image_selector": "img, .image, .thumbnail, [itemprop='image']",
            "author_selector": ".author, .writer, .reporter, [itemprop='author']"
        }        # HTTP settings
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.request_timeout = 5
        
        # Content quality thresholds
        self.min_body_length = 50
        self.min_title_length = 10
        self.high_quality_body_length = 500
        self.high_quality_title_length = 15
        
        # Suspicious content patterns to detect low-quality content
        self.suspicious_patterns = [
            'javascript required',
            'enable javascript',
            'cookie policy',
            'privacy policy',
            'terms of service'
        ]
        
        # Network and timeout settings
        self.http_timeout = 5
        self.max_retries = 3
    
    def _load_site_selectors(self, config_file: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Load site-specific selectors from external configuration.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Dictionary of site selectors
        """
        # Try to load from provided config file
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        # Try to load from default locations
        default_locations = [
            os.path.join(os.getcwd(), 'selectors.json'),
            os.path.join(os.path.dirname(__file__), 'selectors.json'),
            os.path.expanduser('~/.journalist/selectors.json'),
        ]
        
        for location in default_locations:
            if os.path.exists(location):
                try:
                    with open(location, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load config from {location}: {e}")
        
        # Return empty dict if no external config found
        # This means only generic selectors will be used
        return {}
    
    def add_site_selectors(self, domain: str, selectors: Dict[str, str]) -> None:
        """
        Dynamically add selectors for a new site.
        
        Args:
            domain: Domain name (e.g., 'example.com')
            selectors: Dictionary of selectors for the domain
        """
        self.site_specific_selectors[domain] = selectors
    
    def remove_site_selectors(self, domain: str) -> None:
        """
        Remove selectors for a site.
        
        Args:
            domain: Domain name to remove
        """
        if domain in self.site_specific_selectors:
            del self.site_specific_selectors[domain]
    
    def get_selectors_for_domain(self, domain: str) -> Dict[str, str]:
        """
        Get selectors for a specific domain.
        
        Args:
            domain: Domain name to get selectors for
            
        Returns:
            Dictionary of selectors for the domain
        """
        for site_domain, selectors in self.site_specific_selectors.items():
            if site_domain in domain.lower():
                return selectors
        return self.generic_selectors
    
    def get_request_headers(self) -> Dict[str, str]:
        """
        Get HTTP request headers.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": self.user_agent
        }