"""
Cookie jar management
"""

import logging
from http.cookiejar import CookieJar
from typing import Dict, List

logger = logging.getLogger(__name__)


class CookieManager:
    """Manage cookies for crawling sessions"""

    def __init__(self):
        self.jar = CookieJar()

    def get_cookies(self, domain: str) -> List[Dict]:
        """Get cookies for domain"""
        cookies = []
        for cookie in self.jar:
            if domain in cookie.domain:
                cookies.append(
                    {"name": cookie.name, "value": cookie.value, "domain": cookie.domain}
                )
        return cookies

    def set_cookie(self, name: str, value: str, domain: str):
        """Set a cookie"""
        # Implementation would add to jar
        pass
