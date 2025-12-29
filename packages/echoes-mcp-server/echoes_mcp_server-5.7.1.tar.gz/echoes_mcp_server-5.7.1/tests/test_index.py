"""Tests for index tool."""

import tempfile
from pathlib import Path

import pytest

from echoes_mcp.tools.index import index_timeline, prepare_chapter_record


class TestPrepareChapterRecord:
    """Tests for prepare_chapter_record."""

    def test_creates_record(self):
        chapter = {
            "file_path": "/test/ch001.md",
            "file_hash": "abc123",
            "arc": "test",
            "episode": 1,
            "chapter": 1,
            "pov": "Alice",
            "title": "Test Chapter",
            "location": "Milano",
            "date": "2024-01-01",
            "content": "This is test content with some words.",
            "summary": "Test summary",
        }
        vector = [0.1] * 768

        record = prepare_chapter_record(chapter, vector)

        assert record["id"] == "test:ep01:ch001"
        assert record["arc"] == "test"
        assert record["pov"] == "Alice"
        assert record["word_count"] == 7
        assert record["vector"] == vector
        assert "indexed_at" in record

    def test_generates_summary_if_missing(self):
        chapter = {
            "file_path": "/test/ch001.md",
            "file_hash": "abc123",
            "arc": "test",
            "episode": 1,
            "chapter": 1,
            "pov": "Alice",
            "title": "Test",
            "location": None,
            "date": None,
            "content": "A" * 300,
            "summary": None,
        }
        vector = [0.0] * 768

        record = prepare_chapter_record(chapter, vector)

        assert len(record["summary"]) == 200


class TestIndexTimeline:
    """Tests for index_timeline."""

    @pytest.mark.asyncio
    async def test_index_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = Path(tmpdir) / "content"
            content.mkdir()
            db_path = Path(tmpdir) / "db"

            result = await index_timeline(content, db_path, quiet=True, extract_entities=False)

            assert result["indexed"] == 0
            assert result["updated"] == 0
            assert result["deleted"] == 0

    @pytest.mark.asyncio
    async def test_index_single_chapter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = Path(tmpdir) / "content"
            arc_dir = content / "test-arc" / "ep01-test"
            arc_dir.mkdir(parents=True)

            chapter = arc_dir / "ep01-ch001-alice-test.md"
            chapter.write_text("""---
pov: alice
title: Test Chapter
---

This is test content.
""")

            db_path = Path(tmpdir) / "db"

            result = await index_timeline(content, db_path, quiet=True, extract_entities=False)

            assert result["indexed"] == 1
            assert result["updated"] == 0

    @pytest.mark.asyncio
    async def test_incremental_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = Path(tmpdir) / "content"
            arc_dir = content / "test-arc" / "ep01-test"
            arc_dir.mkdir(parents=True)

            chapter = arc_dir / "ep01-ch001-alice-test.md"
            chapter.write_text("""---
pov: alice
title: Test
---

Content.
""")

            db_path = Path(tmpdir) / "db"

            # First index
            result1 = await index_timeline(content, db_path, quiet=True, extract_entities=False)
            assert result1["indexed"] == 1

            # Second index without changes - should be 0 since no migration needed
            # Create a fake metadata file to avoid migration
            metadata_path = db_path / "metadata.json"
            metadata_path.write_text('{"version": "5.7.0"}')

            result2 = await index_timeline(content, db_path, quiet=True, extract_entities=False)
            assert result2["indexed"] == 0
            assert result2["updated"] == 0

            # Modify file
            chapter.write_text("""---
pov: alice
title: Test Updated
---

New content.
""")

            # Third index with changes
            result3 = await index_timeline(content, db_path, quiet=True, extract_entities=False)
            assert result3["updated"] == 1

    @pytest.mark.asyncio
    async def test_force_reindex(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = Path(tmpdir) / "content"
            arc_dir = content / "test-arc" / "ep01-test"
            arc_dir.mkdir(parents=True)

            chapter = arc_dir / "ep01-ch001-alice-test.md"
            chapter.write_text("""---
pov: alice
title: Test
---

Content.
""")

            db_path = Path(tmpdir) / "db"

            # First index
            await index_timeline(content, db_path, quiet=True, extract_entities=False)

            # Force reindex
            result = await index_timeline(
                content, db_path, force=True, quiet=True, extract_entities=False
            )
            assert result["indexed"] == 1

    @pytest.mark.asyncio
    async def test_arc_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = Path(tmpdir) / "content"

            # Create two arcs
            for arc in ["arc1", "arc2"]:
                arc_dir = content / arc / "ep01-test"
                arc_dir.mkdir(parents=True)
                chapter = arc_dir / f"ep01-ch001-alice-{arc}.md"
                chapter.write_text(f"""---
pov: alice
title: {arc} Chapter
---

Content for {arc}.
""")

            db_path = Path(tmpdir) / "db"

            # Index only arc1
            result = await index_timeline(
                content, db_path, arc_filter="arc1", quiet=True, extract_entities=False
            )

            assert result["indexed"] == 1
