"""
CJK segmentation, RTL handling
"""

import logging
import re

logger = logging.getLogger(__name__)


class MultilingualProcessor:
    """Process multilingual text (CJK, RTL, etc.)"""

    # CJK character ranges
    CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uff00-\uffef]")

    def is_cjk(self, text: str) -> bool:
        """Check if text contains CJK characters"""
        return bool(self.CJK_PATTERN.search(text))

    def is_rtl(self, text: str) -> bool:
        """Check if text is right-to-left"""
        # Check for RTL scripts (Arabic, Hebrew, etc.)
        rtl_pattern = re.compile(r"[\u0590-\u05ff\u0600-\u06ff\u0700-\u074f]")
        return bool(rtl_pattern.search(text))

    async def segment_cjk(self, text: str) -> list:
        """Segment CJK text (basic implementation)"""
        # For production, use jieba (Chinese), konlpy (Korean), etc.
        return list(text)

    async def normalize_rtl(self, text: str) -> str:
        """Normalize RTL text"""
        # Basic RTL handling
        return text
