"""
Base extractor class for content extraction strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from bs4 import BeautifulSoup
from ..core.utils import normalize_extracted_content

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for content extractors."""

    def __init__(self, config=None):
        """Initialize base extractor with config."""
        self.config = config
        self.extraction_log = []

    @abstractmethod
    async def extract(self, html_content: str, url: str, soup: Optional[BeautifulSoup] = None) -> dict:
        """
        Extracts content from the given HTML.

        Args:
            html_content: The HTML content of the page.
            url: The URL of the page.
            soup: Optional pre-parsed BeautifulSoup object

        Returns:
            A dictionary containing the extracted data (e.g., title, body, published_at).
            Returns an empty dictionary or a dictionary with error info if extraction fails.
        """
        raise NotImplementedError("Subclasses must implement extract method")

    def get_extraction_priority(self) -> int:
        """
        Get the priority of this extractor (higher numbers = higher priority).

        Returns:
            Priority number (1-100, where 100 is highest priority)
        """
        return 50  # Default priority

    def _log_extraction_step(self, step: str):
        """Log an extraction step for debugging."""
        self.extraction_log.append(step)
        logger.debug("Extraction step: %s", step)

    def _create_result(self, title: str = "", body: str = "", published_at: Optional[str] = None, 
                      extraction_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Create standardized extraction result.
        
        Args:
            title: Extracted title
            body: Extracted body content
            published_at: Extracted publication date
            extraction_method: Method used for extraction
            
        Returns:
            Standardized result dictionary
        """
        # Normalize content and decode HTML entities
        normalized_title = normalize_extracted_content(title)
        normalized_body = normalize_extracted_content(body)
        
        # Create extraction method string
        if not extraction_method:
            extraction_method = self.__class__.__name__.replace('Extractor', '').lower()
        
        if self.extraction_log:
            method_details = " -> ".join(self.extraction_log)
            extraction_method = f"{extraction_method}:{method_details}"
        
        return {
            "title": normalized_title,
            "body": normalized_body,
            "published_at": published_at,
            "extraction_method": extraction_method
        }