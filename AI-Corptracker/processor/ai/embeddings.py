"""
Embeddings Engine — generates vector embeddings for semantic search.

Uses sentence-transformers for multilingual embedding generation
to power the vector knowledge base.
"""

import numpy as np
import structlog
from typing import Optional

logger = structlog.get_logger()

_model = None


def get_embedding_model():
    """Lazy-load the embedding model to save memory when not needed."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded", model="all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(
                "Failed to load embedding model, using random vectors", error=str(e)
            )
            _model = "fallback"
    return _model


def generate_embedding(text: str) -> Optional[list[float]]:
    if not text:
        return None

    model = get_embedding_model()

    if model == "fallback":
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(384).tolist()

    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()

    if model == "fallback":
        results = []
        for text in texts:
            np.random.seed(hash(text) % (2**32))
            results.append(np.random.randn(384).tolist())
        return results

    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return [e.tolist() for e in embeddings]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
