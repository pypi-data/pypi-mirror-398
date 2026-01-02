"""Core functionality for content extraction."""

from .config import ScrapingConfig, JS_HEAVY_PATTERNS, should_use_browserless
from .content_extractor import ContentExtractor  
from .session_manager import SessionManager
from .browserless_client import BrowserlessClient

__all__ = [
    "ScrapingConfig",
    "ContentExtractor",
    "SessionManager",
    "BrowserlessClient",
    "JS_HEAVY_PATTERNS",
    "should_use_browserless",
]
