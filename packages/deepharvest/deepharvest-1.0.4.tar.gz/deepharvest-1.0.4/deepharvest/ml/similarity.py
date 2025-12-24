"""
similarity.py - Content similarity scoring
"""

import logging
from typing import Dict
from .dedup import NearDuplicateDetector

logger = logging.getLogger(__name__)


class SimilarityScorer:
    """Score similarity between pages"""

    def __init__(self):
        self.detector = NearDuplicateDetector()

    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts (0-1)"""

        # Use SimHash for fast similarity
        hash1 = self.detector.get_simhash(text1)
        hash2 = self.detector.get_simhash(text2)

        # Calculate Hamming distance
        hamming = bin(hash1 ^ hash2).count("1")
        similarity = 1 - (hamming / 64.0)

        return max(0.0, min(1.0, similarity))

    async def are_meaningfully_different(
        self, text1: str, text2: str, threshold: float = 0.1
    ) -> bool:
        """Decide if two pages are meaningfully different"""
        similarity = await self.calculate_similarity(text1, text2)
        return similarity < (1.0 - threshold)
