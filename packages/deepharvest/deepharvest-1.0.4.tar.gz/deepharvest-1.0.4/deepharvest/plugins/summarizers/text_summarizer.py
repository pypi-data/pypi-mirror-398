"""
Example Text Summarizer Plugin
"""

from typing import Dict, Any
from ...plugins.base import Plugin


class TextSummarizer(Plugin):
    """Example text summarizer plugin"""

    async def initialize(self):
        """Initialize plugin"""
        pass

    async def process(self, url: str, response) -> Dict[str, Any]:
        """Summarize text content"""
        html = getattr(response, "text", "") if response else ""

        # Simple summarization (first 200 chars)
        summary = html[:200] + "..." if len(html) > 200 else html

        return {"summary": summary, "url": url, "summary_length": len(summary)}

    async def shutdown(self):
        """Cleanup resources"""
        pass
