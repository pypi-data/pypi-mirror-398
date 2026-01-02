"""
Browser Render Service client for JavaScript-heavy page rendering.

This module provides integration with a browser render service (either the custom
Playwright-based service or standard Browserless) for extracting content from pages
that require JavaScript execution (e.g., infinite scroll galleries).

IMPORTANT: This is an opt-in feature. Users must explicitly provide:
- browserless_url: The URL of the browser render service
- browserless_token: Authentication token/API key for the service

Without both parameters, this client will not be used and all requests
will fall back to the standard aiohttp client.
"""

import asyncio
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserlessClient:
    """
    Client for interacting with a browser render service.

    Supports the custom browser-render-service (Playwright-based) with GET /render API.

    Usage:
        client = BrowserlessClient(
            browserless_url="https://browser-render-service-xyz.run.app",
            browserless_token="your-api-key",
            max_scrolls=5
        )
        html = await client.fetch("https://example.com/foto-galeri/123")
    """

    # Default timeout for requests (accounts for cold start + rendering)
    DEFAULT_TIMEOUT = 60

    # Default number of scroll iterations for infinite scroll pages
    DEFAULT_MAX_SCROLLS = 5

    def __init__(
        self,
        browserless_url: str,
        browserless_token: str,
        max_scrolls: int = DEFAULT_MAX_SCROLLS,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the Browser Render Service client.

        Args:
            browserless_url: Base URL of the browser render service (required)
            browserless_token: API key for authentication (required)
            max_scrolls: Maximum number of scroll iterations (default: 5)
            timeout: Request timeout in seconds (default: 60)

        Raises:
            ValueError: If browserless_url or browserless_token is not provided
        """
        if not browserless_url:
            raise ValueError("browserless_url is required for BrowserlessClient")
        if not browserless_token:
            raise ValueError("browserless_token is required for BrowserlessClient")

        self.browserless_url = browserless_url.rstrip('/')
        self.browserless_token = browserless_token
        self.max_scrolls = max_scrolls
        self.timeout = timeout

        logger.info(
            "BrowserlessClient initialized (url=%s, max_scrolls=%d, timeout=%ds)",
            self.browserless_url, self.max_scrolls, self.timeout
        )

    async def fetch(self, url: str, max_scrolls: Optional[int] = None) -> Optional[str]:
        """
        Fetch a URL using the browser render service with JavaScript execution.

        This method:
        1. Calls the /render endpoint with the target URL
        2. The service opens the URL in a headless browser
        3. Scrolls to trigger infinite scroll loading
        4. Returns the fully rendered HTML

        Args:
            url: The URL to fetch
            max_scrolls: Override default max_scrolls for this request

        Returns:
            The fully rendered HTML content, or None if fetch failed
        """
        logger.info("BrowserRenderService: Fetching URL with JS rendering: %s", url)

        scrolls = max_scrolls if max_scrolls is not None else self.max_scrolls

        try:
            # Build the /render endpoint URL
            render_endpoint = f"{self.browserless_url}/render"

            # Query parameters
            params = {
                "url": url,
                "scrolls": scrolls
            }

            # Headers with API key
            headers = {
                "X-API-Key": self.browserless_token
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    render_endpoint,
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        html_content = data.get("html", "")

                        logger.info(
                            "BrowserRenderService: Successfully fetched %s (content length: %d)",
                            url, len(html_content)
                        )
                        return html_content
                    elif response.status == 403:
                        logger.error(
                            "BrowserRenderService: Authentication failed for %s - Invalid API key",
                            url
                        )
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(
                            "BrowserRenderService: Failed to fetch %s - Status %d: %s",
                            url, response.status, error_text[:500]
                        )
                        return None

        except asyncio.TimeoutError:
            logger.error("BrowserRenderService: Timeout fetching %s (timeout=%ds)", url, self.timeout)
            return None
        except aiohttp.ClientError as e:
            logger.error("BrowserRenderService: Client error fetching %s: %s", url, str(e))
            return None
        except Exception as e:
            logger.error("BrowserRenderService: Unexpected error fetching %s: %s", url, str(e))
            return None

    async def fetch_with_fallback(
        self,
        url: str,
        fallback_fetcher,
        max_scrolls: Optional[int] = None
    ) -> Optional[str]:
        """
        Fetch a URL using the browser render service, falling back to another fetcher on failure.

        Args:
            url: The URL to fetch
            fallback_fetcher: Async callable that takes URL and returns HTML
            max_scrolls: Override default max_scrolls for this request

        Returns:
            HTML content from browser service or fallback, or None if both fail
        """
        # Try browser render service first
        html = await self.fetch(url, max_scrolls)

        if html:
            return html

        # Browser service failed, try fallback
        logger.warning(
            "BrowserRenderService: Falling back to standard fetcher for %s", url
        )

        try:
            return await fallback_fetcher(url)
        except Exception as e:
            logger.error("BrowserRenderService: Fallback fetcher also failed for %s: %s", url, str(e))
            return None

    def is_available(self) -> bool:
        """
        Check if the browser render service client is properly configured.

        Returns:
            True if client has URL and token configured
        """
        return bool(self.browserless_url and self.browserless_token)
