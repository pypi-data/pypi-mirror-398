"""
Page Type Classification using ML
"""

import logging
from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
import re
from ..utils.errors import ClassifierError

logger = logging.getLogger(__name__)


class PageClassifier:
    """
    Classify page types: news, blog, product, homepage, category, documentation, generic
    """

    PAGE_TYPES = ["news", "blog", "product", "homepage", "category", "documentation", "generic"]

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.vectorizer = None
        self.scaler = StandardScaler()
        self.model_path = model_path
        self._is_trained = False

    async def load(self, model_path: Optional[str] = None):
        """Load pre-trained model or initialize default"""
        if model_path:
            self.model_path = model_path

        if self.model_path and Path(self.model_path).exists():
            try:
                model_data = joblib.load(self.model_path)
                self.model = model_data.get("model")
                self.vectorizer = model_data.get("vectorizer")
                self.scaler = model_data.get("scaler", StandardScaler())
                self._is_trained = True
                logger.info(f"Loaded classifier from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model from {self.model_path}: {e}")
                self._initialize_default()
        else:
            self._initialize_default()

    def _initialize_default(self):
        """Initialize with default untrained model"""
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        self._is_trained = False
        logger.info("Initialized default classifier (heuristic mode)")

    async def classify(self, html: str, url: str) -> Dict[str, float]:
        """
        Classify page type with confidence scores

        Returns:
            Dict mapping page types to confidence scores (0.0-1.0)
        """
        try:
            features = self._extract_features(html, url)

            if self._is_trained and self.model:
                # Use trained model
                try:
                    # Vectorize text features
                    text_features = self.vectorizer.transform(
                        [self._extract_text_features(html, url)]
                    )
                    text_features_array = text_features.toarray()[0]

                    # Combine with structural features
                    combined_features = np.concatenate([text_features_array, features])
                    combined_features = combined_features.reshape(1, -1)

                    # Scale features
                    combined_features = self.scaler.transform(combined_features)

                    # Predict probabilities
                    probabilities = self.model.predict_proba([combined_features[0]])[0]

                    # Map to page types
                    result = {}
                    for i, ptype in enumerate(self.PAGE_TYPES):
                        if i < len(probabilities):
                            result[ptype] = float(probabilities[i])
                        else:
                            result[ptype] = 0.0

                    # Normalize to sum to 1.0
                    total = sum(result.values())
                    if total > 0:
                        result = {k: v / total for k, v in result.items()}

                    return result
                except Exception as e:
                    logger.warning(f"Model prediction failed: {e}, using heuristics")
                    return self._heuristic_classification(html, url)
            else:
                # Use heuristics
                return self._heuristic_classification(html, url)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            raise ClassifierError(f"Failed to classify page: {e}")

    def _extract_text_features(self, html: str, url: str) -> str:
        """Extract text content for vectorization"""
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html, "html.parser")
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            # Combine with URL
            return f"{url} {text}"
        except:
            return f"{url} {html[:1000]}"

    def _extract_features(self, html: str, url: str) -> np.ndarray:
        """Extract structural features for classification"""
        from bs4 import BeautifulSoup

        features = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            # URL-based features
            url_lower = url.lower()
            features.append(1.0 if "/news/" in url_lower or "/article/" in url_lower else 0.0)
            features.append(1.0 if "/blog/" in url_lower or "/post/" in url_lower else 0.0)
            features.append(
                1.0
                if "/product/" in url_lower or "/item/" in url_lower or "/shop/" in url_lower
                else 0.0
            )
            features.append(1.0 if "/docs/" in url_lower or "/documentation/" in url_lower else 0.0)
            features.append(
                1.0 if "/category/" in url_lower or "/categories/" in url_lower else 0.0
            )
            features.append(url.count("/"))  # URL depth
            features.append(1.0 if url.count("/") <= 2 else 0.0)  # Is homepage-like

            # HTML structure features
            features.append(len(soup.find_all("article")))
            features.append(len(soup.find_all("section")))
            features.append(len(soup.find_all("div", class_=re.compile(r"product|item", re.I))))
            features.append(
                len(soup.find_all("div", class_=re.compile(r"article|post|entry", re.I)))
            )
            features.append(len(soup.find_all("nav")))
            features.append(len(soup.find_all("aside")))

            # Content features
            text = soup.get_text()
            features.append(len(text))
            features.append(
                text.count("$") or text.count("€") or text.count("£")
            )  # Price indicators
            features.append(len(soup.find_all("img")))
            features.append(len(soup.find_all("a")))

            # Meta tags
            meta_title = soup.find("title")
            features.append(1.0 if meta_title and "home" in meta_title.get_text().lower() else 0.0)
            features.append(
                1.0 if meta_title and "product" in meta_title.get_text().lower() else 0.0
            )
            features.append(1.0 if meta_title and "blog" in meta_title.get_text().lower() else 0.0)

        except Exception as e:
            logger.warning(f"Feature extraction error: {e}")
            # Return default features
            features = [0.0] * 20

        # Pad or truncate to fixed size
        target_size = 20
        if len(features) < target_size:
            features.extend([0.0] * (target_size - len(features)))
        elif len(features) > target_size:
            features = features[:target_size]

        return np.array(features, dtype=np.float32)

    def _heuristic_classification(self, html: str, url: str) -> Dict[str, float]:
        """Heuristic-based classification fallback"""
        scores = {ptype: 0.0 for ptype in self.PAGE_TYPES}
        url_lower = url.lower()

        # URL pattern matching
        if "/news/" in url_lower or "/article/" in url_lower or "/newsroom/" in url_lower:
            scores["news"] = 0.8
        elif "/blog/" in url_lower or "/post/" in url_lower or "/entry/" in url_lower:
            scores["blog"] = 0.8
        elif (
            "/product/" in url_lower
            or "/item/" in url_lower
            or "/shop/" in url_lower
            or "/buy/" in url_lower
        ):
            scores["product"] = 0.8
        elif "/docs/" in url_lower or "/documentation/" in url_lower or "/guide/" in url_lower:
            scores["documentation"] = 0.8
        elif "/category/" in url_lower or "/categories/" in url_lower or "/catalog/" in url_lower:
            scores["category"] = 0.8
        elif url.count("/") <= 2 or url.endswith("/") or "index" in url_lower:
            scores["homepage"] = 0.7
        else:
            scores["generic"] = 0.5

        # HTML content hints
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text().lower()

            if any(word in text for word in ["price", "$", "add to cart", "buy now"]):
                scores["product"] = max(scores["product"], 0.6)

            if any(word in text for word in ["published", "author", "posted on"]):
                scores["blog"] = max(scores["blog"], 0.6)
                scores["news"] = max(scores["news"], 0.5)

            if any(word in text for word in ["api", "function", "parameter", "example"]):
                scores["documentation"] = max(scores["documentation"], 0.6)

            if len(soup.find_all("article")) > 0:
                scores["blog"] = max(scores["blog"], 0.5)
                scores["news"] = max(scores["news"], 0.4)
        except:
            pass

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        else:
            scores["generic"] = 1.0

        return scores

    async def predict_importance(self, url: str) -> float:
        """Predict URL importance for priority queue"""
        importance = 0.5

        url_lower = url.lower()

        # Boost important page types
        if any(keyword in url_lower for keyword in ["product", "article", "blog", "news"]):
            importance += 0.2

        # Boost shallow URLs
        depth = url.count("/")
        if depth <= 4:
            importance += 0.2

        # Boost documentation
        if "/docs/" in url_lower or "/documentation/" in url_lower:
            importance += 0.1

        return min(importance, 1.0)

    def get_page_type(self, html: str, url: str) -> str:
        """
        Get the most likely page type (synchronous wrapper)

        Returns:
            Page type string
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use a different approach
                # For now, use heuristics directly
                scores = self._heuristic_classification(html, url)
            else:
                scores = loop.run_until_complete(self.classify(html, url))
        except:
            scores = self._heuristic_classification(html, url)

        return max(scores.items(), key=lambda x: x[1])[0]
