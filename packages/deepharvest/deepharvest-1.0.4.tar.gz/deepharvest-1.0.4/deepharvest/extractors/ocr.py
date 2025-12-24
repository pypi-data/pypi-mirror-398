"""
ocr.py - Tesseract OCR integration
"""

import logging
from typing import Dict, Any
import pytesseract
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OCRExtractor:
    """Extract text from images using OCR"""

    async def extract(self, response) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        result = {"text": "", "confidence": 0.0}

        try:
            # Open image
            img = Image.open(io.BytesIO(response.content))

            # Perform OCR
            text = pytesseract.image_to_string(img)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            result["text"] = text
            if data.get("conf"):
                confidences = [c for c in data["conf"] if c > 0]
                if confidences:
                    result["confidence"] = sum(confidences) / len(confidences)

        except Exception as e:
            logger.error(f"Error performing OCR: {e}")

        return result
