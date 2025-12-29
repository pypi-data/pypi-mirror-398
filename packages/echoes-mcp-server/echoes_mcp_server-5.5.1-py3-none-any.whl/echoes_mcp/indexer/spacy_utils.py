"""spaCy utilities with automatic model download."""

import subprocess
import sys

import spacy
from spacy.language import Language

SPACY_MODEL = "it_core_news_lg"
SPACY_MODEL_URL = (
    f"https://github.com/explosion/spacy-models/releases/download/"
    f"{SPACY_MODEL}-3.8.0/{SPACY_MODEL}-3.8.0-py3-none-any.whl"
)

_nlp: Language | None = None


def get_nlp() -> Language:
    """Get spaCy NLP model, downloading if needed."""
    global _nlp

    if _nlp is not None:
        return _nlp

    try:
        _nlp = spacy.load(SPACY_MODEL)
    except OSError:
        print(f"📥 Downloading spaCy model '{SPACY_MODEL}'...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", SPACY_MODEL_URL],
            stdout=subprocess.DEVNULL,
        )
        _nlp = spacy.load(SPACY_MODEL)
        print(f"✓ Model '{SPACY_MODEL}' installed")

    return _nlp
