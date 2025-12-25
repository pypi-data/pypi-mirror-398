"""
Full-page content extractor.
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_extractor import BaseExtractor
from ..core.utils import clean_unwanted_elements

logger = logging.getLogger(__name__)


class FullPageExtractor(BaseExtractor):
    """Extracts content using full page text cleanup as last resort."""

    async def extract(self, html_content: str, url: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, Any]:
        """
        Extract content using full page text cleanup with intelligent content selection.
        
        Args:
            html_content: Raw HTML content
            url: URL of the page
            soup: Optional pre-parsed BeautifulSoup object
            
        Returns:
            Dictionary containing extracted content
        """
        if soup is None:
            soup = BeautifulSoup(html_content, "html.parser")

        extracted_title = ""
        extracted_body = ""
          # Remove unwanted elements for better content extraction
        clean_unwanted_elements(soup)
        
        # For FullPage extractor, extract clean text content instead of raw HTML
        extracted_body = self._extract_intelligent_content(soup)
        
        # Extract title with fallbacks
        extracted_title = self._extract_title_with_fallbacks(soup)

        logger.debug("FullPage extractor found title: '%s...', body length: %d", 
                    extracted_title[:50], len(extracted_body))
        
        return self._create_result(
            title=extracted_title,
            body=extracted_body,
            extraction_method="full_page"
        )
    
    def _extract_intelligent_content(self, soup: BeautifulSoup) -> str:
        """Extract content using intelligent selection of middle section."""
        # Get all text, split into lines
        full_text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in full_text.split('\n') if line.strip() and len(line.strip()) > 10]
        
        if not lines:
            return ""
        
        # Take substantial content from middle section (skip header/footer)
        start_idx = max(0, len(lines) // 4)
        end_idx = min(len(lines), 3 * len(lines) // 4)
        selected_lines = lines[start_idx:end_idx]
        
        if selected_lines:
            return "\n".join(selected_lines)
        
        return ""
    
    def _extract_title_with_fallbacks(self, soup: BeautifulSoup) -> str:
        """Extract title using multiple fallback strategies."""
        # Try HTML title tag first
        html_title_tag = soup.find('title')
        if html_title_tag:
            title_text = html_title_tag.get_text(strip=True)
            if title_text:
                # Remove site name if present
                for sep in [" - ", " | ", " – ", " — "]:
                    if sep in title_text:
                        title_text = title_text.split(sep)[0]
                        break
                return title_text
        
        # Fallback to first h1
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.get_text(strip=True)
            if h1_text:
                return h1_text
        
        return ""
    
    def get_extraction_priority(self) -> int:
        """Get the priority of this extractor (lowest priority)."""
        return 10  # Lowest priority, as it's a fallback