"""
SQLite Exporter
"""

import sqlite3
import logging
import json
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteExporter:
    """Export data to SQLite database"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()

    def _create_table(self):
        """Create table if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS crawled_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON crawled_data(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON crawled_data(timestamp)")
        self.conn.commit()

    def export(self, data: List[Dict[str, Any]]):
        """
        Export data to SQLite

        Args:
            data: List of dictionaries to export
        """
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        for item in data:
            url = item.get("url", "")
            content = json.dumps(item.get("content", {}))
            metadata = json.dumps(item.get("metadata", {}))

            cursor.execute(
                """
                INSERT OR REPLACE INTO crawled_data (url, content, metadata)
                VALUES (?, ?, ?)
            """,
                (url, content, metadata),
            )

        self.conn.commit()
        logger.info(f"Exported {len(data)} items to SQLite database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
