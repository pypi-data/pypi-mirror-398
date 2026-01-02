"""
HTTP session management for web scraping.

Supports two fetching modes:
1. aiohttp (default): Fast, cheap, static HTML only
2. Browserless (opt-in): Headless Chrome for JavaScript-heavy pages

Browserless is only used when:
- User provides browserless_url AND browserless_token
- URL matches JS_HEAVY_PATTERNS (e.g., /foto-galeri/)
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Any, Dict

from .config import ScrapingConfig, should_use_browserless
from .browserless_client import BrowserlessClient

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages HTTP sessions for web scraping with optional Browserless support."""

    def __init__(
        self, 
        config: ScrapingConfig,
        browserless_url: Optional[str] = None,
        browserless_token: Optional[str] = None,
        max_scrolls: int = 20
    ):
        """
        Initializes the SessionManager.

        Args:
            config: ScrapingConfig object for session settings.
            browserless_url: Optional URL of Browserless service (enables JS rendering)
            browserless_token: Optional auth token for Browserless API (required with URL)
            max_scrolls: Max scroll iterations for infinite scroll pages (default: 20)
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Initialize Browserless client if credentials provided
        self._browserless_client: Optional[BrowserlessClient] = None
        if browserless_url and browserless_token:
            try:
                self._browserless_client = BrowserlessClient(
                    browserless_url=browserless_url,
                    browserless_token=browserless_token,
                    max_scrolls=max_scrolls
                )
                logger.info("SessionManager initialized with Browserless support enabled.")
            except ValueError as e:
                logger.warning("Failed to initialize BrowserlessClient: %s", e)
                self._browserless_client = None
        else:
            logger.info("SessionManager initialized (Browserless disabled - no credentials provided).")

    @property
    def browserless_enabled(self) -> bool:
        """Check if Browserless is configured and available."""
        return self._browserless_client is not None and self._browserless_client.is_available()

    async def get_session(self) -> aiohttp.ClientSession:
        """
        Provides an active HTTP session.
        Initializes a new session if one doesn't exist or is closed.
        """
        if self._session is None or self._session.closed:
            logger.info("Creating new HTTP session.")
            headers = self.config.get_request_headers()
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
            logger.info(f"New HTTP session created with timeout {self.config.request_timeout}s.")
        return self._session

    async def close_session(self) -> None:
        """
        Closes the active HTTP session if it exists and is open.
        """
        if self._session is not None and not self._session.closed:
            logger.info("Closing HTTP session.")
            await self._session.close()
            self._session = None  # Reset session reference to prevent reuse after close
            logger.info("HTTP session closed.")
        else:
            logger.info("No active HTTP session to close or session already closed.")

    async def fetch_content(self, url: str, retries: int = 3, retry_delay: int = 1) -> Optional[str]:
        """
        Fetches content from a URL, automatically routing to Browserless for JS-heavy pages.

        Routing logic:
        1. If Browserless is enabled AND URL matches JS_HEAVY_PATTERNS → use Browserless
        2. Otherwise → use standard aiohttp (faster, cheaper)
        
        If Browserless fails, automatically falls back to aiohttp.

        Args:
            url: The URL to fetch content from.
            retries: Number of times to retry on failure (for aiohttp).
            retry_delay: Delay in seconds between retries (for aiohttp).

        Returns:
            The page content as a string if successful, None otherwise.
        """
        # Check if we should use Browserless for this URL
        if self.browserless_enabled and should_use_browserless(url):
            logger.info("URL matches JS-heavy pattern, routing to Browserless: %s", url)
            
            # Try Browserless with fallback to aiohttp
            async def aiohttp_fallback(fallback_url: str) -> Optional[str]:
                return await self._fetch_with_aiohttp(fallback_url, retries, retry_delay)
            
            return await self._browserless_client.fetch_with_fallback(
                url=url,
                fallback_fetcher=aiohttp_fallback
            )
        else:
            # Standard aiohttp fetch
            return await self._fetch_with_aiohttp(url, retries, retry_delay)

    async def _fetch_with_aiohttp(self, url: str, retries: int = 3, retry_delay: int = 1) -> Optional[str]:
        """
        Fetches content from a URL using aiohttp (standard HTTP client).

        Args:
            url: The URL to fetch content from.
            retries: Number of times to retry on failure.
            retry_delay: Delay in seconds between retries.

        Returns:
            The page content as a string if successful, None otherwise.
        """
        session = await self.get_session()
        last_exception = None

        for attempt in range(retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1} to fetch URL: {url}")
                async with session.get(url) as response:
                    response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
                    content = await response.text()
                    logger.debug(f"Successfully fetched content from {url} (status: {response.status}).")
                    return content
            except aiohttp.ClientResponseError as e:  # More specific error for HTTP errors
                logger.debug(f"HTTP error fetching {url} (attempt {attempt + 1}/{retries + 1}): {e.status} {e.message}")
                last_exception = e
                if e.status in [400, 401, 403, 404]:  # Don't retry on these client errors
                    logger.error(f"Client error {e.status} for {url}. Not retrying.")
                    break
            except aiohttp.ClientError as e:  # Catches other client errors like connection issues
                logger.debug(f"Client error fetching {url} (attempt {attempt + 1}/{retries + 1}): {e}")
                last_exception = e
            except asyncio.TimeoutError as e:  # Catch timeout errors specifically
                logger.debug(f"Timeout error fetching {url} (attempt {attempt + 1}/{retries + 1}): {e}")
                last_exception = e

            if attempt < retries:
                logger.debug(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to fetch {url} after {retries + 1} attempts. Last error: {last_exception}")

        return None

    async def __aenter__(self):
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()