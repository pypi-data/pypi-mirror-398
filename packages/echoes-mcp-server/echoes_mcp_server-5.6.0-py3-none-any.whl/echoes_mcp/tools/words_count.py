"""Words count tool - count words in markdown files."""

import re
from pathlib import Path
from typing import TypedDict


class WordCountResult(TypedDict):
    """Result of word count operation."""

    words: int
    characters: int
    paragraphs: int
    reading_time_minutes: float


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3 :].strip()
    return content


def strip_markdown(content: str) -> str:
    """Remove markdown syntax, keeping only plain text."""
    # Remove code blocks
    content = re.sub(r"```[\s\S]*?```", "", content)
    content = re.sub(r"`[^`]+`", "", content)

    # Remove images and links but keep link text
    content = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

    # Remove headers
    content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

    # Remove emphasis markers
    content = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
    content = re.sub(r"\*([^*]+)\*", r"\1", content)
    content = re.sub(r"__([^_]+)__", r"\1", content)
    content = re.sub(r"_([^_]+)_", r"\1", content)

    # Remove blockquotes
    content = re.sub(r"^>\s*", "", content, flags=re.MULTILINE)

    # Remove horizontal rules
    content = re.sub(r"^[-*_]{3,}\s*$", "", content, flags=re.MULTILINE)

    # Remove list markers
    content = re.sub(r"^[\s]*[-*+]\s+", "", content, flags=re.MULTILINE)
    content = re.sub(r"^[\s]*\d+\.\s+", "", content, flags=re.MULTILINE)

    # Remove HTML tags
    content = re.sub(r"<[^>]+>", "", content)

    return content.strip()


def count_words(text: str) -> int:
    """Count words in text."""
    words = text.split()
    return len(words)


def count_paragraphs(text: str) -> int:
    """Count paragraphs (non-empty lines separated by blank lines)."""
    paragraphs = re.split(r"\n\s*\n", text)
    return len([p for p in paragraphs if p.strip()])


def words_count(file_path: str | Path) -> WordCountResult:
    """
    Count words and statistics in a markdown file.

    Removes frontmatter and markdown syntax before counting.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")

    # Clean content
    content = strip_frontmatter(content)
    clean_text = strip_markdown(content)

    # Calculate statistics
    words = count_words(clean_text)
    characters = len(clean_text)
    paragraphs = count_paragraphs(clean_text)

    # Average reading speed: 200 words per minute
    reading_time = words / 200.0

    return WordCountResult(
        words=words,
        characters=characters,
        paragraphs=paragraphs,
        reading_time_minutes=round(reading_time, 1),
    )
