"""
Example Custom Extractor Plugin
"""

from typing import Dict, Any
from ...plugins.base import Plugin


class CustomExtractor(Plugin):
    """Example custom content extractor plugin"""

    async def initialize(self):
        """Initialize plugin"""
        pass

    async def process(self, url: str, response) -> Dict[str, Any]:
        """Process content and extract custom data"""
        html = getattr(response, "text", "") if response else ""

        # Example: Extract custom metadata
        result = {"custom_field": "custom_value", "url": url, "content_length": len(html)}

        return result

    async def shutdown(self):
        """Cleanup resources"""
        pass
