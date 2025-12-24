"""
Example File Downloader Plugin
"""

from typing import Dict, Any
from ...plugins.base import Plugin


class FileDownloader(Plugin):
    """Example file downloader plugin"""

    async def initialize(self):
        """Initialize plugin"""
        pass

    async def process(self, url: str, response) -> Dict[str, Any]:
        """Download and process files"""
        content = getattr(response, "content", b"") if response else b""

        return {"url": url, "file_size": len(content), "downloaded": True}

    async def shutdown(self):
        """Cleanup resources"""
        pass
