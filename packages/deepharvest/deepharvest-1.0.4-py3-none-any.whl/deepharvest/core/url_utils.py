"""
url_utils.py - URL normalization & dedup
"""

import re
import hashlib
from typing import List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from bs4 import BeautifulSoup


class URLNormalizer:
    """Advanced URL normalization and canonicalization"""

    # Common tracking parameters to remove
    TRACKING_PARAMS = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "msclkid",
        "_ga",
        "_gl",
        "mc_cid",
        "mc_eid",
        "ref",
        "referrer",
        "source",
        "campaign",
    }

    @staticmethod
    def normalize(url: str) -> str:
        """Normalize URL"""

        parsed = urlparse(url)

        # Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if ":80" in netloc and scheme == "http":
            netloc = netloc.replace(":80", "")
        if ":443" in netloc and scheme == "https":
            netloc = netloc.replace(":443", "")

        # Normalize path
        path = parsed.path

        # Remove trailing slash (except for root)
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Collapse duplicate slashes
        path = re.sub(r"/+", "/", path)

        # Remove fragment
        fragment = ""

        # Clean parameters
        params = parse_qs(parsed.query, keep_blank_values=False)

        # Remove tracking parameters
        params = {k: v for k, v in params.items() if k not in URLNormalizer.TRACKING_PARAMS}

        # Sort parameters for consistency
        query = urlencode(sorted(params.items()), doseq=True)

        # Reconstruct URL
        normalized = urlunparse((scheme, netloc, path, "", query, fragment))

        return normalized

    @staticmethod
    def get_canonical_url(html: str, base_url: str) -> Optional[str]:
        """Extract canonical URL from HTML and JSON-LD"""
        import json

        soup = BeautifulSoup(html, "lxml")

        # Check HTML canonical tag
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            return urljoin(base_url, canonical["href"])

        # Check JSON-LD for canonical
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for @id or url field
                    canonical_url = (
                        data.get("@id")
                        or data.get("url")
                        or data.get("mainEntityOfPage", {}).get("@id")
                    )
                    if canonical_url:
                        return urljoin(base_url, canonical_url)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            canonical_url = item.get("@id") or item.get("url")
                            if canonical_url:
                                return urljoin(base_url, canonical_url)
            except:
                pass

        # Heuristic: if URL has no query params and is not too deep, it might be canonical
        parsed = urlparse(base_url)
        if not parsed.query and len(parsed.path.split("/")) <= 4:
            return base_url

        return None

    @staticmethod
    def generate_url_fingerprint(url: str) -> str:
        """Generate URL fingerprint for deduplication"""

        normalized = URLNormalizer.normalize(url)
        return hashlib.sha256(normalized.encode()).hexdigest()


def normalize_url(url: str) -> str:
    """Normalize a URL"""
    return URLNormalizer.normalize(url)


async def deduplicate_urls(urls: List[str]) -> List[str]:
    """Deduplicate URLs"""
    seen = set()
    result = []
    for url in urls:
        normalized = normalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
