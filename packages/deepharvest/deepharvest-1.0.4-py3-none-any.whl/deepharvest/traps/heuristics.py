"""
Rule-based trap detection
"""

import logging
import re

logger = logging.getLogger(__name__)


class TrapHeuristics:
    """Heuristic-based trap detection rules"""

    def check_calendar_patterns(self, url: str) -> bool:
        """Check for calendar-based patterns"""
        patterns = [r"/\d{4}/\d{2}/\d{2}/", r"/archive/\d{4}/", r"/date/\d{4}/"]
        return any(re.search(p, url) for p in patterns)

    def check_session_patterns(self, url: str) -> bool:
        """Check for session ID patterns"""
        patterns = [r"[?&]sessionid=[a-zA-Z0-9]{20,}", r"[?&]sid=[a-zA-Z0-9]{20,}"]
        return any(re.search(p, url) for p in patterns)
