"""
VectorDB Exporter (FAISS/Chroma)
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorDBExporter:
    """Export data to VectorDB (FAISS or Chroma)"""

    def __init__(self, db_type: str = "faiss", db_path: str = "./vectordb"):
        """
        Initialize VectorDB exporter

        Args:
            db_type: 'faiss' or 'chroma'
            db_path: Path to database
        """
        self.db_type = db_type.lower()
        self.db_path = db_path
        self.db = None

    def initialize(self):
        """Initialize VectorDB"""
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

        if self.db_type == "faiss":
            self._initialize_faiss()
        elif self.db_type == "chroma":
            self._initialize_chroma()
        else:
            raise ValueError(f"Unsupported VectorDB type: {self.db_type}")

    def _initialize_faiss(self):
        """Initialize FAISS database"""
        try:
            import faiss
            import numpy as np

            # Create FAISS index (L2 distance, 384 dimensions for sentence embeddings)
            dimension = 384
            self.index = faiss.IndexFlatL2(dimension)
            self.ids = []
            self.metadata = []

            logger.info("Initialized FAISS database")
        except ImportError:
            logger.error("faiss-cpu required for FAISS export")
            raise

    def _initialize_chroma(self):
        """Initialize Chroma database"""
        try:
            import chromadb

            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name="deepharvest", metadata={"description": "DeepHarvest crawled data"}
            )

            logger.info("Initialized Chroma database")
        except ImportError:
            logger.error("chromadb required for Chroma export")
            raise

    def export(self, data: List[Dict[str, Any]], embeddings: Optional[List] = None):
        """
        Export data to VectorDB

        Args:
            data: List of dictionaries to export
            embeddings: Optional pre-computed embeddings
        """
        if not self.db:
            self.initialize()

        if self.db_type == "faiss":
            self._export_faiss(data, embeddings)
        elif self.db_type == "chroma":
            self._export_chroma(data, embeddings)

    def _export_faiss(self, data: List[Dict[str, Any]], embeddings: Optional[List] = None):
        """Export to FAISS"""
        import faiss
        import numpy as np

        if embeddings is None:
            # Generate simple embeddings (dummy - should use real embeddings)
            embeddings = [np.random.rand(384).astype("float32") for _ in data]

        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype("float32")

        # Add to index
        self.index.add(embeddings_array)

        # Store metadata
        for item in data:
            self.ids.append(item.get("url", ""))
            self.metadata.append(item)

        # Save index
        faiss.write_index(self.index, f"{self.db_path}/index.faiss")

        # Save metadata
        import pickle

        with open(f"{self.db_path}/metadata.pkl", "wb") as f:
            pickle.dump({"ids": self.ids, "metadata": self.metadata}, f)

        logger.info(f"Exported {len(data)} items to FAISS database")

    def _export_chroma(self, data: List[Dict[str, Any]], embeddings: Optional[List] = None):
        """Export to Chroma"""
        import json

        ids = [item.get("url", f"item_{i}") for i, item in enumerate(data)]
        documents = [json.dumps(item) for item in data]
        metadatas = [{"url": item.get("url", "")} for item in data]

        if embeddings:
            self.collection.add(
                ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
            )
        else:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

        logger.info(f"Exported {len(data)} items to Chroma database")
