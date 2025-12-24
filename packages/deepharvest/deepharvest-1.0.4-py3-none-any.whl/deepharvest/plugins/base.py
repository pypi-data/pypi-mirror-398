"""
Plugin interface
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base plugin interface"""

    @abstractmethod
    async def initialize(self):
        """Initialize plugin"""
        pass

    @abstractmethod
    async def process(self, url: str, response) -> Dict[str, Any]:
        """Process content"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Cleanup resources"""
        pass
