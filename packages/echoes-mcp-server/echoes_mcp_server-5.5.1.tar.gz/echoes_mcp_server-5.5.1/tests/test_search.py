"""Tests for search tools."""

import tempfile
from pathlib import Path

import pytest

from echoes_mcp.database import Database
from echoes_mcp.tools.search import search_entities, search_relations, search_semantic


@pytest.fixture
def db_with_data():
    """Create a database with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / ".lancedb")

        # Insert test chapters
        db.upsert_chapters(
            [
                {
                    "id": "test:ep01:ch001",
                    "file_path": "/test/ch001.md",
                    "file_hash": "abc123",
                    "arc": "test",
                    "episode": 1,
                    "chapter": 1,
                    "pov": "Alice",
                    "title": "First Chapter",
                    "location": "Milano",
                    "date": "2024-01-01",
                    "content": "Alice walked through Milano.",
                    "summary": "Alice walked...",
                    "word_count": 100,
                    "char_count": 500,
                    "paragraph_count": 3,
                    "vector": [0.1] * 768,
                    "entities": ["test:CHARACTER:Alice"],
                    "indexed_at": 0,
                }
            ]
        )

        # Insert test entities
        db.upsert_entities(
            [
                {
                    "id": "test:CHARACTER:Alice",
                    "arc": "test",
                    "name": "Alice",
                    "type": "CHARACTER",
                    "description": "Protagonista",
                    "aliases": [],
                    "vector": [0.0] * 768,
                    "chapters": ["test:ep01:ch001"],
                    "chapter_count": 1,
                    "first_appearance": "test:ep01:ch001",
                    "indexed_at": 0,
                },
                {
                    "id": "test:CHARACTER:Marco",
                    "arc": "test",
                    "name": "Marco",
                    "type": "CHARACTER",
                    "description": "Amico",
                    "aliases": [],
                    "vector": [0.0] * 768,
                    "chapters": ["test:ep01:ch001"],
                    "chapter_count": 1,
                    "first_appearance": "test:ep01:ch001",
                    "indexed_at": 0,
                },
                {
                    "id": "test:LOCATION:Milano",
                    "arc": "test",
                    "name": "Milano",
                    "type": "LOCATION",
                    "description": "Città",
                    "aliases": [],
                    "vector": [0.0] * 768,
                    "chapters": ["test:ep01:ch001"],
                    "chapter_count": 1,
                    "first_appearance": "test:ep01:ch001",
                    "indexed_at": 0,
                },
            ]
        )

        # Insert test relations
        db.upsert_relations(
            [
                {
                    "id": "test:Alice:LOVES:Marco",
                    "arc": "test",
                    "source_entity": "test:CHARACTER:Alice",
                    "target_entity": "test:CHARACTER:Marco",
                    "type": "LOVES",
                    "description": "",
                    "weight": 1.0,
                    "chapters": ["test:ep01:ch001"],
                    "indexed_at": 0,
                },
                {
                    "id": "test:Alice:LOCATED_IN:Milano",
                    "arc": "test",
                    "source_entity": "test:CHARACTER:Alice",
                    "target_entity": "test:LOCATION:Milano",
                    "type": "LOCATED_IN",
                    "description": "",
                    "weight": 1.0,
                    "chapters": ["test:ep01:ch001"],
                    "indexed_at": 0,
                },
            ]
        )

        yield db


class TestSearchEntities:
    """Tests for search_entities."""

    @pytest.mark.asyncio
    async def test_search_all_entities(self, db_with_data):
        results = await search_entities(db_with_data, limit=10)
        assert len(results) == 3
        names = [r["name"] for r in results]
        assert "Alice" in names
        assert "Marco" in names
        assert "Milano" in names

    @pytest.mark.asyncio
    async def test_filter_by_type(self, db_with_data):
        results = await search_entities(db_with_data, entity_type="CHARACTER", limit=10)
        assert len(results) == 2
        for r in results:
            assert r["type"] == "CHARACTER"

    @pytest.mark.asyncio
    async def test_filter_by_name(self, db_with_data):
        results = await search_entities(db_with_data, name="Alice", limit=10)
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_filter_by_arc(self, db_with_data):
        results = await search_entities(db_with_data, arc="test", limit=10)
        assert len(results) == 3

        results = await search_entities(db_with_data, arc="nonexistent", limit=10)
        assert len(results) == 0


class TestSearchRelations:
    """Tests for search_relations."""

    @pytest.mark.asyncio
    async def test_search_all_relations(self, db_with_data):
        results = await search_relations(db_with_data, limit=10)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_filter_by_type(self, db_with_data):
        results = await search_relations(db_with_data, relation_type="LOVES", limit=10)
        assert len(results) == 1
        assert results[0]["type"] == "LOVES"

    @pytest.mark.asyncio
    async def test_filter_by_entity(self, db_with_data):
        results = await search_relations(db_with_data, entity="test:CHARACTER:Alice", limit=10)
        assert len(results) == 2  # Alice is in both relations

    @pytest.mark.asyncio
    async def test_filter_by_source(self, db_with_data):
        results = await search_relations(db_with_data, source="test:CHARACTER:Alice", limit=10)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_filter_by_target(self, db_with_data):
        results = await search_relations(db_with_data, target="test:CHARACTER:Marco", limit=10)
        assert len(results) == 1
        assert results[0]["target"]["name"] == "Marco"


class TestSearchSemantic:
    """Tests for search_semantic."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, db_with_data):
        query_vector = [0.1] * 768  # Similar to test chapter
        results = await search_semantic(db_with_data, query_vector, limit=10)
        assert len(results) == 1
        assert results[0]["title"] == "First Chapter"

    @pytest.mark.asyncio
    async def test_filter_by_arc(self, db_with_data):
        query_vector = [0.1] * 768
        results = await search_semantic(db_with_data, query_vector, arc="test", limit=10)
        assert len(results) == 1

        results = await search_semantic(db_with_data, query_vector, arc="nonexistent", limit=10)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_filter_by_pov(self, db_with_data):
        query_vector = [0.1] * 768
        results = await search_semantic(db_with_data, query_vector, pov="Alice", limit=10)
        assert len(results) == 1

        results = await search_semantic(db_with_data, query_vector, pov="Bob", limit=10)
        assert len(results) == 0
