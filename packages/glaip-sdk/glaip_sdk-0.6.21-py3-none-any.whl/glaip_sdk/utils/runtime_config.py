"""Runtime configuration helpers for agent execution.

Provides utilities for normalizing runtime_config keys from various input types
(SDK objects, UUIDs, names) to stable platform IDs.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from glaip_sdk.utils.resource_refs import is_uuid
from gllm_core.utils import LoggerManager

if TYPE_CHECKING:
    from glaip_sdk.agents import Agent
    from glaip_sdk.mcps import MCP
    from glaip_sdk.registry import AgentRegistry, MCPRegistry, ToolRegistry
    from glaip_sdk.tools import Tool

    # Type alias for config key inputs (only used in type hints)
    ConfigKeyInput = str | Agent | Tool | MCP | type[Agent] | type[Tool] | type[MCP]

    # Type alias for registry types
    Registry = ToolRegistry | MCPRegistry | AgentRegistry

    # Type alias for runtime config dict shape after normalization
    # Top-level keys include:
    # - "tool_configs", "mcp_configs", "agent_config"
    # - Agent IDs for agent-specific overrides
    # Values are nested dictionaries whose contents depend on the section.
    RuntimeConfigDict = dict[str, dict[str, object]]

logger = LoggerManager().get_logger(__name__)

# Config fields that need key normalization (maps field name to registry type)
_NORMALIZABLE_FIELDS = {
    "tool_configs": "tool",
    "mcp_configs": "mcp",
}

# Config fields that are preserved as-is (no normalization needed)
_PASSTHROUGH_FIELDS = {"agent_config"}


def _extract_id_from_key(key: ConfigKeyInput) -> str | None:
    """Extract ID directly from key if available.

    Args:
        key: The config key to extract ID from.

    Returns:
        The ID string if available, None otherwise.
    """
    if isinstance(key, str) and is_uuid(key):
        return key
    if hasattr(key, "id") and key.id is not None:
        return key.id
    return None


def _resolve_via_registry(key: ConfigKeyInput, registry: Registry | None) -> str | None:
    """Attempt to resolve key via registry.

    Args:
        key: The config key to resolve.
        registry: Registry to use for resolution.

    Returns:
        The resolved ID string if successful, None otherwise.
    """
    if registry is None:
        return None

    try:
        return registry.resolve(key).id
    except (KeyError, ValueError, AttributeError) as exc:
        logger.debug("Failed to resolve key via registry: %r", key, exc_info=exc)
        return None
    except Exception as exc:  # pragma: no cover - unexpected failures
        logger.warning(
            "Unexpected error resolving key via registry for %r: %s",
            key,
            exc,
            exc_info=True,
        )
        return None


def _resolve_config_key(
    key: ConfigKeyInput,
    registry: Registry | None,
    *,
    missing_registry_message: str,
    unresolved_message: str,
) -> str:
    """Resolve a config key using a registry when needed.

    For non-ID keys this always requires a registry; callers customize the
    error messages for missing registries vs unresolved keys.
    """
    # Allow direct UUID / object.id without needing a registry
    if (extracted_id := _extract_id_from_key(key)) is not None:
        return extracted_id

    # For non-ID keys we always require a registry
    if registry is None:
        raise ValueError(missing_registry_message.format(key=key))

    if (resolved_id := _resolve_via_registry(key, registry)) is not None:
        return resolved_id

    raise ValueError(unresolved_message.format(key=key))


def _normalize_section_keys(
    config_section: dict[ConfigKeyInput, dict[str, object]],
    registry: Registry | None,
) -> dict[str, dict[str, object]]:
    """Normalize keys in a single config section (e.g. tool_configs).

    Converts ConfigKeyInput keys (SDK objects, names, classes) to stable IDs
    using the provided registry.

    Example:
        Input:  {ToolClass: {"param": "value"}, "tool-name": {"x": 1}}
        Output: {"uuid-1": {"param": "value"}, "uuid-2": {"x": 1}}

    Args:
        config_section: The config section dict to normalize.
        registry: Registry to use for resolving keys.

    Returns:
        Normalized config section with all keys converted to IDs.
    """
    normalized: dict[str, dict[str, object]] = {}
    for key, value in config_section.items():
        resolved_id = _resolve_config_key(
            key,
            registry,
            missing_registry_message="Unable to resolve runtime_config key via registry: {key!r}",
            unresolved_message="Unable to resolve runtime_config key via registry: {key!r}",
        )
        normalized[resolved_id] = value
    return normalized


def _is_agent_specific_key(key: object) -> bool:
    """Check if a key represents an agent-specific override.

    Agent-specific keys are:
    - Agent instances (from glaip_sdk.agents.Agent)
    - UUID strings (agent IDs)
    - Non-reserved string names (resolved via agent_registry)

    NOT agent-specific:
    - Known config field names (tool_configs, mcp_configs, agent_config)
    - Tool or MCP objects (these are only valid inside *_configs sections)

    Args:
        key: The key to check.

    Returns:
        True if the key could be an agent-specific override.
    """
    from glaip_sdk.agents import Agent  # noqa: PLC0415

    # Agent instance
    if isinstance(key, Agent):
        return True

    # Non-string keys that are not Agent instances are not agent-specific
    if not isinstance(key, str):
        return False

    # Known config field names are not agent-specific
    if key in _NORMALIZABLE_FIELDS or key in _PASSTHROUGH_FIELDS:
        return False

    # Any other string key is treated as an agent reference (ID or name)
    return True


def _normalize_standard_config(
    config: dict[str, object],
    tool_registry: ToolRegistry | None,
    mcp_registry: MCPRegistry | None,
    context: str = "",
) -> dict[str, object]:
    """Normalize a standard config dict with tool_configs, mcp_configs, agent_config sections.

    Used for both global runtime_config and agent-specific nested configs.
    Delegates key normalization to _normalize_section_keys for each section.

    Example:
        Input:  {"tool_configs": {ToolClass: {...}}, "agent_config": {...}}
        Output: {"tool_configs": {"tool-uuid": {...}}, "agent_config": {...}}

    Args:
        config: The config dict to normalize.
        tool_registry: Registry for resolving tool keys.
        mcp_registry: Registry for resolving MCP keys.
        context: Context string for warning messages.

    Returns:
        Normalized config dict.
    """
    registries: dict[str, Registry | None] = {
        "tool": tool_registry,
        "mcp": mcp_registry,
    }

    result: dict[str, object] = {}

    for field, value in config.items():
        if field in _NORMALIZABLE_FIELDS and isinstance(value, dict):
            registry_type = _NORMALIZABLE_FIELDS[field]
            result[field] = _normalize_section_keys(value, registries.get(registry_type))
        elif field in _PASSTHROUGH_FIELDS:
            result[field] = value
        else:
            logger.warning("Unknown field '%s' in %s, ignoring", field, context or "config")

    return result


def normalize_runtime_config_keys(
    runtime_config: RuntimeConfigDict | None,
    tool_registry: ToolRegistry | None,
    mcp_registry: MCPRegistry | None,
    agent_registry: AgentRegistry | None,
) -> RuntimeConfigDict | None:
    """Normalize runtime_config keys from various input types to stable IDs.

    Handles both global configs and agent-specific overrides:
    - Global: tool_configs, mcp_configs, agent_config
    - Agent-specific: keyed by Agent object, agent UUID, or agent name string

    Example:
        Input:
        {
            "tool_configs": {ToolClass: {"param": "val"}},
            "agent_config": {"planning": True},
            AgentClass: {"mcp_configs": {MCPClass: {...}}}
        }
        Output:
        {
            "tool_configs": {"tool-uuid": {"param": "val"}},
            "agent_config": {"planning": True},
            "agent-uuid": {"mcp_configs": {"mcp-uuid": {...}}}
        }

    Converts keys from:
    - SDK objects → their .id attribute
    - UUID strings → passed through
    - Names → resolved via appropriate registry

    Args:
        runtime_config: The runtime configuration dict to normalize.
        tool_registry: Registry for resolving tool keys.
        mcp_registry: Registry for resolving MCP keys.
        agent_registry: Registry for resolving agent keys.

    Returns:
        Normalized runtime_config with all keys converted to IDs, or None if input is None.
    """
    if runtime_config is None:
        return None

    if not runtime_config:
        return {}

    registries: dict[str, Registry | None] = {
        "tool": tool_registry,
        "mcp": mcp_registry,
    }

    result: dict[str, object] = {}

    for field, value in runtime_config.items():
        if field in _NORMALIZABLE_FIELDS and isinstance(value, dict):
            registry_type = _NORMALIZABLE_FIELDS[field]
            result[field] = _normalize_section_keys(value, registries.get(registry_type))
        elif field in _PASSTHROUGH_FIELDS:
            result[field] = value
        elif _is_agent_specific_key(field) and isinstance(value, dict):
            agent_id = _resolve_config_key(
                field,
                agent_registry,
                missing_registry_message=(
                    "Agent-specific runtime_config provided but no agent_registry is available to resolve key: {key!r}"
                ),
                unresolved_message="Unable to resolve agent-specific runtime_config key: {key!r}",
            )
            result[agent_id] = _normalize_standard_config(
                value,
                tool_registry,
                mcp_registry,
                context=f"agent '{agent_id}'",
            )
        else:
            logger.warning("Unknown field '%s' in runtime_config, ignoring", field)

    return result


# =============================================================================
# LOCAL MODE UTILITIES
# =============================================================================
# The functions below are for local execution mode where resources are NOT
# deployed and have no UUIDs. They resolve keys to names (not IDs).
# =============================================================================


def _get_name_from_class(cls: type) -> str:
    """Extract name from a class, handling Pydantic models and @property descriptors.

    Args:
        cls: The class to extract name from.

    Returns:
        The resolved name string.
    """
    # Try class-level name attribute first, but guard against @property descriptors
    # When a class has @property name, getattr returns the property object, not a string
    class_name = getattr(cls, "name", None)
    if isinstance(class_name, str) and class_name:
        return class_name

    # For Pydantic models, check model_fields for default value
    model_fields = getattr(cls, "model_fields", None)
    if model_fields and "name" in model_fields:
        field_info = model_fields["name"]
        default = getattr(field_info, "default", None)
        if default and isinstance(default, str):
            return default

    # Fallback to class __name__
    return cls.__name__


def get_name_from_key(key: object) -> str | None:
    """Resolve config key to name for local mode (no registry needed).

    Supports instances, classes, and string names. UUID strings are not
    supported in local mode and return None with a warning.

    Args:
        key: Tool, MCP, or Agent instance/class/string.

    Returns:
        The resolved name string, or None if UUID (not applicable locally).

    Raises:
        ValueError: If the key cannot be resolved to a valid name.
    """
    # Class type (not instance) - must check BEFORE hasattr("name")
    # because classes with @property name will have hasattr return True
    # but getattr returns the property descriptor, not a string
    if isinstance(key, type):
        return _get_name_from_class(key)

    # String key - check early to avoid attribute access
    if isinstance(key, str):
        if is_uuid(key):
            logger.warning("UUID '%s' not supported in local mode, skipping", key)
            return None
        return key

    # Instance with name attribute
    if hasattr(key, "name"):
        name = getattr(key, "name", None)
        # Guard against @property that returns non-string (e.g., descriptor)
        if isinstance(name, str) and name:
            return name

    raise ValueError(f"Unable to resolve config key: {key!r}")


def normalize_local_config_keys(config: dict[object, object]) -> dict[str, object]:
    """Normalize all keys in a config dict to names for local mode.

    Converts instance/class/string keys to string names without using
    registry. UUID keys are skipped with a warning.

    Args:
        config: Dict with instance/class/string keys and any values.

    Returns:
        Dict with string name keys only. UUID keys are omitted.
    """
    if not config:
        return {}

    result: dict[str, object] = {}
    for key, value in config.items():
        name = get_name_from_key(key)
        if name is not None:
            result[name] = value
    return result


def merge_configs(*configs: dict | None) -> dict:
    """Merge multiple config dicts with priority ordering.

    Later configs override earlier ones for the same key. None configs
    are skipped gracefully.

    Args:
        *configs: Config dicts in priority order (lowest priority first).

    Returns:
        Merged config dict with later values overriding earlier ones.

    Example:
        >>> merge_configs({"a": 1}, {"a": 2, "b": 3})
        {"a": 2, "b": 3}
    """
    result: dict = {}
    for config in configs:
        if config:
            result.update(config)
    return result
