import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from .core.web_scraper import WebScraper
from .core.file_manager import FileManager
from .config import JournalistConfig

logger = logging.getLogger(__name__)

class Journalist:
    def __init__(
        self, 
        persist: bool = True, 
        scrape_depth: int = 1,
        browserless_url: Optional[str] = None,
        browserless_token: Optional[str] = None,
        max_scrolls: int = 20
    ):
        """
        Initialize the Journalist.

        Args:
            persist (bool): If True, create filesystem workspace and save data.
                           If False, operate in memory only without file persistence.
            scrape_depth (int): Depth level for link discovery (default: 1)
            browserless_url (str, optional): URL of Browserless service for JS-heavy pages.
                           Enables headless Chrome rendering for infinite scroll pages.
                           Requires browserless_token to be set as well.
            browserless_token (str, optional): Authentication token for Browserless API.
                           Required when browserless_url is provided.
            max_scrolls (int): Maximum scroll iterations for infinite scroll pages (default: 20).
                           Only used when Browserless is enabled.
        """
        # Generate session_id like in original routes.py
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Store parameters
        self.persist = persist
        self.scrape_depth = scrape_depth
        self.browserless_url = browserless_url
        self.browserless_token = browserless_token
        self.max_scrolls = max_scrolls
        
        # Initialize in-memory storage attributes for type safety
        self.memory_articles = []
        
        # Initialize the web scraper with browserless config
        self.web_scraper = WebScraper(
            browserless_url=browserless_url,
            browserless_token=browserless_token,
            max_scrolls=max_scrolls
        )

        if self.persist:
            # Setup persistent workspace
            self._setup_persistent_workspace()
        else:
            # Setup in-memory storage
            self._setup_memory_storage()
        
        browserless_status = "enabled" if browserless_url and browserless_token else "disabled"
        logger.info(
            "Journalist initialized with session_id: %s, persist: %s, scrape_depth: %s, browserless: %s", 
            self.session_id, persist, scrape_depth, browserless_status
        )

    def _setup_persistent_workspace(self):
        """Setup persistent filesystem workspace"""
        # Get configuration from central config
        self.base_workspace_path = JournalistConfig.get_base_workspace_path()
        
        # Setup session paths
        self.session_path = os.path.join(self.base_workspace_path, self.session_id)
          # Initialize FileManager (it will create its own directories)
        self.file_manager = FileManager(self.session_path)

    def _setup_memory_storage(self):
        """Setup in-memory storage for non-persistent mode"""
        # No filesystem paths needed
        self.session_path = None
        self.news_from_scraping_path = None
        self.file_manager = None
        
        # Initialize in-memory storage
        self.memory_articles = []

    def _filter_articles_by_date(self, articles: List[Dict[str, Any]], max_age_days: int = 7) -> List[Dict[str, Any]]:
        """
        Filter articles by date, removing articles older than max_age_days.
        
        Args:
            articles: List of article dictionaries
            max_age_days: Maximum age in days (default: 7)
            
        Returns:
            List of articles that are not too old
        """
        filtered_articles = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for article in articles:
            try:
                # Check URL for dates using datefinder
                article_url = article.get('url', '')
                is_url_old = False
                
                if article_url:
                    # Import datefinder here to avoid issues if not installed
                    try:
                        import datefinder
                        url_dates = list(datefinder.find_dates(article_url))
                        for date in url_dates:
                            if isinstance(date, datetime) and date < cutoff_date:
                                is_url_old = True
                                logger.debug(f"Filtering out old URL (date: {date.strftime('%Y-%m-%d')}): {article_url}")
                                break
                    except ImportError:
                        logger.warning("datefinder not available, skipping URL date filtering")
                
                # If URL indicates it's old, skip this article
                if is_url_old:
                    continue
                
                # Check published_at metadata
                published_at = article.get('published_at')
                if published_at:
                    try:                        # Parse the published_at field (should be ISO format from extractors)
                        if isinstance(published_at, str):
                            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        elif isinstance(published_at, datetime):
                            pub_date = published_at
                        else:
                            pub_date = None
                        
                        if pub_date:
                            # Make both dates timezone-naive for comparison
                            if pub_date.tzinfo is not None:
                                # Convert timezone-aware to UTC then remove timezone info
                                pub_date_naive = pub_date.utctimetuple()
                                pub_date_naive = datetime(*pub_date_naive[:6])
                            else:
                                pub_date_naive = pub_date
                            
                            if pub_date_naive < cutoff_date:
                                logger.debug(f"Filtering out old article (published: {pub_date.strftime('%Y-%m-%d')}): {article_url}")
                                continue
                            
                    except Exception as e:
                        logger.debug(f"Could not parse published_at '{published_at}' for {article_url}: {e}")
                  # Article passed all filters
                filtered_articles.append(article)
                
            except Exception as e:
                logger.warning(f"Error filtering article {article.get('url', 'unknown')}: {e}")
                # Include article if filtering fails
                filtered_articles.append(article)
        
        logger.info(f"Date filtering: {len(articles)} articles -> {len(filtered_articles)} articles (removed {len(articles) - len(filtered_articles)} old articles)")
        
        # Debug: Log details about filtered articles
        for article in filtered_articles:
            logger.debug(f"Article kept: {article.get('url', 'no-url')} - published_at: {article.get('published_at', 'no-date')}")
        
        return filtered_articles

    def _group_articles_by_source(self, articles: List[Dict[str, Any]], original_urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Group articles by their source domain, ensuring each original URL has an entry.
        
        Args:
            articles: List of article dictionaries
            original_urls: List of original URLs provided by user
            
        Returns:
            Dictionary mapping domain names to source data with articles
        """
        try:
            # Import here to avoid circular imports
            from .core.network_utils import get_domain
            
            grouped_sources = {}
            
            # Initialize all domains from original URLs first
            for orig_url in original_urls:
                domain = get_domain(orig_url)
                if not domain:
                    domain = f'unknown_{len(grouped_sources)}'
                
                if domain not in grouped_sources:
                    grouped_sources[domain] = {
                        'source_domain': domain,
                        'source_url': orig_url,
                        'articles': [],
                        'articles_count': 0
                    }
            
            # Now group articles into existing domains
            for article in articles:
                # Get article URL
                article_url = article.get('url', '')
                
                if not article_url:
                    # If no URL, assign to first available domain
                    if original_urls:
                        domain = get_domain(original_urls[0])
                    else:
                        domain = 'unknown'
                else:
                    domain = get_domain(article_url)
                
                if not domain:
                    domain = 'unknown'
                
                # Find matching domain or create unknown entry
                if domain not in grouped_sources:
                    # This handles cases where articles come from domains not in original URLs
                    grouped_sources[domain] = {
                        'source_domain': domain,
                        'source_url': article_url if article_url else domain,
                        'articles': [],
                        'articles_count': 0
                    }
               
                # Add article to appropriate domain group
                grouped_sources[domain]['articles'].append(article)
                grouped_sources[domain]['articles_count'] += 1
              # Log grouping results
            for domain, source_data in grouped_sources.items():
                logger.info(f"Grouped {source_data['articles_count']} articles for domain: {domain}")
            
            return grouped_sources
            
        except Exception as e:
            logger.error(f"Error grouping articles by source: {e}")
            # Fallback: ensure we have at least one entry per original URL
            fallback_sources = {}
            for i, orig_url in enumerate(original_urls):
                domain = f'unknown_{i}'
                fallback_sources[domain] = {
                    'source_domain': domain,
                    'source_url': orig_url,
                    'articles': articles,
                    'articles_count': len(articles)
                }
            return fallback_sources

    def process_articles(
        self, 
        scraped_articles: List[Dict[str, Any]], 
        original_urls: List[str],
        session_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process articles with filtering, saving, and source segregation.
        
        Always returns the same data structure regardless of persistence mode.
        
        Args:
            scraped_articles: Raw articles from web scraper
            original_urls: Original URLs provided by user for source identification
            session_metadata: Metadata from scraping session
            
        Returns:
            List of source-specific session data dictionaries
        """
        try:
            # 1. Filter articles by date
            filtered_articles = self._filter_articles_by_date(scraped_articles)
            
            # 2. Group articles by source
            grouped_sources = self._group_articles_by_source(filtered_articles, original_urls)
            
            # 3. Create source-specific session data (delegated to WebScraper)
            source_session_data_list = self.web_scraper.create_source_session_data(grouped_sources, session_metadata)
            
            # 4. Handle persistence (if enabled)
            if self.persist and self.file_manager:
                # Save individual articles (delegated to FileManager)
                self.file_manager.save_individual_articles(filtered_articles)
                
                # Save source-specific session data files (delegated to FileManager)
                saved_files = self.file_manager.save_source_session_files(source_session_data_list)
                logger.info(f"Saved {len(saved_files)} source session files: {saved_files}")
            else:
                # Store in memory for non-persistent mode
                self.memory_articles.extend(filtered_articles)
              # 5. Always return the same structure
            return source_session_data_list
            
        except Exception as e:
            logger.error(f"Error processing articles: {e}")
            return []

    async def read(self, urls: List[str], keywords: Optional[List[str]] = None, log_level: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract content from the provided URLs with optional keyword filtering.
        
        Args:
            urls: List of website URLs to process
            keywords: Optional list of keywords for relevance filtering
            log_level: Optional logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            
        Returns:
            Dictionary containing extracted articles and metadata        """        # Store original log level and set new one if provided
        original_log_level = None
        if log_level:
            original_log_level = logger.level
            try:
                # Convert string to logging level constant
                numeric_level = getattr(logging, log_level.upper())
                logger.setLevel(numeric_level)                # Also set level for all related loggers using correct module paths
                logging.getLogger('src.journalist.core').setLevel(numeric_level)
                logging.getLogger('src.journalist.extractors').setLevel(numeric_level)
                logging.getLogger('src.journalist.config').setLevel(numeric_level)
                # Set for all child loggers too
                logging.getLogger('src.journalist.core.session_manager').setLevel(numeric_level)
                logging.getLogger('src.journalist.core.web_scraper').setLevel(numeric_level)
                logging.getLogger('src.journalist.core.link_discoverer').setLevel(numeric_level)
                logging.getLogger('src.journalist.core.file_manager').setLevel(numeric_level)
                logging.getLogger('src.journalist.core.content_extractor').setLevel(numeric_level)
                logger.info(f"Log level set to {log_level.upper()} for this session")
            except AttributeError:
                logger.warning(f"Invalid log level '{log_level}', using default level")
        
        try:
            if not urls:
                # Return empty result for empty URL list instead of raising error
                return {
                    'articles': [],
                    'session_metadata': {
                        'session_id': self.session_id,
                        'total_articles': 0,
                        'total_links_processed': 0,
                        'keywords_used': keywords or [],
                        'scrape_depth': self.scrape_depth,
                        'persist_mode': self.persist
                    }
                }
              # Use instance session_id and prepare parameters
            session_id = self.session_id
            keywords_for_session = keywords or []
            scrape_urls_for_session = urls
            
            # Important logging block from original
            start_time = time.time()
            logger.info("Session [%s]: Starting content extraction for %d URLs", session_id, len(urls))
            logger.info("Session [%s]: URLs: %s", session_id, scrape_urls_for_session)
            
            if keywords:
                logger.info("Session [%s]: Using keywords for filtering: %s", session_id, keywords)            
            # Create tasks for parallel execution
            tasks = []

            # Task 1: Web scraping (if URLs provided)
            if scrape_urls_for_session:
                logger.info("Session [%s]: Creating web scraping task for URLs: %s", session_id, scrape_urls_for_session)
                # Use the web scraper as an async context manager to ensure proper session cleanup
                async def web_scrape_with_context():
                    async with self.web_scraper:
                        return await self.web_scraper.execute_scraping_for_session(
                            session_id=session_id,
                            keywords=keywords_for_session,
                            sites=scrape_urls_for_session,
                            scrape_depth=self.scrape_depth
                        )
                
                web_scrape_task = asyncio.create_task(web_scrape_with_context())
                tasks.append(('web_scrape', web_scrape_task))
            else:
                logger.info("Session [%s]: No URLs provided for scraping.", session_id)# Initialize return values
            articles = []
            
            # Execute tasks in parallel if any exist
            if tasks:
                logger.info("Session [%s]: Executing %d tasks in parallel: %s", session_id, len(tasks), [task[0] for task in tasks])
                
                # Extract just the task objects for gather
                task_objects = [task[1] for task in tasks]
                results = await asyncio.gather(*task_objects, return_exceptions=True)
                
                # Process results based on task type
                for i, (task_type, _) in enumerate(tasks):
                    result = results[i]
                    
                    if isinstance(result, Exception):
                        logger.error("Session [%s]: Error in %s task: %s", session_id, task_type, result, exc_info=True)
                    else:
                        if task_type == 'web_scrape':
                            # New modular WebScraper returns session data with articles and metadata
                            if result and isinstance(result, dict):
                                # Extract articles from the session data
                                scraped_articles = result.get('articles', [])
                                # Filter articles by date
                                filtered_articles = self._filter_articles_by_date(scraped_articles)
                                
                                # Add articles to our result list
                                articles.extend(filtered_articles)
                            
                            logger.info("Session [%s]: Web scraping complete. Found %d scraped articles.", session_id, len(articles))
            else:
                logger.info("Session [%s]: No tasks to execute (no URLs provided).", session_id)
            
            # Create session metadata
            session_metadata = {
                'session_id': session_id,
                'urls_requested': len(urls),
                'urls_processed': len(scrape_urls_for_session),
                'articles_extracted': len(articles),
                'extraction_time_seconds': round(time.time() - start_time, 2),
                'keywords_used': keywords or [],
                'scrape_depth': self.scrape_depth,
                'persist_mode': self.persist,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # Process articles using new source-specific approach
            source_session_data_list = self.process_articles(articles, urls, session_metadata)
              # Return only source-specific session data (no backward compatibility)
            return source_session_data_list
            
        finally:
            # Restore original log level if it was changed
            if original_log_level is not None:
                logger.setLevel(original_log_level)
                logging.getLogger('src.journalist.core').setLevel(original_log_level)
                logging.getLogger('src.journalist.extractors').setLevel(original_log_level)
                logging.getLogger('src.journalist.config').setLevel(original_log_level)
                # Restore for all child loggers too
                logging.getLogger('src.journalist.core.session_manager').setLevel(original_log_level)
                logging.getLogger('src.journalist.core.web_scraper').setLevel(original_log_level)
                logging.getLogger('src.journalist.core.link_discoverer').setLevel(original_log_level)
                logging.getLogger('src.journalist.core.content_extractor').setLevel(original_log_level)
                logger.debug("Log level restored to original setting")
