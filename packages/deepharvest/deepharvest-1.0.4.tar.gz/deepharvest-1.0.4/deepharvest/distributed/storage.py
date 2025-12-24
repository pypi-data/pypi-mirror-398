"""
Storage Backends
"""

import hashlib
import json
import logging
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import boto3
from botocore.client import Config
import psycopg2
from psycopg2.extras import Json

logger = logging.getLogger(__name__)


class StorageBackend:
    """Abstract storage interface"""

    async def store(self, url: str, content: Dict, metadata: Dict, response):
        raise NotImplementedError


class FileSystemStorage(StorageBackend):
    """Local filesystem storage"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def store(self, url: str, content: Dict, metadata: Dict, response):
        """Store to local filesystem"""

        # Generate filename from URL hash
        url_hash = hashlib.sha256(url.encode()).hexdigest()

        # Create subdirectories based on first 2 chars of hash
        subdir = self.output_dir / url_hash[:2] / url_hash[2:4]
        subdir.mkdir(parents=True, exist_ok=True)

        # Store content
        content_file = subdir / f"{url_hash}.json"
        with open(content_file, "w") as f:
            json.dump(
                {
                    "url": url,
                    "content": content,
                    "metadata": metadata,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )

        # Store raw response if needed
        if response:
            raw_file = subdir / f"{url_hash}.html"
            with open(raw_file, "wb") as f:
                f.write(response.content)


class S3Storage(StorageBackend):
    """AWS S3 compatible storage"""

    def __init__(self, bucket: str, endpoint_url: Optional[str] = None):
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3", endpoint_url=endpoint_url, config=Config(signature_version="s3v4")
        )

    async def store(self, url: str, content: Dict, metadata: Dict, response):
        """Store to S3"""

        url_hash = hashlib.sha256(url.encode()).hexdigest()
        key = f"crawl/{url_hash[:2]}/{url_hash[2:4]}/{url_hash}.json"

        data = json.dumps(
            {
                "url": url,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        self.s3.put_object(
            Bucket=self.bucket, Key=key, Body=data.encode("utf-8"), ContentType="application/json"
        )


class PostgresStorage(StorageBackend):
    """PostgreSQL storage"""

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._create_tables()

    def _create_tables(self):
        """Create database schema"""

        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS crawled_pages (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    url_hash TEXT NOT NULL,
                    content JSONB,
                    metadata JSONB,
                    html TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_url_hash ON crawled_pages(url_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_crawled_at ON crawled_pages(crawled_at)")
            self.conn.commit()

    async def store(self, url: str, content: Dict, metadata: Dict, response):
        """Store to PostgreSQL"""

        url_hash = hashlib.sha256(url.encode()).hexdigest()
        html = getattr(response, "text", None) if response else None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO crawled_pages (url, url_hash, content, metadata, html)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    html = EXCLUDED.html,
                    crawled_at = CURRENT_TIMESTAMP
            """,
                (url, url_hash, Json(content), Json(metadata), html),
            )
            self.conn.commit()


# Factory function
def create_storage_backend(config) -> StorageBackend:
    """Create appropriate storage backend from config"""
    if hasattr(config, "storage_backend"):
        if config.storage_backend == "s3":
            return S3Storage(config.s3_bucket)
        elif config.storage_backend == "postgres":
            return PostgresStorage(config.postgres_url)

    return FileSystemStorage(config.output_dir)
