"""Tests for stats tool."""

import tempfile
from pathlib import Path

import pytest

from echoes_mcp.database import Database
from echoes_mcp.tools.stats import stats


@pytest.fixture
def db_with_chapters():
    """Create a database with test chapters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / ".lancedb")

        db.upsert_chapters(
            [
                {
                    "id": "arc1:ep01:ch001",
                    "file_path": "/test/ch001.md",
                    "file_hash": "abc",
                    "arc": "arc1",
                    "episode": 1,
                    "chapter": 1,
                    "pov": "Alice",
                    "title": "Chapter 1",
                    "location": "Milano",
                    "date": "2024-01-01",
                    "content": "Content",
                    "summary": "Summary",
                    "word_count": 1000,
                    "char_count": 5000,
                    "paragraph_count": 10,
                    "vector": [0.1] * 768,
                    "entities": [],
                    "indexed_at": 0,
                },
                {
                    "id": "arc1:ep01:ch002",
                    "file_path": "/test/ch002.md",
                    "file_hash": "def",
                    "arc": "arc1",
                    "episode": 1,
                    "chapter": 2,
                    "pov": "Bob",
                    "title": "Chapter 2",
                    "location": "Roma",
                    "date": "2024-01-02",
                    "content": "Content",
                    "summary": "Summary",
                    "word_count": 2000,
                    "char_count": 10000,
                    "paragraph_count": 20,
                    "vector": [0.2] * 768,
                    "entities": [],
                    "indexed_at": 0,
                },
                {
                    "id": "arc2:ep01:ch001",
                    "file_path": "/test/arc2/ch001.md",
                    "file_hash": "ghi",
                    "arc": "arc2",
                    "episode": 1,
                    "chapter": 1,
                    "pov": "Alice",
                    "title": "Arc2 Chapter",
                    "location": "Napoli",
                    "date": "2024-02-01",
                    "content": "Content",
                    "summary": "Summary",
                    "word_count": 1500,
                    "char_count": 7500,
                    "paragraph_count": 15,
                    "vector": [0.3] * 768,
                    "entities": [],
                    "indexed_at": 0,
                },
            ]
        )

        yield db


class TestStats:
    """Tests for stats function."""

    @pytest.mark.asyncio
    async def test_total_stats(self, db_with_chapters):
        result = await stats(db_with_chapters)

        assert result["chapters"] == 3
        assert result["words"] == 4500
        assert len(result["arcs"]) == 2
        assert "Alice" in result["pov_distribution"]
        assert "Bob" in result["pov_distribution"]

    @pytest.mark.asyncio
    async def test_filter_by_arc(self, db_with_chapters):
        result = await stats(db_with_chapters, arc="arc1")

        assert result["chapters"] == 2
        assert result["words"] == 3000

    @pytest.mark.asyncio
    async def test_filter_by_pov(self, db_with_chapters):
        result = await stats(db_with_chapters, pov="Alice")

        assert result["chapters"] == 2
        assert result["words"] == 2500

    @pytest.mark.asyncio
    async def test_filter_by_episode(self, db_with_chapters):
        result = await stats(db_with_chapters, episode=1)

        assert result["chapters"] == 3

    @pytest.mark.asyncio
    async def test_combined_filters(self, db_with_chapters):
        result = await stats(db_with_chapters, arc="arc1", pov="Alice")

        assert result["chapters"] == 1
        assert result["words"] == 1000

    @pytest.mark.asyncio
    async def test_empty_result(self, db_with_chapters):
        result = await stats(db_with_chapters, arc="nonexistent")

        assert result["chapters"] == 0
        assert result["words"] == 0
