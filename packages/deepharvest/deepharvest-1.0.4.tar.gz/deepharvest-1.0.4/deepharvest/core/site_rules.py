"""
Site-specific rule matching system
"""

import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SiteRule:
    """Rule for site-specific handling"""

    pattern: str  # Regex pattern
    use_browser_directly: bool = False
    require_js: bool = False
    custom_user_agent: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    link_extraction_strategy: Optional[str] = None  # 'standard', 'js-heavy', 'api-based'
    reason: str = ""
    priority: int = 0  # Higher priority rules checked first


class SiteRuleMatcher:
    """Match URLs against site-specific rules"""

    def __init__(self, rules: List[Dict[str, Any]] = None):
        self.rules: List[SiteRule] = []
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        if rules:
            self.load_rules(rules)

    def load_rules(self, rules: List[Dict[str, Any]]):
        """Load rules from configuration"""
        for rule_dict in rules:
            rule = SiteRule(
                pattern=rule_dict.get("pattern", ".*"),
                use_browser_directly=rule_dict.get("use_browser_directly", False),
                require_js=rule_dict.get("require_js", False),
                custom_user_agent=rule_dict.get("custom_user_agent"),
                custom_headers=rule_dict.get("custom_headers"),
                link_extraction_strategy=rule_dict.get("link_extraction_strategy"),
                reason=rule_dict.get("reason", ""),
                priority=rule_dict.get("priority", 0),
            )
            self.rules.append(rule)

        # Sort by priority (higher first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        # Compile patterns for performance
        for rule in self.rules:
            try:
                self._compiled_patterns[rule.pattern] = re.compile(rule.pattern, re.I)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{rule.pattern}': {e}")

    def match(self, url: str) -> Optional[SiteRule]:
        """Match URL against rules, return first match"""
        for rule in self.rules:
            pattern = self._compiled_patterns.get(rule.pattern)
            if pattern and pattern.match(url):
                logger.debug(f"Matched rule for {url}: {rule.reason}")
                return rule
        return None

    def should_use_browser_directly(self, url: str) -> bool:
        """Check if URL should use browser directly"""
        rule = self.match(url)
        return rule.use_browser_directly if rule else False

    def should_require_js(self, url: str) -> bool:
        """Check if URL requires JavaScript"""
        rule = self.match(url)
        return rule.require_js if rule else False

    def get_custom_user_agent(self, url: str) -> Optional[str]:
        """Get custom user agent for URL"""
        rule = self.match(url)
        return rule.custom_user_agent if rule else None

    def get_custom_headers(self, url: str) -> Optional[Dict[str, str]]:
        """Get custom headers for URL"""
        rule = self.match(url)
        return rule.custom_headers if rule else None


class HeuristicSiteDetector:
    """Auto-detect sites needing special handling"""

    @staticmethod
    def detect_js_requirement(response) -> bool:
        """Detect if page requires JS based on content"""
        if not hasattr(response, "text") or not response.text:
            return False

        html = response.text.lower()
        html_stripped = html.strip()

        # Heuristics for JS requirement
        indicators = [
            len(html_stripped) < 500,  # Very short HTML
            "data-reactroot" in html,  # React indicator
            "ng-app" in html or "ng-controller" in html,  # Angular indicator
            (
                "<script" in html and "react" in html and html.count("react") > 2
            ),  # React app (multiple mentions)
            ("<script" in html and "angular" in html and html.count("angular") > 2),  # Angular app
            (
                html.count("<div") > html.count("<a") * 10
                and html.count("<a") > 0
                and len(html_stripped) < 2000
            ),  # SPA pattern: lots of divs, few links, small page
        ]

        return any(indicators)

    @staticmethod
    def detect_link_extraction_issue(response, extracted_links: int) -> bool:
        """Detect if link extraction might have failed"""
        if not hasattr(response, "text") or not response.text:
            return False

        html = response.text.lower()

        # If HTML has many <a> tags but we extracted few links
        link_count = html.count("<a ")
        if link_count > 10 and extracted_links < 2:
            return True

        return False
