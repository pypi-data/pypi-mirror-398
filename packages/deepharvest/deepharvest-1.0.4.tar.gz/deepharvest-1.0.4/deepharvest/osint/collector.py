"""
OSINT Collector - Main OSINT collection interface
"""

import logging
from typing import Dict, Optional
from pathlib import Path
import json
from ..browser import BrowserScraper
from .entities import EntityExtractor
from .tech_detector import TechDetector
from .graph_builder import OSINTGraphBuilder
from ..core.crawler import CrawlConfig

logger = logging.getLogger(__name__)


class OSINTCollector:
    """Main OSINT collection and analysis class"""

    def __init__(self, config: Optional[CrawlConfig] = None):
        self.config = config or CrawlConfig(seed_urls=[])
        self.browser: Optional[BrowserScraper] = None
        self.entity_extractor = EntityExtractor()
        self.tech_detector = TechDetector()
        self.graph_builder = OSINTGraphBuilder()
        self.results: Dict = {}

    async def initialize(self):
        """Initialize browser scraper"""
        self.browser = BrowserScraper(self.config)
        await self.browser.initialize()

    async def collect(self, url: str, capture_screenshot: bool = True) -> Dict:
        """
        Collect OSINT data from a URL

        Returns:
            Dict with entities, tech_stack, graph_data, screenshot_path
        """
        if not self.browser:
            await self.initialize()

        result = {
            "url": url,
            "entities": {},
            "tech_stack": {},
            "graph_data": {},
            "screenshot_path": None,
            "html": "",
        }

        try:
            # Fetch page with browser
            screenshot_path = (
                f"/tmp/osint_screenshot_{hash(url)}.png" if capture_screenshot else None
            )
            browser_result = await self.browser.fetch(
                url,
                use_js=True,
                capture_screenshot=capture_screenshot,
                screenshot_path=screenshot_path,
            )

            result["html"] = browser_result.html
            result["screenshot_path"] = screenshot_path if capture_screenshot else None

            # Extract entities
            result["entities"] = self.entity_extractor.extract(browser_result.html, url)

            # Detect technology stack
            headers = browser_result.headers if hasattr(browser_result, "headers") else {}
            result["tech_stack"] = self.tech_detector.detect(browser_result.html, headers, url)

            # Build link graph
            self.graph_builder.add_page(
                url,
                browser_result.html,
                {"entities": result["entities"], "tech_stack": result["tech_stack"]},
            )
            result["graph_data"] = self.graph_builder.export_json()

            self.results[url] = result

        except Exception as e:
            logger.error(f"OSINT collection error for {url}: {e}")
            result["error"] = str(e)

        return result

    async def collect_many(self, urls: list, capture_screenshots: bool = True) -> Dict[str, Dict]:
        """Collect OSINT data from multiple URLs"""
        results = {}

        for url in urls:
            results[url] = await self.collect(url, capture_screenshots)

        return results

    def get_graph(self):
        """Get the link graph"""
        return self.graph_builder.get_graph()

    def export_graphml(self, filename: str):
        """Export graph to GraphML"""
        self.graph_builder.export_graphml(filename)

    def export_json(self, filename: Optional[str] = None) -> Dict:
        """Export all results as JSON"""
        export_data = {
            "results": self.results,
            "graph": self.graph_builder.export_json(),
            "statistics": self.graph_builder.get_statistics(),
        }

        if filename:
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported OSINT data to {filename}")

        return export_data

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
