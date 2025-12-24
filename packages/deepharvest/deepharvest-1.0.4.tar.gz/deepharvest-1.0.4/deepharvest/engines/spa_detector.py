"""
spa_detector.py - SPA framework detection
"""

import logging
import re

logger = logging.getLogger(__name__)


class SPADetector:
    """Detect Single Page Application frameworks"""

    FRAMEWORKS = {
        "react": [r"__REACT_DEVTOOLS", r"react", r"React"],
        "vue": [r"__VUE__", r"vue", r"Vue"],
        "angular": [r"ng-", r"angular", r"Angular"],
        "next": [r"__NEXT_DATA__", r"next"],
        "nuxt": [r"__NUXT__", r"nuxt"],
    }

    def detect(self, html: str) -> str:
        """Detect SPA framework"""
        html_lower = html.lower()

        for framework, patterns in self.FRAMEWORKS.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    return framework

        return None
