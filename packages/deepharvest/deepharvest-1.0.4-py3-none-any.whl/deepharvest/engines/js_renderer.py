"""
js_renderer.py - Playwright/Puppeteer integration
"""

import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from ..core.crawler import CrawlConfig

logger = logging.getLogger(__name__)


class JSRenderer:
    """JavaScript rendering engine using Playwright"""

    def __init__(self, config: CrawlConfig):
        self.config = config
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("JavaScript renderer initialized")

    async def render(self, url: str, response) -> Optional[object]:
        """Render page with JavaScript"""
        if not self.browser:
            return response

        page: Page = await self.browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for JS to execute
            await page.wait_for_timeout(self.config.wait_for_js_ms)

            # Handle infinite scroll if enabled
            if self.config.handle_infinite_scroll:
                await self._handle_infinite_scroll(page)

            # Get rendered HTML
            html = await page.content()

            # Update response with rendered HTML
            # Set internal attributes directly since text/content are properties
            if hasattr(response, "_text"):
                response._text = html
            if hasattr(response, "_content"):
                response._content = html.encode("utf-8")

            return response

        except Exception as e:
            logger.error(f"Error rendering {url}: {e}")
            return response
        finally:
            await page.close()

    async def _handle_infinite_scroll(self, page: Page):
        """Handle infinite scroll pages"""
        last_height = await page.evaluate("document.body.scrollHeight")

        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
