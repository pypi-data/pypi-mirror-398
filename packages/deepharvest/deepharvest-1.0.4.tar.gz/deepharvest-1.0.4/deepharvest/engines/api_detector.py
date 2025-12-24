"""
api_detector.py - API endpoint detection and XHR/fetch capture
"""

import logging
import re
import json
from typing import List, Dict, Any
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


class APIDetector:
    """Detect API endpoints and capture XHR/fetch responses"""

    def __init__(self):
        self.api_patterns = [r"/api/", r"/v\d+/", r"/graphql", r"/rest/", r"\.json", r"\.xml"]

    def detect_api_endpoints(self, html: str, base_url: str) -> List[str]:
        """Detect API endpoints from HTML"""
        endpoints = []

        # Find API calls in JavaScript
        api_calls = re.findall(r'["\']([^"\']*(?:/api/|/v\d+/|/graphql|/rest/)[^"\']*)["\']', html)
        endpoints.extend(api_calls)

        # Find fetch/XHR calls
        fetch_pattern = r'fetch\(["\']([^"\']+)["\']'
        xhr_pattern = r'\.open\(["\'](GET|POST)["\'],\s*["\']([^"\']+)["\']'

        for match in re.finditer(fetch_pattern, html):
            endpoints.append(match.group(1))

        for match in re.finditer(xhr_pattern, html):
            endpoints.append(match.group(2))

        # Normalize URLs
        normalized = []
        for endpoint in endpoints:
            if endpoint.startswith("http"):
                normalized.append(endpoint)
            else:
                normalized.append(urljoin(base_url, endpoint))

        return list(set(normalized))

    async def extract_api_schema(self, json_content: str) -> Dict[str, Any]:
        """Extract data schema from JSON API response"""
        try:
            data = json.loads(json_content)
            schema = {
                "type": type(data).__name__,
                "keys": list(data.keys()) if isinstance(data, dict) else [],
                "sample": str(data)[:500],
            }
            return schema
        except:
            return {}
