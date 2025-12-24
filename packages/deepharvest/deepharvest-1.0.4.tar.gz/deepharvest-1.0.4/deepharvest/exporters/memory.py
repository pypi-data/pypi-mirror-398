"""
In-Memory Text Exporter
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class InMemoryTextExporter:
    """Export extracted text to in-memory storage"""

    def __init__(self):
        self.texts: List[str] = []

    def export(self, data: List[Dict[str, Any]]):
        """
        Export data to in-memory text storage

        Args:
            data: List of dictionaries to export (expects records with 'text' key)
        """
        for item in data:
            # Only collect text content, ignore non-text records
            if isinstance(item, dict) and "text" in item:
                text = item["text"]
                if text and isinstance(text, str):
                    self.texts.append(text.strip())

        logger.info(f"Collected {len(self.texts)} text items in memory")

    def clear(self):
        """Clear all stored texts"""
        self.texts.clear()

    @property
    def all_text(self) -> str:
        """Get all collected text as a single string"""
        return "\n\n".join(self.texts)
