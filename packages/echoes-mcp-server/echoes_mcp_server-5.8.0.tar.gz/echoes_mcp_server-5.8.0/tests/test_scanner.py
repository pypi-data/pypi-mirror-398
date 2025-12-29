"""Tests for filesystem scanner."""

from pathlib import Path

import pytest

from echoes_mcp.indexer.scanner import (
    compute_hash,
    extract_chapter_info,
    parse_frontmatter,
    scan_content,
)


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_same_content_same_hash(self):
        assert compute_hash("hello") == compute_hash("hello")

    def test_different_content_different_hash(self):
        assert compute_hash("hello") != compute_hash("world")

    def test_returns_16_chars(self):
        assert len(compute_hash("test")) == 16


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parses_yaml(self):
        content = """---
title: Test
pov: Alice
---

Body content."""
        metadata, body = parse_frontmatter(content)
        assert metadata["title"] == "Test"
        assert metadata["pov"] == "Alice"
        assert body == "Body content."

    def test_no_frontmatter(self):
        content = "Just body content."
        with pytest.raises(ValueError, match="No frontmatter found"):
            parse_frontmatter(content)

    def test_incomplete_frontmatter(self):
        content = """---
title: Test
No closing"""
        with pytest.raises(ValueError, match="Frontmatter not properly closed"):
            parse_frontmatter(content)


class TestExtractChapterInfo:
    """Tests for extract_chapter_info function."""

    def test_extracts_from_path_and_frontmatter(self, sample_content_dir: Path):
        chapter_file = (
            sample_content_dir / "arc1" / "ep01-first-episode" / "ep01-ch001-alice-chapter-1.md"
        )
        result = extract_chapter_info(chapter_file, sample_content_dir)

        assert result is not None
        assert result["arc"] == "arc1"
        assert result["episode"] == 1
        assert result["chapter"] == 1
        assert result["pov"] == "alice"
        assert result["title"] == "Chapter 1"

    def test_returns_none_for_invalid_path(self, temp_dir: Path):
        # File directly in temp_dir (not enough path depth)
        file_path = temp_dir / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent")
        with pytest.raises(ValueError, match="Invalid path structure"):
            extract_chapter_info(file_path, temp_dir)


class TestScanContent:
    """Tests for scan_content function."""

    def test_finds_all_chapters(self, sample_content_dir: Path):
        chapters = scan_content(sample_content_dir)
        assert len(chapters) == 3

    def test_sorted_by_arc_episode_chapter(self, sample_content_dir: Path):
        chapters = scan_content(sample_content_dir)
        for i in range(len(chapters) - 1):
            current = (chapters[i]["arc"], chapters[i]["episode"], chapters[i]["chapter"])
            next_ch = (
                chapters[i + 1]["arc"],
                chapters[i + 1]["episode"],
                chapters[i + 1]["chapter"],
            )
            assert current <= next_ch

    def test_skips_readme(self, sample_content_dir: Path):
        readme = sample_content_dir / "README.md"
        readme.write_text("# Timeline README")

        chapters = scan_content(sample_content_dir)
        paths = [c["file_path"] for c in chapters]
        assert "README.md" not in paths
