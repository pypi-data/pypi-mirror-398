"""
JSON-LD structured data extractor.
"""

import json
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_extractor import BaseExtractor
from ..core.utils import parse_iso_date

logger = logging.getLogger(__name__)


class LdJsonExtractor(BaseExtractor):
    """Extracts content from JSON-LD structured data."""
    
    async def extract(self, html_content: str, url: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, Any]:
        """
        Extract content from JSON-LD structured data with comprehensive parsing.
        
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
        extracted_date = None
        
        try:
            ld_json_scripts = soup.find_all("script", type="application/ld+json")
            
            for script_tag in ld_json_scripts:
                script_content = script_tag.get_text()
                if not script_content:
                    continue
                
                try:
                    # Clean up JSON content - handle leading/trailing non-JSON content
                    cleaned_content = self._clean_json_content(script_content)
                    if not cleaned_content:
                        continue
                    
                    ld_data = json.loads(cleaned_content)
                    
                    # Handle both single objects and arrays
                    items_to_check = self._extract_items_from_ld_data(ld_data)
                    
                    # Process each item for article content
                    for item in items_to_check:
                        if not isinstance(item, dict):
                            continue
                        
                        # Check if this is an article-like item
                        if self._is_article_item(item):
                            title, body, date = self._extract_content_from_item(item)
                            
                            # Update extracted content if better than current
                            if body and (not extracted_body or len(body) > len(extracted_body)):
                                extracted_body = body
                            
                            if title and (not extracted_title or len(title) > len(extracted_title)):
                                extracted_title = title
                            
                            if date and not extracted_date:
                                extracted_date = date
                    
                    # If we found substantial content, we can stop
                    if extracted_body and len(extracted_body) > 100 and extracted_title:
                        logger.info("Extracted substantial content via LD+JSON for %s", url)
                        break
                        
                except json.JSONDecodeError as e:
                    logger.debug("Failed to parse LD+JSON content for %s: %s", url, e)
                except Exception as e:
                    logger.warning("Error processing LD+JSON for %s: %s", url, e)
                    
        except Exception as e:
            logger.warning("Outer error during LD+JSON processing for %s: %s", url, e)
        
        logger.debug("LD+JSON extractor found title: '%s...', body length: %d", 
                    extracted_title[:50], len(extracted_body))
        
        return self._create_result(
            title=extracted_title,
            body=extracted_body,
            published_at=extracted_date,
            extraction_method="ld_json"
        )
    
    def _clean_json_content(self, content: str) -> str:
        """Clean JSON content by removing leading/trailing non-JSON content."""
        if not content:
            return ""
        
        # Find JSON boundaries
        first_brace = content.find('{')
        first_bracket = content.find('[')
        last_brace = content.rfind('}')
        last_bracket = content.rfind(']')
        
        # Determine start index
        start_index = -1
        if first_brace != -1 and first_bracket != -1:
            start_index = min(first_brace, first_bracket)
        elif first_brace != -1:
            start_index = first_brace
        elif first_bracket != -1:
            start_index = first_bracket
        
        # Determine end index
        end_index = -1
        if last_brace != -1 and last_bracket != -1:
            end_index = max(last_brace, last_bracket)
        elif last_brace != -1:
            end_index = last_brace
        elif last_bracket != -1:
            end_index = last_bracket
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return content[start_index:end_index+1]
        
        return content
    
    def _clean_json_string(self, content: str) -> str:
        """Alias for _clean_json_content for backward compatibility."""
        return self._clean_json_content(content)
    
    def _parse_ld_json(self, json_string: str) -> dict:
        """Parse LD+JSON string into dictionary."""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            return {}
    
    def _extract_from_ld_data(self, ld_data: dict) -> tuple:
        """Extract title and body from LD+JSON data - simplified version for tests."""
        if not isinstance(ld_data, dict):
            return "", ""
        
        # Check if this item is article-like
        if not self._is_article_item(ld_data):
            return "", ""
        
        title, body, _ = self._extract_content_from_item(ld_data)
        return title, body
    
    def _extract_items_from_ld_data(self, ld_data) -> list:
        """Extract items to check from LD+JSON data structure."""
        items_to_check = []
        
        if isinstance(ld_data, list):
            items_to_check.extend(ld_data)
        elif isinstance(ld_data, dict):
            items_to_check.append(ld_data)
            # Sometimes nested inside "@graph"
            if isinstance(ld_data.get("@graph"), list):
                items_to_check.extend(ld_data["@graph"])
        
        return items_to_check
    
    def _is_article_item(self, item: dict) -> bool:
        """Check if an LD+JSON item represents an article."""
        item_type = item.get("@type", "")
        
        if isinstance(item_type, list):
            item_type_str = " ".join(item_type).lower()
        else:
            item_type_str = str(item_type).lower()
        
        article_types = ["newsarticle", "article", "webpage", "reportage", "blogposting"]
        return any(article_type in item_type_str for article_type in article_types)
    
    def _get_item_type(self, item: dict) -> str:
        """Get simplified item type for logging."""
        item_type = item.get("@type", "unknown")
        if isinstance(item_type, list):
            return item_type[0].lower() if item_type else "unknown"
        return str(item_type).lower()
    
    def _extract_content_from_item(self, item: dict) -> tuple:
        """Extract title, body, and date from an LD+JSON item."""
        # Extract body content
        body = (item.get("articleBody") or 
                item.get("text") or 
                item.get("description") or "")
        
        # Handle body as list
        if isinstance(body, list):
            body = "\n\n".join(str(paragraph) for paragraph in body if paragraph)
        
        # Extract title
        title = (item.get("headline") or 
                item.get("name") or "")
        
        # Handle title as list
        if isinstance(title, list):
            title = " ".join(str(part) for part in title if part)
        
        # Extract date
        date_value = item.get("datePublished")
        extracted_date = None
        
        if isinstance(date_value, list) and date_value:
            if isinstance(date_value[0], str):
                extracted_date = parse_iso_date(date_value[0])
        elif isinstance(date_value, str):
            extracted_date = parse_iso_date(date_value)
        
        return title, body, extracted_date
    
    def get_extraction_priority(self) -> int:
        """Get the priority of this extractor (highest priority)."""
        return 10  # Highest priority - structured data is very reliable