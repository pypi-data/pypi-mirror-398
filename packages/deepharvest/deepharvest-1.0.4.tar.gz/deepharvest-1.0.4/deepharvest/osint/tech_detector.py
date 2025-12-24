"""
Technology Stack Detection
"""

import re
import logging
from typing import Dict, List, Set
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class TechDetector:
    """Detect technology stack from headers, HTML, and JavaScript"""

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "react": [
            r"react[-/]?(\d+\.\d+\.\d+)?",
            r"__REACT_DEVTOOLS",
            r"ReactDOM",
        ],
        "vue": [
            r"vue[-/]?(\d+\.\d+\.\d+)?",
            r"Vue\.config",
            r"__VUE__",
        ],
        "angular": [
            r"angular[-/]?(\d+\.\d+\.\d+)?",
            r"ng\.",
            r"angular\.module",
        ],
        "jquery": [
            r"jquery[-/]?(\d+\.\d+\.\d+)?",
            r"\$\(\)",
            r"jQuery",
        ],
        "bootstrap": [
            r"bootstrap[-/]?(\d+\.\d+\.\d+)?",
            r"data-bs-",
            r"\.navbar",
        ],
    }

    # CMS detection patterns
    CMS_PATTERNS = {
        "wordpress": [
            r"/wp-content/",
            r"/wp-includes/",
            r"wp-json",
            r"WordPress",
        ],
        "drupal": [
            r"/sites/default/",
            r"Drupal\.settings",
            r"misc/drupal\.js",
        ],
        "joomla": [
            r"/media/jui/",
            r"Joomla\.",
            r"/administrator/",
        ],
        "shopify": [
            r"shopify\.com",
            r"cdn\.shopify\.com",
            r"Shopify\.themes",
        ],
    }

    # Server detection from headers
    SERVER_PATTERNS = {
        "nginx": r"nginx",
        "apache": r"Apache",
        "cloudflare": r"cloudflare",
        "cloudfront": r"cloudfront",
    }

    def detect(self, html: str, headers: Dict[str, str], url: str) -> Dict[str, List[str]]:
        """
        Detect technology stack

        Returns:
            Dict with keys: frameworks, cms, servers, libraries, languages
        """
        tech = {"frameworks": [], "cms": [], "servers": [], "libraries": [], "languages": []}

        try:
            # Detect from headers
            server_header = headers.get("Server", "").lower()
            for server, pattern in self.SERVER_PATTERNS.items():
                if re.search(pattern, server_header, re.I):
                    tech["servers"].append(server)

            # Detect from HTML content
            soup = BeautifulSoup(html, "html.parser")

            # Check script tags
            scripts = soup.find_all("script", src=True)
            script_srcs = [script.get("src", "") for script in scripts]

            # Check inline scripts
            inline_scripts = [script.string for script in soup.find_all("script") if script.string]

            # Detect frameworks
            tech["frameworks"] = self._detect_frameworks(html, script_srcs, inline_scripts)

            # Detect CMS
            tech["cms"] = self._detect_cms(html, script_srcs, url)

            # Detect libraries from script sources
            tech["libraries"] = self._detect_libraries(script_srcs)

            # Detect programming languages (from meta tags, comments, etc.)
            tech["languages"] = self._detect_languages(html, soup)

        except Exception as e:
            logger.error(f"Tech detection error: {e}")

        return tech

    def _detect_frameworks(
        self, html: str, script_srcs: List[str], inline_scripts: List[str]
    ) -> List[str]:
        """Detect JavaScript frameworks"""
        detected = set()

        # Check script sources
        for src in script_srcs:
            for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, src, re.I):
                        detected.add(framework)

        # Check inline scripts
        for script in inline_scripts:
            if script:
                for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, script, re.I):
                            detected.add(framework)

        # Check HTML attributes
        if "data-reactroot" in html or "react-" in html:
            detected.add("react")

        if "v-" in html or "vue-" in html:
            detected.add("vue")

        if "ng-" in html or "data-ng-" in html:
            detected.add("angular")

        return list(detected)

    def _detect_cms(self, html: str, script_srcs: List[str], url: str) -> List[str]:
        """Detect CMS platforms"""
        detected = set()

        # Check URL patterns
        for cms, patterns in self.CMS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.I) or re.search(pattern, html, re.I):
                    detected.add(cms)

        # Check script sources
        for src in script_srcs:
            for cms, patterns in self.CMS_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, src, re.I):
                        detected.add(cms)

        return list(detected)

    def _detect_libraries(self, script_srcs: List[str]) -> List[str]:
        """Detect JavaScript libraries from script sources"""
        libraries = set()

        common_libs = {
            "lodash": r"lodash",
            "underscore": r"underscore",
            "moment": r"moment",
            "axios": r"axios",
            "chart": r"chart\.js",
            "d3": r"d3\.js",
            "three": r"three\.js",
        }

        for src in script_srcs:
            for lib, pattern in common_libs.items():
                if re.search(pattern, src, re.I):
                    libraries.add(lib)

        return list(libraries)

    def _detect_languages(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect backend programming languages"""
        languages = set()

        # Check meta tags
        meta_generator = soup.find("meta", attrs={"name": "generator"})
        if meta_generator:
            content = meta_generator.get("content", "").lower()
            if "php" in content:
                languages.add("php")
            if "python" in content:
                languages.add("python")
            if "ruby" in content:
                languages.add("ruby")

        # Check file extensions in links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".php"):
                languages.add("php")
            elif href.endswith(".aspx"):
                languages.add("asp.net")
            elif href.endswith(".jsp"):
                languages.add("java")

        # Check comments
        if "<!--" in html:
            if "php" in html.lower():
                languages.add("php")

        return list(languages)
