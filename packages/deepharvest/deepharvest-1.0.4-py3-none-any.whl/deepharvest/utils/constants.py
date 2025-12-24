"""
Constants for DeepHarvest
"""

from enum import Enum


class PageType(Enum):
    """Page type enumeration"""

    NEWS = "news"
    BLOG = "blog"
    PRODUCT = "product"
    HOMEPAGE = "homepage"
    CATEGORY = "category"
    DOCUMENTATION = "documentation"
    GENERIC = "generic"


class ExportFormat(Enum):
    """Export format enumeration"""

    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"
    SQLITE = "sqlite"
    GRAPHML = "graphml"
    VECTORDB_FAISS = "vectordb_faiss"
    VECTORDB_CHROMA = "vectordb_chroma"


# Default values
DEFAULT_CONCURRENT_REQUESTS = 10
DEFAULT_PER_HOST_CONCURRENT = 2
DEFAULT_REQUEST_DELAY_MS = 100
DEFAULT_MAX_DEPTH = 5
DEFAULT_TIMEOUT = 30

# User agents
DEFAULT_USER_AGENT = "DeepHarvest/1.0 (+https://github.com/deepharvest/deepharvest)"

# File size limits
DEFAULT_MAX_SIZE_MB = 50
DEFAULT_STREAMING_THRESHOLD_MB = 50

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_BACKOFF_FACTOR = 2.0
