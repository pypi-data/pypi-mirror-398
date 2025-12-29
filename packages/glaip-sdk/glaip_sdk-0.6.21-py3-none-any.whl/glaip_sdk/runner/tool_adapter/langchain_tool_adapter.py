"""LangChain tool adapter for local agent runtime.

This module handles adaptation of glaip-sdk tool references to LangChain
BaseTool instances for local execution with aip-agents (LangGraph backend).

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from typing import Any

from glaip_sdk.runner.tool_adapter.base_tool_adapter import BaseToolAdapter
from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)

# Constant for unknown tool name placeholder
_UNKNOWN_TOOL_NAME = "<unknown>"


class LangChainToolAdapter(BaseToolAdapter):
    """Adapts glaip-sdk tools to LangChain BaseTool format for aip-agents.

    Handles:
    - LangChain BaseTool classes → instantiate
    - LangChain BaseTool instances → return as-is
    - Tool.from_langchain() → extract underlying tool
    - @tool_plugin decorator → ignore (just metadata)

    Rejects:
    - Tool.from_native() → platform-specific
    - String tool names → platform-specific
    """

    def adapt_tools(self, tool_refs: list[Any]) -> list[Any]:
        """Adapt tool references to LangChain BaseTool instances.

        Args:
            tool_refs: List of tool references from Agent definition.

        Returns:
            List of LangChain BaseTool instances.

        Raises:
            ValueError: If tool is not supported in local mode.
        """
        langchain_tools = []

        for tool_ref in tool_refs:
            langchain_tool = self._adapt_single_tool(tool_ref)
            langchain_tools.append(langchain_tool)

        logger.debug("Adapted %d tools to LangChain format", len(langchain_tools))
        return langchain_tools

    def _adapt_single_tool(self, tool_ref: Any) -> Any:
        """Adapt a single tool reference.

        Args:
            tool_ref: Single tool reference to adapt.

        Returns:
            LangChain BaseTool instance.

        Raises:
            ValueError: If tool is not supported.
        """
        # 1. Tool.from_langchain() wrapper
        if self._is_tool_wrapper(tool_ref):
            return self._extract_from_wrapper(tool_ref)

        # 2. Direct LangChain BaseTool
        if self._is_langchain_tool(tool_ref):
            return self._instantiate_langchain_tool(tool_ref)

        # 3. Platform tools (not supported)
        if self._is_platform_tool(tool_ref):
            raise ValueError(self._get_platform_tool_error(tool_ref))

        # 4. Unknown type
        raise ValueError(
            f"Unsupported tool type for local mode: {type(tool_ref)}. "
            "Local mode only supports LangChain BaseTool classes/instances."
        )

    def _has_explicit_attr(self, ref: Any, attr: str) -> bool:
        """Check if attribute is explicitly set on the object.

        This avoids false positives from objects like MagicMock, where hasattr()
        can return True even if the attribute was never set.
        """
        ref_dict = getattr(ref, "__dict__", None)
        return isinstance(ref_dict, dict) and attr in ref_dict

    def _is_tool_wrapper(self, ref: Any) -> bool:
        """Check if ref is a Tool.from_langchain() wrapper.

        Args:
            ref: Object to check.

        Returns:
            True if ref is a Tool.from_langchain() wrapper.
        """
        if self._has_explicit_attr(ref, "langchain_tool") and hasattr(ref, "id") and hasattr(ref, "name"):
            return True

        if self._has_explicit_attr(ref, "tool_class"):
            return getattr(ref, "tool_class", None) is not None

        return False

    def _extract_from_wrapper(self, wrapper: Any) -> Any:
        """Extract underlying LangChain tool from Tool.from_langchain().

        Args:
            wrapper: Tool.from_langchain() wrapper object.

        Returns:
            LangChain BaseTool instance.

        Raises:
            ValueError: If the wrapper's underlying tool is not a valid LangChain tool.
        """
        langchain_tool = getattr(wrapper, "langchain_tool", None)
        if langchain_tool is None:
            langchain_tool = getattr(wrapper, "tool_class", None)

        # Validate the extracted object is a valid LangChain tool
        if langchain_tool is None:
            wrapper_name = getattr(wrapper, "name", _UNKNOWN_TOOL_NAME)
            raise ValueError(
                f"Tool wrapper '{wrapper_name}' does not contain a valid LangChain tool. "
                "Ensure Tool.from_langchain() was called with a LangChain BaseTool class or instance."
            )

        # Validate it's actually a LangChain tool (class or instance)
        if not self._is_langchain_tool(langchain_tool):
            wrapper_name = getattr(wrapper, "name", _UNKNOWN_TOOL_NAME)
            raise ValueError(
                f"Tool wrapper '{wrapper_name}' contains an invalid tool type: {type(langchain_tool)}. "
                "Expected a LangChain BaseTool class or instance."
            )

        # If it's a class, instantiate it
        if isinstance(langchain_tool, type):
            langchain_tool = langchain_tool()

        logger.debug(
            "Extracted LangChain tool from wrapper: %s",
            getattr(langchain_tool, "name", _UNKNOWN_TOOL_NAME),
        )
        return langchain_tool

    def _is_langchain_tool(self, ref: Any) -> bool:
        """Check if ref is a LangChain BaseTool class or instance.

        Args:
            ref: Object to check.

        Returns:
            True if ref is a LangChain BaseTool.
        """
        from glaip_sdk.utils.tool_detection import is_langchain_tool  # noqa: PLC0415

        return is_langchain_tool(ref)

    def _instantiate_langchain_tool(self, ref: Any) -> Any:
        """Instantiate LangChain tool if class, return as-is if instance.

        Args:
            ref: LangChain BaseTool class or instance.

        Returns:
            LangChain BaseTool instance.
        """
        if isinstance(ref, type):
            # It's a class, instantiate it
            # Note: @tool_plugin decorator doesn't affect instantiation
            return ref()
        return ref

    def _is_platform_tool(self, ref: Any) -> bool:
        """Check if ref is platform-specific (not supported locally).

        Args:
            ref: Object to check.

        Returns:
            True if ref is a platform-specific tool.
        """
        # String tool names
        if isinstance(ref, str):
            return True

        # Tool.from_native() instances
        if hasattr(ref, "id") and hasattr(ref, "name") and not self._has_explicit_attr(ref, "langchain_tool"):
            tool_class = getattr(ref, "tool_class", None) if self._has_explicit_attr(ref, "tool_class") else None
            if tool_class is None:
                return True

        return False

    def _get_platform_tool_error(self, ref: Any) -> str:
        """Get error message for platform tools.

        Args:
            ref: Platform tool reference.

        Returns:
            Error message string.
        """
        from glaip_sdk.runner.deps import (  # noqa: PLC0415
            get_local_mode_not_supported_for_tool_message,
        )

        tool_name = ref if isinstance(ref, str) else getattr(ref, "name", None)
        if tool_name is None:
            tool_name = getattr(getattr(ref, "tool_class", None), "__name__", _UNKNOWN_TOOL_NAME)
        return get_local_mode_not_supported_for_tool_message(tool_name)
