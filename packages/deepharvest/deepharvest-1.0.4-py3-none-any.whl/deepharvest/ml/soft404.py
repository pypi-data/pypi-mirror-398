"""
Soft 404 Detection
"""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Soft404Detector:
    """Detect soft 404 pages (pages that return 200 but are actually errors)"""

    SOFT_404_INDICATORS = [
        "page not found",
        "404 error",
        "not found",
        "does not exist",
        "no longer available",
        "this page cannot be found",
        "the page you are looking for",
    ]

    async def load(self):
        """Load model"""
        logger.info("Soft 404 detector loaded")

    async def is_soft_404(self, response) -> bool:
        """Detect if page is a soft 404"""

        if not response:
            return False

        # Check status code
        status_code = getattr(response, "status_code", None)
        if status_code in [404, 410]:
            return True

        # Check content
        if not hasattr(response, "text") or not response.text:
            return False

        text = response.text.lower()

        # Require longer content to avoid false positives
        if len(text) < 200:
            # Very short pages with specific error indicators
            if any(indicator in text for indicator in ["page not found", "404 error", "not found"]):
                return True
            return False

        # Count specific indicators (not generic words like "error")
        indicator_count = sum(1 for indicator in self.SOFT_404_INDICATORS if indicator in text)

        # Require multiple indicators for longer pages
        if len(text) < 1000 and indicator_count >= 2:
            return True

        if indicator_count >= 3:
            return True

        # Check title - more specific
        try:
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.find("title")

            if title:
                title_text = title.get_text().lower()
                if any(
                    indicator in title_text
                    for indicator in ["404", "not found", "page not found", "error"]
                ):
                    return True
        except:
            pass

        return False
