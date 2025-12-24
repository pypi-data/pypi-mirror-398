"""
DeepHarvest - The World's Most Complete Web Crawler
"""

from .core.crawler import DeepHarvest, CrawlConfig, CrawlStrategy
from .__version__ import __version__

__all__ = ["DeepHarvest", "CrawlConfig", "CrawlStrategy", "__version__"]
