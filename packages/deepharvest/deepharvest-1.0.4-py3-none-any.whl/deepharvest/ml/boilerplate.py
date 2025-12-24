"""
boilerplate.py - HTML boilerplate removal
"""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BoilerplateRemover:
    """Remove HTML boilerplate (headers, footers, nav, ads)"""

    def __init__(self):
        self.boilerplate_selectors = [
            "header",
            "footer",
            "nav",
            "aside",
            ".advertisement",
            ".ad",
            ".sidebar",
            ".navigation",
            ".menu",
            ".footer",
            "#header",
            "#footer",
            "#nav",
            "#sidebar",
        ]

    def remove_boilerplate(self, html: str) -> str:
        """Remove boilerplate from HTML"""
        soup = BeautifulSoup(html, "lxml")

        # Remove common boilerplate elements
        for selector in self.boilerplate_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Remove script and style tags
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Get clean text
        text = soup.get_text(separator=" ", strip=True)

        # Remove excessive whitespace
        text = " ".join(text.split())

        return text

    def extract_main_content(self, html: str) -> str:
        """Extract main content area"""
        soup = BeautifulSoup(html, "lxml")

        # Try to find main content areas
        main_selectors = ["main", "article", ".content", ".main-content", "#content", "#main"]

        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator=" ", strip=True)

        # Fallback: remove boilerplate and return remaining
        return self.remove_boilerplate(html)
