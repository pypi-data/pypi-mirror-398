"""Generate embeddings using BGE-small-en."""

import logging
import os
from functools import lru_cache

import numpy as np

# Suppress verbose logging from transformers/sentence-transformers
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load the embedding model (cached)."""
    print(f"Loading embedding model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME, device="cpu")


def embed_text(text: str) -> np.ndarray:
    """Generate embedding for a single text.

    Returns a 384-dimensional vector.
    """
    model = get_model()
    return model.encode(text, normalize_embeddings=True)


def embed_batch(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a batch of texts.

    Returns array of shape (n, 384).
    """
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
