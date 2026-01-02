"""
Shared utilities for content extraction.
"""

import html
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def decode_html_entities(text: str) -> str:
    """
    Decode HTML entities in text.
    
    Args:
        text: Text that may contain HTML entities
        
    Returns:
        Text with HTML entities decoded
    """
    if not text or not isinstance(text, str):
        return text
    return html.unescape(text)


def parse_iso_date(date_str: str) -> Optional[str]:
    """
    Parse ISO date string with Z-suffix handling.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        ISO formatted date string or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    try:
        # Handle 'Z' suffix for UTC timezone
        if date_str.endswith('Z'):
            processed_date_str = date_str[:-1] + "+00:00"
        else:
            processed_date_str = date_str
        
        # Parse and return as ISO format
        parsed_date = datetime.fromisoformat(processed_date_str)
        return parsed_date.isoformat()
        
    except ValueError as e:
        logger.debug("Could not parse date string '%s': %s", date_str, e)
        return None
    except Exception as e:
        logger.warning("Error parsing date string '%s': %s", date_str, e)
        return None


def normalize_extracted_content(content) -> str:
    """
    Normalize extracted content (handle lists, decode entities).
    
    Args:
        content: Content that may be a string, list, or other type
        
    Returns:
        Normalized string content
    """
    if not content:
        return ""
    
    if isinstance(content, list):
        # Join list items, filtering out empty ones
        normalized = "\n\n".join(filter(None, [str(item).strip() for item in content]))
    else:
        normalized = str(content).strip()
    
    # Decode HTML entities
    return decode_html_entities(normalized)


def clean_unwanted_elements(soup_element):
    """
    Remove unwanted elements from a BeautifulSoup element.
    
    Args:
        soup_element: BeautifulSoup element to clean
    """
    unwanted_tags = ['nav', 'header', 'footer', 'aside', 'script', 'style', 'form']
    for unwanted in soup_element.find_all(unwanted_tags):
        unwanted.decompose()


def extract_substantial_text(elements, min_length: int = 20) -> list:
    """
    Extract substantial text content from elements.
    
    Args:
        elements: List of BeautifulSoup elements
        min_length: Minimum length for text to be considered substantial
        
    Returns:
        List of substantial text content
    """
    text_parts = []
    for element in elements:
        text = element.get_text(separator='\n', strip=True)
        if text and len(text) >= min_length:
            text_parts.append(text)
    return text_parts
