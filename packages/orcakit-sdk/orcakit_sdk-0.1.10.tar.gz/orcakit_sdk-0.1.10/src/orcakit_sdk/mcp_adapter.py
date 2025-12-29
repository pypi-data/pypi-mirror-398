"""MCP Client setup and management for LangGraph ReAct Agent."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from langchain_mcp_adapters.client import (  # type: ignore[import-untyped]
    MultiServerMCPClient,
)

logger = logging.getLogger(__name__)


@dataclass
class MCPValidationResult:
    """Result of MCP server validation."""

    success: bool
    tools: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    server_details: dict[str, Any] = field(default_factory=dict)


class MCPAdapter:
    """Adapter for managing MCP client, tools and validation."""

    # Supported transport types
    SUPPORTED_TRANSPORTS = ("stdio", "streamable_http", "sse")

    def __init__(self) -> None:
        """Initialize the MCP adapter."""
        # Cache keyed by server_configs JSON string
        self._clients: dict[str, MultiServerMCPClient] = {}
        self._tools_cache: dict[str, list[Callable[..., object]]] = {}

    def _normalize_config(
        self, server_configs: str | dict[str, object]
    ) -> tuple[str, dict[str, object] | None]:
        """Normalize server configs to (cache_key, config_dict).

        Args:
            server_configs: Server configurations as JSON string or dictionary.

        Returns:
            Tuple of (cache_key, config_dict). config_dict is None if parsing fails.
        """
        if isinstance(server_configs, dict):
            # Serialize dict to JSON string for cache key (sorted for consistency)
            cache_key = json.dumps(server_configs, sort_keys=True)
            return cache_key, server_configs
        else:
            try:
                config_dict = json.loads(server_configs)
                # Re-serialize for consistent cache key
                cache_key = json.dumps(config_dict, sort_keys=True)
                return cache_key, config_dict
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON for server_configs: %s", e)
                return server_configs, None

    def _validate_config_format(
        self, mcp_server_configs: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Validate MCP server configuration format.

        Args:
            mcp_server_configs: Dictionary of server name to server config.

        Returns:
            Tuple of (valid_servers, errors).
        """
        errors: list[str] = []
        valid_servers: list[str] = []

        for server_name, config in mcp_server_configs.items():
            if not isinstance(config, dict):
                errors.append(f"Server '{server_name}': config must be a dictionary")
                continue

            transport = config.get("transport", "stdio")

            if transport == "stdio":
                if "command" not in config:
                    errors.append(
                        f"Server '{server_name}': missing 'command' field for stdio transport"
                    )
                    continue
            elif transport in ("streamable_http", "sse"):
                if "url" not in config:
                    errors.append(
                        f"Server '{server_name}': missing 'url' field for {transport} transport"
                    )
                    continue
            else:
                errors.append(
                    f"Server '{server_name}': unsupported transport '{transport}'"
                )
                continue

            valid_servers.append(server_name)

        return valid_servers, errors

    async def validate(self, mcp_server_configs: dict[str, Any]) -> MCPValidationResult:
        """Validate MCP server configurations by connecting and fetching tools.

        Args:
            mcp_server_configs: Dictionary of server name to server config.

        Returns:
            MCPValidationResult with validation status, tools, and details.
        """
        if not mcp_server_configs:
            return MCPValidationResult(
                success=False,
                error="No MCP server configurations provided",
            )

        # First validate config format
        valid_servers, errors = self._validate_config_format(mcp_server_configs)

        if errors:
            return MCPValidationResult(
                success=False,
                error="; ".join(errors),
                server_details={
                    "server_count": len(mcp_server_configs),
                    "valid_servers": valid_servers,
                    "invalid_count": len(errors),
                },
            )

        # Actually connect to MCP servers and fetch tools
        try:
            client = MultiServerMCPClient(mcp_server_configs)
            all_tools = await client.get_tools()
            tools_list = list(all_tools)

            tool_info = [
                {
                    "name": getattr(tool, "name", "Unknown"),
                    "description": getattr(tool, "description", "No description"),
                }
                for tool in tools_list
            ]

            logger.info(
                f"MCP validation successful: {len(tools_list)} tools from {len(valid_servers)} servers"
            )

            return MCPValidationResult(
                success=True,
                tools=tool_info,
                server_details={
                    "server_count": len(mcp_server_configs),
                    "tool_count": len(tools_list),
                    "servers": valid_servers,
                },
            )
        except Exception as e:
            logger.error(f"MCP server connection failed: {e}")
            return MCPValidationResult(
                success=False,
                error=f"Failed to connect to MCP servers: {e}",
                server_details={
                    "server_count": len(mcp_server_configs),
                    "servers": valid_servers,
                },
            )

    async def get_client(
        self,
        server_configs: str | dict[str, object],
    ) -> MultiServerMCPClient | None:
        """Get or initialize the MCP client with given server configurations.

        Args:
            server_configs: Server configurations as JSON string or dictionary.

        Returns:
            MultiServerMCPClient instance or None if initialization fails.
        """
        cache_key, config = self._normalize_config(server_configs)
        if config is None:
            return None

        # Return cached client if available
        if cache_key in self._clients:
            return self._clients[cache_key]

        # Validate config format only (skip full validation to avoid double connection)
        __, errors = self._validate_config_format(config)
        if errors:
            logger.error("MCP config validation failed: %s", "; ".join(errors))
            return None

        try:
            client = MultiServerMCPClient(config)
            self._clients[cache_key] = client
            return client
        except Exception as e:
            logger.error("Failed to initialize MCP client: %s", e)
            return None

    async def get_tools(
        self,
        server_configs: str | dict[str, object],
    ) -> list[Callable[..., object]]:
        """Get MCP tools for a specific server, initializing client if needed.

        Args:
            server_configs: Server configurations as JSON string or dictionary.

        Returns:
            List of callable tools from the MCP server.
        """
        cache_key, config = self._normalize_config(server_configs)
        if config is None:
            return []

        # Return cached tools if available for this config
        if cache_key in self._tools_cache:
            return self._tools_cache[cache_key]

        try:
            client = await self.get_client(server_configs)
            if client is None:
                return []

            # Get all tools from client
            all_tools = await client.get_tools()
            tools: list[Callable[..., object]] = list(all_tools)

            self._tools_cache[cache_key] = tools
            logger.info(f"Loaded {len(tools)} tools from MCP server.")
            for idx, tool in enumerate(tools):
                logger.info(
                    f"Tool {idx + 1}: {getattr(tool, 'name', 'Unknown')}, "
                    f"{getattr(tool, 'description', 'No description')}"
                )
            return tools
        except Exception as e:
            logger.warning("Failed to load tools from MCP server: %s", e)
            return []

    def clear_cache(
        self, server_configs: str | dict[str, object] | None = None
    ) -> None:
        """Clear the MCP client and tools cache.

        Args:
            server_configs: Optional server configurations as JSON string or dictionary.
                If provided, only clear cache for this config.
                If None, clear all caches.
        """
        if server_configs is None:
            self._clients.clear()
            self._tools_cache.clear()
        else:
            cache_key, __ = self._normalize_config(server_configs)
            self._clients.pop(cache_key, None)
            self._tools_cache.pop(cache_key, None)


# Global instance for backward compatibility
_default_adapter: MCPAdapter | None = None


def _get_default_adapter() -> MCPAdapter:
    """Get the default MCPAdapter instance."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = MCPAdapter()
    return _default_adapter


async def get_mcp_client(
    server_configs: str | dict[str, object],
) -> MultiServerMCPClient | None:
    """Get or initialize the global MCP client with given server configurations.

    Args:
        server_configs: Server configurations as JSON string or dictionary.

    Returns:
        MultiServerMCPClient instance or None if initialization fails.
    """
    return await _get_default_adapter().get_client(server_configs)


async def get_mcp_tools(
    server_configs: str | dict[str, object],
) -> list[Callable[..., object]]:
    """Get MCP tools for a specific server, initializing client if needed.

    Args:
        server_configs: Server configurations as JSON string or dictionary.

    Returns:
        List of callable tools from the MCP server.
    """
    return await _get_default_adapter().get_tools(server_configs)


def clear_mcp_cache(server_configs: str | dict[str, object] | None = None) -> None:
    """Clear the MCP client and tools cache.

    Args:
        server_configs: Optional server configurations as JSON string or dictionary.
            If provided, only clear cache for this config.
            If None, clear all caches.
    """
    _get_default_adapter().clear_cache(server_configs)


async def validate_mcp_servers(
    server_configs: str | dict[str, object],
) -> MCPValidationResult:
    """Validate MCP server configurations by connecting and fetching tools.

    Args:
        server_configs: Server configurations as JSON string or dictionary.

    Returns:
        MCPValidationResult with validation status, tools, and details.
    """
    cache_key, config = _get_default_adapter()._normalize_config(server_configs)
    if config is None:
        return MCPValidationResult(
            success=False,
            error=f"Invalid JSON: {server_configs}",
        )
    return await _get_default_adapter().validate(config)
