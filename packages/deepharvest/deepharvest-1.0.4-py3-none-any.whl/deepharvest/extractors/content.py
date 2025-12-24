"""
content.py - Content extraction coordinator
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Coordinate content extraction from various extractors"""

    def __init__(self):
        self.extractors = {}

    async def extract(self, response, extractors: Dict) -> Dict[str, Any]:
        """Extract content using available extractors"""
        result = {}

        content_type = getattr(response, "headers", {}).get("content-type", "").lower()

        if "text/html" in content_type and "text" in extractors:
            result["text"] = await extractors["text"].extract(response)

        return result
