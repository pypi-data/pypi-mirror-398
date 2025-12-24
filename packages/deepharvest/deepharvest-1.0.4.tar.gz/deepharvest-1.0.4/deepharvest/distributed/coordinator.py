"""
Distributed Crawl Coordinator
"""

import asyncio
import logging
from typing import List
from .redis_frontier import RedisFrontier
from .worker import Worker, WorkerConfig

logger = logging.getLogger(__name__)


class DistributedCoordinator:
    """
    Coordinates distributed crawl across multiple workers
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.frontier = RedisFrontier(redis_url)
        self.workers: List[Worker] = []

    async def initialize(self, num_workers: int):
        """Initialize coordinator and workers"""

        await self.frontier.connect()

        # Create workers
        for i in range(num_workers):
            worker_config = WorkerConfig(worker_id=f"worker-{i}", redis_url=self.redis_url)
            worker = Worker(worker_config)
            self.workers.append(worker)

        logger.info(f"Initialized coordinator with {num_workers} workers")

    async def start_crawl(self, seed_urls: List[str]):
        """Start distributed crawl"""

        # Add seed URLs to frontier
        for url in seed_urls:
            await self.frontier.add(url, depth=0, priority=1.0)

        # Start all workers
        worker_tasks = [asyncio.create_task(worker.start()) for worker in self.workers]

        # Monitor progress
        monitor_task = asyncio.create_task(self._monitor_progress())

        # Wait for completion
        await asyncio.gather(*worker_tasks, monitor_task)

    async def _monitor_progress(self):
        """Monitor crawl progress"""

        while True:
            stats = await self.frontier.get_stats()
            logger.info(f"Crawl stats: {stats}")

            # Check if done
            if stats["queued"] == 0 and stats["in_progress"] == 0:
                logger.info("Crawl complete")
                break

            await asyncio.sleep(10)

    async def shutdown(self):
        """Shutdown all workers"""

        for worker in self.workers:
            await worker.stop()

        await self.frontier.close()
