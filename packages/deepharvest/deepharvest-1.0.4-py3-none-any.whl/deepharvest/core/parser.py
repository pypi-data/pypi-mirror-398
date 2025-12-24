"""
parser.py - Multi-strategy HTML parser
"""

import logging
from bs4 import BeautifulSoup
import html5lib

logger = logging.getLogger(__name__)


class MultiStrategyParser:
    """HTML parser with multiple fallback strategies"""

    def __init__(self):
        self.strategies = ["lxml", "html5lib", "html.parser"]

    async def parse(self, html: str):
        """Parse HTML with fallback strategies"""
        last_error = None

        # Try lxml first (fastest, most strict)
        try:
            soup = BeautifulSoup(html, "lxml")
            if soup and soup.find("html"):
                return soup
        except Exception as e:
            last_error = e
            logger.debug(f"lxml parser failed: {e}")

        # Try html5lib (most tolerant)
        try:
            soup = BeautifulSoup(html, "html5lib")
            if soup and soup.find("html"):
                return soup
        except Exception as e:
            last_error = e
            logger.debug(f"html5lib parser failed: {e}")

        # Try html.parser (built-in, most forgiving)
        try:
            soup = BeautifulSoup(html, "html.parser")
            return soup
        except Exception as e:
            last_error = e
            logger.debug(f"html.parser failed: {e}")

        # Ultra-tolerant fallback: create minimal soup
        try:
            # Remove null bytes and other problematic chars
            cleaned = html.replace("\x00", "")
            soup = BeautifulSoup(cleaned, "html.parser", parse_only=None)
            return soup
        except Exception as e:
            logger.error(f"All parsers failed. Last error: {last_error}")
            # Return empty soup as last resort
            return BeautifulSoup("", "html.parser")
