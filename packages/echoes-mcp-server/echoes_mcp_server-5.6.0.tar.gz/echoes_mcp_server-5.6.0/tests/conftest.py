"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown(temp_dir: Path) -> Path:
    """Create a sample markdown file."""
    content = """---
title: Test Chapter
pov: Alice
arc: arc1
episode: 1
chapter: 1
---

# Chapter One

This is the first paragraph of the test chapter. It contains some **bold** text and *italic* text.

This is the second paragraph. It has a [link](https://example.com) and some `code`.

> This is a blockquote that should be included in the word count.

- List item one
- List item two
- List item three
"""
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_content_dir(temp_dir: Path) -> Path:
    """Create a sample content directory structure."""
    content_dir = temp_dir / "content"
    arc_dir = content_dir / "arc1" / "ep01-first-episode"
    arc_dir.mkdir(parents=True)

    # Create chapter files
    for i in range(1, 4):
        chapter = arc_dir / f"ep01-ch{i:03d}-alice-chapter-{i}.md"
        chapter.write_text(f"""---
title: Chapter {i}
pov: Alice
arc: arc1
episode: 1
chapter: {i}
---

# Chapter {i}

This is chapter {i} content. Alice does something interesting here.
The story continues with more words to count.
""")

    return content_dir
