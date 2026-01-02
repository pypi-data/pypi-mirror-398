"""
Modular web scraper orchestrator that coordinates all scraping components.
"""

import logging
import asyncio
import json
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

from .config import ScrapingConfig
from .session_manager import SessionManager
from .link_discoverer import LinkDiscoverer
from .content_extractor import ContentExtractor
from .network_utils import normalize_url, is_valid_url

logger = logging.getLogger(__name__)


class WebScraper:
    """
    Modular web scraper that orchestrates all scraping components.
    
    Supports optional Browserless integration for JavaScript-heavy pages.
    """
    
    def __init__(
        self,
        browserless_url: Optional[str] = None,
        browserless_token: Optional[str] = None,
        max_scrolls: int = 20
    ):
        """
        Initialize the modular web scraper.
        
        Args:
            browserless_url: Optional URL of Browserless service for JS rendering
            browserless_token: Optional auth token for Browserless API
            max_scrolls: Max scroll iterations for infinite scroll pages (default: 20)
        """
        # Initialize components
        self.config = ScrapingConfig()
        
        # Pass browserless config to session manager
        self.session_manager = SessionManager(
            config=self.config,
            browserless_url=browserless_url,
            browserless_token=browserless_token,
            max_scrolls=max_scrolls
        )
        
        self.link_discoverer = LinkDiscoverer(max_concurrent_tasks=3, config=self.config)
        self.content_extractor = ContentExtractor(self.config)
        
        # Semaphores for concurrency control
        self.discover_semaphore = asyncio.Semaphore(3)
        self.scrape_semaphore = asyncio.Semaphore(5)
        
        browserless_status = "enabled" if self.session_manager.browserless_enabled else "disabled"
        logger.info("Modular web scraper initialized (Browserless: %s)", browserless_status)
    
    async def execute_scraping_for_session(self, session_id: str, keywords: List[str], 
                                         sites: Optional[List[str]] = None, scrape_depth: int = 1) -> Dict[str, Any]:
        """
        Execute complete scraping session with link discovery and content extraction
        
        Args:
            session_id: Unique identifier for this scraping session
            keywords: Keywords to search for
            sites: Optional list of specific sites to scrape
            scrape_depth: Depth level for link discovery:
                - 0: Only scrape the provided URLs directly (no link discovery)
                - 1: Scrape provided URLs + discover and scrape links from those pages
                - 2+: Continue recursive discovery
            
        Returns:
            Dict containing scraped articles and session metadata        """
        session_start = datetime.now()
        logger.info("Starting scraping session %s with keywords: %s, scrape_depth: %d", session_id, keywords, scrape_depth)
        
        try:
            # No session caching - always perform fresh scraping
            
            # Get sites to scrape
            target_sites = sites or list(self.config.site_specific_selectors.keys())
            
            # When scrape_depth=0, skip link discovery and scrape provided URLs directly
            if scrape_depth == 0:
                logger.info("scrape_depth=0: Skipping link discovery, will scrape %d provided URLs directly", len(target_sites))
                processed_links = []
                for site in target_sites:
                    normalized = normalize_url(site)
                    if is_valid_url(normalized):
                        if normalized not in processed_links:
                            processed_links.append(normalized)
                    else:
                        logger.warning(f"Skipping invalid provided URL: {site}")
            else:
                # Discover links (scrape_depth >= 1)
                all_links_raw = [] # Renamed to indicate raw links before processing
                async with self.session_manager: # SessionManager handles session start/stop
                    for site in target_sites:  # Sequential discovery per site for now
                        try:
                            # Pass scrape_depth - 1 to link discoverer since we're already at level 0 (the provided URLs)
                            site_links = await self._discover_links_for_site(site, keywords, scrape_depth - 1)
                            all_links_raw.extend(site_links)
                            logger.info("Discovered %d links from %s", len(site_links), site)
                        except Exception as e:
                            logger.error("Failed to discover links from %s: %s", site, e)

                if not all_links_raw:
                    logger.warning("No raw links discovered for session %s", session_id)
                    return {'articles': [], 'session_metadata': self._create_session_metadata(session_id, session_start, 0, 0)}
                
                logger.info("Total %d raw links discovered across all sites", len(all_links_raw))
                
                # Normalize and filter discovered links
                processed_links = []
                for link_info in all_links_raw: # Assuming _discover_links_for_site now returns list of dicts
                    url = link_info.get('url')
                    if not url:
                        logger.warning(f"Link info missing 'url': {link_info}")
                        continue
                    
                    normalized = normalize_url(url)
                    if is_valid_url(normalized):
                        if normalized not in processed_links: # Ensure uniqueness after normalization
                            processed_links.append(normalized)
                    else:
                        logger.warning(f"Skipping invalid or non-normalizable URL: {url} (normalized: {normalized})")

            if not processed_links:
                logger.warning(f"No valid links remaining after normalization and filtering for session {session_id}")
                return {'articles': [], 'session_metadata': self._create_session_metadata(session_id, session_start, 0, 0)}

            logger.info(f"Normalized and filtered to {len(processed_links)} unique, valid links.")
            
            # Scrape content from links (use session_manager context for HTTP sessions)
            scraped_articles = []
            async with self.session_manager:  # Ensure session is active for scraping
                tasks = [self._scrape_single_article(link, keywords, index + 1) for index, link in enumerate(processed_links)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result:
                    scraped_articles.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Scraping task failed: {result}")
            
            logger.info(f"Successfully scraped {len(scraped_articles)} articles out of {len(processed_links)} links")
            
            # Prepare session results (remove html_content for serialization)
            articles_for_serialization = [self._remove_html_content_for_serialization(article) for article in scraped_articles]
            session_data = {
                'articles': articles_for_serialization,
                'session_metadata': self._create_session_metadata(
                    session_id, session_start, len(processed_links), len(scraped_articles)                )
            }
            
            # No session data saving to cache - only workspace saving in persist mode handled by Journalist
            
            return session_data
            
        except Exception as e:
            logger.error(f"Scraping session {session_id} failed: {e}")
            return {
                'articles': [],
                'session_metadata': self._create_session_metadata(session_id, session_start, 0, 0),
                'error': str(e)
            }
    
    async def _discover_links_for_site(self, site: str, keywords: List[str], search_depth: int = 1) -> List[Dict[str, Any]]: # Return list of dicts
        """Discover links for a specific site using the LinkDiscoverer module."""
        async with self.discover_semaphore:
            session = await self.session_manager.get_session() # Explicitly get session
            if not session or session.closed:
                logger.error("Session not active or closed in SessionManager, cannot discover links.")
                return []            # Use the provided search_depth parameter instead of config
            # LinkDiscoverer.discover_links returns List[Dict[str, Any]]
            discovered_link_infos = await self.link_discoverer.discover_links(
                site_url=site,
                keywords=keywords,
                session=session, 
                search_depth=search_depth)
            
            # No need to extract just URLs here, return the full info
            # Normalization and validation will happen in execute_scraping_for_session
            return discovered_link_infos
    
    async def _scrape_single_article(self, url: str, keywords: List[str], article_index: int) -> Optional[Dict[str, Any]]:
        """
        Enhanced multi-strategy content extraction from a single article URL.
        Uses LD+JSON, readability-lxml, CSS selectors, and full page text as fallbacks.
        """
        
        original_url = url
        normalized_url = normalize_url(url)

        if not is_valid_url(normalized_url):
            logger.warning(f"Skipping scraping for invalid or non-normalizable URL: {original_url} (normalized: {normalized_url})")
            return None
            
        async with self.scrape_semaphore:
            try:
                # Fetch content directly (no cache)
                fetched_html_content = await self.session_manager.fetch_content(normalized_url)
                if not fetched_html_content:
                    logger.warning(f"Failed to fetch HTML content from {normalized_url}")
                    return None
                
                # Use the modular content extractor
                extracted_content = await self.content_extractor.extract_content(normalized_url, fetched_html_content)
                if not extracted_content:
                    logger.warning(f"Failed to extract quality content from {normalized_url}")
                    return None
                  # Prepare article data
                article_data = {
                    'url': normalized_url,
                    'scraped_at': datetime.now().isoformat(),
                    'keywords_used': keywords,
                    'title': extracted_content.get('title', ''),
                    'body': extracted_content.get('body', ''),
                    'published_at': extracted_content.get('published_at'),
                    'source': urlparse(normalized_url).netloc,
                    'html_content': fetched_html_content,
                    'extraction_method': extracted_content.get('extraction_method', 'unknown'),
                    'site': urlparse(normalized_url).netloc                }
                
                return article_data
                
            except Exception as e:
                logger.error(f"Failed to scrape article {normalized_url} (original: {original_url}): {e}")
                return None

    # LEGACY METHOD - COMMENTED OUT DURING MIGRATION
    # async def _extract_content_multi_strategy(self, article_url: str, html_content: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Enhanced multi-strategy content extraction with proper HTML entity decoding.
    #     
    #     Strategy 1: JSON-LD structured data
    #     Strategy 2: Readability-lxml (key improvement for HTML entity handling)  
    #     Strategy 3: CSS selectors (site-specific and generic)
    #     Strategy 4: Full page text cleanup (last resort)
    #     """
    #     # This method has been migrated to individual extractors in the modular architecture
    #     # Keeping commented for reference during migration validation
    #     pass
    
    def _remove_html_content_for_serialization(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove html_content field from article data for serialization to reduce file size.
        
        Args:
            article_data: Original article data dictionary
            
        Returns:
            Article data without html_content field        """
        # Create a copy to avoid modifying the original
        serialized_data = article_data.copy()
        serialized_data.pop('html_content', None)
        return serialized_data

    def _create_session_metadata(self, session_id: str, start_time: datetime,
                               links_found: int, articles_scraped: int) -> Dict[str, Any]:
        """Create session metadata"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'session_id': session_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'links_discovered': links_found,
            'articles_scraped': articles_scraped,
            'success_rate': articles_scraped / links_found if links_found > 0 else 0,
            'scraper_version': 'modular-v1.0'
        }
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the scraper configuration"""
        return {
            'supported_sites': list(self.config.site_specific_selectors.keys()),
            'extraction_strategies': self.content_extractor.get_extractor_info(),
            'http_timeout': self.config.http_timeout,
            'max_retries': self.config.max_retries        }
    
    def cleanup_old_data(self, session_days: int = 7, article_days: int = 30) -> Dict[str, int]:
        """Clean up old cached data - no longer used since cache is removed"""
        logger.info("cleanup_old_data called but cache functionality removed")
        return {
            'sessions_cleaned': 0,
            'articles_cleaned': 0
        }

    def _generate_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key for URL with optional parameters.
        
        Args:
            url: URL to generate key for
            params: Optional parameters to include in key
            
        Returns:
            Cache key string
        """
        key_data = {'url': url}
        if params:
            key_data.update(params)
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.session_manager.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.session_manager.__aexit__(exc_type, exc_val, exc_tb)

    def create_source_session_data(self, grouped_sources: Dict[str, Dict[str, Any]], session_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create source-specific session data structures.
        
        Args:
            grouped_sources: Articles grouped by source domain
            session_metadata: Metadata from scraping session
            
        Returns:
            List of source-specific session data dictionaries
        """
        try:
            source_session_data_list = []
            
            for domain, source_data in grouped_sources.items():
                # Create source-specific session data
                source_session_item = {
                    'source_domain': source_data['source_domain'],
                    'source_url': source_data['source_url'],
                    'articles': source_data['articles'],
                    'articles_count': source_data['articles_count'],
                    'saved_at': datetime.now().isoformat(),
                    'session_metadata': {
                        **session_metadata,
                        'source_specific': True,
                        'source_domain': domain,
                        'articles_scraped': source_data['articles_count']
                    }
                }
                
                source_session_data_list.append(source_session_item)
            
            return source_session_data_list
            
        except Exception as e:
            logger.error(f"Error creating source session data: {e}")
            return []