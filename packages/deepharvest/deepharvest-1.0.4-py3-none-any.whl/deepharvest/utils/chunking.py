"""
chunking.py - Chunking for huge binary files
"""

import logging
from typing import Iterator
from io import BytesIO

logger = logging.getLogger(__name__)


class BinaryChunker:
    """Chunk large binary files for processing"""

    def __init__(self, chunk_size: int = 10 * 1024 * 1024):  # 10MB default
        self.chunk_size = chunk_size

    def chunk_file(self, content: bytes) -> Iterator[bytes]:
        """Yield chunks of binary content"""
        buffer = BytesIO(content)

        while True:
            chunk = buffer.read(self.chunk_size)
            if not chunk:
                break
            yield chunk

    def process_in_chunks(self, content: bytes, processor):
        """Process file in chunks"""
        for chunk in self.chunk_file(content):
            processor(chunk)
