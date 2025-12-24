"""
text.py - Text extraction & normalization
"""

import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
import chardet

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract and normalize text from HTML"""

    async def extract(self, response) -> Dict[str, Any]:
        """Extract text content from response"""
        from ..multilingual.language import LanguageDetector

        result = {
            "title": "",
            "text": "",
            "meta": {},
            "keywords": [],
            "language": "en",
            "word_count": 0,
            "description": "",
        }

        # Detect encoding
        encoding = await self._detect_encoding(response.content)

        # Parse HTML
        html = response.content.decode(encoding, errors="ignore")
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            result["title"] = title_tag.get_text().strip()

        # Extract meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                result["meta"][name] = content

                # Extract specific meta tags
                if name.lower() == "description":
                    result["description"] = content
                elif name.lower() == "keywords":
                    result["keywords"] = [k.strip() for k in content.split(",")]

        # Extract main text
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        result["text"] = soup.get_text(separator=" ", strip=True)

        # Calculate word count
        result["word_count"] = len(result["text"].split())

        # Detect language
        detector = LanguageDetector()
        result["language"] = await detector.detect(result["text"])

        return result

    async def _detect_encoding(self, content: bytes) -> str:
        """Detect content encoding"""
        detected = chardet.detect(content)
        return detected.get("encoding", "utf-8") or "utf-8"
