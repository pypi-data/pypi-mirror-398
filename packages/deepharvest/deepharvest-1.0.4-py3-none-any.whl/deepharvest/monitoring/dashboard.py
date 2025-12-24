"""
Grafana dashboard configs
"""

import logging

logger = logging.getLogger(__name__)

DASHBOARD_CONFIG = {
    "dashboard": {
        "title": "DeepHarvest Metrics",
        "panels": [
            {"title": "Pages Crawled", "targets": [{"expr": "deepharvest_pages_crawled_total"}]}
        ],
    }
}
