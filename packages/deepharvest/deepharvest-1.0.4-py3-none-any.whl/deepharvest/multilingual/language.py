"""
Language detection
"""

import logging
from langdetect import detect, detect_langs

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect language of text"""

    async def detect(self, text: str) -> str:
        """Detect primary language"""
        try:
            return detect(text)
        except:
            return "en"

    async def detect_multiple(self, text: str) -> list:
        """Detect multiple languages with confidence"""
        try:
            langs = detect_langs(text)
            return [{"lang": lang.lang, "prob": lang.prob} for lang in langs]
        except:
            return [{"lang": "en", "prob": 1.0}]
