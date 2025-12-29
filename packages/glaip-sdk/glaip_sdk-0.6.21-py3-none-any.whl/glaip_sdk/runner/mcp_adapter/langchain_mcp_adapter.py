"""LangChain MCP adapter for local agent runtime.

This module handles adaptation of glaip-sdk MCP references to aip-agents
MCP configuration format for local execution.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from typing import Any

from glaip_sdk.runner.mcp_adapter.base_mcp_adapter import BaseMCPAdapter
from glaip_sdk.runner.mcp_adapter.mcp_config_builder import MCPConfigBuilder
from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)


class LangChainMCPAdapter(BaseMCPAdapter):
    """Adapts glaip-sdk MCPs to aip-agents mcp_config dict format.

    Handles:
    - MCP class with http transport → convert to mcp_config
    - MCP class with sse transport → convert to mcp_config
    - MCP class with stdio transport → convert to mcp_config

    Rejects:
    - MCP.from_native() → platform-specific
    - String MCP references → platform-specific
    """

    def adapt_mcps(self, mcp_refs: list[Any]) -> dict[str, Any]:
        """Adapt MCP references to aip-agents mcp_config format.

        Args:
            mcp_refs: List of MCP references from Agent definition.

        Returns:
            Dictionary mapping server names to configuration dicts.
            Format: {server_name: {transport: ..., url: ..., ...}}

        Raises:
            ValueError: If MCP is not supported in local mode.
        """
        mcp_configs = {}

        for mcp_ref in mcp_refs:
            server_name, config = self._adapt_single_mcp(mcp_ref)
            mcp_configs[server_name] = config

        logger.debug("Adapted %d MCPs to aip-agents format", len(mcp_configs))
        return mcp_configs

    def _adapt_single_mcp(self, mcp_ref: Any) -> tuple[str, dict[str, Any]]:
        """Adapt a single MCP reference.

        Args:
            mcp_ref: Single MCP reference to adapt.

        Returns:
            Tuple of (server_name, config_dict).

        Raises:
            ValueError: If MCP is not supported.
        """
        # 1. String references (not supported)
        if isinstance(mcp_ref, str):
            raise ValueError(self._get_platform_mcp_error(mcp_ref))

        # 2. MCP instance - check if it's local or platform
        if self._is_local_mcp(mcp_ref):
            config = self._convert_mcp_config(mcp_ref)
            return mcp_ref.name, config

        # 3. Platform MCP (from_native, from_id)
        if self._is_platform_mcp(mcp_ref):
            raise ValueError(self._get_platform_mcp_error(mcp_ref))

        # 4. Unknown type
        raise ValueError(
            f"Unsupported MCP type for local mode: {type(mcp_ref)}. "
            "Local mode only supports MCP class instances with http/sse/stdio transport."
        )

    def _is_local_mcp(self, ref: Any) -> bool:
        """Check if ref is a local MCP (has transport config)."""
        return (
            hasattr(ref, "transport")
            and hasattr(ref, "name")
            and getattr(ref, "transport", None) in ("http", "sse", "stdio")
            and not self._is_lookup_only(ref)
        )

    def _is_lookup_only(self, ref: Any) -> bool:
        """Check if MCP is lookup-only (platform reference)."""
        return hasattr(ref, "_lookup_only") and getattr(ref, "_lookup_only", False)

    def _convert_mcp_config(self, mcp: Any) -> dict[str, Any]:
        """Convert glaip-sdk MCP to aip-agents mcp_config format.

        Args:
            mcp: glaip-sdk MCP instance.

        Returns:
            aip-agents compatible MCP config dict.
        """
        # Start with user-provided config
        config = mcp.config.copy() if mcp.config else {}

        # Ensure transport is set
        config["transport"] = mcp.transport

        # Map server_url to url if needed (aip-agents uses 'url')
        if "server_url" in config and "url" not in config:
            config["url"] = config.pop("server_url")

        self._validate_converted_config(
            mcp_name=mcp.name,
            transport=mcp.transport,
            config=config,
        )

        # Convert authentication to headers using MCPConfigBuilder
        # Merge with existing headers (auth headers take precedence for conflicts)
        if hasattr(mcp, "authentication") and mcp.authentication:
            auth_headers = MCPConfigBuilder.build_headers_from_auth(mcp.authentication)
            if auth_headers:
                existing_headers = config.get("headers", {})
                config["headers"] = {**existing_headers, **auth_headers}
            else:
                logger.warning("Failed to build headers from authentication for MCP '%s'", mcp.name)

        logger.debug("Converted MCP '%s' with transport '%s'", mcp.name, mcp.transport)
        return config

    def _validate_converted_config(self, mcp_name: str, transport: str, config: dict[str, Any]) -> None:
        """Validate converted MCP config matches aip-agents schema expectations.

        This method performs transport-specific validation after the glaip-sdk MCP
        has been converted into the `aip-agents` `mcp_config` dictionary.

        Args:
            mcp_name: The MCP server name.
            transport: The MCP transport type.
            config: The converted MCP configuration dictionary.

        Raises:
            ValueError: If the configuration is invalid for the chosen transport.
        """
        self._validate_transport_config(mcp_name, transport)
        if transport in ("http", "sse"):
            self._validate_http_sse_config(
                mcp_name=mcp_name,
                transport=transport,
                config=config,
            )
            return
        if transport == "stdio":
            self._validate_stdio_config(
                mcp_name=mcp_name,
                config=config,
            )

    def _validate_transport_config(self, mcp_name: str, transport: str) -> None:
        """Validate that the MCP transport is supported by local mode.

        Args:
            mcp_name: The MCP server name.
            transport: The MCP transport type.

        Raises:
            ValueError: If the transport is not one of 'http', 'sse', or 'stdio'.
        """
        if transport not in ("http", "sse", "stdio"):
            raise ValueError(
                f"Invalid MCP config for '{mcp_name}': transport must be one of "
                f"'http', 'sse', or 'stdio'. Got: {transport!r}"
            )

    def _validate_http_sse_config(self, mcp_name: str, transport: str, config: dict[str, Any]) -> None:
        """Validate http/sse config has a usable URL.

        Args:
            mcp_name: The MCP server name.
            transport: The MCP transport type ('http' or 'sse').
            config: The converted MCP configuration dictionary.

        Raises:
            ValueError: If url is missing/empty or does not use http(s) scheme.
        """
        url = config.get("url")
        if not isinstance(url, str) or not url:
            raise ValueError(
                f"Invalid MCP config for '{mcp_name}': transport='{transport}' "
                "requires config['url'] as a non-empty string."
            )

        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(
                f"Invalid MCP config for '{mcp_name}': config['url'] must start with "
                f"'http://' or 'https://'. Got: {url!r}"
            )

    def _validate_stdio_config(self, mcp_name: str, config: dict[str, Any]) -> None:
        """Validate stdio config has a usable command and optional args list.

        Args:
            mcp_name: The MCP server name.
            config: The converted MCP configuration dictionary.

        Raises:
            ValueError: If command is missing/empty or args is not a list of strings.
        """
        command = config.get("command")
        if not isinstance(command, str) or not command:
            raise ValueError(
                f"Invalid MCP config for '{mcp_name}': transport='stdio' "
                "requires config['command'] as a non-empty string."
            )

        args = config.get("args")
        if args is not None and (not isinstance(args, list) or any(not isinstance(x, str) for x in args)):
            raise ValueError(
                f"Invalid MCP config for '{mcp_name}': transport='stdio' expects "
                "config['args'] to be a list[str] if provided."
            )

    def _is_platform_mcp(self, ref: Any) -> bool:
        """Check if ref is platform-specific (not supported locally)."""
        # MCP.from_native() or MCP.from_id() instances
        if self._is_lookup_only(ref):
            return True

        # MCP with ID but no local transport
        if hasattr(ref, "id") and getattr(ref, "id") and not self._is_local_mcp(ref):
            return True

        return False

    def _get_platform_mcp_error(self, ref: Any) -> str:
        """Get error message for platform MCPs."""
        if isinstance(ref, str):
            mcp_name = ref
        else:
            mcp_name = getattr(ref, "name", "<unknown>")

        return (
            f"MCP '{mcp_name}' is not supported in local mode.\n\n"
            "Local mode only supports MCPs with local transport configurations:\n"
            "  - MCP(name='...', transport='http', config={{'url': '...'}})\n"
            "  - MCP(name='...', transport='sse', config={{'url': '...'}})\n"
            "  - MCP(name='...', transport='stdio', config={{'command': '...'}})\n\n"
            "Alternatives:\n"
            "  1. Configure MCP with a local server URL\n"
            "  2. Deploy the agent to use platform MCPs: agent.deploy()\n"
            "  3. Remove MCP for local testing"
        )
