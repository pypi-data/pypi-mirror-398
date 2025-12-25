"""
CSS selector-based content extractor.
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from .base_extractor import BaseExtractor
from ..core.utils import parse_iso_date, clean_unwanted_elements

logger = logging.getLogger(__name__)


class SelectorExtractor(BaseExtractor):
    """Extracts content using CSS selectors (site-specific and generic)."""
    
    def __init__(self, config):
        """
        Initialize the selector extractor.
        
        Args:
            config: Scraping configuration instance
        """
        super().__init__(config)
    
    async def extract(self, html_content: str, url: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, Any]:
        """
        Extract content using CSS selectors with comprehensive site-specific logic.
        
        Args:
            html_content: Raw HTML content
            url: URL of the page
            soup: Optional pre-parsed BeautifulSoup object
            
        Returns:
            Dictionary containing extracted content
        """
        if soup is None:
            soup = BeautifulSoup(html_content, "html.parser")
        
        domain = urlparse(url).netloc.lower()
        
        # Determine if we have site-specific selectors
        has_site_specific = self._has_site_specific_selectors(domain)
        selectors = self._get_selectors_for_domain(domain)
        
        # Extract title using CSS selectors
        extracted_title = self._extract_title_with_css(soup, selectors)
        
        # Extract body using CSS selectors
        extracted_body = self._extract_body_with_css(soup, selectors)
        
        # Extract date using CSS selectors
        extracted_date = self._extract_date_with_css(soup, selectors)
        
        # Log extraction method based on selector type
        method_type = "site_specific" if has_site_specific else "generic"
        
        logger.debug("Selector extractor (%s) found title: '%s...', body length: %d", 
                    method_type, extracted_title[:50], len(extracted_body))
        
        return self._create_result(
            title=extracted_title,
            body=extracted_body,
            published_at=extracted_date,
            extraction_method=f"css_{method_type}"
        )
    
    def _has_site_specific_selectors(self, domain: str) -> bool:
        """Check if we have site-specific selectors for this domain."""
        if not self.config or not hasattr(self.config, 'site_specific_selectors'):
            return False
        
        for site_domain_key in self.config.site_specific_selectors:
            if site_domain_key in domain:
                return True
        return False
    
    def _get_selectors_for_domain(self, domain: str) -> Dict[str, str]:
        """Get selectors for a domain (site-specific or generic)."""
        if self.config and hasattr(self.config, 'site_specific_selectors'):
            for site_domain_key in self.config.site_specific_selectors:
                if site_domain_key in domain:
                    logger.debug("Using site-specific selectors for %s", domain)
                    return self.config.site_specific_selectors[site_domain_key]
        
        # Fall back to generic selectors
        return getattr(self.config, 'generic_selectors', {}) if self.config else {}
    
    def _extract_title_with_css(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> str:
        """Extract title using CSS selectors with fallbacks."""
        # Try CSS selector first
        title_selector = selectors.get("title_selector", "h1")
        title_tag = soup.select_one(title_selector)
        
        if title_tag:
            css_title = title_tag.get_text(strip=True)
            if css_title and len(css_title) > 0:
                self._log_extraction_step("title_css")
                return css_title
        
        # Fallback to HTML title tag
        html_title_tag = soup.find('title')
        if html_title_tag:
            title_text = html_title_tag.get_text(strip=True)
            if title_text:
                # Remove site name if present
                for sep in [" - ", " | ", " – ", " — "]:
                    if sep in title_text:
                        title_text = title_text.split(sep)[0]
                        break
                self._log_extraction_step("title_fallback")
                return title_text
        
        return ""
    
    def _extract_body_with_css(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> str:
        """Extract body content using CSS selectors with comprehensive logic."""
        # Try primary content selector
        content_selector = selectors.get("content_selector", "article")
        content_tag = soup.select_one(content_selector)
        
        if content_tag:
            # Clean unwanted elements
            clean_unwanted_elements(content_tag)
            
            # Extract substantial text from paragraphs and divs
            css_body_parts = []
            for element in content_tag.find_all(['p', 'div'], recursive=True):
                text = element.get_text(separator='\n', strip=True)
                if text and len(text) > 20:
                    css_body_parts.append(text)
            
            if css_body_parts:
                self._log_extraction_step("body_css_primary")
                return "\n\n".join(css_body_parts)
            else:
                # Fallback to getting all text from content tag
                css_body = content_tag.get_text(separator='\n', strip=True)
                if css_body:
                    self._log_extraction_step("body_css_fallback")
                    return css_body
        
        # Try fallback selectors if primary didn't work
        fallback_selectors = [
            "article", ".article", ".story-content", ".entry-content",
            "div[role='main']", ".article-body", ".article-content",
            ".news-text", "main", ".content"
        ]
        
        for fallback_selector in fallback_selectors:
            if fallback_selector == content_selector:
                continue  # Skip if already tried
                
            content_tag = soup.select_one(fallback_selector)
            if content_tag:
                # Clean unwanted elements
                clean_unwanted_elements(content_tag)
                text = content_tag.get_text(separator='\n', strip=True)
                if text and len(text) > 20:
                    self._log_extraction_step(f"body_css_{fallback_selector.replace('.', '').replace('[', '').replace(']', '')}")
                    return text
        
        return ""
    
    def _extract_date_with_css(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Optional[str]:
        """Extract publication date using CSS selectors."""
        date_selector = selectors.get("date_selector")
        if not date_selector:
            return None
        
        date_tag = soup.select_one(date_selector)
        if date_tag:
            # Try datetime attribute first
            date_text = date_tag.get("datetime") or date_tag.get_text(strip=True)
            
            if date_text:
                # Ensure date_text is a string (handle potential list cases)
                if isinstance(date_text, list):
                    date_text = date_text[0] if date_text else ""
                elif not isinstance(date_text, str):
                    date_text = str(date_text)
                    
                parsed_date = parse_iso_date(date_text)
                if parsed_date:
                    self._log_extraction_step("date_css")
                    return parsed_date
        
        return None
    
    def get_extraction_priority(self) -> int:
        """Get the priority of this extractor (dynamic based on site-specific availability)."""
        # Higher priority if we likely have site-specific selectors
        # This will be determined dynamically during extraction
        return 30  # Medium-high priority - can be site-specific