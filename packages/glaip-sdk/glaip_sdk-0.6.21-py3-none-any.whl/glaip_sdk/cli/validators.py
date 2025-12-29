"""CLI validation utilities that wrap core validation with Click exceptions.

This module provides thin wrappers over utils.validation that translate
ValueError exceptions to click.ClickException for CLI user experience.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

from glaip_sdk.cli.utils import handle_best_effort_check
from glaip_sdk.utils.validation import (
    coerce_timeout,
    validate_agent_instruction,
    validate_agent_name,
    validate_api_key,
    validate_directory_path,
    validate_file_path,
    validate_mcp_name,
    validate_timeout,
    validate_tool_name,
    validate_url,
)


def validate_agent_name_cli(name: str) -> str:
    """Validate agent name and return cleaned version.

    Args:
        name: Agent name to validate

    Returns:
        Cleaned agent name

    Raises:
        click.ClickException: If name is invalid
    """
    try:
        return validate_agent_name(name)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_agent_instruction_cli(instruction: str) -> str:
    """Validate agent instruction and return cleaned version.

    Args:
        instruction: Agent instruction to validate

    Returns:
        Cleaned agent instruction

    Raises:
        click.ClickException: If instruction is invalid
    """
    try:
        return validate_agent_instruction(instruction)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_timeout_cli(timeout: int) -> int:
    """Validate timeout value.

    Args:
        timeout: Timeout value in seconds

    Returns:
        Validated timeout value

    Raises:
        click.ClickException: If timeout is invalid
    """
    try:
        return validate_timeout(timeout)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_tool_name_cli(name: str) -> str:
    """Validate tool name and return cleaned version.

    Args:
        name: Tool name to validate

    Returns:
        Cleaned tool name

    Raises:
        click.ClickException: If name is invalid
    """
    try:
        return validate_tool_name(name)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_mcp_name_cli(name: str) -> str:
    """Validate MCP name and return cleaned version.

    Args:
        name: MCP name to validate

    Returns:
        Cleaned MCP name

    Raises:
        click.ClickException: If name is invalid
    """
    try:
        return validate_mcp_name(name)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_file_path_cli(file_path: str | Path, must_exist: bool = True) -> Path:
    """Validate file path.

    Args:
        file_path: File path to validate
        must_exist: Whether file must exist

    Returns:
        Path object

    Raises:
        click.ClickException: If file path is invalid
    """
    try:
        return validate_file_path(file_path, must_exist)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_directory_path_cli(dir_path: str | Path, must_exist: bool = True) -> Path:
    """Validate directory path.

    Args:
        dir_path: Directory path to validate
        must_exist: Whether directory must exist

    Returns:
        Path object

    Raises:
        click.ClickException: If directory path is invalid
    """
    try:
        return validate_directory_path(dir_path, must_exist)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_url_cli(url: str) -> str:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        click.ClickException: If URL is invalid
    """
    try:
        return validate_url(url)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_api_key_cli(api_key: str) -> str:
    """Validate API key format.

    Args:
        api_key: API key to validate

    Returns:
        Validated API key

    Raises:
        click.ClickException: If API key is invalid
    """
    try:
        return validate_api_key(api_key)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def coerce_timeout_cli(value: int | float | str) -> int:
    """Coerce timeout value to integer with CLI-friendly error handling.

    Args:
        value: The timeout value to coerce (int, float, str, etc.)

    Returns:
        Integer timeout value

    Raises:
        click.ClickException: If value cannot be coerced to valid timeout
    """
    try:
        return coerce_timeout(value)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def validate_name_uniqueness_cli(
    _client: Any,
    name: str,
    resource_type: str,
    finder_func: Callable[..., list[Any]],
) -> None:
    """Validate that a resource name is unique.

    Args:
        client: API client
        name: Name to validate
        resource_type: Type of resource (for error messages)
        finder_func: Function to find existing resources by name

    Raises:
        click.ClickException: If name is not unique
    """

    def _check_duplicate() -> None:
        existing = finder_func(name=name)
        if existing:
            raise click.ClickException(
                f"A {resource_type.lower()} named '{name}' already exists. Please choose a unique name."
            )

    handle_best_effort_check(_check_duplicate)
