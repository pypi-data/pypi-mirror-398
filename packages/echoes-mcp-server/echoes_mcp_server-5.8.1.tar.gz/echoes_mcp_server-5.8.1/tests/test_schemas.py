"""Tests for database schemas."""

import pytest
from pydantic import ValidationError

from echoes_mcp.database.schemas import ChapterRecord, EntityRecord, RelationRecord


class TestChapterRecord:
    """Tests for ChapterRecord schema."""

    def test_valid_chapter(self):
        chapter = ChapterRecord(
            id="arc1:ep01:ch001",
            file_path="content/arc1/ep01/ch001.md",
            file_hash="abc123",
            arc="arc1",
            episode=1,
            chapter=1,
            pov="Alice",
            title="The Beginning",
            content="Chapter content here",
            word_count=100,
            char_count=500,
            paragraph_count=3,
            vector=[0.1] * 768,
            indexed_at=1234567890,
        )
        assert chapter.id == "arc1:ep01:ch001"
        assert chapter.pov == "Alice"

    def test_optional_fields(self):
        chapter = ChapterRecord(
            id="arc1:ep01:ch001",
            file_path="content/arc1/ep01/ch001.md",
            file_hash="abc123",
            arc="arc1",
            episode=1,
            chapter=1,
            pov="Alice",
            title="The Beginning",
            content="Content",
            word_count=100,
            char_count=500,
            paragraph_count=3,
            vector=[0.1] * 768,
            indexed_at=1234567890,
        )
        assert chapter.location is None
        assert chapter.summary is None


class TestEntityRecord:
    """Tests for EntityRecord schema."""

    def test_valid_character(self):
        entity = EntityRecord(
            id="bloom:CHARACTER:alice",
            arc="bloom",
            name="Alice",
            type="CHARACTER",
            description="The protagonist",
            vector=[0.1] * 768,
            indexed_at=1234567890,
        )
        assert entity.type == "CHARACTER"
        assert entity.arc == "bloom"

    def test_invalid_type(self):
        # Note: type is now a plain str for LanceDB compatibility, so this test
        # just verifies the record can be created with any type string
        entity = EntityRecord(
            id="bloom:CUSTOM:test",
            arc="bloom",
            name="Test",
            type="CUSTOM_TYPE",
            description="Test",
            vector=[0.1] * 768,
            indexed_at=1234567890,
        )
        assert entity.type == "CUSTOM_TYPE"

    def test_aliases_default_empty(self):
        entity = EntityRecord(
            id="bloom:CHARACTER:bob",
            arc="bloom",
            name="Bob",
            type="CHARACTER",
            description="A friend",
            vector=[0.1] * 768,
            indexed_at=1234567890,
        )
        assert entity.aliases == []


class TestRelationRecord:
    """Tests for RelationRecord schema."""

    def test_valid_relation(self):
        relation = RelationRecord(
            id="bloom:alice:LOVES:bob",
            arc="bloom",
            source_entity="bloom:CHARACTER:alice",
            target_entity="bloom:CHARACTER:bob",
            type="LOVES",
            description="Alice loves Bob",
            weight=0.9,
            indexed_at=1234567890,
        )
        assert relation.weight == 0.9
        assert relation.arc == "bloom"

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            RelationRecord(
                id="bloom:a:KNOWS:b",
                arc="bloom",
                source_entity="a",
                target_entity="b",
                type="KNOWS",
                description="Test",
                weight=1.5,  # Invalid: > 1.0
                indexed_at=1234567890,
            )
