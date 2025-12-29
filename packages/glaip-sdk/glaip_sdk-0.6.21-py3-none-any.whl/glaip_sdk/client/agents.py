#!/usr/bin/env python3
"""Agent client for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable, Iterator, Mapping
from contextlib import asynccontextmanager
from os import PathLike
from pathlib import Path
from typing import Any, BinaryIO

import httpx
from glaip_sdk.agents import Agent
from glaip_sdk.client._agent_payloads import (
    AgentCreateRequest,
    AgentListParams,
    AgentListResult,
    AgentUpdateRequest,
)
from glaip_sdk.client.agent_runs import AgentRunsClient
from glaip_sdk.client.base import BaseClient
from glaip_sdk.client.mcps import MCPClient
from glaip_sdk.client.run_rendering import (
    AgentRunRenderingManager,
    compute_timeout_seconds,
)
from glaip_sdk.client.shared import build_shared_config
from glaip_sdk.client.tools import ToolClient
from glaip_sdk.config.constants import (
    AGENT_CONFIG_FIELDS,
    DEFAULT_AGENT_FRAMEWORK,
    DEFAULT_AGENT_RUN_TIMEOUT,
    DEFAULT_AGENT_TYPE,
    DEFAULT_AGENT_VERSION,
    DEFAULT_MODEL,
)
from glaip_sdk.exceptions import NotFoundError, ValidationError
from glaip_sdk.models import AgentResponse
from glaip_sdk.payload_schemas.agent import list_server_only_fields
from glaip_sdk.utils.agent_config import normalize_agent_config_for_import
from glaip_sdk.utils.client_utils import (
    aiter_sse_events,
    create_model_instances,
    find_by_name,
    prepare_multipart_data,
)
from glaip_sdk.utils.import_export import (
    convert_export_to_import_format,
    merge_import_with_cli_args,
)
from glaip_sdk.utils.rendering.renderer import RichStreamRenderer
from glaip_sdk.utils.resource_refs import is_uuid
from glaip_sdk.utils.serialization import load_resource_from_file
from glaip_sdk.utils.validation import validate_agent_instruction

# API endpoints
AGENTS_ENDPOINT = "/agents/"

# SSE content type
SSE_CONTENT_TYPE = "text/event-stream"

# Set up module-level logger
logger = logging.getLogger("glaip_sdk.agents")

_SERVER_ONLY_IMPORT_FIELDS = set(list_server_only_fields()) | {"success", "message"}
_MERGED_SEQUENCE_FIELDS = ("tools", "agents", "mcps")
_DEFAULT_METADATA_TYPE = "custom"


@asynccontextmanager
async def _async_timeout_guard(
    timeout_seconds: float | None,
) -> AsyncGenerator[None, None]:
    """Apply an asyncio timeout when a custom timeout is provided."""
    if timeout_seconds is None:
        yield
        return
    try:
        async with asyncio.timeout(timeout_seconds):
            yield
    except asyncio.TimeoutError as exc:
        raise httpx.TimeoutException(f"Request timed out after {timeout_seconds}s") from exc


def _normalise_sequence(value: Any) -> list[Any] | None:
    """Normalise optional sequence inputs to plain lists."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _normalise_sequence_fields(mapping: dict[str, Any]) -> None:
    """Normalise merged sequence fields in-place."""
    for field in _MERGED_SEQUENCE_FIELDS:
        if field in mapping:
            normalised = _normalise_sequence(mapping[field])
            if normalised is not None:
                mapping[field] = normalised


def _merge_override_maps(
    base_values: Mapping[str, Any],
    extra_values: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge override mappings while normalising sequence fields."""
    merged: dict[str, Any] = {}
    for source in (base_values, extra_values):
        for key, value in source.items():
            if value is None:
                continue
            merged[key] = _normalise_sequence(value) if key in _MERGED_SEQUENCE_FIELDS else value
    return merged


def _split_known_and_extra(
    payload: Mapping[str, Any],
    known_fields: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split payload mapping into known request fields and extras."""
    known: dict[str, Any] = {}
    extras: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if key in known_fields:
            known[key] = value
        else:
            extras[key] = value
    return known, extras


def _prepare_agent_metadata(value: Any) -> dict[str, Any]:
    """Ensure agent metadata contains ``type: custom`` by default."""
    if value is None:
        return {"type": _DEFAULT_METADATA_TYPE}
    if not isinstance(value, Mapping):
        return {"type": _DEFAULT_METADATA_TYPE}

    prepared = dict(value)
    metadata_type = prepared.get("type")
    if not metadata_type:
        prepared["type"] = _DEFAULT_METADATA_TYPE
    return prepared


def _load_agent_file_payload(file_path: Path, *, model_override: str | None) -> dict[str, Any]:
    """Load agent configuration from disk and normalise legacy fields."""
    if not file_path.exists():
        raise FileNotFoundError(f"Agent configuration file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Agent configuration path must point to a file: {file_path}")

    raw_data = load_resource_from_file(file_path)
    if not isinstance(raw_data, Mapping):
        raise ValueError("Agent configuration file must contain a mapping/object.")

    payload = convert_export_to_import_format(dict(raw_data))
    payload = normalize_agent_config_for_import(payload, model_override)

    for field in _SERVER_ONLY_IMPORT_FIELDS:
        payload.pop(field, None)

    return payload


def _prepare_import_payload(
    file_path: Path,
    overrides: Mapping[str, Any],
    *,
    drop_model_fields: bool = False,
) -> dict[str, Any]:
    """Prepare merged payload from file contents and explicit overrides."""
    overrides_dict = dict(overrides)

    raw_definition = load_resource_from_file(file_path)
    original_refs = _extract_original_refs(raw_definition)

    base_payload = _load_agent_file_payload(file_path, model_override=overrides_dict.get("model"))

    cli_args = _build_cli_args(overrides_dict)

    merged = merge_import_with_cli_args(base_payload, cli_args)

    additional = _build_additional_args(overrides_dict, cli_args)
    merged.update(additional)

    if drop_model_fields:
        _remove_model_fields_if_needed(merged, overrides_dict)

    _set_default_refs(merged, original_refs)

    _normalise_sequence_fields(merged)
    return merged


def _extract_original_refs(raw_definition: dict) -> dict[str, list]:
    """Extract original tool/agent/mcp references from raw definition."""
    return {
        "tools": list(raw_definition.get("tools") or []),
        "agents": list(raw_definition.get("agents") or []),
        "mcps": list(raw_definition.get("mcps") or []),
    }


def _build_cli_args(overrides_dict: dict) -> dict[str, Any]:
    """Build CLI args from overrides, filtering out None values."""
    cli_args = {key: overrides_dict.get(key) for key in AGENT_CONFIG_FIELDS if overrides_dict.get(key) is not None}

    # Normalize sequence fields
    for field in _MERGED_SEQUENCE_FIELDS:
        if field in cli_args:
            cli_args[field] = tuple(_normalise_sequence(cli_args[field]) or [])

    return cli_args


def _build_additional_args(overrides_dict: dict, cli_args: dict) -> dict[str, Any]:
    """Build additional args not already in CLI args."""
    return {key: value for key, value in overrides_dict.items() if value is not None and key not in cli_args}


def _remove_model_fields_if_needed(merged: dict, overrides_dict: dict) -> None:
    """Remove model fields if not explicitly overridden."""
    if overrides_dict.get("language_model_id") is None:
        merged.pop("language_model_id", None)
    if overrides_dict.get("provider") is None:
        merged.pop("provider", None)


def _set_default_refs(merged: dict, original_refs: dict) -> None:
    """Set default references if not already present."""
    merged.setdefault("_tool_refs", original_refs["tools"])
    merged.setdefault("_agent_refs", original_refs["agents"])
    merged.setdefault("_mcp_refs", original_refs["mcps"])


class AgentClient(BaseClient):
    """Client for agent operations."""

    def __init__(
        self,
        *,
        parent_client: BaseClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the agent client.

        Args:
            parent_client: Parent client to adopt session/config from
            **kwargs: Additional arguments for standalone initialization
        """
        super().__init__(parent_client=parent_client, **kwargs)
        self._renderer_manager = AgentRunRenderingManager(logger)
        self._tool_client: ToolClient | None = None
        self._mcp_client: MCPClient | None = None
        self._runs_client: AgentRunsClient | None = None

    def list_agents(
        self,
        query: AgentListParams | None = None,
        **kwargs: Any,
    ) -> AgentListResult:
        """List agents with optional filtering and pagination support.

        Args:
            query: Query parameters for filtering agents. If None, uses kwargs to create query.
            **kwargs: Individual filter parameters for backward compatibility.
        """
        if query is not None and kwargs:
            # Both query object and individual parameters provided
            raise ValueError("Provide either `query` or individual filter arguments, not both.")

        if query is None:
            # Create query from individual parameters for backward compatibility
            query = AgentListParams(**kwargs)

        params = query.to_query_params()
        envelope = self._request_with_envelope(
            "GET",
            AGENTS_ENDPOINT,
            params=params if params else None,
        )

        if not isinstance(envelope, dict):
            envelope = {"data": envelope}

        data_payload = envelope.get("data") or []
        items = create_model_instances(data_payload, Agent, self)

        return AgentListResult(
            items=items,
            total=envelope.get("total"),
            page=envelope.get("page"),
            limit=envelope.get("limit"),
            has_next=envelope.get("has_next"),
            has_prev=envelope.get("has_prev"),
            message=envelope.get("message"),
        )

    def sync_langflow_agents(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Sync LangFlow agents by fetching flows from the LangFlow server.

        This method synchronizes agents with LangFlow flows. It fetches all flows
        from the configured LangFlow server and creates/updates corresponding agents.

        Args:
            base_url: Custom LangFlow server base URL. If not provided, uses LANGFLOW_BASE_URL env var.
            api_key: Custom LangFlow API key. If not provided, uses LANGFLOW_API_KEY env var.

        Returns:
            Response containing sync results and statistics

        Raises:
            ValueError: If LangFlow server configuration is missing
        """
        payload = {}
        if base_url is not None:
            payload["base_url"] = base_url
        if api_key is not None:
            payload["api_key"] = api_key

        return self._request("POST", "/agents/langflow/sync", json=payload)

    def get_agent_by_id(self, agent_id: str) -> Agent:
        """Get agent by ID."""
        try:
            data = self._request("GET", f"/agents/{agent_id}")
        except ValidationError as exc:
            if exc.status_code == 422:
                message = f"Agent '{agent_id}' not found"
                raise NotFoundError(
                    message,
                    status_code=404,
                    error_type=exc.error_type,
                    payload=exc.payload,
                    request_id=exc.request_id,
                ) from exc
            raise

        if isinstance(data, str):
            # Some backends may respond with plain text for missing agents.
            message = data.strip() or f"Agent '{agent_id}' not found"
            raise NotFoundError(message, status_code=404)

        if not isinstance(data, dict):
            raise NotFoundError(
                f"Agent '{agent_id}' not found (unexpected response type)",
                status_code=404,
            )

        response = AgentResponse(**data)
        return Agent.from_response(response, client=self)

    def find_agents(self, name: str | None = None) -> list[Agent]:
        """Find agents by name."""
        result = self.list_agents(name=name)
        agents = list(result)
        if name is None:
            return agents
        return find_by_name(agents, name, case_sensitive=False)

    # ------------------------------------------------------------------ #
    # Renderer delegation helpers
    # ------------------------------------------------------------------ #
    def _get_renderer_manager(self) -> AgentRunRenderingManager:
        """Get or create the renderer manager instance.

        Returns:
            AgentRunRenderingManager instance.
        """
        manager = getattr(self, "_renderer_manager", None)
        if manager is None:
            manager = AgentRunRenderingManager(logger)
            self._renderer_manager = manager
        return manager

    def _create_renderer(self, renderer: RichStreamRenderer | str | None, **kwargs: Any) -> RichStreamRenderer:
        """Create or return a renderer instance.

        Args:
            renderer: Renderer instance, string identifier, or None.
            **kwargs: Additional keyword arguments (e.g., verbose).

        Returns:
            RichStreamRenderer instance.
        """
        manager = self._get_renderer_manager()
        verbose = kwargs.get("verbose", False)
        if isinstance(renderer, RichStreamRenderer) or hasattr(renderer, "on_start"):
            return renderer  # type: ignore[return-value]
        return manager.create_renderer(renderer, verbose=verbose)

    def _process_stream_events(
        self,
        stream_response: httpx.Response,
        renderer: RichStreamRenderer,
        timeout_seconds: float,
        agent_name: str | None,
        meta: dict[str, Any],
    ) -> tuple[str, dict[str, Any], float | None, float | None]:
        """Process stream events from an HTTP response.

        Args:
            stream_response: HTTP response stream.
            renderer: Renderer to use for displaying events.
            timeout_seconds: Timeout in seconds.
            agent_name: Optional agent name.
            meta: Metadata dictionary.

        Returns:
            Tuple of (final_text, stats_usage, started_monotonic, finished_monotonic).
        """
        manager = self._get_renderer_manager()
        return manager.process_stream_events(
            stream_response,
            renderer,
            timeout_seconds,
            agent_name,
            meta,
        )

    def _finalize_renderer(
        self,
        renderer: RichStreamRenderer,
        final_text: str,
        stats_usage: dict[str, Any],
        started_monotonic: float | None,
        finished_monotonic: float | None,
    ) -> str:
        """Finalize the renderer and return the final response text.

        Args:
            renderer: Renderer to finalize.
            final_text: Final text content.
            stats_usage: Usage statistics dictionary.
            started_monotonic: Start time (monotonic).
            finished_monotonic: Finish time (monotonic).

        Returns:
            Final text string.
        """
        from glaip_sdk.client.run_rendering import finalize_render_manager  # noqa: PLC0415

        manager = self._get_renderer_manager()
        return finalize_render_manager(
            manager, renderer, final_text, stats_usage, started_monotonic, finished_monotonic
        )

    def _get_tool_client(self) -> ToolClient:
        """Get or create the tool client instance.

        Returns:
            ToolClient instance.
        """
        if self._tool_client is None:
            self._tool_client = ToolClient(parent_client=self)
        return self._tool_client

    def _get_mcp_client(self) -> MCPClient:
        """Get or create the MCP client instance.

        Returns:
            MCPClient instance.
        """
        if self._mcp_client is None:
            self._mcp_client = MCPClient(parent_client=self)
        return self._mcp_client

    def _normalise_reference_entry(
        self,
        entry: Any,
        fallback_iter: Iterator[Any] | None,
    ) -> tuple[str | None, str | None]:
        """Normalize a reference entry to extract ID and name.

        Args:
            entry: Reference entry (string, dict, or other).
            fallback_iter: Optional iterator for fallback values.

        Returns:
            Tuple of (entry_id, entry_name).
        """
        entry_id: str | None = None
        entry_name: str | None = None

        if isinstance(entry, str):
            if is_uuid(entry):
                entry_id = entry
            else:
                entry_name = entry
        elif isinstance(entry, dict):
            entry_id = entry.get("id")
            entry_name = entry.get("name")
        else:
            entry_name = str(entry)

        if entry_name or fallback_iter is None:
            return entry_id, entry_name

        try:
            ref = next(fallback_iter)
        except StopIteration:
            ref = None
        if isinstance(ref, dict):
            entry_name = ref.get("name") or entry_name

        return entry_id, entry_name

    def _resolve_resource_ids(
        self,
        items: list[Any] | None,
        references: list[Any] | None,
        *,
        fetch_by_id: Callable[[str], Any],
        find_by_name: Callable[[str], list[Any]],
        label: str,
        plural_label: str | None = None,
    ) -> list[str] | None:
        """Resolve a list of resource references to IDs.

        Args:
            items: List of resource references to resolve.
            references: Optional list of reference objects for fallback.
            fetch_by_id: Function to fetch resource by ID.
            find_by_name: Function to find resources by name.
            label: Singular label for error messages.
            plural_label: Plural label for error messages.

        Returns:
            List of resolved resource IDs, or None if items is empty.
        """
        if not items:
            return None

        if references is None:
            return [self._coerce_reference_value(entry) for entry in items]

        singular = label
        plural = plural_label or f"{label}s"
        fallback_iter = iter(references or [])

        return [
            self._resolve_single_resource(
                entry,
                fallback_iter,
                fetch_by_id,
                find_by_name,
                singular,
                plural,
            )
            for entry in items
        ]

    def _resolve_single_resource(
        self,
        entry: Any,
        fallback_iter: Iterator[Any] | None,
        fetch_by_id: Callable[[str], Any],
        find_by_name: Callable[[str], list[Any]],
        singular: str,
        plural: str,
    ) -> str:
        """Resolve a single resource reference to an ID.

        Args:
            entry: Resource reference to resolve.
            fallback_iter: Optional iterator for fallback values.
            fetch_by_id: Function to fetch resource by ID.
            find_by_name: Function to find resources by name.
            singular: Singular label for error messages.
            plural: Plural label for error messages.

        Returns:
            Resolved resource ID string.

        Raises:
            ValueError: If the resource cannot be resolved.
        """
        entry_id, entry_name = self._normalise_reference_entry(entry, fallback_iter)

        validated_id = self._validate_resource_id(fetch_by_id, entry_id)
        if validated_id:
            return validated_id
        if entry_id and entry_name is None:
            return entry_id

        if entry_name:
            resolved, success = self._resolve_resource_by_name(find_by_name, entry_name, singular, plural)
            return resolved if success else entry_name

        raise ValueError(f"{singular} references must include a valid ID or name.")

    @staticmethod
    def _coerce_reference_value(entry: Any) -> str:
        """Coerce a reference entry to a string value.

        Args:
            entry: Reference entry (dict, string, or other).

        Returns:
            String representation of the reference.
        """
        if isinstance(entry, dict):
            if entry.get("id"):
                return str(entry["id"])
            if entry.get("name"):
                return str(entry["name"])
        return str(entry)

    @staticmethod
    def _validate_resource_id(fetch_by_id: Callable[[str], Any], candidate_id: str | None) -> str | None:
        """Validate a resource ID by attempting to fetch it.

        Args:
            fetch_by_id: Function to fetch resource by ID.
            candidate_id: Candidate ID to validate.

        Returns:
            Validated ID if found, None otherwise.
        """
        if not candidate_id:
            return None
        try:
            fetch_by_id(candidate_id)
        except Exception:
            return None
        return candidate_id

    @staticmethod
    def _resolve_resource_by_name(
        find_by_name: Callable[[str], list[Any]],
        entry_name: str,
        singular: str,
        plural: str,
    ) -> tuple[str, bool]:
        """Resolve a resource by name to an ID.

        Args:
            find_by_name: Function to find resources by name.
            entry_name: Name of the resource to find.
            singular: Singular label for error messages.
            plural: Plural label for error messages.

        Returns:
            Tuple of (resolved_id, success).

        Raises:
            ValueError: If resource not found or multiple matches exist.
        """
        try:
            matches = find_by_name(entry_name)
        except Exception:
            return entry_name, False

        if not matches:
            raise ValueError(f"{singular} '{entry_name}' not found in current workspace.")
        if len(matches) > 1:
            exact = [m for m in matches if getattr(m, "name", "").lower() == entry_name.lower()]
            if len(exact) == 1:
                matches = exact
            else:
                raise ValueError(f"Multiple {plural} named '{entry_name}'. Please disambiguate.")
        return str(matches[0].id), True

    def _resolve_tool_ids(
        self,
        tools: list[Any] | None,
        references: list[Any] | None = None,
    ) -> list[str] | None:
        """Resolve tool references to IDs.

        Args:
            tools: List of tool references to resolve.
            references: Optional list of reference objects for fallback.

        Returns:
            List of resolved tool IDs, or None if tools is empty.
        """
        tool_client = self._get_tool_client()
        return self._resolve_resource_ids(
            tools,
            references,
            fetch_by_id=tool_client.get_tool_by_id,
            find_by_name=tool_client.find_tools,
            label="Tool",
            plural_label="tools",
        )

    def _resolve_agent_ids(
        self,
        agents: list[Any] | None,
        references: list[Any] | None = None,
    ) -> list[str] | None:
        """Resolve agent references to IDs.

        Args:
            agents: List of agent references to resolve.
            references: Optional list of reference objects for fallback.

        Returns:
            List of resolved agent IDs, or None if agents is empty.
        """
        return self._resolve_resource_ids(
            agents,
            references,
            fetch_by_id=self.get_agent_by_id,
            find_by_name=self.find_agents,
            label="Agent",
            plural_label="agents",
        )

    def _resolve_mcp_ids(
        self,
        mcps: list[Any] | None,
        references: list[Any] | None = None,
    ) -> list[str] | None:
        """Resolve MCP references to IDs.

        Args:
            mcps: List of MCP references to resolve.
            references: Optional list of reference objects for fallback.

        Returns:
            List of resolved MCP IDs, or None if mcps is empty.
        """
        mcp_client = self._get_mcp_client()
        return self._resolve_resource_ids(
            mcps,
            references,
            fetch_by_id=mcp_client.get_mcp_by_id,
            find_by_name=mcp_client.find_mcps,
            label="MCP",
            plural_label="MCPs",
        )

    def _create_agent_from_payload(self, payload: Mapping[str, Any]) -> "Agent":
        """Create an agent using a fully prepared payload mapping."""
        known, extras = _split_known_and_extra(payload, AgentCreateRequest.__dataclass_fields__)

        name = known.pop("name", None)
        instruction = known.pop("instruction", None)
        if not name or not str(name).strip():
            raise ValueError("Agent name cannot be empty or whitespace")
        if not instruction or not str(instruction).strip():
            raise ValueError("Agent instruction cannot be empty or whitespace")

        validated_instruction = validate_agent_instruction(str(instruction))
        _normalise_sequence_fields(known)

        resolved_model = known.pop("model", None) or DEFAULT_MODEL
        tool_refs = extras.pop("_tool_refs", None)
        agent_refs = extras.pop("_agent_refs", None)
        mcp_refs = extras.pop("_mcp_refs", None)

        tools_raw = known.pop("tools", None)
        agents_raw = known.pop("agents", None)
        mcps_raw = known.pop("mcps", None)

        resolved_tools = self._resolve_tool_ids(tools_raw, tool_refs)
        resolved_agents = self._resolve_agent_ids(agents_raw, agent_refs)
        resolved_mcps = self._resolve_mcp_ids(mcps_raw, mcp_refs)

        language_model_id = known.pop("language_model_id", None)
        provider = known.pop("provider", None)
        model_name = known.pop("model_name", None)

        agent_type_value = known.pop("agent_type", None)
        fallback_type_value = known.pop("type", None)
        if agent_type_value is None:
            agent_type_value = fallback_type_value or DEFAULT_AGENT_TYPE

        framework_value = known.pop("framework", None) or DEFAULT_AGENT_FRAMEWORK
        version_value = known.pop("version", None) or DEFAULT_AGENT_VERSION
        account_id = known.pop("account_id", None)
        description = known.pop("description", None)
        metadata = _prepare_agent_metadata(known.pop("metadata", None))
        tool_configs = known.pop("tool_configs", None)
        agent_config = known.pop("agent_config", None)
        timeout_value = known.pop("timeout", None)
        a2a_profile = known.pop("a2a_profile", None)

        final_extras = {**known, **extras}
        final_extras.setdefault("model", resolved_model)

        request = AgentCreateRequest(
            name=str(name).strip(),
            instruction=validated_instruction,
            model=resolved_model,
            language_model_id=language_model_id,
            provider=provider,
            model_name=model_name,
            agent_type=agent_type_value,
            framework=framework_value,
            version=version_value,
            account_id=account_id,
            description=description,
            metadata=metadata,
            tools=resolved_tools,
            agents=resolved_agents,
            mcps=resolved_mcps,
            tool_configs=tool_configs,
            agent_config=agent_config,
            timeout=timeout_value or DEFAULT_AGENT_RUN_TIMEOUT,
            a2a_profile=a2a_profile,
            extras=final_extras,
        )

        payload_dict = request.to_payload()
        payload_dict.setdefault("model", resolved_model)

        full_agent_data = self._post_then_fetch(
            id_key="id",
            post_endpoint=AGENTS_ENDPOINT,
            get_endpoint_fmt=f"{AGENTS_ENDPOINT}{{id}}",
            json=payload_dict,
        )
        response = AgentResponse(**full_agent_data)
        return Agent.from_response(response, client=self)

    def create_agent(
        self,
        name: str | None = None,
        instruction: str | None = None,
        model: str | None = None,
        tools: list[str | Any] | None = None,
        agents: list[str | Any] | None = None,
        timeout: int | None = None,
        *,
        file: str | PathLike[str] | None = None,
        mcps: list[str | Any] | None = None,
        tool_configs: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> "Agent":
        """Create a new agent, optionally loading configuration from a file."""
        base_overrides = {
            "name": name,
            "instruction": instruction,
            "model": model,
            "tools": tools,
            "agents": agents,
            "timeout": timeout,
            "mcps": mcps,
            "tool_configs": tool_configs,
        }
        overrides = _merge_override_maps(base_overrides, kwargs)

        if file is not None:
            payload = _prepare_import_payload(Path(file).expanduser(), overrides, drop_model_fields=True)
            if overrides.get("model") is None:
                payload.pop("model", None)
        else:
            payload = overrides

        return self._create_agent_from_payload(payload)

    def create_agent_from_file(  # pragma: no cover - thin compatibility wrapper
        self,
        file_path: str | PathLike[str],
        **overrides: Any,
    ) -> "Agent":
        """Backward-compatible helper to create an agent from a configuration file."""
        return self.create_agent(file=file_path, **overrides)

    def _update_agent_from_payload(
        self,
        agent_id: str,
        current_agent: Agent,
        payload: Mapping[str, Any],
    ) -> "Agent":
        """Update an agent using a prepared payload mapping."""
        known, extras = _split_known_and_extra(payload, AgentUpdateRequest.__dataclass_fields__)
        _normalise_sequence_fields(known)

        tool_refs = extras.pop("_tool_refs", None)
        agent_refs = extras.pop("_agent_refs", None)
        mcp_refs = extras.pop("_mcp_refs", None)

        tools_value = known.pop("tools", None)
        agents_value = known.pop("agents", None)
        mcps_value = known.pop("mcps", None)

        if tools_value is not None:
            tools_value = self._resolve_tool_ids(tools_value, tool_refs)
        if agents_value is not None:
            agents_value = self._resolve_agent_ids(agents_value, agent_refs)
        if mcps_value is not None:
            mcps_value = self._resolve_mcp_ids(mcps_value, mcp_refs)  # pragma: no cover

        request = AgentUpdateRequest(
            name=known.pop("name", None),
            instruction=known.pop("instruction", None),
            description=known.pop("description", None),
            model=known.pop("model", None),
            language_model_id=known.pop("language_model_id", None),
            provider=known.pop("provider", None),
            model_name=known.pop("model_name", None),
            agent_type=known.pop("agent_type", known.pop("type", None)),
            framework=known.pop("framework", None),
            version=known.pop("version", None),
            account_id=known.pop("account_id", None),
            metadata=known.pop("metadata", None),
            tools=tools_value,
            tool_configs=known.pop("tool_configs", None),
            agents=agents_value,
            mcps=mcps_value,
            agent_config=known.pop("agent_config", None),
            a2a_profile=known.pop("a2a_profile", None),
            extras={**known, **extras},
        )

        payload_dict = request.to_payload(current_agent)

        api_response = self._request("PUT", f"/agents/{agent_id}", json=payload_dict)
        response = AgentResponse(**api_response)
        return Agent.from_response(response, client=self)

    def update_agent(
        self,
        agent_id: str,
        name: str | None = None,
        instruction: str | None = None,
        model: str | None = None,
        *,
        file: str | PathLike[str] | None = None,
        tools: list[str | Any] | None = None,
        agents: list[str | Any] | None = None,
        mcps: list[str | Any] | None = None,
        **kwargs: Any,
    ) -> "Agent":
        """Update an existing agent."""
        base_overrides = {
            "name": name,
            "instruction": instruction,
            "model": model,
            "tools": tools,
            "agents": agents,
            "mcps": mcps,
        }
        overrides = _merge_override_maps(base_overrides, kwargs)

        if file is not None:
            payload = _prepare_import_payload(Path(file).expanduser(), overrides, drop_model_fields=True)
        else:
            payload = overrides

        current_agent = self.get_agent_by_id(agent_id)
        return self._update_agent_from_payload(agent_id, current_agent, payload)

    def update_agent_from_file(  # pragma: no cover - thin compatibility wrapper
        self,
        agent_id: str,
        file_path: str | PathLike[str],
        **overrides: Any,
    ) -> "Agent":
        """Backward-compatible helper to update an agent from a configuration file."""
        return self.update_agent(agent_id, file=file_path, **overrides)

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent."""
        self._request("DELETE", f"/agents/{agent_id}")

    def upsert_agent(self, identifier: str | Agent, **kwargs) -> Agent:
        """Create or update an agent by instance, ID, or name.

        Args:
            identifier: Agent instance, ID (UUID string), or name
            **kwargs: Agent configuration (instruction, description, tools, etc.)

        Returns:
            The created or updated agent.

        Example:
            >>> # By name (creates if not exists)
            >>> agent = client.agents.upsert_agent(
            ...     "hello_agent",
            ...     instruction="You are a helpful assistant.",
            ...     description="A friendly agent",
            ... )
            >>> # By instance
            >>> agent = client.agents.upsert_agent(existing_agent, description="Updated")
            >>> # By ID
            >>> agent = client.agents.upsert_agent("uuid-here", description="Updated")
        """
        # Handle Agent instance
        if isinstance(identifier, Agent):
            if identifier.id:
                logger.info("Updating agent by instance: %s", identifier.name)
                return self.update_agent(identifier.id, name=identifier.name, **kwargs)
            identifier = identifier.name

        # Handle string (ID or name)
        if isinstance(identifier, str):
            # Check if it's a UUID
            if is_uuid(identifier):
                logger.info("Updating agent by ID: %s", identifier)
                return self.update_agent(identifier, **kwargs)

            # It's a name - find or create
            return self._upsert_agent_by_name(identifier, **kwargs)

        raise ValueError(f"Invalid identifier type: {type(identifier)}")

    def _upsert_agent_by_name(self, name: str, **kwargs) -> Agent:
        """Find agent by name and update, or create if not found."""
        existing = self.find_agents(name)

        if len(existing) == 1:
            logger.info("Updating existing agent: %s", name)
            return self.update_agent(existing[0].id, name=name, **kwargs)

        if len(existing) > 1:
            raise ValueError(f"Multiple agents found with name '{name}'")

        # Create new agent
        logger.info("Creating new agent: %s", name)
        return self.create_agent(name=name, **kwargs)

    def _prepare_sync_request_data(
        self,
        message: str,
        files: list[str | BinaryIO] | None,
        tty: bool,
        **kwargs: Any,
    ) -> tuple[dict | None, dict | None, list | None, dict, Any | None]:
        """Prepare request data for synchronous agent runs with renderer support.

        Args:
            message: Message to send
            files: Optional files to include
            tty: Whether to enable TTY mode
            **kwargs: Additional request parameters

        Returns:
            Tuple of (payload, data_payload, files_payload, headers, multipart_data)
        """
        headers = {"Accept": SSE_CONTENT_TYPE}

        if files:
            # Handle multipart data for file uploads
            multipart_data = prepare_multipart_data(message, files)
            if "chat_history" in kwargs and kwargs["chat_history"] is not None:
                multipart_data.data["chat_history"] = kwargs["chat_history"]
            if "pii_mapping" in kwargs and kwargs["pii_mapping"] is not None:
                multipart_data.data["pii_mapping"] = kwargs["pii_mapping"]

            return (
                None,
                multipart_data.data,
                multipart_data.files,
                headers,
                multipart_data,
            )
        else:
            # Simple JSON payload for text-only requests
            payload = {"input": message, "stream": True, **kwargs}
            if tty:
                payload["tty"] = True
            return payload, None, None, headers, None

    def _get_timeout_values(self, timeout: float | None, **kwargs: Any) -> tuple[float, float]:
        """Get request timeout and execution timeout values.

        Args:
            timeout: Request timeout (overrides instance timeout)
            **kwargs: Additional parameters including execution timeout

        Returns:
            Tuple of (request_timeout, execution_timeout)
        """
        request_timeout = timeout or self.timeout
        execution_timeout = kwargs.get("timeout", DEFAULT_AGENT_RUN_TIMEOUT)
        return request_timeout, execution_timeout

    def run_agent(
        self,
        agent_id: str,
        message: str,
        files: list[str | BinaryIO] | None = None,
        tty: bool = False,
        *,
        renderer: RichStreamRenderer | str | None = "auto",
        runtime_config: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """Run an agent with a message, streaming via a renderer.

        Args:
            agent_id: The ID of the agent to run.
            message: The message to send to the agent.
            files: Optional list of files to include with the request.
            tty: Whether to enable TTY mode.
            renderer: Renderer for streaming output.
            runtime_config: Optional runtime configuration for tools, MCPs, and agents.
                Keys should be platform IDs. Example:
                {
                    "tool_configs": {"tool-id": {"param": "value"}},
                    "mcp_configs": {"mcp-id": {"setting": "on"}},
                    "agent_config": {"planning": True},
                }
            **kwargs: Additional arguments to pass to the run API.

        Returns:
            The agent's response as a string.
        """
        # Include runtime_config in kwargs only when caller hasn't already provided it
        if runtime_config is not None and "runtime_config" not in kwargs:
            kwargs["runtime_config"] = runtime_config
        (
            payload,
            data_payload,
            files_payload,
            headers,
            multipart_data,
        ) = self._prepare_sync_request_data(message, files, tty, **kwargs)

        render_manager = self._get_renderer_manager()
        verbose = kwargs.get("verbose", False)
        r = self._create_renderer(renderer, verbose=verbose)
        meta = render_manager.build_initial_metadata(agent_id, message, kwargs)
        render_manager.start_renderer(r, meta)

        final_text = ""
        stats_usage: dict[str, Any] = {}
        started_monotonic: float | None = None
        finished_monotonic: float | None = None

        timeout_seconds = compute_timeout_seconds(kwargs)

        try:
            response = self.http_client.stream(
                "POST",
                f"/agents/{agent_id}/run",
                json=payload,
                data=data_payload,
                files=files_payload,
                headers=headers,
                timeout=timeout_seconds,
            )

            with response as stream_response:
                stream_response.raise_for_status()

                agent_name = kwargs.get("agent_name")

                (
                    final_text,
                    stats_usage,
                    started_monotonic,
                    finished_monotonic,
                ) = self._process_stream_events(
                    stream_response,
                    r,
                    timeout_seconds,
                    agent_name,
                    meta,
                )

        except KeyboardInterrupt:
            try:
                r.close()
            finally:
                raise
        except Exception:
            try:
                r.close()
            finally:
                raise
        finally:
            if multipart_data:
                multipart_data.close()

        return self._finalize_renderer(
            r,
            final_text,
            stats_usage,
            started_monotonic,
            finished_monotonic,
        )

    def _prepare_request_data(
        self,
        message: str,
        files: list[str | BinaryIO] | None,
        **kwargs,
    ) -> tuple[dict | None, dict | None, dict | None, dict | None]:
        """Prepare request data for async agent runs.

        Returns:
            Tuple of (payload, data_payload, files_payload, headers)
        """
        if files:
            # Handle multipart data for file uploads
            multipart_data = prepare_multipart_data(message, files)
            # Inject optional multipart extras expected by backend
            if "chat_history" in kwargs and kwargs["chat_history"] is not None:
                multipart_data.data["chat_history"] = kwargs["chat_history"]
            if "pii_mapping" in kwargs and kwargs["pii_mapping"] is not None:
                multipart_data.data["pii_mapping"] = kwargs["pii_mapping"]

            headers = {"Accept": SSE_CONTENT_TYPE}
            return None, multipart_data.data, multipart_data.files, headers
        else:
            # Simple JSON payload for text-only requests
            payload = {"input": message, "stream": True, **kwargs}
            headers = {"Accept": SSE_CONTENT_TYPE}
            return payload, None, None, headers

    def _create_async_client_config(self, timeout: float | None, headers: dict | None) -> dict:
        """Create async client configuration with proper headers and timeout."""
        config = self._build_async_client(timeout or self.timeout)
        if headers:
            config["headers"] = {**config["headers"], **headers}
        return config

    async def _stream_agent_response(
        self,
        async_client: httpx.AsyncClient,
        agent_id: str,
        payload: dict | None,
        data_payload: dict | None,
        files_payload: dict | None,
        headers: dict | None,
        timeout_seconds: float,
        agent_name: str | None,
    ) -> AsyncGenerator[dict, None]:
        """Stream the agent response and yield parsed JSON chunks."""
        async with async_client.stream(
            "POST",
            f"/agents/{agent_id}/run",
            json=payload,
            data=data_payload,
            files=files_payload,
            headers=headers,
        ) as stream_response:
            stream_response.raise_for_status()

            async for event in aiter_sse_events(stream_response, timeout_seconds, agent_name):
                try:
                    chunk = json.loads(event["data"])
                    yield chunk
                except json.JSONDecodeError:
                    logger.debug("Non-JSON SSE fragment skipped")
                    continue

    async def arun_agent(
        self,
        agent_id: str,
        message: str,
        files: list[str | BinaryIO] | None = None,
        *,
        request_timeout: float | None = None,
        runtime_config: dict[str, Any] | None = None,
        **kwargs,
    ) -> AsyncGenerator[dict, None]:
        """Async run an agent with a message, yielding streaming JSON chunks.

        Args:
            agent_id: ID of the agent to run
            message: Message to send to the agent
            files: Optional list of files to include
            request_timeout: Optional request timeout in seconds (defaults to client timeout)
            runtime_config: Optional runtime configuration for tools, MCPs, and agents.
                Keys should be platform IDs. Example:
                {
                    "tool_configs": {"tool-id": {"param": "value"}},
                    "mcp_configs": {"mcp-id": {"setting": "on"}},
                    "agent_config": {"planning": True},
                }
            **kwargs: Additional arguments (chat_history, pii_mapping, etc.)

        Yields:
            Dictionary containing parsed JSON chunks from the streaming response

        Raises:
            AgentTimeoutError: When agent execution times out
            httpx.TimeoutException: When general timeout occurs
            Exception: For other unexpected errors
        """
        # Include runtime_config in kwargs only when caller hasn't already provided it
        if runtime_config is not None and "runtime_config" not in kwargs:
            kwargs["runtime_config"] = runtime_config
        # Derive timeout values for request/control flow
        legacy_timeout = kwargs.get("timeout")
        http_timeout_override = request_timeout if request_timeout is not None else legacy_timeout
        http_timeout = http_timeout_override or self.timeout

        # Prepare request data
        payload, data_payload, files_payload, headers = self._prepare_request_data(message, files, **kwargs)

        # Create async client configuration
        async_client_config = self._create_async_client_config(http_timeout_override, headers)

        # Get execution timeout for streaming control
        timeout_seconds = kwargs.get("timeout", DEFAULT_AGENT_RUN_TIMEOUT)
        agent_name = kwargs.get("agent_name")

        async def _chunk_stream() -> AsyncGenerator[dict, None]:
            async with httpx.AsyncClient(**async_client_config) as async_client:
                async for chunk in self._stream_agent_response(
                    async_client,
                    agent_id,
                    payload,
                    data_payload,
                    files_payload,
                    headers,
                    timeout_seconds,
                    agent_name,
                ):
                    yield chunk

        async with _async_timeout_guard(http_timeout):
            async for chunk in _chunk_stream():
                yield chunk

    @property
    def runs(self) -> "AgentRunsClient":
        """Get the agent runs client."""
        if self._runs_client is None:
            shared_config = build_shared_config(self)
            self._runs_client = AgentRunsClient(**shared_config)
        return self._runs_client
