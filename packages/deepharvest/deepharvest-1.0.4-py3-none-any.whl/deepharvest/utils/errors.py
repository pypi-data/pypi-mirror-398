"""
Error classification
"""

import logging

logger = logging.getLogger(__name__)


class DeepharvestError(Exception):
    """Base error for all DeepHarvest exceptions"""

    pass


class CrawlError(DeepharvestError):
    """Base crawl error"""

    pass


class NetworkError(CrawlError):
    """Network-related error"""

    pass


class ConnectionError(NetworkError):
    """Connection error"""

    pass


class ParseError(CrawlError):
    """Parsing error"""

    pass


class ExtractionError(CrawlError):
    """Content extraction error"""

    pass


class TrapDetectedError(CrawlError):
    """Trap detected error"""

    pass


class ClassifierError(DeepharvestError):
    """ML classifier error"""

    pass


class PluginLoadError(DeepharvestError):
    """Plugin loading error"""

    pass
