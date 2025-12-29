"""Entity and relation extraction with Gemini (primary) or spaCy (fallback)."""

import json
import logging
import os
from typing import TypedDict

logger = logging.getLogger(__name__)

# Entity types for narrative content (Italian for LLM prompt)
ENTITY_TYPES = ["PERSONAGGIO", "LUOGO", "EVENTO", "OGGETTO"]

# Relation types for narrative content (Italian for LLM prompt)
RELATION_TYPES = [
    "AMA",
    "ODIA",
    "CONOSCE",
    "PARENTE_DI",
    "AMICO_DI",
    "SI_TROVA_IN",
    "VIVE_A",
    "VA_A",
    "CAUSA",
    "PRECEDE",
    "SEGUE",
    "POSSIEDE",
    "USA",
]

# Mapping Italian -> English for database schema
ENTITY_TYPE_MAP = {
    "PERSONAGGIO": "CHARACTER",
    "LUOGO": "LOCATION",
    "EVENTO": "EVENT",
    "OGGETTO": "OBJECT",
}

RELATION_TYPE_MAP = {
    "AMA": "LOVES",
    "ODIA": "HATES",
    "CONOSCE": "KNOWS",
    "PARENTE_DI": "RELATED_TO",
    "AMICO_DI": "FRIENDS_WITH",
    "SI_TROVA_IN": "LOCATED_IN",
    "VIVE_A": "LIVES_IN",
    "VA_A": "TRAVELS_TO",
    "CAUSA": "CAUSES",
    "PRECEDE": "HAPPENS_BEFORE",
    "SEGUE": "HAPPENS_AFTER",
    "POSSIEDE": "OWNS",
    "USA": "USES",
}


class ExtractedEntity(TypedDict):
    """Extracted entity."""

    name: str
    type: str
    description: str


class ExtractedRelation(TypedDict):
    """Extracted relation."""

    source: str
    target: str
    type: str


class ExtractionResult(TypedDict):
    """Result of entity/relation extraction."""

    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]


EXTRACTION_PROMPT = """Analizza questo testo narrativo italiano ed estrai entità e relazioni.

TIPI DI ENTITÀ: {entity_types}
TIPI DI RELAZIONI: {relation_types}

TESTO:
{text}

Rispondi SOLO con JSON valido in questo formato:
{{
  "entities": [
    {{"name": "Nome", "type": "PERSONAGGIO", "description": "breve descrizione"}}
  ],
  "relations": [
    {{"source": "Nome1", "target": "Nome2", "type": "AMA"}}
  ]
}}

Estrai solo entità e relazioni esplicitamente menzionate nel testo. JSON:"""


def _extract_with_gemini(text: str) -> ExtractionResult | None:
    """Extract entities using Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = EXTRACTION_PROMPT.format(
            entity_types=", ".join(ENTITY_TYPES),
            relation_types=", ".join(RELATION_TYPES),
            text=text[:4000],  # Limit text length
        )

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        response_text = response.text.strip()

        # Clean markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        result = json.loads(response_text)
        return ExtractionResult(
            entities=result.get("entities", []),
            relations=result.get("relations", []),
        )

    except Exception as e:
        logger.warning(f"Gemini extraction failed: {e}")
        return None


def _extract_with_spacy(text: str) -> ExtractionResult:
    """Extract entities using spaCy NER (fallback)."""
    from .spacy_utils import get_nlp

    nlp = get_nlp()
    doc = nlp(text[:100000])  # spaCy limit

    entities: list[ExtractedEntity] = []
    seen_names: set[str] = set()

    for ent in doc.ents:
        name = ent.text.strip()
        if name in seen_names or len(name) < 2:
            continue
        seen_names.add(name)

        # Map spaCy labels to our types
        if ent.label_ == "PER":
            entity_type = "PERSONAGGIO"
        elif ent.label_ in ("LOC", "GPE"):
            entity_type = "LUOGO"
        elif ent.label_ == "ORG":
            entity_type = "OGGETTO"  # Organizations as objects
        else:
            continue

        entities.append(
            ExtractedEntity(
                name=name,
                type=entity_type,
                description=f"Estratto da spaCy ({ent.label_})",
            )
        )

    # spaCy doesn't extract relations
    return ExtractionResult(entities=entities, relations=[])


def extract_entities_and_relations(text: str) -> ExtractionResult:
    """
    Extract entities and relations from text.

    Uses Gemini if GEMINI_API_KEY is set, otherwise falls back to spaCy.
    """
    # Try Gemini first
    result = _extract_with_gemini(text)
    if result is not None:
        logger.info(
            f"Gemini extracted {len(result['entities'])} entities, {len(result['relations'])} relations"
        )
        return result

    # Fallback to spaCy
    logger.info("Using spaCy fallback for entity extraction")
    result = _extract_with_spacy(text)
    logger.info(f"spaCy extracted {len(result['entities'])} entities")
    return result
