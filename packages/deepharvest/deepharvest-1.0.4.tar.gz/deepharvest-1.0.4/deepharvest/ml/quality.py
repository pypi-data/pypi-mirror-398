"""
Content Quality Scoring
"""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class QualityScorer:
    """Score content quality"""

    async def load(self):
        """Load model"""
        logger.info("Quality scorer loaded")

    async def score(self, html: str) -> float:
        """Score content quality (0-1)"""

        soup = BeautifulSoup(html, "lxml")

        score = 0.5  # Base score

        # Positive indicators
        text = soup.get_text()
        word_count = len(text.split())

        if word_count > 300:
            score += 0.1
        if word_count > 1000:
            score += 0.1

        # Has headings
        if soup.find_all(["h1", "h2", "h3"]):
            score += 0.1

        # Has images with alt text
        images_with_alt = len([img for img in soup.find_all("img") if img.get("alt")])
        if images_with_alt > 0:
            score += 0.1

        # Has structured data
        if soup.find("script", type="application/ld+json"):
            score += 0.1

        # Negative indicators
        ad_indicators = text.lower().count("advertisement") + text.lower().count("sponsored")
        if ad_indicators > 5:
            score -= 0.2

        return max(0.0, min(1.0, score))
