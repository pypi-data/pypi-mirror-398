"""
structured.py - JSON-LD, microdata, OpenGraph
"""

import logging
from typing import Dict, Any
import json
from bs4 import BeautifulSoup
import extruct

logger = logging.getLogger(__name__)


class StructuredDataExtractor:
    """Extract structured data from HTML"""

    async def extract(self, response) -> Dict[str, Any]:
        """Extract all structured data"""
        result = {"jsonld": [], "microdata": {}, "opengraph": {}, "twitter": {}}

        try:
            html = response.text if hasattr(response, "text") else response.content.decode("utf-8")
            soup = BeautifulSoup(html, "lxml")

            # Extract JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    result["jsonld"].append(data)
                except:
                    pass

            # Extract using extruct
            extracted = extruct.extract(html)
            result["microdata"] = extracted.get("microdata", {})

            # Extract OpenGraph
            for meta in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
                prop = meta.get("property", "").replace("og:", "")
                result["opengraph"][prop] = meta.get("content", "")

            # Extract Twitter Cards
            for meta in soup.find_all(
                "meta", attrs={"name": lambda x: x and x.startswith("twitter:")}
            ):
                name = meta.get("name", "").replace("twitter:", "")
                result["twitter"][name] = meta.get("content", "")

        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")

        return result
