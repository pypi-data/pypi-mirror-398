"""
Site graph construction
"""

import logging
from typing import Dict, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class SiteGraphBuilder:
    """Build site graph from crawl results"""

    def __init__(self):
        self.nodes = {}
        self.edges = []

    async def build(self) -> Dict:
        """Build site graph"""
        graph = {"nodes": list(self.nodes.values()), "edges": self.edges}
        return graph

    def add_node(self, url: str, metadata: Dict):
        """Add node to graph"""
        self.nodes[url] = {"url": url, "metadata": metadata}

    def add_edge(self, source: str, target: str):
        """Add edge to graph"""
        self.edges.append({"source": source, "target": target})
