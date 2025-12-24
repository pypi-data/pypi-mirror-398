"""
Redis-based Distributed Frontier
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, Any, List, Set, Optional, Tuple
from datetime import datetime
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisFrontier:
    """
    Distributed URL frontier using Redis
    Supports multiple strategies: BFS, DFS, Priority Queue
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

        # Redis key prefixes
        self.QUEUE_KEY = "deepharvest:queue"
        self.PRIORITY_QUEUE_KEY = "deepharvest:priority_queue"
        self.VISITED_SET_KEY = "deepharvest:visited"
        self.CONTENT_HASH_KEY = "deepharvest:content_hashes"
        self.IN_PROGRESS_KEY = "deepharvest:in_progress"
        self.STATS_KEY = "deepharvest:stats"
        self.LOCKS_KEY = "deepharvest:locks"

    async def connect(self):
        """Connect to Redis"""
        self.redis = await aioredis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=False  # Handle binary data
        )
        logger.info("Connected to Redis frontier")

    async def add(self, url: str, depth: int, priority: float = 0.5):
        """Add URL to frontier"""

        # Check if already visited or in queue
        if await self.is_visited(url):
            return

        # Create item
        item = {
            "url": url,
            "depth": depth,
            "priority": priority,
            "added_at": datetime.utcnow().isoformat(),
        }

        item_json = json.dumps(item)

        # Add to priority queue with score
        await self.redis.zadd(self.PRIORITY_QUEUE_KEY, {item_json: priority})

        # Update stats
        await self.redis.hincrby(self.STATS_KEY, "queued", 1)

    async def get(self, timeout: float = 5.0) -> Optional[Tuple[str, int, float]]:
        """Get next URL from frontier (highest priority)"""

        try:
            # Pop highest priority item
            result = await self.redis.bzpopmax(self.PRIORITY_QUEUE_KEY, timeout=timeout)

            if not result:
                return None

            _, item_json, score = result
            item = json.loads(item_json)

            # Add to in-progress set
            await self.redis.sadd(self.IN_PROGRESS_KEY, item["url"])

            return item["url"], item["depth"], item["priority"]

        except asyncio.TimeoutError:
            return None

    async def mark_done(self, url: str):
        """Mark URL as completed"""

        # Remove from in-progress
        await self.redis.srem(self.IN_PROGRESS_KEY, url)

        # Add to visited set
        await self.mark_visited(url)

        # Update stats
        await self.redis.hincrby(self.STATS_KEY, "processed", 1)

    async def is_visited(self, url: str) -> bool:
        """Check if URL has been visited"""

        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return await self.redis.sismember(self.VISITED_SET_KEY, url_hash)

    async def mark_visited(self, url: str):
        """Mark URL as visited"""

        url_hash = hashlib.sha256(url.encode()).hexdigest()
        await self.redis.sadd(self.VISITED_SET_KEY, url_hash)

    async def add_content_hash(self, url: str, content_hash: str) -> bool:
        """
        Add content hash for near-duplicate detection
        Returns True if content is unique, False if duplicate
        """

        # Check if hash already exists
        exists = await self.redis.sismember(self.CONTENT_HASH_KEY, content_hash)

        if exists:
            return False

        # Add hash and associate with URL
        await self.redis.sadd(self.CONTENT_HASH_KEY, content_hash)
        await self.redis.hset(f"{self.CONTENT_HASH_KEY}:urls", content_hash, url)

        return True

    async def get_stats(self) -> Dict[str, int]:
        """Get crawl statistics"""

        stats = await self.redis.hgetall(self.STATS_KEY)

        return {
            "queued": int(stats.get(b"queued", 0)),
            "processed": int(stats.get(b"processed", 0)),
            "in_progress": await self.redis.scard(self.IN_PROGRESS_KEY),
            "visited": await self.redis.scard(self.VISITED_SET_KEY),
        }

    async def acquire_lock(self, resource: str, timeout: int = 60) -> bool:
        """Acquire distributed lock"""

        lock_key = f"{self.LOCKS_KEY}:{resource}"
        lock_id = hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()

        # Try to acquire lock
        acquired = await self.redis.set(
            lock_key, lock_id, nx=True, ex=timeout  # Only set if doesn't exist  # Expiration
        )

        return bool(acquired)

    async def release_lock(self, resource: str):
        """Release distributed lock"""

        lock_key = f"{self.LOCKS_KEY}:{resource}"
        await self.redis.delete(lock_key)

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
