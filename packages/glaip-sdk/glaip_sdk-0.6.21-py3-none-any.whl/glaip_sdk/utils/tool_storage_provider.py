"""Helpers for local tool output storage setup.

This module bridges agent_config.tool_output_sharing to ToolOutputManager
for local execution without modifying aip-agents.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from __future__ import annotations

import os
from typing import Any

from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)


def build_tool_output_manager(agent_name: str, agent_config: dict[str, Any]) -> Any | None:
    """Build a ToolOutputManager for local tool output sharing.

    Args:
        agent_name: Name of the agent whose tool outputs will be stored.
        agent_config: Agent configuration that may enable tool output sharing and contain task_id.

    Returns:
        A ToolOutputManager instance when tool output sharing is enabled and
        dependencies are available, otherwise ``None``.
    """
    tool_output_sharing_enabled = agent_config.get("tool_output_sharing", False)
    if not tool_output_sharing_enabled:
        return None

    try:
        from aip_agents.storage.clients.minio_client import MinioConfig, MinioObjectStorage  # noqa: PLC0415
        from aip_agents.storage.providers.memory import InMemoryStorageProvider  # noqa: PLC0415
        from aip_agents.storage.providers.object_storage import ObjectStorageProvider  # noqa: PLC0415
        from aip_agents.utils.langgraph.tool_output_management import (  # noqa: PLC0415
            ToolOutputConfig,
            ToolOutputManager,
        )
    except ImportError:
        logger.warning("Tool output sharing requested but aip-agents is unavailable; skipping.")
        return None

    task_id = agent_config.get("task_id")

    storage_provider = _build_tool_output_storage_provider(
        agent_name=agent_name,
        task_id=task_id,
        minio_config_cls=MinioConfig,
        minio_client_cls=MinioObjectStorage,
        object_storage_provider_cls=ObjectStorageProvider,
        memory_storage_provider_cls=InMemoryStorageProvider,
    )
    tool_output_config = _build_tool_output_config(storage_provider, ToolOutputConfig)
    return ToolOutputManager(tool_output_config)


def _build_tool_output_storage_provider(
    agent_name: str,
    task_id: str | None,
    minio_config_cls: Any,
    minio_client_cls: Any,
    object_storage_provider_cls: Any,
    memory_storage_provider_cls: Any,
) -> Any:
    """Create a storage provider for tool output sharing.

    Args:
        agent_name: Name of the agent whose tool outputs are stored.
        task_id: Optional task identifier for coordination context.
        minio_config_cls: Class exposing a ``from_env`` constructor for MinIO config.
        minio_client_cls: MinIO client class used to talk to the object store.
        object_storage_provider_cls: Storage provider wrapping the MinIO client.
        memory_storage_provider_cls: In-memory provider used as a fallback.

    Returns:
        An instance of ``object_storage_provider_cls`` when MinIO initialization
        succeeds, otherwise an instance of ``memory_storage_provider_cls``.
    """
    try:
        config_obj = minio_config_cls.from_env()
        minio_client = minio_client_cls(config=config_obj)
        prefix = _build_tool_output_prefix(agent_name, task_id)
        return object_storage_provider_cls(client=minio_client, prefix=prefix, use_json=False)
    except Exception as exc:
        logger.warning("Failed to initialize MinIO for tool outputs: %s. Using in-memory storage.", exc)
        return memory_storage_provider_cls()


def _build_tool_output_prefix(agent_name: str, task_id: str | None) -> str:
    """Build object storage prefix for tool outputs in local mode.

    Args:
        agent_name: Name of the agent whose outputs are stored.
        task_id: Optional task identifier for coordination context.

    Returns:
        Object storage key prefix dedicated to the provided agent.
    """
    if task_id:
        return f"tool-outputs/tasks/{task_id}/agents/{agent_name}/"
    return f"tool-outputs/agents/{agent_name}/"


def _build_tool_output_config(storage_provider: Any, config_cls: Any) -> Any:
    """Build ToolOutputConfig using env vars, with safe defaults.

    Args:
        storage_provider: Provider that will persist tool outputs.
        config_cls: Tool output configuration class to instantiate.

    Returns:
        A configured ``config_cls`` instance ready for ToolOutputManager use.
    """

    def safe_int_conversion(env_var: str, default: str) -> int:
        """Convert an environment variable to int with a fallback default.

        Args:
            env_var: Environment variable name to read.
            default: Default string value used when parsing fails.

        Returns:
            Integer representation of the environment variable or the default.
        """
        try:
            return int(os.getenv(env_var, default))
        except (ValueError, TypeError):
            logger.warning("Invalid value for %s, using default: %s", env_var, default)
            return int(default)

    return config_cls(
        max_stored_outputs=safe_int_conversion("TOOL_OUTPUT_MAX_STORED", "200"),
        max_age_minutes=safe_int_conversion("TOOL_OUTPUT_MAX_AGE_MINUTES", str(24 * 60)),
        cleanup_interval=safe_int_conversion("TOOL_OUTPUT_CLEANUP_INTERVAL", "50"),
        storage_provider=storage_provider,
    )
