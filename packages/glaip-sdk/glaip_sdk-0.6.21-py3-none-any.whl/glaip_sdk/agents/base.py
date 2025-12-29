"""Agent class for GL AIP platform.

This module provides the Agent class that serves as the foundation
for defining agents in glaip-sdk. The Agent class supports both:
- Direct instantiation for simple agents
- Subclassing for complex, reusable agent definitions

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

Example - Direct Instantiation:
    >>> from glaip_sdk.agents import Agent
    >>>
    >>> agent = Agent(
    ...     name="hello_agent",
    ...     instruction="You are a helpful assistant.",
    ... )
    >>> agent.deploy()
    >>> result = agent.run("Hello!")

Example - Subclassing:
    >>> from glaip_sdk.agents import Agent
    >>>
    >>> class WeatherAgent(Agent):
    ...     @property
    ...     def name(self) -> str:
    ...         return "weather_agent"
    ...
    ...     @property
    ...     def instruction(self) -> str:
    ...         return "You are a helpful weather assistant."
    ...
    ...     @property
    ...     def tools(self) -> list:
    ...         return [WeatherAPITool, "web_search"]
    >>>
    >>> # Deploy and run the agent
    >>> agent = WeatherAgent()
    >>> agent.deploy()
    >>> result = agent.run("What's the weather?")
"""

from __future__ import annotations

import inspect
import logging
import warnings
from collections.abc import AsyncGenerator


from pathlib import Path
from typing import TYPE_CHECKING, Any

from glaip_sdk.registry import get_agent_registry, get_mcp_registry, get_tool_registry
from glaip_sdk.utils.resource_refs import is_uuid

if TYPE_CHECKING:
    from glaip_sdk.models import AgentResponse
    from glaip_sdk.registry import AgentRegistry, MCPRegistry, ToolRegistry

logger = logging.getLogger(__name__)

_AGENT_NOT_DEPLOYED_MSG = "Agent must be deployed before running. Call deploy() first."
_CLIENT_NOT_AVAILABLE_MSG = "Client not available. Agent may not have been deployed properly."


class Agent:
    """Agent class for GL AIP platform.

    Supports both direct instantiation and subclassing.
    The deploy() method updates the agent in-place, so you can use the
    same instance for deployment and running.

    Direct instantiation (simple):
        >>> agent = Agent(
        ...     name="my_agent",
        ...     instruction="You are helpful.",
        ...     tools=["web_search"],
        ... )
        >>> agent.deploy()
        >>> result = agent.run("Hello!")

    Subclassing (complex):
        >>> class MyAgent(Agent):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_agent"
        ...
        ...     @property
        ...     def instruction(self) -> str:
        ...         return self.load_instruction_from_file("instructions.md")
        ...
        >>> agent = MyAgent()
        >>> agent.deploy()
        >>> result = agent.run("Hello!")

    Properties (override in subclass OR pass to __init__):
        - name: Agent name on the AIP platform (required)
        - instruction: Agent instruction text (required)
        - description: Agent description (default: "")
        - tools: List of tools (default: [])
        - agents: List of sub-agents (default: [])
        - mcps: List of MCPs (default: [])
        - timeout: Timeout in seconds (default: 300)
        - metadata: Optional metadata dict (default: None)
        - model: Optional model override (default: None)
        - framework: Agent framework (default: "langchain")
        - version: Agent version (default: "1.0.0")
        - agent_type: Agent type (default: "config")
        - agent_config: Agent execution config (default: None)
        - tool_configs: Per-tool config overrides (default: None)
        - mcp_configs: Per-MCP config overrides (default: None)
        - a2a_profile: A2A profile config (default: None)

    Instance attributes (set after deployment or from_response):
        - id: The agent's unique ID on the platform
        - _client: Client reference for run/update/delete operations
    """

    # Sentinel value to detect unset optional params
    _UNSET = object()

    def __init__(
        self,
        name: str | None = None,
        instruction: str | None = None,
        *,
        id: str | None = None,  # noqa: A002 - Allow shadowing builtin for API compat
        description: str | None = _UNSET,  # type: ignore[assignment]
        tools: list | None = None,
        agents: list | None = None,
        mcps: list | None = None,
        model: str | None = _UNSET,  # type: ignore[assignment]
        _client: Any = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an Agent.

        For direct instantiation, name and instruction are required.
        For subclassing, override the properties instead.

        Args:
            name: Agent name (required for direct instantiation).
            instruction: Agent instruction (required for direct instantiation).
            id: Agent ID (set after deployment or when created from API response).
            description: Agent description.
            tools: List of tools (Tool classes, SDK Tool objects, or strings).
            agents: List of sub-agents (Agent classes, instances, or strings).
            mcps: List of MCPs.
            model: Model identifier.
            _client: Internal client reference (set automatically).
            **kwargs: Additional configuration parameters:
                - timeout: Execution timeout in seconds.
                - metadata: Optional metadata dictionary.
                - framework: Agent framework identifier.
                - version: Agent version string.
                - agent_type: Agent type identifier.
                - agent_config: Agent execution configuration.
                - tool_configs: Per-tool configuration overrides.
                - mcp_configs: Per-MCP configuration overrides.
                - a2a_profile: A2A profile configuration.
        """
        # Instance attributes for deployed agents
        self._id = id
        self._client = _client
        self._created_at: str | None = None
        self._updated_at: str | None = None

        # Store values (None/UNSET means "use property default or override")
        self._name = name
        self._instruction = instruction
        self._description = description
        self._tools = tools
        self._agents = agents
        self._mcps = mcps
        self._model = model
        self._language_model_id: str | None = None
        # Extract parameters from kwargs with _UNSET defaults
        self._timeout = kwargs.pop("timeout", Agent._UNSET)  # type: ignore[assignment]
        self._metadata = kwargs.pop("metadata", Agent._UNSET)  # type: ignore[assignment]
        self._framework = kwargs.pop("framework", Agent._UNSET)  # type: ignore[assignment]
        self._version = kwargs.pop("version", Agent._UNSET)  # type: ignore[assignment]
        self._agent_type = kwargs.pop("agent_type", Agent._UNSET)  # type: ignore[assignment]
        self._agent_config = kwargs.pop("agent_config", Agent._UNSET)  # type: ignore[assignment]
        self._tool_configs = kwargs.pop("tool_configs", Agent._UNSET)  # type: ignore[assignment]
        self._mcp_configs = kwargs.pop("mcp_configs", Agent._UNSET)  # type: ignore[assignment]
        self._a2a_profile = kwargs.pop("a2a_profile", Agent._UNSET)  # type: ignore[assignment]

        # Warn about unexpected kwargs
        if kwargs:
            warnings.warn(
                f"Unexpected keyword arguments: {list(kwargs.keys())}. These will be ignored.",
                UserWarning,
                stacklevel=2,
            )

    # ─────────────────────────────────────────────────────────────────
    # Properties (override in subclasses OR pass to __init__)
    # ─────────────────────────────────────────────────────────────────

    @property
    def id(self) -> str | None:  # noqa: A003 - Allow shadowing builtin for API compat
        """Agent ID on the platform.

        This is set after deployment or when created from an API response.

        Returns:
            The unique ID or None if not deployed yet.
        """
        return self._id

    @id.setter
    def id(self, value: str | None) -> None:  # noqa: A003
        """Set the agent ID."""
        self._id = value

    @property
    def created_at(self) -> str | None:
        """Timestamp when the agent was created.

        Returns:
            ISO format timestamp string or None if not deployed.
        """
        return self._created_at

    @created_at.setter
    def created_at(self, value: str | None) -> None:
        """Set the created_at timestamp."""
        self._created_at = value

    @property
    def updated_at(self) -> str | None:
        """Timestamp when the agent was last updated.

        Returns:
            ISO format timestamp string or None if not deployed.
        """
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: str | None) -> None:
        """Set the updated_at timestamp."""
        self._updated_at = value

    @property
    def name(self) -> str:
        """Agent name on the AIP platform.

        Returns:
            The unique identifier name for this agent.

        Raises:
            ValueError: If name is not provided via __init__ or property override.
        """
        if self._name is None:
            raise ValueError(
                "Agent name is required. Either pass name to __init__() or override the name property in a subclass."
            )
        return self._name

    @property
    def instruction(self) -> str:
        """Agent instruction text.

        Returns:
            The instruction/prompt for the agent.

        Raises:
            ValueError: If instruction is not provided via __init__ or property
                override.
        """
        if self._instruction is None:
            raise ValueError(
                "Agent instruction is required. Either pass instruction to __init__() "
                "or override the instruction property in a subclass."
            )
        return self._instruction

    @property
    def description(self) -> str:
        """Agent description.

        Returns:
            A description of what this agent does. Defaults to empty string.
        """
        if self._description is not self._UNSET:
            return self._description or ""
        return ""

    @property
    def tools(self) -> list:
        """Tools available to this agent.

        Tools can be:
            - Tool class: Custom tool that will be auto-uploaded
            - glaip_sdk.models.Tool: SDK Tool object (uses tool.id)
            - str: Native tool name or ID (resolved by platform)

        Returns:
            List of tool references. Defaults to empty list.
        """
        return self._tools or []

    @property
    def agents(self) -> list:
        """Sub-agents available to this agent.

        Sub-agents can be:
            - Agent class: Will be deployed recursively
            - glaip_sdk.models.Agent: SDK Agent object (uses agent.id)
            - str: Agent name or ID (resolved by platform)

        Returns:
            List of sub-agent references. Defaults to empty list.
        """
        return self._agents or []

    @property
    def timeout(self) -> int:
        """Agent timeout in seconds.

        Returns:
            Timeout value in seconds. Defaults to 300.
        """
        if self._timeout is not self._UNSET and self._timeout is not None:
            return self._timeout
        return 300

    @property
    def metadata(self) -> dict[str, Any] | None:
        """Optional metadata dictionary.

        Returns:
            Metadata dict or None.
        """
        if self._metadata is not self._UNSET:
            return self._metadata
        return None

    @property
    def model(self) -> str | None:
        """Optional model override.

        Returns:
            Model identifier string or None to use default.
        """
        if self._model is not self._UNSET:
            return self._model
        return None

    @property
    def language_model_id(self) -> str | None:
        """Language model ID from the API.

        Returns:
            The language model UUID or None.
        """
        return self._language_model_id

    @property
    def framework(self) -> str:
        """Agent framework identifier.

        Returns:
            The framework name. Defaults to "langchain".
        """
        if self._framework is not self._UNSET and self._framework is not None:
            return self._framework
        return "langchain"

    @property
    def version(self) -> str:
        """Agent version string.

        Returns:
            The version identifier. Defaults to "1.0.0".
        """
        if self._version is not self._UNSET and self._version is not None:
            return self._version
        return "1.0.0"

    @property
    def agent_type(self) -> str:
        """Agent type identifier.

        Returns:
            The agent type. Defaults to "config".
        """
        if self._agent_type is not self._UNSET and self._agent_type is not None:
            return self._agent_type
        return "config"

    @property
    def agent_config(self) -> dict[str, Any] | None:
        """Agent configuration for execution settings.

        This is used for agent-level settings like execution_timeout.
        Note: The `timeout` property is a convenience shortcut that
        maps to agent_config.execution_timeout.

        Returns:
            Agent configuration dict or None.
        """
        if self._agent_config is not self._UNSET:
            return self._agent_config
        return None

    @property
    def tool_configs(self) -> dict[Any, dict[str, Any]] | None:
        """Per-tool configuration overrides.

        A mapping of tool references (classes, names, or IDs) to their
        configuration overrides. Supports both class keys and string keys.

        Example:
            >>> @property
            ... def tool_configs(self):
            ...     return {
            ...         MyToolClass: {"api_key": "xxx"},  # Class key
            ...         "other_tool": {"setting": "value"},  # String key
            ...     }

        Returns:
            Tool configurations dict or None.
        """
        if self._tool_configs is not self._UNSET:
            return self._tool_configs
        return None

    @property
    def mcps(self) -> list:
        """MCPs (Model Context Protocols) available to this agent.

        MCPs can be:
            - glaip_sdk.models.MCP: SDK MCP object (uses mcp.id)
            - str: MCP name or ID (resolved by platform)

        Returns:
            List of MCP references. Defaults to empty list.
        """
        return self._mcps or []

    @property
    def mcp_configs(self) -> dict[str, Any] | None:
        """Per-MCP configuration overrides.

        A mapping of MCP IDs to their configuration overrides.

        Returns:
            MCP configurations dict or None.
        """
        if self._mcp_configs is not self._UNSET:
            return self._mcp_configs
        return None

    @property
    def a2a_profile(self) -> dict[str, Any] | None:
        """A2A (Agent-to-Agent) profile configuration.

        Configuration for agent-to-agent communication capabilities.

        Returns:
            A2A profile dict or None.
        """
        if self._a2a_profile is not self._UNSET:
            return self._a2a_profile
        return None

    def deploy(self) -> Agent:
        """Deploy this agent (with tools and sub-agents) to GL AIP.

        Performs the following steps:
            1. Upload custom tools (Tool classes) - cached by ToolRegistry
            2. Deploy sub-agents recursively (Agent classes) - cached by AgentRegistry
            3. Resolve tool_configs (requires tools to be in registry first)
            4. Create/update this agent

        Tools and agents are cached globally by their respective registries
        to avoid duplicate uploads across deployments.

        After deployment, this Agent instance is updated in-place with:
            - id: The agent's unique ID on the platform
            - _client: A client reference for run/update/delete operations

        Returns:
            Self with id and _client set, ready for run() calls.

        Raises:
            Exception: If deployment fails due to API error.

        Example:
            >>> agent = Agent(
            ...     name="my_agent",
            ...     instruction="You are helpful.",
            ... )
            >>> agent.deploy()
            >>> print(f"Deployed: {agent.name} (ID: {agent.id})")
            >>> result = agent.run("Hello!")
        """
        logger.info("Deploying agent: %s", self.name)

        # Resolve tools FIRST - this uploads them and populates the registry
        tool_ids = self._resolve_tools(get_tool_registry())

        # Resolve agents
        agent_ids = self._resolve_agents(get_agent_registry())

        # Now build config - tool_configs can be resolved because tools are in registry
        config = self._build_config(get_tool_registry(), get_mcp_registry())
        config["tools"] = tool_ids
        config["agents"] = agent_ids

        from glaip_sdk.utils.client import get_client  # noqa: PLC0415

        client = get_client()
        from glaip_sdk.utils.discovery import find_agent  # noqa: PLC0415

        response = self._create_or_update_agent(config, client, find_agent)

        # Update self with deployed info
        self._id = response.id
        self._client = client

        return self

    def _build_config(self, tool_registry: ToolRegistry, mcp_registry: MCPRegistry) -> dict[str, Any]:
        """Build the base configuration dictionary.

        Args:
            tool_registry: The tool registry for resolving tool configs.
            mcp_registry: The MCP registry for resolving MCPs.

        Returns:
            Dictionary with agent configuration.
        """
        config: dict[str, Any] = {
            "name": self.name,
            "instruction": self.instruction,
            "description": self.description,
            "framework": self.framework,
            "version": self.version,
            "agent_type": self.agent_type,
            "model": self.model,
        }

        # Handle metadata (default to empty dict if None)
        config["metadata"] = self.metadata or {}

        # Handle agent_config with timeout
        # The timeout property is a convenience that maps to agent_config.execution_timeout
        agent_config = dict(self.agent_config) if self.agent_config else {}
        if self.timeout and "execution_timeout" not in agent_config:
            agent_config["execution_timeout"] = self.timeout
        if agent_config:
            config["agent_config"] = agent_config

        # Handle tool_configs - resolve tool names/classes to IDs
        if self.tool_configs:
            config["tool_configs"] = self._resolve_tool_configs(tool_registry)

        # Handle MCPs
        if self.mcps:
            config["mcps"] = self._resolve_mcps(mcp_registry)

        # Handle mcp_configs - normalize keys to MCP IDs
        if self.mcp_configs:
            config["mcp_configs"] = self._resolve_mcp_configs(mcp_registry)

        # Handle a2a_profile
        if self.a2a_profile:
            config["a2a_profile"] = self.a2a_profile

        return config

    def _resolve_mcps(self, registry: MCPRegistry) -> list[str]:
        """Resolve MCP references to IDs using MCPRegistry.

        Uses the global MCPRegistry to cache MCP objects across deployments.
        The registry handles all MCP types: MCP helpers, strings, dicts,
        and glaip_sdk.models.MCP objects.

        Args:
            registry: The MCP registry.

        Returns:
            List of resolved MCP IDs for the API payload.
        """
        if not self.mcps:
            return []

        return [registry.resolve(mcp_ref).id for mcp_ref in self.mcps]

    def _resolve_tools(self, registry: ToolRegistry) -> list[str]:
        """Resolve tool references to IDs using ToolRegistry.

        Uses the global ToolRegistry to cache Tool objects across deployments.
        The registry handles all tool types: Tool classes, LangChain BaseTool,
        glaip_sdk.models.Tool, and string names.

        Args:
            registry: The tool registry.

        Returns:
            List of resolved tool IDs for the API payload.
        """
        if not self.tools:
            return []

        # Resolve each tool reference to a Tool object, extract ID
        return [registry.resolve(tool_ref).id for tool_ref in self.tools]

    def _resolve_tool_configs(self, registry: ToolRegistry) -> dict[str, Any]:
        """Resolve tool_configs keys from tool names/classes to tool IDs.

        Allows tool_configs to be defined with tool names, class names, or
        Tool classes as keys. These are resolved to actual tool IDs using
        the ToolRegistry.

        Supported key formats:
            - Tool class: SyncReportSchedulerTool
            - Tool name string: "sync_report_scheduler"
            - Tool ID (UUID): Passed through unchanged

        Args:
            registry: The tool registry.

        Returns:
            Dict with resolved tool IDs as keys and configs as values.

        Example:
            >>> class MyAgent(Agent):
            ...     @property
            ...     def tool_configs(self):
            ...         return {
            ...             SyncReportSchedulerTool: {"api_key": "xxx"},
            ...             "other_tool": {"setting": "value"},
            ...         }
        """
        if not self.tool_configs:
            return {}

        resolved: dict[str, Any] = {}

        for key, config in self.tool_configs.items():
            # If key is already a UUID-like string, pass through
            if isinstance(key, str) and is_uuid(key):
                resolved[key] = config
                continue

            try:
                # Resolve key (tool name/class) to Tool object, get ID
                tool = registry.resolve(key)
                resolved[tool.id] = config
            except (ValueError, KeyError) as e:
                raise ValueError(f"Failed to resolve tool config key: {key}") from e

        return resolved

    def _resolve_mcp_configs(self, registry: MCPRegistry) -> dict[str, Any]:
        """Resolve mcp_configs keys from MCP names/objects to MCP IDs.

        Allows mcp_configs to be defined with MCP names, MCP objects, or UUIDs
        as keys. Keys are resolved to MCP IDs using the MCPRegistry.

        Supported key formats:
            - MCP object (with id): uses id directly
            - MCP name string: resolved via registry to ID
            - MCP ID (UUID string): passed through unchanged

        Args:
            registry: The MCP registry.

        Returns:
            Dict with resolved MCP IDs as keys and configs as values.
        """
        if not self.mcp_configs:
            return {}

        resolved: dict[str, Any] = {}

        for key, config in self.mcp_configs.items():
            try:
                # If key is already a UUID-like string, pass through
                if isinstance(key, str) and is_uuid(key):
                    resolved_id = key
                else:
                    mcp = registry.resolve(key)
                    resolved_id = mcp.id

                if resolved_id in resolved:
                    raise ValueError(
                        f"Duplicate mcp_configs entries resolve to the same MCP id '{resolved_id}' (key={key!r})"
                    )

                resolved[resolved_id] = config
            except (ValueError, KeyError) as exc:
                raise ValueError(
                    f"Failed to resolve mcp config key {key!r} (type={type(key).__name__}): {exc}"
                ) from exc

        return resolved

    def _resolve_agents(self, registry: AgentRegistry) -> list:
        """Resolve sub-agent references using AgentRegistry.

        Uses the global AgentRegistry to cache Agent objects across deployments.
        The registry handles all agent types: Agent classes, instances,
        glaip_sdk.models.Agent, and string names.

        Args:
            registry: The agent registry.

        Returns:
            List of resolved agent IDs for the API payload.
        """
        if not self.agents:
            return []

        # Resolve each agent reference to a deployed Agent, extract ID
        return [registry.resolve(agent_ref).id for agent_ref in self.agents]

    def _create_or_update_agent(
        self,
        config: dict[str, Any],
        client: Any,
        find_agent_fn: Any,
    ) -> AgentResponse:
        """Create or update the agent on the platform.

        Args:
            config: The agent configuration dictionary.
            client: The API client.
            find_agent_fn: Function to find existing agent by name.

        Returns:
            The created or updated AgentResponse from the API.
        """
        existing = find_agent_fn(self.name)

        if existing:
            logger.info("Updating existing agent: %s", self.name)
            updated = client.update_agent(agent_id=existing.id, **config)
            logger.info("✓ Agent '%s' updated successfully", self.name)
            return updated

        logger.info("Creating new agent: %s", self.name)
        created = client.create_agent(**config)
        logger.info("✓ Agent '%s' created successfully", self.name)
        return created

    @staticmethod
    def load_instruction_from_file(
        path: str,
        base_path: Path | None = None,
        variables: dict[str, str] | None = None,
    ) -> str:
        """Load instruction text from a markdown file.

        Args:
            path: File path (absolute or relative to base_path).
            base_path: Base directory for relative paths. If None, auto-detected
                from the caller's file location.
            variables: Template variables for {{variable}} substitution.

        Returns:
            Loaded instruction text with variables substituted.

        Raises:
            FileNotFoundError: If the instruction file doesn't exist.

        Example:
            >>> instruction = Agent.load_instruction_from_file(
            ...     "instructions/agent.md",
            ...     variables={"agent_name": "Weather Bot"}
            ... )
        """
        file_path = Path(path)

        if not file_path.is_absolute():
            if base_path is None:
                caller_frame = inspect.stack()[1]
                base_path = Path(caller_frame.filename).parent
            file_path = base_path / path

        if not file_path.exists():
            raise FileNotFoundError(f"Instruction file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        if variables:
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", value)

        return content

    # =========================================================================
    # API Methods - Available after deploy()
    # =========================================================================

    def model_dump(self, *, exclude_none: bool = False) -> dict[str, Any]:
        """Return a dict representation of the Agent.

        Provides Pydantic-style serialization for backward compatibility.

        Args:
            exclude_none: If True, exclude None values from the output.

        Returns:
            Dictionary containing Agent attributes.
        """
        data = {
            "id": self._id,
            "name": self.name,
            "instruction": self.instruction,
            "description": self.description,
            "type": self.agent_type,
            "framework": self.framework,
            "version": self.version,
            "tools": self.tools,
            "agents": self.agents,
            "mcps": self.mcps,
            "timeout": self.timeout,
            "metadata": self.metadata,
            "agent_config": self.agent_config,
            "tool_configs": self.tool_configs,
            "mcp_configs": self.mcp_configs,
            "a2a_profile": self.a2a_profile,
            "created_at": self._created_at,
            "updated_at": self._updated_at,
        }
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        return data

    def _set_client(self, client: Any) -> Agent:
        """Set the client for API operations.

        Args:
            client: The Glaip client instance.

        Returns:
            Self for method chaining.
        """
        self._client = client
        return self

    def _prepare_run_kwargs(
        self,
        message: str,
        verbose: bool,
        runtime_config: dict[str, Any] | None,
        **kwargs: Any,
    ) -> tuple[Any, dict[str, Any]]:
        """Prepare common arguments for run/arun methods.

        Args:
            message: The message to send to the agent.
            verbose: If True, print streaming output to console.
            runtime_config: Optional runtime configuration.
            **kwargs: Additional arguments to pass to the run API.

        Returns:
            Tuple of (agent_client, call_kwargs).

        Raises:
            ValueError: If the agent hasn't been deployed yet.
            RuntimeError: If client is not available.
        """
        if not self.id:  # pragma: no cover - defensive: called only when self.id is truthy
            raise ValueError(_AGENT_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        agent_client = getattr(self._client, "agents", self._client)

        call_kwargs: dict[str, Any] = {
            "agent_id": self.id,
            "message": message,
            "verbose": verbose,
        }

        if runtime_config is not None:
            from glaip_sdk.utils.runtime_config import (  # noqa: PLC0415
                normalize_runtime_config_keys,
            )

            call_kwargs["runtime_config"] = normalize_runtime_config_keys(
                runtime_config,
                tool_registry=get_tool_registry(),
                mcp_registry=get_mcp_registry(),
                agent_registry=get_agent_registry(),
            )

        call_kwargs.update(kwargs)
        return agent_client, call_kwargs

    def _get_local_runner_or_raise(self) -> Any:
        """Get the local runner if available, otherwise raise ValueError.

        Returns:
            The default local runner instance.

        Raises:
            ValueError: If local runtime is not available.
        """
        from glaip_sdk.runner import get_default_runner  # noqa: PLC0415
        from glaip_sdk.runner.deps import (  # noqa: PLC0415
            check_local_runtime_available,
            get_local_runtime_missing_message,
        )

        if check_local_runtime_available():
            return get_default_runner()
        raise ValueError(f"{_AGENT_NOT_DEPLOYED_MSG}\n\n{get_local_runtime_missing_message()}")

    def _prepare_local_runner_kwargs(
        self,
        message: str,
        verbose: bool,
        runtime_config: dict[str, Any] | None,
        chat_history: list[dict[str, str]] | None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare kwargs for local runner execution.

        Args:
            message: The message to send to the agent.
            verbose: If True, print streaming output to console.
            runtime_config: Optional runtime configuration.
            chat_history: Optional list of prior conversation messages.
            **kwargs: Additional arguments.

        Returns:
            Dictionary of prepared kwargs for runner.run() or runner.arun().
        """
        return {
            "agent": self,
            "message": message,
            "verbose": verbose,
            "runtime_config": runtime_config,
            "chat_history": chat_history,
            **kwargs,
        }

    def run(
        self,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Run the agent synchronously with a message.

        Supports two execution modes:
        - **Server-backed**: When the agent is deployed (has an ID), execution
          happens via the AIP backend server.
        - **Local**: When the agent is not deployed and glaip-sdk[local] is installed,
          execution happens locally via aip-agents (no server required).

        Args:
            message: The message to send to the agent.
            verbose: If True, print streaming output to console. Defaults to False.
            runtime_config: Optional runtime configuration for tools, MCPs, and agents.
                Keys can be SDK objects, UUIDs, or names. Example:
                {
                    "tool_configs": {"tool-id": {"param": "value"}},
                    "mcp_configs": {"mcp-id": {"setting": "on"}},
                    "agent_config": {"planning": True},
                }
                Defaults to None.
            chat_history: Optional list of prior conversation messages for context.
                Each message is a dict with "role" and "content" keys.
                Defaults to None.
            **kwargs: Additional arguments to pass to the run API.

        Returns:
            The agent's response as a string.

        Raises:
            ValueError: If the agent is not deployed and local runtime is not available.
            RuntimeError: If server-backed execution fails due to client issues.
        """
        # Backend routing: deployed agents use server, undeployed use local (if available)
        if self.id:
            # Server-backed execution path (agent is deployed)
            agent_client, call_kwargs = self._prepare_run_kwargs(
                message, verbose, runtime_config or kwargs.get("runtime_config"), **kwargs
            )
            if chat_history is not None:
                call_kwargs["chat_history"] = chat_history
            return agent_client.run_agent(**call_kwargs)

        # Local execution path (agent is not deployed)
        runner = self._get_local_runner_or_raise()
        local_kwargs = self._prepare_local_runner_kwargs(message, verbose, runtime_config, chat_history, **kwargs)
        return runner.run(**local_kwargs)

    async def arun(
        self,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict, None]:
        """Run the agent asynchronously with streaming output.

        Supports two execution modes:
        - **Server-backed**: When the agent is deployed (has an ID), execution
          happens via the AIP backend server with streaming.
        - **Local**: When the agent is not deployed and glaip-sdk[local] is installed,
          execution happens locally via aip-agents (no server required).

        Args:
            message: The message to send to the agent.
            verbose: If True, print streaming output to console. Defaults to False.
            runtime_config: Optional runtime configuration for tools, MCPs, and agents.
                Keys can be SDK objects, UUIDs, or names. Example:
                {
                    "tool_configs": {"tool-id": {"param": "value"}},
                    "mcp_configs": {"mcp-id": {"setting": "on"}},
                    "agent_config": {"planning": True},
                }
                Defaults to None.
            chat_history: Optional list of prior conversation messages for context.
                Each message is a dict with "role" and "content" keys.
                Defaults to None.
            **kwargs: Additional arguments to pass to the run API.

        Yields:
            Streaming response chunks from the agent.

        Raises:
            ValueError: If the agent is not deployed and local runtime is not available.
            RuntimeError: If server-backed execution fails due to client issues.
        """
        # Backend routing: deployed agents use server, undeployed use local (if available)
        if self.id:
            # Server-backed execution path (agent is deployed)
            agent_client, call_kwargs = self._prepare_run_kwargs(
                message, verbose, runtime_config or kwargs.get("runtime_config"), **kwargs
            )
            if chat_history is not None:
                call_kwargs["chat_history"] = chat_history

            async for chunk in agent_client.arun_agent(**call_kwargs):
                yield chunk
            return

        # Local execution path (agent is not deployed)
        runner = self._get_local_runner_or_raise()
        local_kwargs = self._prepare_local_runner_kwargs(message, verbose, runtime_config, chat_history, **kwargs)
        result = await runner.arun(**local_kwargs)
        # Yield a final_response event for consistency with server-backed execution
        # Include event_type for A2A event shape parity
        yield {
            "event_type": "final_response",
            "metadata": {"kind": "final_response"},
            "content": result,
            "is_final": True,
        }

    def update(self, **kwargs: Any) -> Agent:
        """Update the deployed agent with new configuration.

        Args:
            **kwargs: Agent properties to update (name, instruction, etc.).

        Returns:
            Self with updated properties.

        Raises:
            ValueError: If the agent hasn't been deployed yet.
            RuntimeError: If client is not available.
        """
        if not self.id:
            raise ValueError(_AGENT_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        # _client can be either main Client or AgentClient
        agent_client = getattr(self._client, "agents", self._client)
        response = agent_client.update_agent(agent_id=self.id, **kwargs)

        # Update local properties from response (read-only props via private attrs)
        name = getattr(response, "name", None)
        if name:
            self._name = name

        instruction = getattr(response, "instruction", None)
        if instruction:
            self._instruction = instruction

        # Populate remaining fields like description, metadata, updated_at, etc.
        type(self)._populate_from_response(self, response)

        return self

    def delete(self) -> None:
        """Delete the deployed agent.

        Raises:
            ValueError: If the agent hasn't been deployed yet.
            RuntimeError: If client is not available.
        """
        if not self.id:
            raise ValueError(_AGENT_NOT_DEPLOYED_MSG)
        if not self._client:
            raise RuntimeError(_CLIENT_NOT_AVAILABLE_MSG)

        # _client can be either main Client or AgentClient
        agent_client = getattr(self._client, "agents", self._client)
        agent_client.delete_agent(self.id)
        self.id = None
        self._client = None

    @classmethod
    def _populate_from_response(cls, agent: Agent, response: AgentResponse) -> None:
        """Populate agent fields from API response."""
        # Field mappings: (response_attr, agent_attr, require_truthy)
        field_mappings = [
            ("description", "_description", True),
            ("model", "_model", True),
            ("type", "_agent_type", True),
            ("framework", "_framework", True),
            ("version", "_version", True),
            ("timeout", "_timeout", True),
            ("metadata", "_metadata", True),
            ("agent_config", "_agent_config", True),
            ("tool_configs", "_tool_configs", True),
            ("mcp_configs", "_mcp_configs", True),
            ("a2a_profile", "_a2a_profile", True),
            ("language_model_id", "_language_model_id", True),
            ("created_at", "_created_at", False),
            ("updated_at", "_updated_at", False),
        ]

        for resp_attr, agent_attr, require_truthy in field_mappings:
            value = getattr(response, resp_attr, None)
            if require_truthy:
                if value:
                    setattr(agent, agent_attr, value)
            else:
                if value is not None:
                    setattr(agent, agent_attr, value)

        # Copy relationship refs as-is (preserve full objects for serialization)
        # Registry resolution handles extracting IDs during deployment
        tools_val = getattr(response, "tools", None)
        if tools_val:
            agent._tools = tools_val

        agents_val = getattr(response, "agents", None)
        if agents_val:
            agent._agents = agents_val

        mcps_val = getattr(response, "mcps", None)
        if mcps_val:
            agent._mcps = mcps_val

    @classmethod
    def from_response(
        cls,
        response: AgentResponse,
        client: Any = None,
    ) -> Agent:
        """Create an Agent instance from an API response.

        This allows you to work with agents retrieved from the API
        as full Agent instances with all methods available.

        Args:
            response: The AgentResponse from an API call.
            client: The Glaip client instance for API operations.

        Returns:
            An Agent instance initialized from the response.

        Example:
            >>> response = client.agents.get("agent-123")
            >>> agent = Agent.from_response(response, client)
            >>> result = agent.run("Hello!")
        """
        agent = cls(
            name=response.name,
            instruction=response.instruction or "",
            id=response.id,
        )

        cls._populate_from_response(agent, response)

        if client:
            agent._set_client(client)

        return agent
