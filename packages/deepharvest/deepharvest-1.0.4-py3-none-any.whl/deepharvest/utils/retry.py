"""
Retry logic with backoff
"""

import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    func: Callable, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0
) -> Any:
    """Retry function with exponential backoff"""
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= backoff_factor

    raise Exception("Max retries exceeded")
