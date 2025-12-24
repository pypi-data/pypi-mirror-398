"""
media.py - Image/Video/Audio handling
"""

import logging
from typing import Dict, Any
from PIL import Image
import io

logger = logging.getLogger(__name__)


class MediaExtractor:
    """Extract metadata from media files"""

    async def extract_image(self, response) -> Dict[str, Any]:
        """Extract image metadata"""
        result = {"format": None, "size": None, "width": None, "height": None}

        try:
            img = Image.open(io.BytesIO(response.content))
            result["format"] = img.format
            result["size"] = len(response.content)
            result["width"], result["height"] = img.size
        except Exception as e:
            logger.error(f"Error extracting image: {e}")

        return result

    async def extract_video(self, response) -> Dict[str, Any]:
        """Extract video metadata"""
        return {
            "size": len(response.content),
            "content_type": getattr(response, "headers", {}).get("content-type"),
        }

    async def extract_audio(self, response) -> Dict[str, Any]:
        """Extract audio metadata"""
        return {
            "size": len(response.content),
            "content_type": getattr(response, "headers", {}).get("content-type"),
        }
