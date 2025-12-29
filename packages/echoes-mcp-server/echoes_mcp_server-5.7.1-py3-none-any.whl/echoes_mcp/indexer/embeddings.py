"""Embedding model wrapper."""

import os
from collections.abc import Callable
from functools import lru_cache

from sentence_transformers import SentenceTransformer

# Default model - best quality for Italian under 500M params
# Override with ECHOES_EMBEDDING_MODEL env var
DEFAULT_MODEL = os.getenv("ECHOES_EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

# Batch size for embedding - smaller = smoother progress, larger = faster
BATCH_SIZE = 8


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str | None = None) -> SentenceTransformer:
    """Get cached embedding model."""
    model = model_name or DEFAULT_MODEL
    return SentenceTransformer(model)


def embed_texts(
    texts: list[str],
    model_name: str | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[list[float]]:
    """
    Embed multiple texts with optional progress callback.

    Args:
        texts: List of texts to embed
        model_name: Model name override
        progress_callback: Called with (completed, total) after each batch
    """
    if not texts:
        return []

    model_name = model_name or DEFAULT_MODEL
    model = get_embedding_model(model_name)

    # E5 models need "passage: " prefix for documents
    if "e5" in model_name.lower():
        texts = [f"passage: {t}" for t in texts]

    # Process in batches with progress
    all_embeddings: list[list[float]] = []
    total = len(texts)

    for i in range(0, total, BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.extend(emb.tolist() for emb in embeddings)

        if progress_callback:
            progress_callback(min(i + BATCH_SIZE, total), total)

    return all_embeddings


def embed_query(query: str, model_name: str | None = None) -> list[float]:
    """Embed a single query."""
    model_name = model_name or DEFAULT_MODEL
    model = get_embedding_model(model_name)

    # E5 models need "query: " prefix for queries
    if "e5" in model_name.lower():
        query = f"query: {query}"

    embedding = model.encode(query)
    return embedding.tolist()
