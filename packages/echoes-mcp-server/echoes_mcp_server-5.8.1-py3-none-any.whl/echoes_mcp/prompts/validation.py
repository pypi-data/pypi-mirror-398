"""Validation utilities for prompts."""

import re
from pathlib import Path


def validate_github_repo() -> dict[str, bool | str]:
    """Check if .github repo exists with prompts."""
    github_path = Path.cwd().parent / ".github" / ".kiro" / "prompts"
    return {
        "exists": github_path.exists(),
        "path": str(github_path),
    }


def get_available_arcs(content_path: Path) -> list[str]:
    """Get list of arc names from content directory."""
    if not content_path.exists():
        return []
    return sorted(
        [d.name for d in content_path.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )


def validate_arc_exists(arc: str, content_path: Path) -> bool:
    """Check if arc exists in content directory."""
    arc_path = content_path / arc
    return arc_path.exists() and arc_path.is_dir()


def validate_arc_not_exists(arc: str, content_path: Path) -> bool:
    """Check if arc does NOT exist (for new-arc)."""
    return not validate_arc_exists(arc, content_path)


def validate_is_number(value: str) -> bool:
    """Check if value is a valid number."""
    return bool(re.match(r"^\d+$", value))
