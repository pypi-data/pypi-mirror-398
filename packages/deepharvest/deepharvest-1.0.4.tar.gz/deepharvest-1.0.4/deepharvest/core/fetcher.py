"""
fetcher.py - Advanced HTTP Client
"""

import logging
import aiohttp
from typing import Optional
from .crawler import CrawlConfig
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class AdvancedFetcher:
    """HTTP/2, HTTP/3 capable fetcher with connection pooling"""

    def __init__(self, config: CrawlConfig, site_rule_matcher=None):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector = None
        self.site_rule_matcher = site_rule_matcher

    async def initialize(self):
        """Initialize HTTP session with HTTP/2 support"""
        import sys
        import aiohttp
        from aiohttp import ClientSession, TCPConnector

        # Use ThreadedResolver on Windows to avoid aiodns issues
        resolver = None
        if sys.platform == "win32":
            from aiohttp.resolver import ThreadedResolver

            resolver = ThreadedResolver()

        # Try HTTP/2 connector
        try:
            # Create connector with HTTP/2 support if available
            connector = TCPConnector(
                limit=self.config.concurrent_requests,
                limit_per_host=self.config.per_host_concurrent,
                ssl=False,  # Can be configured
                resolver=resolver,  # Use Windows-compatible resolver
            )

            timeout = aiohttp.ClientTimeout(total=30)

            # Default headers
            headers = {
                "User-Agent": getattr(self.config, "user_agent", "DeepHarvest/1.0"),
                "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }

            # Apply custom headers from config if available
            if hasattr(self.config, "headers") and self.config.headers:
                headers.update(self.config.headers)

            self.session = ClientSession(connector=connector, timeout=timeout, headers=headers)
        except Exception as e:
            logger.warning(f"Failed to initialize HTTP/2 session: {e}, falling back to HTTP/1.1")
            # Fallback to standard session with Windows-compatible resolver
            try:
                self.session = ClientSession(resolver=resolver)
            except Exception as e2:
                logger.error(f"Failed to initialize fallback session: {e2}")
                # Last resort: use default resolver
                self.session = ClientSession()

    async def fetch(self, url: str, retries: int = 3):
        """Fetch URL with retries, compression, and error handling"""
        if not self.session:
            await self.initialize()

        # Get custom headers for this URL from site rules
        custom_headers = {}
        if self.site_rule_matcher:
            custom_ua = self.site_rule_matcher.get_custom_user_agent(url)
            if custom_ua:
                custom_headers["User-Agent"] = custom_ua
            custom_site_headers = self.site_rule_matcher.get_custom_headers(url)
            if custom_site_headers:
                custom_headers.update(custom_site_headers)

        async def _fetch():
            try:
                # Merge custom headers with session headers
                request_headers = dict(self.session.headers)
                request_headers.update(custom_headers)

                async with self.session.get(
                    url, allow_redirects=True, headers=request_headers
                ) as response:
                    # Create response-like object
                    class Response:
                        def __init__(self, resp):
                            self.status_code = resp.status
                            self.headers = resp.headers
                            self.url = str(resp.url)
                            self._content = None
                            self._text = None

                        @property
                        def content(self):
                            return self._content

                        @property
                        def text(self):
                            return self._text

                    resp_obj = Response(response)
                    resp_obj._content = await response.read()

                    # Try to decode text with proper encoding detection
                    try:
                        # First try aiohttp's built-in text() which uses charset from headers
                        resp_obj._text = await response.text()
                    except (UnicodeDecodeError, LookupError) as e:
                        # If that fails, try encoding detection
                        try:
                            import chardet

                            detected = chardet.detect(resp_obj._content)
                            encoding = detected.get("encoding", "utf-8")
                            if encoding:
                                resp_obj._text = resp_obj._content.decode(
                                    encoding, errors="replace"
                                )
                            else:
                                # Fallback to utf-8 with error replacement
                                resp_obj._text = resp_obj._content.decode("utf-8", errors="replace")
                        except ImportError:
                            # If chardet not available, try charset_normalizer
                            try:
                                from charset_normalizer import detect

                                detected = detect(resp_obj._content)
                                if detected and len(detected) > 0:
                                    encoding = detected[0].encoding
                                    resp_obj._text = resp_obj._content.decode(
                                        encoding, errors="replace"
                                    )
                                else:
                                    resp_obj._text = resp_obj._content.decode(
                                        "utf-8", errors="replace"
                                    )
                            except ImportError:
                                # Last resort: try common encodings
                                for enc in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]:
                                    try:
                                        resp_obj._text = resp_obj._content.decode(
                                            enc, errors="strict"
                                        )
                                        break
                                    except (UnicodeDecodeError, LookupError):
                                        continue
                                else:
                                    # If all fail, use replace mode
                                    resp_obj._text = resp_obj._content.decode(
                                        "utf-8", errors="replace"
                                    )
                        except Exception as decode_error:
                            logger.warning(
                                f"Encoding detection failed for {url}: {decode_error}, using utf-8 with replace"
                            )
                            resp_obj._text = resp_obj._content.decode("utf-8", errors="replace")

                    return resp_obj

            except aiohttp.ClientError as e:
                logger.error(f"Network error fetching {url}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise

        # Use retry with backoff
        try:
            return await retry_with_backoff(_fetch, max_retries=retries)
        except Exception as e:
            logger.error(f"Failed to fetch {url} after {retries} retries: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
