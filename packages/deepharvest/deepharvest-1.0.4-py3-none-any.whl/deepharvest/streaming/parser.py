"""
Incremental HTML parsing
"""

import logging
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class IncrementalParser(HTMLParser):
    """Parse HTML incrementally"""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        """Handle start tags"""
        if tag == "a":
            attrs_dict = dict(attrs)
            if "href" in attrs_dict:
                self.links.append(attrs_dict["href"])
