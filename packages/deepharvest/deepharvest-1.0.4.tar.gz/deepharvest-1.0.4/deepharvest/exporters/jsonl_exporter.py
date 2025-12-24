"""
JSONL (JSON Lines) Exporter
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class JSONLExporter:
    """Export data to JSONL format"""

    def export(self, data: List[Dict[str, Any]], output_path: str):
        """
        Export data to JSONL file

        Args:
            data: List of dictionaries to export
            output_path: Path to output file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(data)} items to {output_path}")
