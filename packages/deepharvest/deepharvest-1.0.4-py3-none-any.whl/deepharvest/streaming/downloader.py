"""
Streaming large files
"""

import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)


class StreamingDownloader:
    """Download large files in streaming mode"""

    async def download(self, url: str, output_path: str, chunk_size: int = 8192):
        """Download file in chunks"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                with open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
