"""
Encoding detection & normalization
"""

import logging
import chardet
from charset_normalizer import detect

logger = logging.getLogger(__name__)


class EncodingDetector:
    """Detect and normalize text encoding"""

    async def detect(self, content: bytes) -> str:
        """Detect encoding"""
        # Try charset_normalizer first (more accurate)
        try:
            result = detect(content)
            if result:
                # charset_normalizer returns a list, get the best match
                if isinstance(result, list) and len(result) > 0:
                    return result[0].encoding
                elif hasattr(result, "best"):
                    return result.best().encoding
        except Exception:
            pass

        # Fallback to chardet
        try:
            detected = chardet.detect(content)
            return detected.get("encoding", "utf-8") or "utf-8"
        except Exception:
            return "utf-8"

    async def normalize(self, text: str, encoding: str) -> str:
        """Normalize text encoding"""
        try:
            return text.encode(encoding).decode("utf-8")
        except:
            return text
