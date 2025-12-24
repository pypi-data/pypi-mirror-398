"""
memory_guard.py - Memory guards per worker
"""

import logging
import psutil
import os
from typing import Optional

logger = logging.getLogger(__name__)


class MemoryGuard:
    """Monitor and limit memory usage per worker"""

    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process(os.getpid())

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def is_over_limit(self) -> bool:
        """Check if memory usage exceeds limit"""
        return self.get_memory_usage_mb() > self.max_memory_mb

    def should_pause(self) -> bool:
        """Determine if worker should pause due to memory"""
        if self.is_over_limit():
            logger.warning(
                f"Memory usage {self.get_memory_usage_mb():.1f}MB exceeds limit {self.max_memory_mb}MB"
            )
            return True
        return False
