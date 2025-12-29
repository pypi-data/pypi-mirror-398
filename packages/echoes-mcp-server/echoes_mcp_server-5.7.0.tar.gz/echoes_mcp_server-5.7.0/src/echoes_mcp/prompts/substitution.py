"""Placeholder substitution for prompts."""

import re
from pathlib import Path

from .validation import (
    get_available_arcs,
    validate_arc_exists,
    validate_arc_not_exists,
    validate_is_number,
)


def substitute_placeholders(
    prompt_name: str,
    template: str,
    args: dict[str, str],
    timeline: str,
    content_path: Path,
) -> str:
    """
    Substitute placeholders in prompt template.

    Args:
        prompt_name: Name of the prompt (for validation rules)
        template: Prompt template with {PLACEHOLDER} markers
        args: User-provided arguments
        timeline: Timeline name
        content_path: Path to content directory

    Returns:
        Template with placeholders replaced

    Raises:
        ValueError: If validation fails
    """
    replacements: dict[str, str] = {
        "TIMELINE": timeline,
        **{k.upper(): v for k, v in args.items()},
    }

    # Prompt-specific validations
    if prompt_name in ("new-chapter", "revise-chapter", "expand-chapter"):
        arc = args.get("arc")
        chapter = args.get("chapter")

        if not arc:
            raise ValueError("Missing required argument: arc")
        if not chapter:
            raise ValueError("Missing required argument: chapter")

        # Validate arc exists
        if not validate_arc_exists(arc, content_path):
            available = get_available_arcs(content_path)
            raise ValueError(
                f'Arc "{arc}" not found.\nAvailable arcs: {", ".join(available) or "none"}'
            )

        # Validate chapter is a number
        if not validate_is_number(chapter):
            raise ValueError(f'Chapter must be a number, got: "{chapter}"')

    if prompt_name == "expand-chapter":
        target = args.get("target")
        if not target:
            raise ValueError("Missing required argument: target")
        if not validate_is_number(target):
            raise ValueError(f'Target must be a number, got: "{target}"')

    if prompt_name == "new-arc":
        name = args.get("name")
        if not name:
            raise ValueError("Missing required argument: name")

        # Validate arc doesn't exist
        if not validate_arc_not_exists(name, content_path):
            raise ValueError(f'Arc "{name}" already exists.')

    if prompt_name == "new-episode":
        arc = args.get("arc")
        episode = args.get("episode")

        if not arc:
            raise ValueError("Missing required argument: arc")
        if not episode:
            raise ValueError("Missing required argument: episode")

        if not validate_arc_exists(arc, content_path):
            available = get_available_arcs(content_path)
            raise ValueError(
                f'Arc "{arc}" not found.\nAvailable arcs: {", ".join(available) or "none"}'
            )

        if not validate_is_number(episode):
            raise ValueError(f'Episode must be a number, got: "{episode}"')

    if prompt_name == "new-character":
        name = args.get("name")
        if not name:
            raise ValueError("Missing required argument: name")

    if prompt_name == "revise-arc":
        arc = args.get("arc")
        if not arc:
            raise ValueError("Missing required argument: arc")

        if not validate_arc_exists(arc, content_path):
            available = get_available_arcs(content_path)
            raise ValueError(
                f'Arc "{arc}" not found.\nAvailable arcs: {", ".join(available) or "none"}'
            )

    # Replace all placeholders
    result = template
    for key, value in replacements.items():
        placeholder = f"{{{key}}}"
        result = re.sub(re.escape(placeholder), value, result, flags=re.IGNORECASE)

    return result
