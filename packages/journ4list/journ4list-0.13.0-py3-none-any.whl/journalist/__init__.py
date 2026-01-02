"""
journalist - Universal News Content Extraction Library

A powerful and flexible library for extracting content from news websites worldwide.
"""

__version__ = "0.13.0"
__author__ = "Oktay Burak Ertaş"
__email__ = "oktay.burak.ertas@gmail.com"

# Public API exports
from .journalist import Journalist
from .exceptions import journalistError, ValidationError, NetworkError, ExtractionError

# Browserless integration utilities (for advanced users)
from .core.config import JS_HEAVY_PATTERNS, should_use_browserless

__all__ = [
    "Journalist",
    "journalistError",
    "ValidationError",
    "NetworkError",
    "ExtractionError",
    # Browserless utilities
    "JS_HEAVY_PATTERNS",
    "should_use_browserless",
]
