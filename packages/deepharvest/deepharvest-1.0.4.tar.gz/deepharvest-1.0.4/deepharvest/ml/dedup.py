"""
Near-duplicate content detection using SimHash and MinHash
"""

import logging
from typing import Dict
from simhash import Simhash
from datasketch import MinHash, MinHashLSH

logger = logging.getLogger(__name__)


class NearDuplicateDetector:
    """Near-duplicate content detection"""

    def __init__(self):
        self.simhashes = {}
        self.minhash_lsh = MinHashLSH(threshold=0.8, num_perm=128)

    async def load(self):
        """Load model"""
        logger.info("Near-duplicate detector loaded")

    def get_simhash(self, text: str) -> int:
        """Calculate SimHash"""
        return Simhash(text).value

    def get_minhash(self, text: str) -> MinHash:
        """Calculate MinHash"""
        m = MinHash(num_perm=128)

        # Tokenize text
        words = text.lower().split()

        for word in words:
            m.update(word.encode("utf-8"))

        return m

    async def is_duplicate(self, url: str, text: str, threshold: float = 0.9) -> bool:
        """Check if content is near-duplicate"""

        # Calculate SimHash
        simhash = self.get_simhash(text)

        # Check against existing hashes first
        for existing_url, existing_hash in self.simhashes.items():
            # Calculate Hamming distance
            hamming = bin(simhash ^ existing_hash).count("1")
            similarity = 1 - (hamming / 64.0)

            if similarity >= threshold:
                logger.info(
                    f"Near-duplicate detected: {url} similar to {existing_url} (similarity: {similarity:.2f})"
                )
                return True

        # Also use MinHash LSH (check before storing)
        minhash = self.get_minhash(text)

        # Query LSH
        result = self.minhash_lsh.query(minhash)

        if result:
            logger.info(f"LSH duplicate detected: {url}")
            return True

        # Store hash and insert into LSH only if not duplicate
        self.simhashes[url] = simhash
        self.minhash_lsh.insert(url, minhash)

        return False
