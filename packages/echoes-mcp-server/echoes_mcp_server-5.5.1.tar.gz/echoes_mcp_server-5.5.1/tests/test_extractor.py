"""Tests for entity extraction."""

from unittest.mock import MagicMock, patch

from echoes_mcp.indexer.extractor import (
    ENTITY_TYPE_MAP,
    RELATION_TYPE_MAP,
    ExtractionResult,
)


class TestTypeMappings:
    """Tests for type mappings."""

    def test_entity_type_map_complete(self):
        """All Italian types map to English."""
        assert ENTITY_TYPE_MAP["PERSONAGGIO"] == "CHARACTER"
        assert ENTITY_TYPE_MAP["LUOGO"] == "LOCATION"
        assert ENTITY_TYPE_MAP["EVENTO"] == "EVENT"
        assert ENTITY_TYPE_MAP["OGGETTO"] == "OBJECT"

    def test_relation_type_map_complete(self):
        """All Italian relation types map to English."""
        assert RELATION_TYPE_MAP["AMA"] == "LOVES"
        assert RELATION_TYPE_MAP["ODIA"] == "HATES"
        assert RELATION_TYPE_MAP["CONOSCE"] == "KNOWS"
        assert RELATION_TYPE_MAP["SI_TROVA_IN"] == "LOCATED_IN"
        assert RELATION_TYPE_MAP["VIVE_A"] == "LIVES_IN"


class TestSpacyExtraction:
    """Tests for spaCy fallback extraction."""

    def test_extracts_entities_with_mock(self):
        """Test spaCy extraction with mocked nlp."""
        mock_ent = MagicMock()
        mock_ent.text = "Milano"
        mock_ent.label_ = "LOC"

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent]

        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("echoes_mcp.indexer.spacy_utils.get_nlp", return_value=mock_nlp):
            from echoes_mcp.indexer.extractor import _extract_with_spacy

            result = _extract_with_spacy("Test text")

            assert len(result["entities"]) == 1
            assert result["entities"][0]["name"] == "Milano"
            assert result["entities"][0]["type"] == "LUOGO"

    def test_no_relations_from_spacy(self):
        """spaCy doesn't extract relations."""
        mock_doc = MagicMock()
        mock_doc.ents = []

        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("echoes_mcp.indexer.spacy_utils.get_nlp", return_value=mock_nlp):
            from echoes_mcp.indexer.extractor import _extract_with_spacy

            result = _extract_with_spacy("Alice ama Marco.")
            assert result["relations"] == []

    def test_deduplicates_entities(self):
        """Should not have duplicate entries."""
        mock_ent1 = MagicMock()
        mock_ent1.text = "Alice"
        mock_ent1.label_ = "PER"

        mock_ent2 = MagicMock()
        mock_ent2.text = "Alice"
        mock_ent2.label_ = "PER"

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent1, mock_ent2]

        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("echoes_mcp.indexer.spacy_utils.get_nlp", return_value=mock_nlp):
            from echoes_mcp.indexer.extractor import _extract_with_spacy

            result = _extract_with_spacy("Alice vide Alice.")
            names = [e["name"] for e in result["entities"]]
            assert len(names) == len(set(names))


class TestExtractionResult:
    """Tests for ExtractionResult type."""

    def test_extraction_result_structure(self):
        result: ExtractionResult = {
            "entities": [{"name": "Alice", "type": "PERSONAGGIO", "description": "Test"}],
            "relations": [{"source": "Alice", "target": "Marco", "type": "AMA"}],
        }
        assert len(result["entities"]) == 1
        assert len(result["relations"]) == 1
