"""
clustering.py - Content clustering and similarity grouping
"""

import logging
from typing import List, Dict, Set
from collections import defaultdict
from .similarity import SimilarityScorer

logger = logging.getLogger(__name__)


class ContentClustering:
    """Cluster similar pages together"""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.scorer = SimilarityScorer()
        self.clusters = defaultdict(list)

    async def add_page(self, url: str, text: str) -> int:
        """Add page to appropriate cluster, returns cluster ID"""
        # Find best matching cluster
        best_cluster = None
        best_similarity = 0.0

        for cluster_id, cluster_pages in self.clusters.items():
            # Compare with first page in cluster (representative)
            if cluster_pages:
                rep_url, rep_text = cluster_pages[0]
                similarity = await self.scorer.calculate_similarity(text, rep_text)

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_cluster = cluster_id

        # Add to existing cluster or create new
        if best_cluster is not None:
            self.clusters[best_cluster].append((url, text))
            return best_cluster
        else:
            # Create new cluster
            new_cluster_id = len(self.clusters)
            self.clusters[new_cluster_id].append((url, text))
            return new_cluster_id

    def get_clusters(self) -> Dict[int, List[str]]:
        """Get all clusters with URLs"""
        return {
            cluster_id: [url for url, _ in pages] for cluster_id, pages in self.clusters.items()
        }

    def get_cluster_sizes(self) -> Dict[int, int]:
        """Get size of each cluster"""
        return {cluster_id: len(pages) for cluster_id, pages in self.clusters.items()}

    async def detect_duplicates_across_site(self, pages: List[tuple]) -> Set[tuple]:
        """Detect duplicate pages across the site"""
        duplicates = set()

        for i, (url1, text1) in enumerate(pages):
            for j, (url2, text2) in enumerate(pages[i + 1 :], i + 1):
                similarity = await self.scorer.calculate_similarity(text1, text2)
                if similarity >= self.similarity_threshold:
                    duplicates.add((url1, url2))

        return duplicates
