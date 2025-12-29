"""CLI-specific agent configuration utilities.

This module provides CLI-only affordances for agent configuration,
such as merging CLI flags over imported data.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any

from glaip_sdk.utils.agent_config import (
    resolve_language_model_selection,
    sanitize_agent_config,
)
from glaip_sdk.utils.import_export import merge_import_with_cli_args


def merge_agent_config_with_cli_args(import_data: dict[str, Any], cli_args: dict[str, Any]) -> dict[str, Any]:
    """Merge imported agent data with CLI arguments, preferring CLI args.

    This is a CLI-specific wrapper that handles agent-specific merging logic.

    Args:
        import_data: Data loaded from import file
        cli_args: Arguments passed via CLI

    Returns:
        Merged data dictionary

    Notes:
        - CLI arguments take precedence over imported data
        - Handles agent-specific fields like tools and agents arrays
        - Preserves agent configuration structure
    """
    return merge_import_with_cli_args(import_data, cli_args, array_fields=["tools", "agents"])


def resolve_agent_language_model_selection(
    merged_data: dict[str, Any], cli_model: str | None
) -> tuple[dict[str, Any], bool]:
    """Resolve language model selection for agent creation/update.

    This is a CLI-specific wrapper around the core LM selection logic.

    Args:
        merged_data: Merged import data and CLI args
        cli_model: Model specified via CLI --model flag

    Returns:
        Tuple of (lm_selection_dict, should_strip_lm_identity)
    """
    return resolve_language_model_selection(merged_data, cli_model)


def sanitize_agent_config_for_cli(
    agent_config: dict | None,
    *,
    strip_credentials: bool = True,
    strip_lm_identity: bool = False,
) -> dict:
    """Sanitize agent_config for CLI operations.

    This is a CLI-specific wrapper around the core sanitization logic.

    Args:
        agent_config: The agent configuration to sanitize
        strip_credentials: Always drop lm_credentials (default: True)
        strip_lm_identity: Also drop lm_provider/lm_name/lm_base_url when True

    Returns:
        Sanitized agent configuration
    """
    return sanitize_agent_config(
        agent_config,
        strip_credentials=strip_credentials,
        strip_lm_identity=strip_lm_identity,
    )
