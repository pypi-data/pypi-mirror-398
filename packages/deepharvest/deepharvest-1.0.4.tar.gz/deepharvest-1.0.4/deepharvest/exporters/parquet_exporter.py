"""
Parquet Exporter
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ParquetExporter:
    """Export data to Parquet format"""

    def export(self, data: List[Dict[str, Any]], output_path: str):
        """
        Export data to Parquet file

        Args:
            data: List of dictionaries to export
            output_path: Path to output file
        """
        try:
            import pandas as pd

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Export to Parquet
            df.to_parquet(output_path, index=False, engine="pyarrow")

            logger.info(f"Exported {len(data)} items to {output_path}")
        except ImportError:
            logger.error("pandas and pyarrow required for Parquet export")
            raise
        except Exception as e:
            logger.error(f"Parquet export error: {e}")
            raise
