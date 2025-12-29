"""LangGraph-based runner for local agent execution.

This module provides the LangGraphRunner which executes glaip-sdk agents
locally via the aip-agents LangGraphReactAgent, without requiring the AIP server.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

Example:
    >>> from glaip_sdk.runner import LangGraphRunner
    >>> from glaip_sdk.agents import Agent
    >>>
    >>> runner = LangGraphRunner()
    >>> agent = Agent(name="my-agent", instruction="You are helpful.")
    >>> result = runner.run(agent, "Hello, world!")
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aip_agents.agent.hitl.manager import ApprovalManager  # noqa: PLC0415
from gllm_core.utils import LoggerManager

from glaip_sdk.client.run_rendering import AgentRunRenderingManager
from glaip_sdk.hitl import LocalPromptHandler, PauseResumeCallback
from glaip_sdk.runner.base import BaseRunner
from glaip_sdk.runner.deps import (
    check_local_runtime_available,
    get_local_runtime_missing_message,
)
from glaip_sdk.utils.tool_storage_provider import build_tool_output_manager

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

    from glaip_sdk.agents.base import Agent


_AIP_LOGS_SWALLOWED = False


def _swallow_aip_logs(level: int = logging.ERROR) -> None:
    """Consume noisy AIPAgents logs once (opt-in via runner flag)."""
    global _AIP_LOGS_SWALLOWED
    if _AIP_LOGS_SWALLOWED:
        return
    prefixes = ("aip_agents.",)

    def _silence(name: str) -> None:
        lg = logging.getLogger(name)
        lg.handlers = [logging.NullHandler()]
        lg.propagate = False
        lg.setLevel(level)

    # Silence any already-registered loggers under the given prefixes
    for logger_name in logging.root.manager.loggerDict:
        if any(logger_name.startswith(prefix) for prefix in prefixes):
            _silence(logger_name)

    # Also set the base prefix loggers so future children inherit silence
    for prefix in prefixes:
        _silence(prefix.rstrip("."))
    _AIP_LOGS_SWALLOWED = True


logger = LoggerManager().get_logger(__name__)


def _convert_chat_history_to_messages(
    chat_history: list[dict[str, str]] | None,
) -> list[BaseMessage]:
    """Convert chat history dicts to LangChain messages.

    Args:
        chat_history: List of dicts with "role" and "content" keys.
            Supported roles: "user"/"human", "assistant"/"ai", "system".

    Returns:
        List of LangChain BaseMessage instances.
    """
    if not chat_history:
        return []

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: PLC0415

    messages: list[BaseMessage] = []
    for msg in chat_history:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")

        if role in ("user", "human"):
            messages.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            # Default to human message for unknown roles
            logger.warning("Unknown chat history role '%s', treating as user message", role)
            messages.append(HumanMessage(content=content))

    return messages


@dataclass(frozen=True, slots=True)
class LangGraphRunner(BaseRunner):
    """Runner implementation using aip-agents LangGraphReactAgent.

    Current behavior:
    - Execute via `LangGraphReactAgent.arun_sse_stream()` (normalized SSE-compatible stream)
    - Route all events through `AgentRunRenderingManager.async_process_stream_events`
      for unified rendering between local and remote agents

    Attributes:
        default_model: Model name to use when agent.model is not set.
            Defaults to "gpt-4o-mini".
    """

    default_model: str = "openai/gpt-4o-mini"

    def run(
        self,
        agent: Agent,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        *,
        swallow_aip_logs: bool = True,
        **kwargs: Any,
    ) -> str:
        """Execute agent synchronously and return final response text.

        Args:
            agent: The glaip_sdk Agent to execute.
            message: The user message to send to the agent.
            verbose: If True, emit debug trace output during execution.
                Defaults to False.
            runtime_config: Optional runtime configuration for tools, MCPs, etc.
                Defaults to None. (Implemented in PR-04+)
            chat_history: Optional list of prior conversation messages.
                Each message is a dict with "role" and "content" keys.
                Defaults to None.
            swallow_aip_logs: When True (default), silence noisy logs from aip-agents,
                gllm_inference, OpenAILMInvoker, and httpx. Set to False to honor user
                logging configuration.
            **kwargs: Additional keyword arguments passed to the backend.

        Returns:
            The final response text from the agent.

        Raises:
            RuntimeError: If the local runtime dependencies are not available.
            RuntimeError: If no final response is received from the agent.
        """
        if not check_local_runtime_available():
            raise RuntimeError(get_local_runtime_missing_message())

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError(
                "LangGraphRunner.run() cannot be called from a running event loop. "
                "Use 'await LangGraphRunner.arun(...)' instead."
            )

        coro = self._arun_internal(
            agent=agent,
            message=message,
            verbose=verbose,
            runtime_config=runtime_config,
            chat_history=chat_history,
            swallow_aip_logs=swallow_aip_logs,
            **kwargs,
        )

        return asyncio.run(coro)

    async def arun(
        self,
        agent: Agent,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        *,
        swallow_aip_logs: bool = True,
        **kwargs: Any,
    ) -> str:
        """Execute agent asynchronously and return final response text.

        Args:
            agent: The glaip_sdk Agent to execute.
            message: The user message to send to the agent.
            verbose: If True, emit debug trace output during execution.
                Defaults to False.
            runtime_config: Optional runtime configuration for tools, MCPs, etc.
                Defaults to None. (Implemented in PR-04+)
            chat_history: Optional list of prior conversation messages.
                Each message is a dict with "role" and "content" keys.
                Defaults to None.
            swallow_aip_logs: When True (default), silence noisy AIPAgents logs.
            **kwargs: Additional keyword arguments passed to the backend.

        Returns:
            The final response text from the agent.

        Raises:
            RuntimeError: If no final response is received from the agent.
        """
        return await self._arun_internal(
            agent=agent,
            message=message,
            verbose=verbose,
            runtime_config=runtime_config,
            chat_history=chat_history,
            swallow_aip_logs=swallow_aip_logs,
            **kwargs,
        )

    async def _arun_internal(
        self,
        agent: Agent,
        message: str,
        verbose: bool = False,
        runtime_config: dict[str, Any] | None = None,
        chat_history: list[dict[str, str]] | None = None,
        *,
        swallow_aip_logs: bool = True,
        **kwargs: Any,
    ) -> str:
        """Internal async implementation of agent execution.

        Args:
            agent: The glaip_sdk Agent to execute.
            message: The user message to send to the agent.
            verbose: If True, emit debug trace output during execution.
            runtime_config: Optional runtime configuration for tools, MCPs, etc.
            chat_history: Optional list of prior conversation messages.
            swallow_aip_logs: When True (default), silence noisy AIPAgents logs.
            **kwargs: Additional keyword arguments passed to the backend.

        Returns:
            The final response text from the agent.
        """
        # Optionally swallow noisy AIPAgents logs
        if swallow_aip_logs:
            _swallow_aip_logs()

        # POC/MVP: Create pause/resume callback for interactive HITL input
        pause_resume_callback = PauseResumeCallback()

        # Build the local LangGraphReactAgent from the glaip_sdk Agent
        local_agent = self.build_langgraph_agent(
            agent, runtime_config=runtime_config, pause_resume_callback=pause_resume_callback
        )

        # Convert chat history to LangChain messages for the agent
        langchain_messages = _convert_chat_history_to_messages(chat_history)
        if langchain_messages:
            kwargs["messages"] = langchain_messages
            logger.debug(
                "Passing %d chat history messages to agent '%s'",
                len(langchain_messages),
                agent.name,
            )

        # Use shared render manager for unified processing
        render_manager = AgentRunRenderingManager(logger)
        renderer = render_manager.create_renderer(kwargs.get("renderer"), verbose=verbose)

        # POC/MVP: Set renderer on callback so LocalPromptHandler can pause/resume Live
        pause_resume_callback.set_renderer(renderer)

        meta = render_manager.build_initial_metadata(agent.name, message, kwargs)
        render_manager.start_renderer(renderer, meta)

        try:
            # Use shared async stream processor for unified event handling
            (
                final_text,
                stats_usage,
                started_monotonic,
                finished_monotonic,
            ) = await render_manager.async_process_stream_events(
                local_agent.arun_sse_stream(message, **kwargs),
                renderer,
                meta,
                skip_final_render=True,
            )
        except KeyboardInterrupt:
            try:
                renderer.close()
            finally:
                raise
        except Exception:
            try:
                renderer.close()
            finally:
                raise

        # Use shared finalizer to avoid code duplication
        from glaip_sdk.client.run_rendering import finalize_render_manager  # noqa: PLC0415

        return finalize_render_manager(
            render_manager, renderer, final_text, stats_usage, started_monotonic, finished_monotonic
        )

    def build_langgraph_agent(
        self,
        agent: Agent,
        runtime_config: dict[str, Any] | None = None,
        shared_tool_output_manager: Any | None = None,
        *,
        pause_resume_callback: Any | None = None,
    ) -> Any:
        """Build a LangGraphReactAgent from a glaip_sdk Agent definition.

        Args:
            agent: The glaip_sdk Agent to convert.
            runtime_config: Optional runtime configuration with tool_configs,
                mcp_configs, agent_config, and agent-specific overrides.
            shared_tool_output_manager: Optional ToolOutputManager to reuse across
                agents with tool_output_sharing enabled.
            pause_resume_callback: Optional callback used to pause/resume the renderer
                during interactive HITL prompts.

        Returns:
            A configured LangGraphReactAgent instance.

        Raises:
            ImportError: If aip-agents is not installed.
            ValueError: If agent has unsupported tools, MCPs, or sub-agents for local mode.
        """
        from aip_agents.agent import LangGraphReactAgent  # noqa: PLC0415

        from glaip_sdk.runner.tool_adapter import LangChainToolAdapter  # noqa: PLC0415

        # Adapt tools for local execution
        # NOTE: CLI parity waiver - local tool execution is SDK-only for MVP.
        # See specs/f/local-agent-runtime/plan.md: "CLI parity is explicitly deferred
        # and will require SDK Technical Lead sign-off per constitution principle IV."
        langchain_tools: list[Any] = []
        if agent.tools:
            adapter = LangChainToolAdapter()
            langchain_tools = adapter.adapt_tools(agent.tools)

        # Normalize runtime config: merge global and agent-specific configs
        normalized_config = self._normalize_runtime_config(runtime_config, agent)

        # Merge tool_configs: agent definition < runtime config
        tool_configs = self._merge_tool_configs(agent, normalized_config)

        # Merge mcp_configs: agent definition < runtime config
        mcp_configs = self._merge_mcp_configs(agent, normalized_config)

        # Merge agent_config: agent definition < runtime config
        merged_agent_config = self._merge_agent_config(agent, normalized_config)
        agent_config_params, agent_config_kwargs = self._apply_agent_config(merged_agent_config)

        tool_output_manager = self._resolve_tool_output_manager(
            agent,
            merged_agent_config,
            shared_tool_output_manager,
        )

        # Build sub-agents recursively, sharing tool output manager when enabled.
        sub_agent_instances = self._build_sub_agents(
            agent.agents,
            runtime_config,
            shared_tool_output_manager=tool_output_manager,
        )

        # Build the LangGraphReactAgent with tools, sub-agents, and configs
        local_agent = LangGraphReactAgent(
            name=agent.name,
            instruction=agent.instruction,
            description=agent.description,
            model=agent.model or self.default_model,
            tools=langchain_tools,
            agents=sub_agent_instances if sub_agent_instances else None,
            tool_configs=tool_configs if tool_configs else None,
            tool_output_manager=tool_output_manager,
            **agent_config_params,
            **agent_config_kwargs,
        )

        # Add MCP servers if configured
        self._add_mcp_servers(local_agent, agent, mcp_configs)

        # Inject local HITL manager only if hitl_enabled is True (master switch).
        # This matches remote behavior: hitl_enabled gates the HITL plumbing.
        # Tool-level HITL configs are only enforced when hitl_enabled=True.
        self._inject_hitl_manager(local_agent, merged_agent_config, agent.name, pause_resume_callback)

        logger.debug(
            "Built local LangGraphReactAgent for agent '%s' with %d tools, %d sub-agents, and %d MCPs",
            agent.name,
            len(langchain_tools),
            len(sub_agent_instances),
            len(agent.mcps) if agent.mcps else 0,
        )
        return local_agent

    def _resolve_tool_output_manager(
        self,
        agent: Agent,
        merged_agent_config: dict[str, Any],
        shared_tool_output_manager: Any | None,
    ) -> Any | None:
        """Resolve tool output manager for local agent execution."""
        tool_output_sharing_enabled = merged_agent_config.get("tool_output_sharing", False)
        if not tool_output_sharing_enabled:
            return None
        if shared_tool_output_manager is not None:
            return shared_tool_output_manager
        return build_tool_output_manager(agent.name, merged_agent_config)

    def _inject_hitl_manager(
        self,
        local_agent: Any,
        merged_agent_config: dict[str, Any],
        agent_name: str,
        pause_resume_callback: Any | None,
    ) -> None:
        """Inject HITL manager when enabled, mirroring remote gating behavior."""
        hitl_enabled = merged_agent_config.get("hitl_enabled", False)
        if hitl_enabled:
            try:
                local_agent.hitl_manager = ApprovalManager(
                    prompt_handler=LocalPromptHandler(pause_resume_callback=pause_resume_callback)
                )
                # Store callback reference for setting renderer later
                if pause_resume_callback:
                    local_agent._pause_resume_callback = pause_resume_callback
                logger.debug("HITL manager injected for agent '%s' (hitl_enabled=True)", agent_name)
            except ImportError as e:
                # Missing dependencies - fail fast
                raise ImportError("Local HITL requires aip_agents. Install with: pip install 'glaip-sdk[local]'") from e
            except Exception as e:
                # Other errors during HITL setup - fail fast
                raise RuntimeError(f"Failed to initialize HITL manager for agent '{agent_name}'") from e
        else:
            logger.debug("HITL manager not injected for agent '%s' (hitl_enabled=False)", agent_name)

    def _build_sub_agents(
        self,
        sub_agents: list[Any] | None,
        runtime_config: dict[str, Any] | None,
        shared_tool_output_manager: Any | None = None,
    ) -> list[Any]:
        """Build sub-agent instances recursively.

        Args:
            sub_agents: List of sub-agent definitions.
            runtime_config: Runtime config to pass to sub-agents.
            shared_tool_output_manager: Optional ToolOutputManager to reuse across
                agents with tool_output_sharing enabled.

        Returns:
            List of built sub-agent instances.

        Raises:
            ValueError: If sub-agent is platform-only.
        """
        if not sub_agents:
            return []

        sub_agent_instances = []
        for sub_agent in sub_agents:
            self._validate_sub_agent_for_local_mode(sub_agent)
            sub_agent_instances.append(
                self.build_langgraph_agent(
                    sub_agent,
                    runtime_config,
                    shared_tool_output_manager=shared_tool_output_manager,
                )
            )
        return sub_agent_instances

    def _add_mcp_servers(
        self,
        local_agent: Any,
        agent: Agent,
        merged_mcp_configs: dict[str, Any],
    ) -> None:
        """Add MCP servers to a built agent.

        Args:
            local_agent: The LangGraphReactAgent to add MCPs to.
            agent: The glaip_sdk Agent with MCP definitions.
            merged_mcp_configs: Merged mcp_configs (agent definition + runtime).
        """
        if not agent.mcps:
            return

        from glaip_sdk.runner.mcp_adapter import LangChainMCPAdapter  # noqa: PLC0415

        mcp_adapter = LangChainMCPAdapter()
        base_mcp_configs = mcp_adapter.adapt_mcps(agent.mcps)

        # Apply merged mcp_configs overrides (agent definition + runtime)
        if merged_mcp_configs:
            base_mcp_configs = self._apply_runtime_mcp_configs(base_mcp_configs, merged_mcp_configs)

        if base_mcp_configs:
            local_agent.add_mcp_server(base_mcp_configs)
            logger.debug(
                "Registered %d MCP server(s) for agent '%s'",
                len(base_mcp_configs),
                agent.name,
            )

    def _normalize_runtime_config(
        self,
        runtime_config: dict[str, Any] | None,
        agent: Agent,
    ) -> dict[str, Any]:
        """Normalize runtime_config for local execution.

        Merges global and agent-specific configs with proper priority.
        Keys are resolved from instances/classes to string names.

        Args:
            runtime_config: Raw runtime config from user.
            agent: The agent being built (for resolving agent-specific overrides).

        Returns:
            Normalized config with string keys and merged priorities.
        """
        from glaip_sdk.utils.runtime_config import (  # noqa: PLC0415
            merge_configs,
            normalize_local_config_keys,
        )

        if not runtime_config:
            return {}

        # 1. Extract global configs and normalize keys
        global_tool_configs = normalize_local_config_keys(runtime_config.get("tool_configs", {}))
        global_mcp_configs = normalize_local_config_keys(runtime_config.get("mcp_configs", {}))
        global_agent_config = runtime_config.get("agent_config", {})

        # 2. Extract agent-specific overrides (highest priority)
        agent_specific = self._get_agent_specific_config(runtime_config, agent)
        agent_tool_configs = normalize_local_config_keys(agent_specific.get("tool_configs", {}))
        agent_mcp_configs = normalize_local_config_keys(agent_specific.get("mcp_configs", {}))
        agent_config_override = agent_specific.get("agent_config", {})

        # 3. Merge with priority: global < agent-specific
        merged_result = {
            "tool_configs": merge_configs(global_tool_configs, agent_tool_configs),
            "mcp_configs": merge_configs(global_mcp_configs, agent_mcp_configs),
            "agent_config": merge_configs(global_agent_config, agent_config_override),
        }
        return merged_result

    def _get_agent_specific_config(
        self,
        runtime_config: dict[str, Any],
        agent: Agent,
    ) -> dict[str, Any]:
        """Extract agent-specific config from runtime_config.

        Args:
            runtime_config: Runtime config that may contain agent-specific overrides.
            agent: The agent to find config for.

        Returns:
            Agent-specific config dict, or empty dict if not found.
        """
        from glaip_sdk.utils.resource_refs import is_uuid  # noqa: PLC0415
        from glaip_sdk.utils.runtime_config import get_name_from_key  # noqa: PLC0415

        # Reserved keys at the top level
        reserved_keys = {"tool_configs", "mcp_configs", "agent_config"}

        # Try finding agent by instance, class, or name
        for key, value in runtime_config.items():
            if key in reserved_keys:
                continue  # Skip global configs

            if isinstance(key, str) and is_uuid(key):
                logger.warning(
                    "UUID agent override key '%s' is not supported in local mode; skipping. "
                    "Use agent name string or Agent instance as the key instead.",
                    key,
                )
                continue

            # Check if this key matches the agent
            try:
                key_name = get_name_from_key(key)
            except ValueError:
                continue  # Skip invalid keys

            if key_name and key_name == agent.name:
                return value if isinstance(value, dict) else {}

        return {}

    def _merge_tool_configs(
        self,
        agent: Agent,
        normalized_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge agent.tool_configs with runtime tool_configs.

        Priority (lowest to highest):
        1. Agent definition (agent.tool_configs)
        2. Runtime config (normalized_config["tool_configs"])

        Args:
            agent: The agent with optional tool_configs property.
            normalized_config: Normalized runtime config.

        Returns:
            Merged tool_configs dict.
        """
        from glaip_sdk.utils.runtime_config import (  # noqa: PLC0415
            merge_configs,
            normalize_local_config_keys,
        )

        # Get agent's tool_configs if defined
        agent_tool_configs = {}
        if hasattr(agent, "tool_configs") and agent.tool_configs:
            agent_tool_configs = normalize_local_config_keys(agent.tool_configs)

        # Get runtime tool_configs
        runtime_tool_configs = normalized_config.get("tool_configs", {})

        # Merge: agent definition < runtime config
        return merge_configs(agent_tool_configs, runtime_tool_configs)

    def _merge_mcp_configs(
        self,
        agent: Agent,
        normalized_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge agent.mcp_configs with runtime mcp_configs.

        Priority (lowest to highest):
        1. Agent definition (agent.mcp_configs)
        2. Runtime config (normalized_config["mcp_configs"])

        Args:
            agent: The agent with optional mcp_configs property.
            normalized_config: Normalized runtime config.

        Returns:
            Merged mcp_configs dict.
        """
        from glaip_sdk.utils.runtime_config import (  # noqa: PLC0415
            merge_configs,
            normalize_local_config_keys,
        )

        # Get agent's mcp_configs if defined
        agent_mcp_configs = {}
        if hasattr(agent, "mcp_configs") and agent.mcp_configs:
            agent_mcp_configs = normalize_local_config_keys(agent.mcp_configs)

        # Get runtime mcp_configs
        runtime_mcp_configs = normalized_config.get("mcp_configs", {})

        # Merge: agent definition < runtime config
        return merge_configs(agent_mcp_configs, runtime_mcp_configs)

    def _merge_agent_config(
        self,
        agent: Agent,
        normalized_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge agent.agent_config with runtime agent_config.

        Priority (lowest to highest):
        1. Agent definition (agent.agent_config)
        2. Runtime config (normalized_config["agent_config"])

        Args:
            agent: The agent with optional agent_config property.
            normalized_config: Normalized runtime config.

        Returns:
            Merged agent_config dict.
        """
        from glaip_sdk.utils.runtime_config import merge_configs  # noqa: PLC0415

        # Get agent's agent_config if defined
        agent_agent_config = {}
        if hasattr(agent, "agent_config") and agent.agent_config:
            agent_agent_config = agent.agent_config

        # Get runtime agent_config
        runtime_agent_config = normalized_config.get("agent_config", {})

        # Merge: agent definition < runtime config
        return merge_configs(agent_agent_config, runtime_agent_config)

    def _apply_agent_config(
        self,
        agent_config: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Extract and separate agent_config into direct params and kwargs.

        Separates agent_config into parameters that go directly to LangGraphReactAgent
        constructor vs those that go through **kwargs.

        Args:
            agent_config: Runtime agent configuration dict.

        Returns:
            Tuple of (direct_params, kwargs_params):
            - direct_params: Parameters passed directly to LangGraphReactAgent.__init__()
            - kwargs_params: Parameters passed via **kwargs to BaseAgent
        """
        direct_params = {}
        kwargs_params = {}

        # Direct constructor parameters
        if "planning" in agent_config:
            direct_params["planning"] = agent_config["planning"]

        if "enable_a2a_token_streaming" in agent_config:
            direct_params["enable_a2a_token_streaming"] = agent_config["enable_a2a_token_streaming"]

        # Kwargs parameters (passed through **kwargs to BaseAgent)
        if "enable_pii" in agent_config:
            kwargs_params["enable_pii"] = agent_config["enable_pii"]

        if "memory" in agent_config:
            # Map "memory" to "memory_backend" for aip-agents compatibility
            kwargs_params["memory_backend"] = agent_config["memory"]

        # Additional memory-related settings
        memory_settings = ["agent_id", "memory_namespace", "save_interaction_to_memory"]
        for key in memory_settings:
            if key in agent_config:
                kwargs_params[key] = agent_config[key]

        return direct_params, kwargs_params

    def _apply_runtime_mcp_configs(
        self,
        base_configs: dict[str, Any],
        runtime_overrides: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply runtime mcp_configs overrides to base MCP configurations.

        Merges runtime overrides into the base configs, handling authentication
        conversion to headers using MCPConfigBuilder.

        Args:
            base_configs: Base MCP configs from adapter (server_name -> config).
            runtime_overrides: Runtime mcp_configs overrides (server_name -> config).

        Returns:
            Merged MCP configs with authentication converted to headers.
        """
        return {
            server_name: self._merge_single_mcp_config(server_name, base_config, runtime_overrides.get(server_name))
            for server_name, base_config in base_configs.items()
        }

    def _merge_single_mcp_config(
        self,
        server_name: str,
        base_config: dict[str, Any],
        override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Merge a single MCP config with runtime override.

        Args:
            server_name: Name of the MCP server.
            base_config: Base config from adapter.
            override: Optional runtime override config.

        Returns:
            Merged config dict.
        """
        merged = base_config.copy()

        if not override:
            return merged

        from glaip_sdk.runner.mcp_adapter.mcp_config_builder import (  # noqa: PLC0415
            MCPConfigBuilder,
        )

        # Handle authentication override
        if "authentication" in override:
            headers = MCPConfigBuilder.build_headers_from_auth(override["authentication"])
            if headers:
                merged["headers"] = headers
                logger.debug("Applied runtime authentication headers for MCP '%s'", server_name)

        # Merge other config keys (excluding authentication since we converted it)
        for key, value in override.items():
            if key != "authentication":
                merged[key] = value

        return merged

    def _validate_sub_agent_for_local_mode(self, sub_agent: Any) -> None:
        """Validate that a sub-agent reference is supported for local execution.

        Args:
            sub_agent: The sub-agent reference to validate.

        Raises:
            ValueError: If the sub-agent is not supported in local mode.
        """
        # String references are allowed by SDK API but not for local mode
        if isinstance(sub_agent, str):
            raise ValueError(
                f"Sub-agent '{sub_agent}' is a string reference and cannot be used in local mode. "
                "String sub-agent references are only supported for server execution. "
                "For local mode, define the sub-agent with Agent(name=..., instruction=...)."
            )

        # Validate sub-agent is not a class
        if inspect.isclass(sub_agent):
            raise ValueError(
                f"Sub-agent '{sub_agent.__name__}' is a class, not an instance. "
                "Local mode requires Agent INSTANCES. "
                "Did you forget to instantiate it? e.g., Agent(...), not Agent"
            )

        # Validate sub-agent is an Agent-like object (has required attributes)
        if not hasattr(sub_agent, "name") or not hasattr(sub_agent, "instruction"):
            raise ValueError(
                f"Sub-agent {type(sub_agent).__name__} is not supported in local mode. "
                "Local mode requires Agent instances with 'name' and 'instruction' attributes. "
                "Define the sub-agent with Agent(name=..., instruction=...)."
            )

        # Validate sub-agent is not platform-only (from_id, from_native)
        if getattr(sub_agent, "_lookup_only", False):
            agent_name = getattr(sub_agent, "name", "<unknown>")
            raise ValueError(
                f"Sub-agent '{agent_name}' is not supported in local mode. "
                "Platform agents (from_id, from_native) cannot be used as "
                "sub-agents in local execution. "
                "Define the sub-agent locally with Agent(name=..., instruction=...) instead."
            )

    def _log_event(self, event: dict[str, Any]) -> None:
        """Log an A2AEvent for verbose debug output.

        Args:
            event: The A2AEvent dictionary to log.
        """
        event_type = event.get("event_type", "unknown")
        content = event.get("content", "")
        is_final = event.get("is_final", False)

        # Truncate long content for readability
        content_str = str(content) if content else ""
        content_preview = content_str[:100] + "..." if len(content_str) > 100 else content_str

        final_marker = "(final)" if is_final else ""
        logger.info("[%s] %s %s", event_type, final_marker, content_preview)
