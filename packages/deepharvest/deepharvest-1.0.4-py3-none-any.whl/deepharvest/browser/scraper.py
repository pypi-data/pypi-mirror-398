"""
Browser Automation with Playwright
"""

import logging
import asyncio
from typing import Optional, Tuple
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import aiohttp
from ..core.crawler import CrawlConfig

logger = logging.getLogger(__name__)


class BrowserResult:
    """Result from browser fetch operation"""

    def __init__(
        self, html: str, screenshot: Optional[bytes] = None, url: str = "", status_code: int = 200
    ):
        self.html = html
        self.screenshot = screenshot
        self.url = url
        self.status_code = status_code
        self.headers = {}
        self._content = html.encode("utf-8") if html else b""
        self._text = html

    @property
    def content(self) -> bytes:
        """Raw content bytes"""
        return self._content

    @property
    def text(self) -> str:
        """Text content"""
        return self._text


class BrowserScraper:
    """
    High-level browser scraper with Playwright integration
    Supports screenshot capture, HTML export, and fallback to aiohttp
    """

    def __init__(self, config: Optional[CrawlConfig] = None, headless: bool = True):
        self.config = config or CrawlConfig(seed_urls=[])
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=getattr(self.config, "user_agent", "DeepHarvest/1.0"),
            )
            logger.info("Browser scraper initialized")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def _initialize_http_fallback(self):
        """Initialize aiohttp session for fallback"""
        if not self._http_session:
            import sys
            from aiohttp import TCPConnector
            from aiohttp.resolver import ThreadedResolver

            # Use ThreadedResolver on Windows to avoid aiodns issues
            resolver = ThreadedResolver() if sys.platform == "win32" else None
            connector = TCPConnector(resolver=resolver) if resolver else None

            self._http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=connector,
                headers={
                    "User-Agent": getattr(self.config, "user_agent", "DeepHarvest/1.0"),
                    "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
                },
            )

    async def _wait_for_dom_ready(self, page: Page, timeout: int = 30000):
        """Wait for DOM to be ready"""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
            await page.wait_for_load_state("networkidle", timeout=timeout)

            # Additional wait for JS execution
            if hasattr(self.config, "wait_for_js_ms"):
                await asyncio.sleep(self.config.wait_for_js_ms / 1000.0)
            else:
                await asyncio.sleep(2.0)
        except Exception as e:
            logger.warning(f"DOM ready wait timeout: {e}")

    async def fetch(
        self,
        url: str,
        use_js: bool = True,
        capture_screenshot: bool = True,
        screenshot_path: Optional[str] = None,
    ) -> BrowserResult:
        """
        Fetch URL with browser automation

        Args:
            url: URL to fetch
            use_js: Whether to use JavaScript rendering
            capture_screenshot: Whether to capture screenshot
            screenshot_path: Optional path to save screenshot

        Returns:
            BrowserResult with html, screenshot, and metadata
        """
        if use_js and self.browser:
            return await self._fetch_with_browser(url, capture_screenshot, screenshot_path)
        else:
            return await self._fetch_with_http(url)

    async def _fetch_with_browser(
        self, url: str, capture_screenshot: bool = True, screenshot_path: Optional[str] = None
    ) -> BrowserResult:
        """Fetch using Playwright browser"""
        if not self.browser or not self.context:
            raise RuntimeError("Browser not initialized. Call initialize() first.")

        page: Page = await self.context.new_page()

        # For Twitter/X, use domcontentloaded instead of networkidle
        # Twitter often never reaches networkidle due to continuous updates
        is_twitter = "twitter.com" in url.lower() or "x.com" in url.lower()
        wait_until = "domcontentloaded" if is_twitter else "networkidle"
        timeout = 60000 if is_twitter else 30000  # 60s for Twitter, 30s for others

        try:
            # Navigate to URL
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)
            status_code = response.status if response else 200

            # Wait for DOM readiness (skip networkidle wait for Twitter)
            if not is_twitter:
                await self._wait_for_dom_ready(page)
            else:
                # For Twitter, just wait a bit for JS to execute
                await asyncio.sleep(3.0)

            # Handle infinite scroll if enabled
            if (
                hasattr(self.config, "handle_infinite_scroll")
                and self.config.handle_infinite_scroll
            ):
                await self._handle_infinite_scroll(page)

            # Get rendered HTML
            html = await page.content()

            # Capture screenshot if requested
            screenshot: Optional[bytes] = None
            if capture_screenshot:
                screenshot = await page.screenshot(full_page=True, type="png")

                # Save to file if path provided
                if screenshot_path:
                    Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot)

            return BrowserResult(html=html, screenshot=screenshot, url=url, status_code=status_code)

        except Exception as e:
            logger.error(f"Error fetching {url} with browser: {e}")
            # Fallback to HTTP
            return await self._fetch_with_http(url)
        finally:
            await page.close()

    async def _handle_infinite_scroll(self, page: Page, max_scrolls: int = 10):
        """Handle infinite scroll pages"""
        last_height = await page.evaluate("document.body.scrollHeight")
        scrolls = 0

        while scrolls < max_scrolls:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scrolls += 1

    async def _fetch_with_http(self, url: str) -> BrowserResult:
        """Fallback to aiohttp when JS is not needed"""
        await self._initialize_http_fallback()

        if not self._http_session:
            raise RuntimeError("HTTP session not initialized")

        try:
            async with self._http_session.get(url, allow_redirects=True) as response:
                html = await response.text()
                return BrowserResult(
                    html=html, screenshot=None, url=str(response.url), status_code=response.status
                )
        except Exception as e:
            logger.error(f"Error fetching {url} with HTTP: {e}")
            return BrowserResult(html="", screenshot=None, url=url, status_code=0)

    async def close(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        if self._http_session:
            await self._http_session.close()
            self._http_session = None

        logger.info("Browser scraper closed")
