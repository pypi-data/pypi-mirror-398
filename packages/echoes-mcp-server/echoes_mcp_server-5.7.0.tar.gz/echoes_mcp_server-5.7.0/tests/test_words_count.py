"""Tests for words_count tool."""

from pathlib import Path

import pytest

from echoes_mcp.tools.words_count import (
    count_paragraphs,
    count_words,
    strip_frontmatter,
    strip_markdown,
    words_count,
)


class TestStripFrontmatter:
    """Tests for strip_frontmatter function."""

    def test_removes_yaml_frontmatter(self):
        content = """---
title: Test
author: Alice
---

Content here."""
        result = strip_frontmatter(content)
        assert result == "Content here."

    def test_no_frontmatter(self):
        content = "Just content without frontmatter."
        result = strip_frontmatter(content)
        assert result == content

    def test_incomplete_frontmatter(self):
        content = """---
title: Test
No closing delimiter"""
        result = strip_frontmatter(content)
        assert result == content


class TestStripMarkdown:
    """Tests for strip_markdown function."""

    def test_removes_headers(self):
        content = "# Header\n## Subheader\nContent"
        result = strip_markdown(content)
        assert "Header" in result
        assert "#" not in result

    def test_removes_bold_italic(self):
        content = "This is **bold** and *italic* text."
        result = strip_markdown(content)
        assert result == "This is bold and italic text."

    def test_removes_links_keeps_text(self):
        content = "Click [here](https://example.com) for more."
        result = strip_markdown(content)
        assert result == "Click here for more."

    def test_removes_images(self):
        content = "Text ![alt](image.png) more text"
        result = strip_markdown(content)
        assert "![" not in result
        assert "Text" in result

    def test_removes_code_blocks(self):
        content = "Before\n```python\ncode here\n```\nAfter"
        result = strip_markdown(content)
        assert "code here" not in result
        assert "Before" in result
        assert "After" in result

    def test_removes_inline_code(self):
        content = "Use `print()` function"
        result = strip_markdown(content)
        assert "`" not in result

    def test_removes_blockquotes(self):
        content = "> This is a quote\nNormal text"
        result = strip_markdown(content)
        assert ">" not in result
        assert "This is a quote" in result

    def test_removes_list_markers(self):
        content = "- Item one\n- Item two\n1. Numbered"
        result = strip_markdown(content)
        assert "-" not in result
        assert "Item one" in result


class TestCountWords:
    """Tests for count_words function."""

    def test_simple_sentence(self):
        assert count_words("Hello world") == 2

    def test_empty_string(self):
        assert count_words("") == 0

    def test_multiple_spaces(self):
        assert count_words("Hello    world") == 2

    def test_newlines(self):
        assert count_words("Hello\nworld\ntest") == 3


class TestCountParagraphs:
    """Tests for count_paragraphs function."""

    def test_single_paragraph(self):
        assert count_paragraphs("Just one paragraph.") == 1

    def test_multiple_paragraphs(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird."
        assert count_paragraphs(text) == 3

    def test_empty_lines_ignored(self):
        text = "Paragraph one.\n\n\n\nParagraph two."
        assert count_paragraphs(text) == 2


class TestWordsCount:
    """Tests for words_count function."""

    def test_counts_markdown_file(self, sample_markdown: Path):
        result = words_count(sample_markdown)
        assert result["words"] > 0
        assert result["characters"] > 0
        assert result["paragraphs"] > 0
        assert result["reading_time_minutes"] >= 0

    def test_file_not_found(self, temp_dir: Path):
        with pytest.raises(FileNotFoundError):
            words_count(temp_dir / "nonexistent.md")

    def test_excludes_frontmatter(self, temp_dir: Path):
        # File with only frontmatter
        file_path = temp_dir / "frontmatter_only.md"
        file_path.write_text("""---
title: Test
---

Hello world.""")
        result = words_count(file_path)
        assert result["words"] == 2  # Only "Hello world"
