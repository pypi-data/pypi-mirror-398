"""Indexer module."""

from .embeddings import embed_query, embed_texts
from .scanner import scan_content
from .spacy_utils import get_nlp

__all__ = ["embed_query", "embed_texts", "get_nlp", "scan_content"]
