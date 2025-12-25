"""
File management operations for article persistence in workspace folders.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from werkzeug.utils import secure_filename
import datefinder

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for article storage in workspace folders"""
    
    def __init__(self, base_data_dir: str):
        """
        Initialize the FileManager.
        Args:
            base_data_dir: The root directory where article data will be stored.
                         An 'articles' subdirectory will be created here.
        """
        self.base_data_dir = base_data_dir
        self.articles_dir = os.path.join(self.base_data_dir, 'articles')
        
        # Ensure directories exist
        try:
            os.makedirs(self.base_data_dir, exist_ok=True)
            os.makedirs(self.articles_dir, exist_ok=True)
            logger.info(f"FileManager initialized. Articles dir: {self.articles_dir}")
        except OSError as e:
            logger.error(f"Error creating directories for FileManager at {self.base_data_dir}: {e}")
            # Depending on desired behavior, could raise an exception here
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitizes a string to be used as a filename component."""
        # Use a more robust sanitization than just secure_filename if needed,
        # especially if names can be very long or have many special chars.
        # For now, secure_filename is a good start.
        # Limit length to avoid issues with max path length on some OS.
        # Max filename length is often 255, but keep it shorter for safety.
        return secure_filename(name)[:100] # Limit sanitized name length

    def _get_article_file_path(self, article_id: str) -> str:
        """Get the file path for an article, using sanitized article_id."""
        # article_id is often a hash, which is already safe, but sanitize just in case.
        safe_article_id = self._sanitize_filename(article_id)
        return os.path.join(self.articles_dir, f"article_{safe_article_id}.json")

    def save_json_data(self, file_path: str, data: Dict[str, Any], data_type: str = "data") -> bool:
        """
        Generic method to save dictionary data to a JSON file.
        
        Args:
            file_path: Full path to the file where data should be saved.
            data: The dictionary data to save.
            data_type: A string describing the type of data (e.g., "article") for logging.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Successfully saved {data_type} to {file_path}")
            return True
        except IOError as e:
            logger.error(f"IOError saving {data_type} to {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving {data_type} to {file_path}: {e}")
        return False

    def load_json_data(self, file_path: str, data_type: str = "data") -> Optional[Dict[str, Any]]:
        """
        Generic method to load dictionary data from a JSON file.
        
        Args:
            file_path: Full path to the file from which data should be loaded.
            data_type: A string describing the type of data (e.g., "article") for logging.

        Returns:
            Loaded dictionary data or None if an error occurs or file not found.
        """
        if not os.path.exists(file_path):
            logger.debug(f"{data_type.capitalize()} file not found: {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Successfully loaded {data_type} from {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError loading {data_type} from {file_path}: {e}. File might be corrupted.")
            # Optionally, attempt to delete or move corrupted file
        except IOError as e:
            logger.error(f"IOError loading {data_type} from {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading {data_type} from {file_path}: {e}")
        return None

    def save_article(self, article_id: str, article_data: Dict[str, Any], include_html_content: bool = False) -> bool:
        """
        Save individual article data, including a timestamp
        
        Args:
            article_id: Unique article identifier (usually URL hash)
            article_data: Article content and metadata
            include_html_content: Whether to include html_content in saved data (default: False to reduce file size)
            
        Returns:
            True if saved successfully
        """
        try:
            article_file = self._get_article_file_path(article_id)
            
            # Remove html_content if not requested to reduce file size
            if not include_html_content:
                # Create a copy to avoid modifying the original
                article_data = article_data.copy()
                article_data.pop('html_content', None)
              # Add metadata (timestamp is now part of the main data)
            # The article_data itself should contain 'scraped_at' as per web_scraper.py
            article_payload = {
                **article_data # Spread the original article data
            }
            return self.save_json_data(article_file, article_payload, data_type="article")
            
        except Exception as e:
            logger.error(f"Failed to prepare article data {article_id}: {e}")
            return False
    
    def load_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Load individual article data
        
        Args:
            article_id: Unique article identifier
            
        Returns:
            Article data dict or None if not found
        """
        try:
            article_file = self._get_article_file_path(article_id)
            # The loaded data is the full payload including our metadata + original article_data
            loaded_payload = self.load_json_data(article_file, data_type="article")
            # If we want to return just the original article_data (without our 'article_id_meta' and 'file_saved_at')
            # we would need to reconstruct it. For now, return the full saved structure.
            return loaded_payload
            
        except Exception as e:
            logger.error(f"Failed to load article {article_id}: {e}")
            return None
    
    def cleanup_old_files(self, directory: str, days_old: int, file_prefix: Optional[str] = None) -> int:
        """
        Generic method to clean up files older than specified days in a directory.
        
        Args:
            directory: The directory to clean up.
            days_old: Remove files older than this many days based on modification time.
            file_prefix: Optional prefix to filter files (e.g., "article_").
            
        Returns:
            Number of files removed.
        """
        if not os.path.isdir(directory):
            logger.warning(f"Cleanup directory {directory} does not exist. Skipping cleanup.")
            return 0

        try:
            import time # Keep import local to method if not used elsewhere extensively
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            removed_count = 0
            files_processed = 0
            
            for filename in os.listdir(directory):
                if file_prefix and not filename.startswith(file_prefix):
                    continue
                if not filename.endswith('.json'): # Assuming we only manage .json files this way
                    continue

                files_processed += 1
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path): # Ensure it's a file
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            removed_count += 1
                            logger.debug(f"Removed old file: {file_path}")
                except FileNotFoundError:
                    logger.debug(f"File {file_path} not found during cleanup (possibly removed by another process). Skipping.")
                except Exception as e_file:
                    logger.error(f"Error processing file {file_path} during cleanup: {e_file}")
            
            logger.info(f"Cleanup in {directory} (prefix: {file_prefix or '*'}): Processed {files_processed} files, removed {removed_count} old files.")
            return removed_count
            
        except Exception as e_main:
            logger.error(f"Failed to cleanup old files in {directory}: {e_main}")
            return 0

    def cleanup_old_articles(self, days_old: int = 30) -> int:
        """
        Clean up article files older than specified days.
        Args:
            days_old: Remove articles older than this many days.
        Returns:
            Number of files removed.
        """
        return self.cleanup_old_files(self.articles_dir, days_old, file_prefix="article_")

    def _generate_url_based_filename(self, url: str, counter: int = 0) -> str:
        """
        Generate a URL-based filename similar to the old system.
        
        Args:
            url: The article URL
            counter: Optional counter for uniqueness
            
        Returns:
            Sanitized filename based on URL
        """
        from urllib.parse import urlparse
        
        try:
            # Parse the URL
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            path = parsed.path.replace('/', '_').strip('_')
              # Create base filename from domain and path
            if path:
                base_name = f"{domain}_{path}"
            else:
                base_name = domain
            
            # Sanitize the base name first
            safe_base_name = self._sanitize_filename(base_name)
            
            # Ensure base name is not too long (leaving room for counter prefix and .json extension)
            if len(safe_base_name) > 90:  # Leave room for counter prefix
                safe_base_name = safe_base_name[:90]
            
            # Add counter as prefix if provided
            if counter > 0:
                final_name = f"{counter}_{safe_base_name}"
            else:
                final_name = safe_base_name
            
            return final_name
            
        except Exception as e:
            logger.warning(f"Could not generate URL-based filename for {url}: {e}")
            # Fallback to hash-based name
            import hashlib
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]
            return f"article_{url_hash}"

    def _extract_dates_from_url(self, url: str) -> list:
        """
        Extract dates from URL using datefinder library.
        
        Args:
            url: The URL to extract dates from
            
        Returns:
            List of datetime objects found in the URL
        """
        try:
            # Use datefinder to extract dates from URL
            dates = list(datefinder.find_dates(url))
            return dates
        except Exception as e:
            logger.debug(f"Error extracting dates from URL {url}: {e}")
            return []

    def _is_url_too_old(self, url: str, max_age_days: int = 7) -> bool:
        """
        Check if URL contains a date that is older than the specified number of days.
        
        Args:
            url: The URL to check
            max_age_days: Maximum age in days (default: 7)
            
        Returns:
            True if URL contains an old date, False otherwise
        """
        try:
            dates = self._extract_dates_from_url(url)
            
            if not dates:
                # No dates found, assume URL is current
                return False
            
            # Check if any date is older than max_age_days
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            for date in dates:
                # Only consider dates that seem like article publication dates
                # (not too far in the future, not before year 2000)
                if datetime(2000, 1, 1) <= date <= datetime.now() + timedelta(days=1):
                    if date < cutoff_date:
                        logger.info(f"URL {url} contains old date {date.strftime('%Y-%m-%d')}, skipping")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking URL age for {url}: {e}")
            # On error, don't filter the URL
            return False

    def save_article_by_url(self, url: str, article_data: Dict[str, Any], 
                          counter: int = 0, include_html_content: bool = False) -> bool:
        """
        Save article data using URL-based filename.
        
        Args:
            url: The article URL
            article_data: Article content and metadata
            counter: Optional counter for filename uniqueness
            include_html_content: Whether to include html_content in saved data
            
        Returns:
            True if saved successfully
        """
        try:
            # Generate URL-based filename
            filename = self._generate_url_based_filename(url, counter)
            article_file = os.path.join(self.articles_dir, f"{filename}.json")
            
            # Remove html_content if not requested to reduce file size
            if not include_html_content:
                # Create a copy to avoid modifying the original
                article_data = article_data.copy()
                article_data.pop('html_content', None)
              # Add metadata
            article_payload = {
                'url': url,
                **article_data # Spread the original article data
            }
            
            return self.save_json_data(article_file, article_payload, data_type="article")
            
        except Exception as e:
            logger.error(f"Failed to save article by URL {url}: {e}")
            return False

    def _parse_article_published_date(self, article_data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract and parse the published date from article data.
        
        Args:
            article_data: Article content and metadata
            
        Returns:
            datetime object if published date found and parsed, None otherwise
        """
        try:
            # Check the published_at field that comes from extractors
            published_at = article_data.get('published_at')
            
            if not published_at:
                return None
            
            # If it's already a datetime object
            if isinstance(published_at, datetime):
                return published_at
            
            # If it's a string (ISO format from extractors), parse it
            if isinstance(published_at, str):
                return datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing article published date: {e}")
            return None

    def _is_article_too_old(self, url: str, article_data: Dict[str, Any], max_age_days: int = 7) -> bool:
        """
        Check if article is too old based on URL dates or published_at metadata.
        
        Args:
            url: The article URL
            article_data: Article content and metadata
            max_age_days: Maximum age in days (default: 7)
            
        Returns:
            True if article is too old, False otherwise
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # First check URL for dates
            url_dates = self._extract_dates_from_url(url)
            for date in url_dates:
                if datetime(2000, 1, 1) <= date <= datetime.now() + timedelta(days=1):
                    if date < cutoff_date:
                        logger.info(f"Article URL {url} contains old date {date.strftime('%Y-%m-%d')}, skipping")
                        return True
            
            # Then check article metadata for published date
            published_date = self._parse_article_published_date(article_data)
            if published_date and published_date < cutoff_date:
                logger.info(f"Article from {url} has old published date {published_date.strftime('%Y-%m-%d')}, skipping")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking article age for {url}: {e}")
            # On error, don't filter the article
            return False

    def _get_source_session_filename(self, domain: str) -> str:
        """
        Generate session filename for specific domain, reusing existing sanitization.
        
        Args:
            domain: Domain name like 'www.fanatik.com.tr'
            
        Returns:
            Filename like 'session_data_fanatik_com_tr.json'
        """
        # Remove www prefix and replace dots/dashes with underscores
        sanitized_domain = domain.replace('www.', '').replace('.', '_').replace('-', '_').replace(':', '_')
        # Use existing sanitization method
        safe_domain = self._sanitize_filename(sanitized_domain)
        return f"session_data_{safe_domain}.json"

    def save_source_specific_session_data(self, domain: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data for specific source domain.
        
        Args:
            domain: Source domain name
            session_data: Session data dictionary to save
              Returns:
            True if saved successfully, False otherwise
        """
        try:
            filename = self._get_source_session_filename(domain)
            file_path = os.path.join(self.base_data_dir, filename)
            
            logger.info(f"Saving source session data to: {file_path}")
            
            # Add domain metadata if not already present
            if 'source_domain' not in session_data:
                session_data['source_domain'] = domain

            # Add file_path if not already present
            if 'file_path' not in session_data:
                session_data['file_path'] = file_path
            
            # Add timestamp if not already present
            if 'saved_at' not in session_data:
                session_data['saved_at'] = datetime.now().isoformat()
            
            return self.save_json_data(file_path, session_data, data_type=f"source session ({domain})")
            
        except Exception as e:
            logger.error(f"Failed to save source-specific session data for domain {domain}: {e}")
            return False

    def load_source_specific_session_data(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Load session data for specific source domain.
        
        Args:
            domain: Source domain name
            
        Returns:
            Session data dictionary or None if not found
        """
        try:
            filename = self._get_source_session_filename(domain)
            file_path = os.path.join(self.base_data_dir, filename)
            return self.load_json_data(file_path, data_type=f"source session ({domain})")
            
        except Exception as e:
            logger.error(f"Failed to load source-specific session data for domain {domain}: {e}")
            return None

    def list_source_session_files(self) -> List[str]:
        """
        List all source-specific session data files in the session directory.
        
        Returns:
            List of source session filenames (not full paths)
        """
        try:
            if not os.path.exists(self.base_data_dir):
                return []
            
            files = []
            for filename in os.listdir(self.base_data_dir):
                if filename.startswith('session_data_') and filename.endswith('.json') and filename != 'session_data.json':
                    files.append(filename)
            
            return sorted(files)  # Sort for consistent ordering
            
        except Exception as e:
            logger.error(f"Error listing source session files: {e}")
            return []

    def save_individual_articles(self, articles: List[Dict[str, Any]]) -> None:
        """
        Save individual articles to files.
        
        Args:
            articles: List of article dictionaries to save
        """
        try:
            for i, article in enumerate(articles):
                article_url = article.get('url', '')
                if article_url:
                    # Use URL-based filename
                    self.save_article_by_url(
                        url=article_url,
                        article_data=article,
                        counter=i,
                        include_html_content=False
                    )
                else:
                    # Fallback to old method if no URL
                    article_id = article.get('id') or f"article_{i}"
                    self.save_article(article_id, article, include_html_content=False)
        except Exception as e:
            logger.error(f"Error saving individual articles: {e}")

    def save_source_session_files(self, source_session_data_list: List[Dict[str, Any]]) -> List[str]:
        """
        Save source-specific session data files.
        
        Args:
            source_session_data_list: List of source session data to save
            
        Returns:
            List of saved filenames
        """
        saved_files = []
        try:
            for source_data in source_session_data_list:
                domain = source_data.get('source_domain', 'unknown')
                success = self.save_source_specific_session_data(domain, source_data)
                if success:
                    filename = self._get_source_session_filename(domain)
                    saved_files.append(filename)
            
            # List workspace files after saving is completed
            self.list_workspace_files()
                    
            return saved_files
        except Exception as e:
            logger.error(f"Error saving source session files: {e}")
            return saved_files

    def list_workspace_files(self) -> None:
        """List all files in the workspace directory for debugging."""
        try:
            if os.path.exists(self.base_data_dir):
                files = os.listdir(self.base_data_dir)
                logger.info(f"Workspace files in {self.base_data_dir}: {files}")
            else:
                logger.info(f"Workspace directory {self.base_data_dir} does not exist")
        except Exception as e:
            logger.error(f"Error listing workspace files: {e}")
