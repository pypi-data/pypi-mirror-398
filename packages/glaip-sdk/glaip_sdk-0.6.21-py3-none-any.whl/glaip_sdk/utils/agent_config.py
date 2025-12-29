"""Agent configuration utilities for import/export normalization and LM selection.

This module consolidates language model selection logic and agent configuration
sanitization that was previously split between CLI and SDK layers.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any


def _strip_agent_config_credentials(agent_config: dict | None) -> dict:
    """Return agent_config without sensitive credentials; keep all other keys.

    We intentionally keep keys like memory and agent_id so that backends supporting
    mem0 memory (gllm-agents-binary>=0.4.6) receive them under agent_config.

    Args:
        agent_config: The agent configuration dictionary

    Returns:
        Agent config with credentials stripped but mem0 keys preserved
    """
    if not isinstance(agent_config, dict):
        return {}
    return {k: v for k, v in agent_config.items() if k != "lm_credentials"}


def sanitize_agent_config(
    agent_config: dict | None,
    *,
    strip_credentials: bool = True,
    strip_lm_identity: bool = False,
) -> dict:
    """Sanitize agent_config based on chosen LM selection method.

    Args:
        agent_config: The agent configuration to sanitize
        strip_credentials: Always drop lm_credentials (default: True)
        strip_lm_identity: Also drop lm_provider/lm_name/lm_base_url when True

    Returns:
        Sanitized agent configuration

    Notes:
        - Always drops lm_credentials to prevent credential leakage
        - When strip_lm_identity=True, also drops LM identity keys to avoid conflicts
        - Never drops mem0 keys (memory, agent_id) as they're needed by backends
    """
    if strip_credentials:
        cfg = _strip_agent_config_credentials(agent_config)
    else:
        cfg = agent_config or {}

    if strip_lm_identity and isinstance(cfg, dict):
        cfg = {k: v for k, v in cfg.items() if k not in {"lm_provider", "lm_name", "lm_base_url"}}
    return cfg


def resolve_language_model_selection(merged_data: dict[str, Any], cli_model: str | None) -> tuple[dict[str, Any], bool]:
    """Resolve language model selection from merged data and CLI args.

    Implements the LM selection priority:
    1. CLI --model (maps to provider/model_name)
    2. language_model_id from import
    3. agent_config.lm_name from import (legacy)

    Args:
        merged_data: Merged import data and CLI args
        cli_model: Model specified via CLI --model flag

    Returns:
        Tuple of (lm_selection_dict, should_strip_lm_identity)
        - lm_selection_dict: Dict with exactly one LM method: {"language_model_id": "..."} OR {"model": "..."}
        - should_strip_lm_identity: True when LM identity keys should be stripped from agent_config

    Notes:
        - Returns exactly one LM selection method to avoid conflicts
        - CLI model takes highest priority
        - language_model_id is preferred over legacy lm_name
        - When extracting from agent_config, signals that LM identity should be stripped
    """
    # Priority 1: CLI --model flag
    if cli_model:
        return {"model": cli_model}, False

    # Priority 2: language_model_id from import
    if merged_data.get("language_model_id"):
        return {"language_model_id": merged_data["language_model_id"]}, True

    # Priority 3: Legacy lm_name from agent_config
    agent_config = merged_data.get("agent_config") or {}
    if isinstance(agent_config, dict) and agent_config.get("lm_name"):
        return {"model": agent_config["lm_name"]}, True  # Strip LM identity when extracting from agent_config

    # No LM selection found
    return {}, False


def normalize_agent_config_for_import(agent_data: dict[str, Any], cli_model: str | None = None) -> dict[str, Any]:
    """Automatically normalize agent configuration by extracting LM settings from agent_config.

    This function addresses the common issue where exported agent configurations contain
    language model settings in agent_config, but the backend expects them at the top level
    to avoid conflicts.

    Args:
        agent_data: Raw agent configuration data (from import file)
        cli_model: CLI model override (highest priority)

    Returns:
        Normalized agent configuration with LM settings properly positioned

    Notes:
        - Automatically extracts lm_provider/lm_name from agent_config to top level
        - Preserves memory settings (memory, agent_id) in agent_config
        - Handles conflicts by prioritizing CLI model > existing language_model_id > extracted lm_name
        - Strips redundant LM settings from agent_config after extraction
    """
    normalized_data = agent_data.copy()
    agent_config = normalized_data.get("agent_config", {})

    if not isinstance(agent_config, dict):
        return normalized_data

    # Apply normalization based on priority order
    if cli_model:
        return _apply_cli_model_override(normalized_data, cli_model)

    if normalized_data.get("language_model_id"):
        return _cleanup_existing_language_model(normalized_data, agent_config)

    return _extract_lm_from_agent_config(normalized_data, agent_config)


def _apply_cli_model_override(normalized_data: dict, cli_model: str) -> dict:
    """Apply CLI model override (highest priority)."""
    normalized_data["model"] = cli_model
    return normalized_data


def _cleanup_existing_language_model(normalized_data: dict, agent_config: dict) -> dict:
    """Clean up agent_config when language_model_id already exists."""
    # Remove LM identity keys from agent_config since language_model_id takes precedence
    lm_keys_to_remove = {"lm_provider", "lm_name", "lm_base_url"}
    for key in lm_keys_to_remove:
        agent_config.pop(key, None)
    normalized_data["agent_config"] = agent_config
    return normalized_data


def _extract_lm_from_agent_config(normalized_data: dict, agent_config: dict) -> dict:
    """Extract LM settings from agent_config (lowest priority)."""
    extracted_lm = _extract_lm_settings(agent_config)

    if not extracted_lm:
        return normalized_data

    # Add extracted LM settings to top level
    normalized_data.update(extracted_lm)

    # Create sanitized agent_config (remove extracted LM settings but keep memory)
    sanitized_config = _sanitize_agent_config(agent_config)
    normalized_data["agent_config"] = sanitized_config

    return normalized_data


def _extract_lm_settings(agent_config: dict) -> dict[str, Any]:
    """Extract LM settings from agent_config."""
    extracted_lm = {}

    # Extract lm_name if present
    if "lm_name" in agent_config:
        extracted_lm["model"] = agent_config["lm_name"]

    # Extract lm_provider if present (for completeness)
    if "lm_provider" in agent_config:
        extracted_lm["lm_provider"] = agent_config["lm_provider"]

    return extracted_lm


def _sanitize_agent_config(agent_config: dict) -> dict:
    """Create sanitized agent_config by removing LM identity keys."""
    sanitized_config = agent_config.copy()

    # Remove LM identity keys but preserve memory and other settings
    lm_keys_to_remove = {"lm_provider", "lm_name", "lm_base_url"}
    for key in lm_keys_to_remove:
        sanitized_config.pop(key, None)

    return sanitized_config
