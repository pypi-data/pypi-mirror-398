"""
link_extractor.py - Advanced link extraction
"""

import logging
import re
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

logger = logging.getLogger(__name__)


class AdvancedLinkExtractor:
    """Extract links from HTML with various strategies"""

    async def extract(self, response, base_url: str) -> List[str]:
        """Extract all links from response"""
        urls = []

        if hasattr(response, "text") and response.text:
            html = response.text
        elif hasattr(response, "content"):
            html = response.content.decode("utf-8", errors="ignore")
        else:
            return urls

        soup = BeautifulSoup(html, "lxml")

        # Extract <a> tags
        for link in soup.find_all("a", href=True):
            url = urljoin(base_url, link["href"])
            urls.append(url)

        # Extract <link> tags
        for link in soup.find_all("link", href=True):
            url = urljoin(base_url, link["href"])
            urls.append(url)

        # Extract <script src>
        for script in soup.find_all("script", src=True):
            url = urljoin(base_url, script["src"])
            urls.append(url)

        # Extract <img src> and srcset
        for img in soup.find_all("img"):
            if img.get("src"):
                urls.append(urljoin(base_url, img["src"]))
            if img.get("srcset"):
                # Parse srcset (format: "url1 1x, url2 2x")
                srcset = img["srcset"]
                for item in srcset.split(","):
                    url = item.strip().split()[0]
                    urls.append(urljoin(base_url, url))

        # Extract <picture> sources
        for picture in soup.find_all("picture"):
            for source in picture.find_all("source", srcset=True):
                srcset = source["srcset"]
                for item in srcset.split(","):
                    url = item.strip().split()[0]
                    urls.append(urljoin(base_url, url))

        # Extract URLs from inline JavaScript
        js_urls = self._extract_js_urls(html, base_url)
        urls.extend(js_urls)

        # Extract blob and data URIs (for reference)
        blob_urls = self._extract_blob_urls(html)
        urls.extend(blob_urls)

        # Extract meta refresh URLs
        meta_refresh = soup.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)})
        if meta_refresh and meta_refresh.get("content"):
            content = meta_refresh["content"]
            url_match = re.search(r"url=([^;]+)", content, re.I)
            if url_match:
                urls.append(urljoin(base_url, url_match.group(1)))

        return urls

    def _extract_js_urls(self, html: str, base_url: str) -> List[str]:
        """Extract URLs from inline JavaScript"""
        urls = []

        # Common patterns for URLs in JS
        patterns = [
            r'["\'](https?://[^"\']+)["\']',
            r'["\'](/[^"\']+)["\']',
            r'url:\s*["\']([^"\']+)["\']',
            r'href:\s*["\']([^"\']+)["\']',
            r'src:\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, html)
            for match in matches:
                url = match.group(1)
                if url.startswith("http"):
                    urls.append(url)
                elif url.startswith("/"):
                    urls.append(urljoin(base_url, url))

        return urls

    def _extract_blob_urls(self, html: str) -> List[str]:
        """Extract blob: and data: URIs (for reference, not crawlable)"""
        urls = []

        blob_pattern = r'blob:https?://[^\s"\'<>]+'
        data_pattern = r'data:[^;]+;base64,[^\s"\'<>]+'

        urls.extend(re.findall(blob_pattern, html))
        urls.extend(re.findall(data_pattern, html))

        return urls
