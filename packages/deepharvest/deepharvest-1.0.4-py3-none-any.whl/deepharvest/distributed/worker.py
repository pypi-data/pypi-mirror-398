"""
Worker Process Implementation
"""

import asyncio
import logging
from typing import Dict
from dataclasses import dataclass
from urllib.parse import urlparse
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    worker_id: str
    redis_url: str
    concurrent_requests: int = 5
    per_host_limit: int = 2
    request_timeout: int = 30


class Worker:
    """
    Stateless worker process for distributed crawling
    """

    def __init__(self, config: WorkerConfig):
        self.config = config
        self.frontier = None
        self.running = False
        self.host_semaphores = defaultdict(lambda: asyncio.Semaphore(config.per_host_limit))

    async def start(self):
        """Start worker"""

        logger.info(f"Starting worker {self.config.worker_id}")

        from .redis_frontier import RedisFrontier

        self.frontier = RedisFrontier(self.config.redis_url)
        await self.frontier.connect()
        self.running = True

        # Create worker tasks
        tasks = [
            asyncio.create_task(self._worker_loop()) for _ in range(self.config.concurrent_requests)
        ]

        # Wait for all tasks
        await asyncio.gather(*tasks)

        logger.info(f"Worker {self.config.worker_id} stopped")

    async def _worker_loop(self):
        """Main worker loop"""

        while self.running:
            try:
                # Get next URL from frontier
                item = await self.frontier.get(timeout=5.0)

                if item is None:
                    continue

                url, depth, priority = item

                # Get host for rate limiting
                host = urlparse(url).netloc

                # Respect per-host concurrency
                async with self.host_semaphores[host]:
                    await self._process_url(url, depth, priority)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)

    async def _process_url(self, url: str, depth: int, priority: float):
        """Process single URL"""

        # Implementation would call main crawler logic
        logger.debug(f"Worker {self.config.worker_id} processing {url}")

        # Simulate processing
        await asyncio.sleep(0.1)

        # Mark as done
        await self.frontier.mark_done(url)

    async def stop(self):
        """Graceful shutdown"""

        logger.info(f"Stopping worker {self.config.worker_id}")
        self.running = False
        if self.frontier:
            await self.frontier.close()
