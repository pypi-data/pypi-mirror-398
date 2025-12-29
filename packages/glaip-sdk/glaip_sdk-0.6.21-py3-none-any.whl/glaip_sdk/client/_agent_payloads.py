#!/usr/bin/env python3
"""Shared helpers for Agent client payload construction and query handling."""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from glaip_sdk.config.constants import (
    DEFAULT_AGENT_FRAMEWORK,
    DEFAULT_AGENT_PROVIDER,
    DEFAULT_AGENT_TYPE,
    DEFAULT_AGENT_VERSION,
    DEFAULT_MODEL,
)
from glaip_sdk.payload_schemas.agent import AgentImportOperation, get_import_field_plan
from glaip_sdk.utils.client_utils import extract_ids

_LM_CONFLICT_KEYS = {
    "lm_provider",
    "lm_name",
    "lm_base_url",
    "lm_hyperparameters",
}


def _copy_structure(value: Any) -> Any:
    """Return a defensive copy for mutable payload structures."""
    if isinstance(value, (dict, list, tuple)):
        return deepcopy(value)
    return value


def _sanitize_agent_config(
    agent_config: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Remove legacy LM keys that conflict with modern language model fields."""
    if agent_config is None:
        return None

    sanitized = deepcopy(agent_config)
    for key in _LM_CONFLICT_KEYS:
        sanitized.pop(key, None)
    return sanitized


def _merge_execution_timeout(
    agent_config: dict[str, Any] | None,
    timeout: int | None,
) -> dict[str, Any] | None:
    """Merge execution timeout into agent_config if provided."""
    if timeout is None:
        return agent_config

    merged = agent_config or {}
    merged.setdefault("execution_timeout", timeout)
    return merged


def merge_payload_fields(
    payload: MutableMapping[str, Any],
    extra_fields: Mapping[str, Any] | None,
    operation: AgentImportOperation,
) -> None:
    """Merge additional fields into payload respecting schema hints."""
    if not extra_fields:
        return

    for key, value in extra_fields.items():
        plan = get_import_field_plan(key, operation)
        if not plan.copy or value is None:
            continue

        copied_value = _copy_structure(value)
        if plan.sanitize and isinstance(copied_value, dict):
            copied_value = _sanitize_agent_config(copied_value)

        payload[key] = copied_value


def resolve_language_model_fields(
    *,
    model: str | None,
    language_model_id: str | None,
    provider: str | None,
    model_name: str | None,
    default_provider: str = DEFAULT_AGENT_PROVIDER,
    default_model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Resolve mutually exclusive language model specification fields."""
    if language_model_id:
        return {"language_model_id": language_model_id}

    resolved_model = model_name or model or default_model
    resolved_provider = provider if provider is not None else default_provider

    result: dict[str, Any] = {}
    if resolved_model is not None:
        result["model_name"] = resolved_model
    if resolved_provider:
        result["provider"] = resolved_provider
    return result


def _extract_ids_or_empty(items: Sequence[str | Any] | None) -> list[str]:
    """Extract IDs, returning an empty list when no IDs are present."""
    if items is None:
        return []

    try:
        iterable = list(items)
    except TypeError:
        return []

    extracted = extract_ids(iterable)
    return extracted or []


def _extract_existing_ids(source: Any, attribute: str) -> list[str]:
    """Extract IDs from an attribute on the current agent instance."""
    if source is None:
        return []
    value = getattr(source, attribute, None)
    if not value:
        return []
    return _extract_ids_or_empty(value)


def _resolve_relation_ids(
    new_items: Sequence[str | Any] | None,
    current_agent: Any,
    attribute: str,
) -> list[str]:
    """Resolve relationship IDs favouring explicit values when provided."""
    if new_items is not None:
        return _extract_ids_or_empty(new_items)
    return _extract_existing_ids(current_agent, attribute)


def _pick_optional(
    new_value: Any,
    fallback: Any,
    *,
    transform: Callable[[Any], Any] | None = None,
) -> Any | None:
    """Return new_value when present, otherwise fallback, applying transform."""
    value = new_value if new_value is not None else fallback
    if value is None:
        return None
    return transform(value) if transform else value


def _existing_language_model_fields(current_agent: Any) -> dict[str, Any]:
    """Derive language model fields from the current agent or defaults."""
    result: dict[str, Any] = {}

    language_model_id = getattr(current_agent, "language_model_id", None)
    if language_model_id:
        result["language_model_id"] = language_model_id
        return result

    agent_config = getattr(current_agent, "agent_config", None)
    if isinstance(agent_config, Mapping):
        provider = agent_config.get("lm_provider")
        model_name = agent_config.get("lm_name")
        if provider:
            result["provider"] = provider
        if model_name:
            result["model_name"] = model_name

    if not result:
        if DEFAULT_AGENT_PROVIDER:
            result["provider"] = DEFAULT_AGENT_PROVIDER
        result["model_name"] = DEFAULT_MODEL

    return result


@dataclass(slots=True)
class AgentListParams:
    """Structured query parameters for listing agents."""

    agent_type: str | None = None
    framework: str | None = None
    name: str | None = None
    version: str | None = None
    limit: int | None = None
    page: int | None = None
    include_deleted: bool | None = None
    created_at_start: str | None = None
    created_at_end: str | None = None
    updated_at_start: str | None = None
    updated_at_end: str | None = None
    sync_langflow_agents: bool | None = None
    metadata: Mapping[str, str] | None = None

    def to_query_params(self) -> dict[str, Any]:
        """Convert the dataclass to API-ready query params."""
        params = self._base_filter_params()
        self._apply_pagination_params(params)
        self._apply_timestamp_filters(params)
        self._apply_metadata_filters(params)

        return params

    def _base_filter_params(self) -> dict[str, Any]:
        """Build base filter parameters from non-None fields.

        Returns:
            Dictionary of filter parameters with non-None values.
        """
        return {
            key: value
            for key, value in (
                ("agent_type", self.agent_type),
                ("framework", self.framework),
                ("name", self.name),
                ("version", self.version),
            )
            if value is not None
        }

    def _apply_pagination_params(self, params: dict[str, Any]) -> None:
        """Apply pagination parameters to the params dictionary.

        Args:
            params: Dictionary to update with pagination parameters.
        """
        if self.limit is not None:
            if not 1 <= self.limit <= 100:
                raise ValueError("limit must be between 1 and 100 inclusive")
            params["limit"] = self.limit

        if self.page is not None:
            if self.page < 1:
                raise ValueError("page must be >= 1")
            params["page"] = self.page

        if self.include_deleted is not None:
            params["include_deleted"] = str(self.include_deleted).lower()

        if self.sync_langflow_agents is not None:
            params["sync_langflow_agents"] = str(self.sync_langflow_agents).lower()

    def _apply_timestamp_filters(self, params: dict[str, Any]) -> None:
        """Apply timestamp filter parameters to the params dictionary.

        Args:
            params: Dictionary to update with timestamp filter parameters.
        """
        timestamp_filters = {
            "created_at_start": self.created_at_start,
            "created_at_end": self.created_at_end,
            "updated_at_start": self.updated_at_start,
            "updated_at_end": self.updated_at_end,
        }
        for key, value in timestamp_filters.items():
            if value is not None:
                params[key] = value

    def _apply_metadata_filters(self, params: dict[str, Any]) -> None:
        """Apply metadata filter parameters to the params dictionary.

        Args:
            params: Dictionary to update with metadata filter parameters.
        """
        if not self.metadata:
            return
        for key, value in self.metadata.items():
            if value is not None:
                params[f"metadata.{key}"] = value


@dataclass(slots=True)
class AgentListResult:
    """Structured response for list_agents that retains pagination metadata."""

    items: list[Any] = field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None
    has_next: bool | None = None
    has_prev: bool | None = None
    message: str | None = None

    def __len__(self) -> int:  # pragma: no cover - simple delegation
        """Return the number of items in the result list."""
        return len(self.items)

    def __iter__(self):  # pragma: no cover - simple delegation
        """Return an iterator over the items in the result list."""
        return iter(self.items)

    def __getitem__(self, index: int) -> Any:  # pragma: no cover - simple delegation
        """Get an item from the result list by index.

        Args:
            index: Index of the item to retrieve.

        Returns:
            The item at the specified index.
        """
        return self.items[index]


@dataclass(slots=True)
class AgentCreateRequest:
    """Declarative representation of an agent creation payload."""

    name: str
    instruction: str
    model: str | None = DEFAULT_MODEL
    language_model_id: str | None = None
    provider: str | None = None
    model_name: str | None = None
    agent_type: str = DEFAULT_AGENT_TYPE
    framework: str = DEFAULT_AGENT_FRAMEWORK
    version: str = DEFAULT_AGENT_VERSION
    account_id: str | None = None
    description: str | None = None
    metadata: Mapping[str, Any] | None = None
    tools: Sequence[str | Any] | None = None
    tool_configs: Mapping[str, Any] | None = None
    agents: Sequence[str | Any] | None = None
    mcps: Sequence[str | Any] | None = None
    agent_config: Mapping[str, Any] | None = None
    timeout: int | None = None
    a2a_profile: Mapping[str, Any] | None = None
    extras: Mapping[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        """Materialise the request as a dict suitable for API submission."""
        payload: dict[str, Any] = {
            "name": self.name.strip(),
            "instruction": self.instruction.strip(),
            "type": self.agent_type,
            "framework": self.framework,
            "version": self.version,
        }

        payload.update(
            resolve_language_model_fields(
                model=self.model,
                language_model_id=self.language_model_id,
                provider=self.provider,
                model_name=self.model_name,
            )
        )

        if self.account_id is not None:
            payload["account_id"] = self.account_id
        if self.description is not None:
            payload["description"] = self.description
        if self.metadata is not None:
            payload["metadata"] = _copy_structure(self.metadata)

        if self.a2a_profile is not None:
            payload["a2a_profile"] = _copy_structure(self.a2a_profile)

        tool_ids = extract_ids(list(self.tools) if self.tools is not None else None)
        if tool_ids:
            payload["tools"] = tool_ids

        agent_ids = extract_ids(list(self.agents) if self.agents is not None else None)
        if agent_ids:
            payload["agents"] = agent_ids

        mcp_ids = extract_ids(list(self.mcps) if self.mcps is not None else None)
        if mcp_ids:
            payload["mcps"] = mcp_ids

        if self.tool_configs is not None:
            payload["tool_configs"] = _copy_structure(self.tool_configs)

        effective_agent_config = _sanitize_agent_config(self.agent_config)
        effective_agent_config = _merge_execution_timeout(effective_agent_config, self.timeout)
        if effective_agent_config:
            payload["agent_config"] = effective_agent_config

        merge_payload_fields(payload, self.extras, "create")
        return payload


@dataclass(slots=True)
class AgentUpdateRequest:
    """Declarative representation of an agent update payload."""

    name: str | None = None
    instruction: str | None = None
    description: str | None = None
    model: str | None = None
    language_model_id: str | None = None
    provider: str | None = None
    model_name: str | None = None
    agent_type: str | None = None
    framework: str | None = None
    version: str | None = None
    account_id: str | None = None
    metadata: Mapping[str, Any] | None = None
    tools: Sequence[str | Any] | None = None
    tool_configs: Mapping[str, Any] | None = None
    agents: Sequence[str | Any] | None = None
    mcps: Sequence[str | Any] | None = None
    agent_config: Mapping[str, Any] | None = None
    a2a_profile: Mapping[str, Any] | None = None
    extras: Mapping[str, Any] | None = None

    def to_payload(self, current_agent: Any) -> dict[str, Any]:
        """Materialise the request using current agent data as fallbacks."""
        payload = _build_base_update_payload(self, current_agent)
        payload.update(_resolve_update_language_model_fields(self, current_agent))
        payload.update(_collect_optional_update_fields(self, current_agent))
        payload.update(_collect_relationship_fields(self, current_agent))

        agent_config_value = _resolve_agent_config_update(self, current_agent)
        if agent_config_value is not None:
            payload["agent_config"] = agent_config_value

        merge_payload_fields(payload, self.extras, "update")
        return payload


__all__ = [
    "AgentCreateRequest",
    "AgentListParams",
    "AgentListResult",
    "AgentUpdateRequest",
    "merge_payload_fields",
    "resolve_language_model_fields",
]


def _build_base_update_payload(request: AgentUpdateRequest, current_agent: Any) -> dict[str, Any]:
    """Populate immutable agent update fields using request data or existing agent defaults."""
    # Support both "agent_type" (runtime class) and "type" (API response) attributes
    current_type = getattr(current_agent, "agent_type", None) or getattr(current_agent, "type", None)
    return {
        "name": (request.name.strip() if request.name is not None else getattr(current_agent, "name", None)),
        "instruction": (
            request.instruction.strip()
            if request.instruction is not None
            else getattr(current_agent, "instruction", None)
        ),
        "type": request.agent_type or current_type or DEFAULT_AGENT_TYPE,
        "framework": request.framework or getattr(current_agent, "framework", None) or DEFAULT_AGENT_FRAMEWORK,
        "version": request.version or getattr(current_agent, "version", None) or DEFAULT_AGENT_VERSION,
    }


def _resolve_update_language_model_fields(request: AgentUpdateRequest, current_agent: Any) -> dict[str, Any]:
    """Resolve the language-model portion of an update request with sensible fallbacks."""
    fields = resolve_language_model_fields(
        model=request.model,
        language_model_id=request.language_model_id,
        provider=request.provider,
        model_name=request.model_name,
    )
    if not fields:
        fields = _existing_language_model_fields(current_agent)
    return fields


def _collect_optional_update_fields(request: AgentUpdateRequest, current_agent: Any) -> dict[str, Any]:
    """Collect optional agent fields, preserving current values when updates are absent."""
    result: dict[str, Any] = {}

    for field_name, value in (
        ("account_id", request.account_id),
        ("description", request.description),
    ):
        resolved_value = _pick_optional(value, getattr(current_agent, field_name, None))
        if resolved_value is not None:
            result[field_name] = resolved_value

    metadata_value = _pick_optional(
        request.metadata,
        getattr(current_agent, "metadata", None),
        transform=_copy_structure,
    )
    if metadata_value is not None:
        result["metadata"] = metadata_value

    profile_value = _pick_optional(
        request.a2a_profile,
        getattr(current_agent, "a2a_profile", None),
        transform=_copy_structure,
    )
    if profile_value is not None:
        result["a2a_profile"] = profile_value

    tool_configs_value = _pick_optional(
        request.tool_configs,
        getattr(current_agent, "tool_configs", None),
        transform=_copy_structure,
    )
    if tool_configs_value is not None:
        result["tool_configs"] = tool_configs_value

    return result


def _collect_relationship_fields(request: AgentUpdateRequest, current_agent: Any) -> dict[str, Any]:
    """Return relationship identifiers (tools/agents/mcps) for an update request."""
    return {
        "tools": _resolve_relation_ids(request.tools, current_agent, "tools"),
        "agents": _resolve_relation_ids(request.agents, current_agent, "agents"),
        "mcps": _resolve_relation_ids(request.mcps, current_agent, "mcps"),
    }


def _resolve_agent_config_update(request: AgentUpdateRequest, current_agent: Any) -> dict[str, Any] | None:
    """Determine the agent_config payload to send, if any."""
    effective_agent_config = _sanitize_agent_config(request.agent_config)
    if effective_agent_config is not None:
        return effective_agent_config
    if getattr(current_agent, "agent_config", None):
        return _sanitize_agent_config(current_agent.agent_config)
    return None
