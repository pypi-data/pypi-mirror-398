#!/usr/bin/env python3
"""MCP client for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import logging
from typing import Any

from glaip_sdk.client.base import BaseClient
from glaip_sdk.config.constants import DEFAULT_MCP_TRANSPORT, DEFAULT_MCP_TYPE
from glaip_sdk.mcps import MCP
from glaip_sdk.models import MCPResponse
from glaip_sdk.utils.client_utils import (
    add_kwargs_to_payload,
    create_model_instances,
    find_by_name,
)
from glaip_sdk.utils.resource_refs import is_uuid

# API endpoints
MCPS_ENDPOINT = "/mcps/"
MCPS_CONNECT_ENDPOINT = "/mcps/connect"
MCPS_CONNECT_TOOLS_ENDPOINT = "/mcps/connect/tools"

# Set up module-level logger
logger = logging.getLogger("glaip_sdk.mcps")


class MCPClient(BaseClient):
    """Client for MCP operations."""

    def __init__(self, *, parent_client: BaseClient | None = None, **kwargs):
        """Initialize the MCP client.

        Args:
            parent_client: Parent client to adopt session/config from
            **kwargs: Additional arguments for standalone initialization
        """
        super().__init__(parent_client=parent_client, **kwargs)

    def list_mcps(self) -> list[MCP]:
        """List all MCPs."""
        data = self._request("GET", MCPS_ENDPOINT)
        return create_model_instances(data, MCP, self)

    def get_mcp_by_id(self, mcp_id: str) -> MCP:
        """Get MCP by ID."""
        data = self._request("GET", f"{MCPS_ENDPOINT}{mcp_id}")
        response = MCPResponse(**data)
        return MCP.from_response(response, client=self)

    def find_mcps(self, name: str | None = None) -> list[MCP]:
        """Find MCPs by name."""
        # Backend doesn't support name query parameter, so we fetch all and filter client-side
        data = self._request("GET", MCPS_ENDPOINT)
        mcps = create_model_instances(data, MCP, self)
        return find_by_name(mcps, name, case_sensitive=False)

    def create_mcp(
        self,
        name: str,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> MCP:
        """Create a new MCP."""
        # Use the helper method to build a properly structured payload
        payload = self._build_create_payload(
            name=name,
            description=description,
            config=config,
            **kwargs,
        )

        # Create the MCP and fetch full details
        full_mcp_data = self._post_then_fetch(
            id_key="id",
            post_endpoint=MCPS_ENDPOINT,
            get_endpoint_fmt=f"{MCPS_ENDPOINT}{{id}}",
            json=payload,
        )
        response = MCPResponse(**full_mcp_data)
        return MCP.from_response(response, client=self)

    def update_mcp(self, mcp_id: str, **kwargs) -> MCP:
        """Update an existing MCP.

        Automatically chooses between PUT (full update) and PATCH (partial update)
        based on the provided fields:
        - Uses PUT if name, config, and transport are all provided (full update)
        - Uses PATCH otherwise (partial update)
        """
        # Check if all required fields for full update are provided
        required_fields = {"name", "config", "transport"}
        provided_fields = set(kwargs.keys())

        if required_fields.issubset(provided_fields):
            # All required fields provided - use full update (PUT)
            method = "PUT"
        else:
            # Partial update - use PATCH
            method = "PATCH"

        data = self._request(method, f"{MCPS_ENDPOINT}{mcp_id}", json=kwargs)
        response = MCPResponse(**data)
        return MCP.from_response(response, client=self)

    def delete_mcp(self, mcp_id: str) -> None:
        """Delete an MCP."""
        self._request("DELETE", f"{MCPS_ENDPOINT}{mcp_id}")

    def upsert_mcp(
        self,
        identifier: str | MCP,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> MCP:
        """Create or update an MCP by instance, ID, or name.

        Args:
            identifier: MCP instance, ID (UUID string), or name
            description: MCP description
            config: MCP configuration dictionary
            **kwargs: Additional parameters (transport, metadata, etc.)

        Returns:
            The created or updated MCP.

        Example:
            >>> # By name (creates if not exists)
            >>> mcp = client.mcps.upsert_mcp(
            ...     "deepwiki",
            ...     transport="sse",
            ...     config={"url": "https://mcp.deepwiki.com/sse"},
            ... )
            >>> # By instance
            >>> mcp = client.mcps.upsert_mcp(existing_mcp, description="Updated")
            >>> # By ID
            >>> mcp = client.mcps.upsert_mcp("uuid-here", description="Updated")
        """
        # Handle MCP instance
        if isinstance(identifier, MCP):
            if identifier.id:
                logger.info("Updating MCP by instance: %s", identifier.name)
                return self._do_upsert_update(identifier.id, identifier.name, description, config, **kwargs)
            # MCP without ID - treat name as identifier
            identifier = identifier.name

        # Handle string (ID or name)
        if isinstance(identifier, str):
            if is_uuid(identifier):
                logger.info("Updating MCP by ID: %s", identifier)
                existing = self.get_mcp_by_id(identifier)
                return self._do_upsert_update(identifier, existing.name, description, config, **kwargs)

            # It's a name - find or create
            return self._upsert_by_name(identifier, description, config, **kwargs)

        raise ValueError(f"Invalid identifier type: {type(identifier)}")

    def _do_upsert_update(
        self,
        mcp_id: str,
        name: str | None,
        description: str | None,
        config: dict[str, Any] | None,
        **kwargs,
    ) -> MCP:
        """Perform the update part of upsert."""
        update_kwargs = {**kwargs}
        if name is not None:
            update_kwargs["name"] = name
        if description is not None:
            update_kwargs["description"] = description
        if config is not None:
            update_kwargs["config"] = config
        return self.update_mcp(mcp_id, **update_kwargs)

    def _upsert_by_name(
        self,
        name: str,
        description: str | None,
        config: dict[str, Any] | None,
        **kwargs,
    ) -> MCP:
        """Find by name and update, or create if not found."""
        existing = self.find_mcps(name)

        if len(existing) == 1:
            logger.info("Updating existing MCP: %s", name)
            return self._do_upsert_update(existing[0].id, name, description, config, **kwargs)

        if len(existing) > 1:
            raise ValueError(f"Multiple MCPs found with name '{name}'")

        # Create new MCP
        logger.info("Creating new MCP: %s", name)
        return self.create_mcp(name=name, description=description, config=config, **kwargs)

    def _build_create_payload(
        self,
        name: str,
        description: str | None = None,
        transport: str = DEFAULT_MCP_TRANSPORT,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Build payload for MCP creation with proper metadata handling.

        CENTRALIZED PAYLOAD BUILDING LOGIC:
        - Sets proper defaults and required fields
        - Handles config serialization consistently
        - Processes transport and other metadata properly

        Args:
            name: MCP name
            description: MCP description (optional)
            transport: MCP transport protocol (defaults to stdio)
            config: MCP configuration dictionary
            **kwargs: Additional parameters

        Returns:
            Complete payload dictionary for MCP creation
        """
        # Prepare the creation payload with required fields
        payload: dict[str, Any] = {
            "name": name.strip(),
            "type": DEFAULT_MCP_TYPE,  # MCPs are always server type
            "transport": transport,
        }

        # Add description if provided
        if description:
            payload["description"] = description.strip()

        # Handle config - ensure it's properly serialized
        if config:
            payload["config"] = config

        # Add any other kwargs (excluding already handled ones)
        excluded_keys = {"type"}  # type is handled above
        add_kwargs_to_payload(payload, kwargs, excluded_keys)

        return payload

    def _build_update_payload(
        self,
        current_mcp: MCP,
        name: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Build payload for MCP update with proper current state preservation.

        Args:
            current_mcp: Current MCP object to update
            name: New MCP name (None to keep current)
            description: New description (None to keep current)
            **kwargs: Additional parameters (config, transport, etc.)

        Returns:
            Complete payload dictionary for MCP update

        Notes:
            - Preserves current values as defaults when new values not provided
            - Handles config updates properly
        """
        # Prepare the update payload with current values as defaults
        update_data = {
            "name": name if name is not None else current_mcp.name,
            "type": DEFAULT_MCP_TYPE,  # Required by backend, MCPs are always server type
            "transport": kwargs.get("transport", getattr(current_mcp, "transport", DEFAULT_MCP_TRANSPORT)),
        }

        # Handle description with proper None handling
        if description is not None:
            update_data["description"] = description.strip()
        elif hasattr(current_mcp, "description") and current_mcp.description:
            update_data["description"] = current_mcp.description

        # Handle config with proper merging
        if "config" in kwargs:
            update_data["config"] = kwargs["config"]
        elif hasattr(current_mcp, "config") and current_mcp.config:
            # Preserve existing config if present
            update_data["config"] = current_mcp.config

        # Add any other kwargs (excluding already handled ones)
        excluded_keys = {"transport", "config"}
        for key, value in kwargs.items():
            if key not in excluded_keys:
                update_data[key] = value

        return update_data

    def get_mcp_tools(self, mcp_id: str) -> list[dict[str, Any]]:
        """Get tools available from an MCP."""
        data = self._request("GET", f"{MCPS_ENDPOINT}{mcp_id}/tools")
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "tools" in data:
                return data.get("tools", []) or []
            logger.warning(
                "Unexpected MCP tools response keys %s; returning empty list",
                list(data.keys()),
            )
            return []
        logger.warning(
            "Unexpected MCP tools response type %s; returning empty list",
            type(data).__name__,
        )
        return []

    def test_mcp_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """Test MCP connection using configuration.

        Args:
            config: MCP configuration dictionary

        Returns:
            dict: Connection test result

        Raises:
            Exception: If connection test fails
        """
        try:
            response = self._request("POST", MCPS_CONNECT_ENDPOINT, json=config)
            return response
        except Exception as e:
            logger.error(f"Failed to test MCP connection: {e}")
            raise

    def test_mcp_connection_from_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Test MCP connection using configuration (alias for test_mcp_connection).

        Args:
            config: MCP configuration dictionary

        Returns:
            dict: Connection test result
        """
        return self.test_mcp_connection(config)

    def get_mcp_tools_from_config(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch tools from MCP configuration without saving.

        Args:
            config: MCP configuration dictionary

        Returns:
            list: List of available tools from the MCP

        Raises:
            Exception: If tool fetching fails
        """
        try:
            response = self._request("POST", MCPS_CONNECT_TOOLS_ENDPOINT, json=config)
            if response is None:
                return []
            return response.get("tools", []) or []
        except Exception as e:
            logger.error(f"Failed to get MCP tools from config: {e}")
            raise
