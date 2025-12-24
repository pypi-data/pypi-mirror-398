"""
pdf.py - PDF text extraction
"""

import logging
from typing import Dict, Any
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files"""

    async def extract(self, response) -> Dict[str, Any]:
        """Extract text from PDF"""
        result = {"text": "", "pages": [], "metadata": {}}

        try:
            # Open PDF from bytes
            doc = fitz.open(stream=response.content, filetype="pdf")

            # Extract metadata
            result["metadata"] = doc.metadata

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                result["pages"].append({"page": page_num + 1, "text": text})
                result["text"] += text + "\n\n"

            doc.close()

        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")

        return result
