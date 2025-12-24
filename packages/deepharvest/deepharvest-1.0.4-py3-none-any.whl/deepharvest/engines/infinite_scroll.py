"""
infinite_scroll.py - Auto-scroll handler
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class InfiniteScrollHandler:
    """Handle infinite scroll pages"""

    async def scroll_to_bottom(self, page: Page, max_scrolls: int = 10):
        """Scroll to bottom of page"""
        for _ in range(max_scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            # Check if new content loaded
            new_height = await page.evaluate("document.body.scrollHeight")
            current_scroll = await page.evaluate("window.pageYOffset")

            if current_scroll + 1000 >= new_height:
                break
