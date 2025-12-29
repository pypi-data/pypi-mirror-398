"""Instruction template loading and processing.

This module provides functions for loading and processing instruction
templates from markdown files.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from pathlib import Path


def load_instruction_from_file(
    instructions_path: str,
    variables: dict[str, str] | None = None,
    base_path: Path | None = None,
) -> str:
    """Load and process instruction template from markdown file.

    Args:
        instructions_path: Path to instructions markdown file.
        variables: Template variables for {{variable}} substitution.
        base_path: Base path to resolve relative paths from.

    Returns:
        Processed instructions with variables substituted.

    Raises:
        FileNotFoundError: If instructions file doesn't exist.

    Example:
        >>> instructions = load_instruction_from_file(
        ...     "instructions.md",
        ...     variables={"agent_name": "Weather Bot"}
        ... )
    """
    full_path = _resolve_instructions_path(instructions_path, base_path)

    if not full_path.exists():
        raise FileNotFoundError(f"Instructions file not found: {full_path}")

    with open(full_path, encoding="utf-8") as f:
        template = f.read()

    if variables:
        template = _substitute_variables(template, variables)

    return template


# Alias for backwards compatibility
load_instructions = load_instruction_from_file


def _resolve_instructions_path(instructions_path: str, base_path: Path | None) -> Path:
    """Resolve instructions path to an absolute path.

    Handles absolute paths, tilde expansion, and relative paths.
    Guards against path traversal escaping base_path when provided.

    Args:
        instructions_path: Path to instructions file (may be relative).
        base_path: Base path for relative resolution.

    Returns:
        Resolved absolute path.

    Raises:
        ValueError: If resolved path escapes base_path.
    """
    raw_path = Path(instructions_path).expanduser()

    if raw_path.is_absolute():
        return raw_path.resolve()

    base = (base_path or Path.cwd()).resolve()
    relative_part = raw_path.relative_to(".") if instructions_path.startswith("./") else raw_path
    resolved = (base / relative_part).resolve()

    if base_path and not resolved.is_relative_to(base):
        raise ValueError(f"Resolved instructions path escapes base path: {resolved}")

    return resolved


def _substitute_variables(template: str, variables: dict[str, str]) -> str:
    """Substitute template variables in the format {{variable_name}}.

    Args:
        template: Template string with {{variable}} placeholders.
        variables: Dictionary of variable names to values.

    Returns:
        Template with variables substituted.
    """
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result
