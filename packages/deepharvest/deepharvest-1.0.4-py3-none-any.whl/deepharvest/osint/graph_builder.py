"""
OSINT Link Graph Builder
"""

import logging
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import networkx as nx

logger = logging.getLogger(__name__)


class OSINTGraphBuilder:
    """Build link graph for OSINT analysis"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.visited: Set[str] = set()

    def add_page(self, url: str, html: str, metadata: Dict = None):
        """Add a page and its links to the graph"""
        if url in self.visited:
            return

        self.visited.add(url)

        # Add node
        self.graph.add_node(url, **metadata or {})

        # Extract and add links
        links = self._extract_links(html, url)
        for link_url in links:
            self.graph.add_edge(url, link_url)

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML"""
        links = []

        try:
            soup = BeautifulSoup(html, "html.parser")
            base_parsed = urlparse(base_url)

            for link in soup.find_all("a", href=True):
                href = link["href"]

                # Resolve relative URLs
                if href.startswith("#"):
                    continue

                try:
                    parsed = urlparse(href)
                    if not parsed.netloc:
                        # Relative URL
                        full_url = urljoin(base_url, href)
                    else:
                        # Absolute URL
                        full_url = href

                    # Normalize URL
                    full_url = self._normalize_url(full_url)

                    if full_url and full_url.startswith(("http://", "https://")):
                        links.append(full_url)
                except Exception as e:
                    logger.debug(f"Error parsing link {href}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error extracting links: {e}")

        return links

    def _normalize_url(self, url: str) -> str:
        """Normalize URL"""
        try:
            parsed = urlparse(url)
            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.rstrip("/")
        except:
            return url

    def get_graph(self) -> nx.DiGraph:
        """Get the NetworkX graph"""
        return self.graph

    def export_graphml(self, filename: str):
        """Export to GraphML format"""
        nx.write_graphml(self.graph, filename)
        logger.info(f"Exported graph to {filename}")

    def export_json(self) -> Dict:
        """Export graph as JSON"""
        return {
            "nodes": [{"id": node, **self.graph.nodes[node]} for node in self.graph.nodes()],
            "edges": [
                {"source": source, "target": target} for source, target in self.graph.edges()
            ],
            "stats": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "density": nx.density(self.graph),
            },
        }

    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        if self.graph.number_of_nodes() == 0:
            return {"nodes": 0, "edges": 0, "density": 0.0}

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph),
            "components": nx.number_weakly_connected_components(self.graph),
        }
