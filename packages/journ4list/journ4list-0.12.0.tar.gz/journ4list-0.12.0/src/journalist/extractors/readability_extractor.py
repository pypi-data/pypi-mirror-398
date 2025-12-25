"""
Readability-based content extractor.
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ReadabilityExtractor(BaseExtractor):
    """Extracts content using readability-lxml library."""
    
    async def extract(self, html_content: str, url: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, Any]:
        """
        Extract content using readability algorithm with enhanced HTML entity handling.
        
        Args:
            html_content: Raw HTML content
            url: URL of the page
            soup: Optional pre-parsed BeautifulSoup object
            
        Returns:
            Dictionary containing extracted content
        """
        extracted_title = ""
        extracted_body = ""
        
        try:
            from readability import Document
            
            doc = Document(html_content)
            readability_title = doc.title()
            content_html = doc.summary(html_partial=True)
            
            # Parse the extracted content
            content_soup = BeautifulSoup(content_html, "html.parser")
            
            # Extract paragraphs and divs with substantial text
            body_paragraphs = []
            for element in content_soup.find_all(['p', 'div']):
                text = element.get_text(strip=True)
                if text and len(text) > 20:  # Filter out short text fragments
                    body_paragraphs.append(text)
            
            if body_paragraphs:
                extracted_body = "\n\n".join(body_paragraphs)
            
            # Use readability title if substantial
            if readability_title and len(readability_title.strip()) > 0:
                extracted_title = readability_title.strip()
            
            logger.debug("Readability extractor found title: '%s...', body length: %d", 
                        extracted_title[:50], len(extracted_body))
            
        except ImportError:
            logger.error("readability-lxml library not installed. Please install it with: pip install readability-lxml")
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Error using readability for %s: %s", url, e)
        
        return self._create_result(
            title=extracted_title,
            body=extracted_body,
            extraction_method="readability"
        )
    
    def get_extraction_priority(self) -> int:
        """Get the priority of this extractor (medium-high priority)."""
        return 20  # Medium-high priority - readability is quite reliable