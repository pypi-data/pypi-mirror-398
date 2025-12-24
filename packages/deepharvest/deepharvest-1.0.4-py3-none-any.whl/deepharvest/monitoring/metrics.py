"""
Prometheus metrics
"""

import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Define metrics
pages_crawled = Counter("deepharvest_pages_crawled_total", "Total pages crawled")
pages_failed = Counter("deepharvest_pages_failed_total", "Total pages failed")
queue_size = Gauge("deepharvest_queue_size", "Current queue size")
bandwidth = Counter("deepharvest_bandwidth_bytes", "Total bandwidth used")
response_time = Histogram("deepharvest_response_time_seconds", "Response time")


class MetricsCollector:
    """Collect and expose metrics"""

    def record_page_crawled(self):
        """Record successful page crawl"""
        pages_crawled.inc()

    def record_page_failed(self):
        """Record failed page crawl"""
        pages_failed.inc()

    def update_queue_size(self, size: int):
        """Update queue size"""
        queue_size.set(size)

    def record_bandwidth(self, bytes: int):
        """Record bandwidth usage"""
        bandwidth.inc(bytes)
