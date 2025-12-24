"""
Page Type Classification using ML
"""

import logging
from typing import Dict, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class PageClassifier:
    """
    Classify page types: article, product, homepage, listing, etc.
    """

    PAGE_TYPES = [
        "article",
        "product",
        "homepage",
        "category",
        "search_results",
        "contact",
        "about",
        "login",
        "error",
        "other",
    ]

    def __init__(self):
        self.model = None
        self.vectorizer = None

    async def load(self, model_path: str = None):
        """Load pre-trained model"""

        if model_path and Path(model_path).exists():
            self.model = joblib.load(model_path)
            logger.info(f"Loaded classifier from {model_path}")
        else:
            # Initialize with default model
            self.model = RandomForestClassifier(n_estimators=100)
            self.vectorizer = TfidfVectorizer(max_features=1000)
            logger.info("Initialized default classifier")

    async def classify(self, html: str, url: str) -> Dict[str, float]:
        """Classify page type with confidence scores"""

        features = self._extract_features(html, url)

        if self.model:
            # Use trained model
            probabilities = self.model.predict_proba([features])[0]
            return dict(zip(self.PAGE_TYPES, probabilities))
        else:
            # Use heuristics
            return self._heuristic_classification(html, url)

    def _extract_features(self, html: str, url: str) -> np.ndarray:
        """Extract features for classification"""

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        features = []

        # URL features
        features.append(1.0 if "/product/" in url or "/item/" in url else 0.0)
        features.append(1.0 if "/article/" in url or "/post/" in url else 0.0)
        features.append(1.0 if "/category/" in url or "/catalog/" in url else 0.0)
        features.append(1.0 if "search" in url or "query" in url else 0.0)
        features.append(1.0 if url.count("/") <= 3 else 0.0)  # Likely homepage

        # HTML structure features
        features.append(len(soup.find_all("article")))
        features.append(len(soup.find_all(class_="product")))
        features.append(len(soup.find_all("form")))
        features.append(len(soup.find_all("table")))
        features.append(1.0 if soup.find(itemprop="price") else 0.0)

        # Content features
        text = soup.get_text()
        features.append(len(text) / 1000)  # Normalized length
        features.append(text.lower().count("article") / 100)
        features.append(text.lower().count("product") / 100)
        features.append(text.lower().count("search") / 100)

        return np.array(features)

    def _heuristic_classification(self, html: str, url: str) -> Dict[str, float]:
        """Heuristic-based classification fallback"""

        scores = {ptype: 0.0 for ptype in self.PAGE_TYPES}

        # Simple heuristics
        if "/product/" in url or "/item/" in url:
            scores["product"] = 0.8
        elif "/article/" in url or "/post/" in url or "/blog/" in url:
            scores["article"] = 0.8
        elif url.count("/") <= 3:
            scores["homepage"] = 0.7
        elif "search" in url:
            scores["search_results"] = 0.7
        else:
            scores["other"] = 0.5

        return scores

    async def predict_importance(self, url: str) -> float:
        """Predict URL importance for priority queue"""

        # Heuristic importance scoring
        importance = 0.5

        # Boost important page types
        if any(keyword in url.lower() for keyword in ["product", "article", "blog"]):
            importance += 0.2

        # Boost shallow URLs
        depth = url.count("/")
        if depth <= 4:
            importance += 0.2

        return min(importance, 1.0)
