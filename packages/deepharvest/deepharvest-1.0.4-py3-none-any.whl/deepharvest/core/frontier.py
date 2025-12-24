"""
frontier.py - URL Frontier Management
"""

import asyncio
from typing import Optional, Tuple
from .crawler import CrawlStrategy


class LocalFrontier:
    """Local in-memory frontier with BFS/DFS/Priority support"""

    def __init__(self, strategy: CrawlStrategy):
        self.strategy = strategy
        self.queue = asyncio.Queue() if strategy == CrawlStrategy.BFS else asyncio.LifoQueue()
        self._stopped = False  # Flag to stop accepting new URLs

    async def add(self, url: str, depth: int, priority: float):
        """Add URL to queue if not stopped"""
        if not self._stopped:
            await self.queue.put((url, depth, priority))

    async def get(self):
        """Get next URL from queue"""
        if self._stopped and self.queue.empty():
            return None
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    async def mark_done(self, url: str):
        """Mark URL as processed"""
        self.queue.task_done()

    def stop(self):
        """Stop accepting new URLs"""
        self._stopped = True

    def is_stopped(self) -> bool:
        """Check if frontier is stopped"""
        return self._stopped
