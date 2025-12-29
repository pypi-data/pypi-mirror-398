"""Prompt handlers for MCP server."""

from pathlib import Path
from typing import Any

from .substitution import substitute_placeholders
from .validation import validate_github_repo

# Prompt definitions with their arguments
PROMPTS = [
    {
        "name": "new-chapter",
        "description": "Create a new chapter for a timeline arc",
        "arguments": [
            {"name": "arc", "description": "Arc name (e.g., 'work', 'anima')", "required": True},
            {
                "name": "chapter",
                "description": "Chapter number (e.g., '1', '12')",
                "required": True,
            },
        ],
    },
    {
        "name": "revise-chapter",
        "description": "Revise an existing chapter with specific improvements",
        "arguments": [
            {"name": "arc", "description": "Arc name", "required": True},
            {"name": "chapter", "description": "Chapter number", "required": True},
        ],
    },
    {
        "name": "expand-chapter",
        "description": "Expand a chapter to reach target word count",
        "arguments": [
            {"name": "arc", "description": "Arc name", "required": True},
            {"name": "chapter", "description": "Chapter number", "required": True},
            {"name": "target", "description": "Target word count (e.g., '4000')", "required": True},
        ],
    },
    {
        "name": "new-character",
        "description": "Create a new character sheet",
        "arguments": [
            {"name": "name", "description": "Character name", "required": True},
        ],
    },
    {
        "name": "new-episode",
        "description": "Create a new episode outline",
        "arguments": [
            {"name": "arc", "description": "Arc name", "required": True},
            {"name": "episode", "description": "Episode number", "required": True},
        ],
    },
    {
        "name": "new-arc",
        "description": "Create a new story arc",
        "arguments": [
            {"name": "name", "description": "Arc name (lowercase, no spaces)", "required": True},
        ],
    },
    {
        "name": "revise-arc",
        "description": "Review and fix an entire arc (documentation, word counts, narrative quality)",
        "arguments": [
            {"name": "arc", "description": "Arc name to revise", "required": True},
        ],
    },
]


def list_prompts() -> dict[str, list[dict[str, Any]]]:
    """Return list of available prompts."""
    return {"prompts": PROMPTS}


def get_prompt(
    name: str,
    args: dict[str, str],
    timeline: str,
    content_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """
    Get a prompt by name with substituted placeholders.

    Args:
        name: Prompt name (e.g., 'new-chapter')
        args: Arguments for placeholder substitution
        timeline: Timeline name
        content_path: Path to content directory (for arc validation)

    Returns:
        MCP prompt message structure
    """
    try:
        # Validate .github repo exists
        github_result = validate_github_repo()
        if not github_result["exists"]:
            raise ValueError(
                ".github repository not found.\n"
                "Clone it as sibling: git clone https://github.com/echoes-io/.github ../.github"
            )

        github_path = Path(github_result["path"])

        # Read base template (required)
        base_path = github_path / f"{name}.md"
        if not base_path.exists():
            raise ValueError(
                f"Prompt template not found: {name}.md\n"
                f"Expected location: ../.github/.kiro/prompts/{name}.md"
            )

        base_prompt = base_path.read_text()

        # Check for timeline override (optional)
        override_path = Path.cwd() / ".kiro" / "prompts" / f"{name}.md"
        override_prompt = ""
        if override_path.exists():
            override_prompt = override_path.read_text()

        # Concatenate (base first, then override)
        combined_prompt = (
            f"{base_prompt}\n\n---\n\n{override_prompt}" if override_prompt else base_prompt
        )

        # Substitute placeholders
        final_prompt = substitute_placeholders(
            prompt_name=name,
            template=combined_prompt,
            args=args,
            timeline=timeline,
            content_path=content_path,
        )

        return {
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": final_prompt},
                }
            ]
        }

    except Exception as e:
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f'❌ Error loading prompt "{name}":\n\n{e}',
                    },
                }
            ]
        }
