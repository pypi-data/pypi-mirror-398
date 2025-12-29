"""Persistent MCP Session wrapper for connection reuse.

This module implements persistent MCP sessions that reuse connections across
multiple tool calls, avoiding the session recreation overhead.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
from typing import Any

from gllm_tools.mcp.client.config import MCPConfiguration
from mcp import ClientSession
from mcp.types import CallToolResult, Tool

from aip_agents.mcp.client.connection_manager import MCPConnectionManager
from aip_agents.mcp.utils.config_validator import validate_allowed_tools_list
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class PersistentMCPSession:
    """Persistent MCP session that reuses connections.

    This session wrapper manages the connection lifecycle and caches tools
    to avoid repeated initialization overhead. It provides automatic reconnection
    and thread-safe operations.

    Tool Filtering:
        When allowed_tools is configured, tools are filtered inline during list_tools()
        and permission checked in call_tool() using set lookup.
    """

    def __init__(
        self,
        server_name: str,
        config: MCPConfiguration,
        allowed_tools: list[str] | None = None,
    ):
        """Initialize persistent session.

        Args:
            server_name: Name of the MCP server
            config: MCP server configuration
            allowed_tools: Optional list of tool names to allow. None or empty means all tools allowed.
        """
        self.server_name = server_name
        self.config = config
        self.connection_manager = MCPConnectionManager(server_name, config)
        self.client_session: ClientSession | None = None
        self.tools: list[Tool] = []

        # Keep only the set for fast permission checks
        validated_allowed = validate_allowed_tools_list(allowed_tools, "'allowed_tools' parameter")
        self._allowed_tools_set: set[str] | None = set(validated_allowed) if validated_allowed else None
        self._warned_unknown_tools: set[str] = set()
        self._filtered_tools_cache: list[Tool] | None = None  # Cache for filtered tools

        # Log allowed tools configuration
        if self._allowed_tools_set:
            logger.info(
                f"Session for '{server_name}' configured with {len(self._allowed_tools_set)} allowed tool(s): "
                f"{', '.join(sorted(self._allowed_tools_set))}"
            )
        else:
            logger.debug(f"Session for '{server_name}' allows all tools (no restriction)")

        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize session once and cache tools.

        This method is idempotent and can be called multiple times safely.

        Raises:
            Exception: If session initialization fails
        """
        if self._initialized:
            return

        async with self._lock:
            # Double-check pattern
            if self._initialized:
                return

            try:
                logger.info(f"Initializing persistent session for {self.server_name}")

                # Start connection manager
                read_stream, write_stream = await self.connection_manager.start()

                # Create client session
                self.client_session = ClientSession(read_stream, write_stream)
                await self.client_session.__aenter__()

                # MCP handshake
                result = await self.client_session.initialize()
                logger.debug(f"MCP handshake complete for {self.server_name}: {result.capabilities}")

                # Discover and cache tools
                if result.capabilities.tools:
                    tools_result = await self.client_session.list_tools()
                    self.tools = tools_result.tools if tools_result else []
                    self._filtered_tools_cache = None  # Invalidate cache when tools change
                    logger.info(f"Cached {len(self.tools)} tools for {self.server_name}")
                else:
                    logger.info(f"No tools available for {self.server_name}")

                # Warn once per initialization if allowed_tools references unknown names
                if self._allowed_tools_set:
                    self._warn_on_unknown_allowed_tools(list(self._allowed_tools_set), self.tools)

                # Discover resources (for future use)
                if result.capabilities.resources:
                    resources_result = await self.client_session.list_resources()
                    if resources_result:
                        logger.debug(f"Found {len(resources_result.resources)} resources for {self.server_name}")

                self._initialized = True
                logger.info(f"Session initialization complete for {self.server_name}")

            except Exception as e:
                logger.error(f"Failed to initialize session for {self.server_name}: {e}", exc_info=True)
                await self._cleanup_on_error()
                raise ConnectionError(f"Failed to initialize MCP session for {self.server_name}: {str(e)}") from e

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Call MCP tool using persistent session.

        Args:
            name (str): Tool name
            arguments (dict[str, Any]): Tool arguments

        Returns:
            CallToolResult: Tool call result

        Raises:
            Exception: If tool call fails
        """
        await self.ensure_connected()

        if self._allowed_tools_set and name not in self._allowed_tools_set:
            allowed_display = ", ".join(sorted(self._allowed_tools_set))
            error_msg = (
                f"Tool '{name}' is not allowed on server '{self.server_name}' (allowed tools: {allowed_display})"
            )
            logger.warning(f"[{self.server_name}] Tool '{name}' blocked: not in allowed_tools ({allowed_display})")
            raise PermissionError(error_msg)

        try:
            logger.debug(f"Calling tool '{name}' on {self.server_name} with args: {arguments}")
            result = await self.client_session.call_tool(name, arguments)
            logger.debug(f"Tool '{name}' completed successfully")
            return result
        except Exception as e:
            self._handle_connection_error(e, f"Tool call '{name}'")

    async def read_resource(self, uri: str) -> Any:
        """Read an MCP resource using persistent session.

        Args:
            uri (str): The URI of the resource to read

        Returns:
            Any: The resource content

        Raises:
            Exception: If resource reading fails
        """
        await self.ensure_connected()
        return await self._execute_read_resource(uri)

    async def _execute_read_resource(self, uri: str) -> Any:
        """Execute the reading of an MCP resource.

        Args:
            uri (str): The URI of the resource to read

        Returns:
            Any: The resource content

        Raises:
            Exception: If resource reading fails
        """
        try:
            logger.debug(f"Reading resource '{uri}' on {self.server_name}")
            result = await self.client_session.read_resource(uri)
            logger.debug(f"Resource '{uri}' read successfully")
            return result
        except Exception as e:
            self._handle_connection_error(e, f"Reading resource '{uri}'")

    async def list_tools(self) -> list[Tool]:
        """Get cached tools list with allowed tools filtering applied.

        Returns:
            list[Tool]: a copy of list of available tools, filtered to only allowed tools if configured
        """
        await self.ensure_connected()

        if not self._allowed_tools_set:
            return list(self.tools)

        if self._filtered_tools_cache is None:
            self._filtered_tools_cache = [tool for tool in self.tools if tool.name in self._allowed_tools_set]

        return list(self._filtered_tools_cache)

    def get_tools_count(self) -> int:
        """Get count of allowed tools.

        Returns:
            Count of allowed tools
        """
        if not self._allowed_tools_set:
            return len(self.tools)

        if self._filtered_tools_cache is not None:
            return len(self._filtered_tools_cache)

        return sum(1 for tool in self.tools if tool.name in self._allowed_tools_set)

    async def ensure_connected(self) -> None:
        """Ensure connection is healthy, reconnect if needed.

        This method provides automatic reconnection capability.

        Raises:
            Exception: If reconnection fails
        """
        if not self._initialized or not self.connection_manager.is_connected:
            logger.info(f"Reconnecting session for {self.server_name}")
            await self.initialize()

    def _handle_connection_error(self, e: Exception, operation: str) -> None:
        """Handle connection-related errors with logging and reconnection marking.

        Args:
            e (Exception): The exception that occurred
            operation (str): The operation that failed
        """
        logger.error(f"{operation} failed on {self.server_name}: {e}")
        if not self.connection_manager.is_connected:
            logger.info(f"Connection lost for {self.server_name}, marking for reconnection")
            self._initialized = False
        raise ConnectionError(f"{operation} failed on {self.server_name}: {str(e)}") from e

    async def disconnect(self) -> None:
        """Disconnect session gracefully.

        This method cleans up all resources and connections.
        """
        logger.info(f"Disconnecting session for {self.server_name}")

        async with self._lock:
            try:
                # Close client session
                if self.client_session:
                    try:
                        await self.client_session.__aexit__(None, None, None)
                    except Exception as e:
                        logger.warning(f"Error closing client session for {self.server_name}: {e}")
                    self.client_session = None

                # Stop connection manager
                await self.connection_manager.stop()

            except Exception as e:
                logger.error(f"Error during disconnect for {self.server_name}: {e}")
            finally:
                self._initialized = False
                self.tools.clear()
                self._filtered_tools_cache = None  # Clear cache on disconnect
                logger.info(f"Session disconnected for {self.server_name}")

    async def _cleanup_on_error(self) -> None:
        """Internal cleanup method for error scenarios."""
        try:
            if self.client_session:
                await self.client_session.__aexit__(None, None, None)
                self.client_session = None
        except Exception as e:
            logger.debug(f"Ignored cleanup error for client_session: {e}")

        try:
            await self.connection_manager.stop()
        except Exception as e:
            logger.debug(f"Ignored cleanup error for connection_manager: {e}")

        self._initialized = False
        self.tools.clear()
        self._filtered_tools_cache = None  # Clear cache on error cleanup

    @property
    def is_initialized(self) -> bool:
        """Check if session is initialized.

        Returns:
            bool: True if initialized and connected, False otherwise
        """
        return self._initialized and self.connection_manager.is_connected

    def update_allowed_tools(self, allowed_tools: list[str] | None) -> bool:
        """Update the list of allowed tools for this session.

        Args:
            allowed_tools: New list of allowed tool names or None for no restriction.
                None and empty list both mean 'no restrictions, allow all tools'.

        Returns:
            bool: True if the configuration changed, False otherwise.

        Raises:
            ValueError: If allowed_tools contains invalid entries.
        """
        # Validate first - ensures consistent error handling regardless of current state
        validated = validate_allowed_tools_list(allowed_tools, f"Server '{self.server_name}'")
        new_set = set(validated) if validated else None

        # Check if actually changed
        if self._allowed_tools_set == new_set:
            logger.debug(f"Allowed tools unchanged for {self.server_name}")
            return False

        # Log and update
        old_display = sorted(self._allowed_tools_set) if self._allowed_tools_set else None
        self._allowed_tools_set = new_set
        self._filtered_tools_cache = None  # Invalidate cache when allowed_tools changes
        logger.debug(f"Updated allowed_tools for {self.server_name}: {old_display} -> {validated}")

        # Warn immediately if we already have cached tools
        if self.tools:
            self._warn_on_unknown_allowed_tools(validated, self.tools)
        return True

    def _warn_on_unknown_allowed_tools(self, allowed_tools: list[str] | None, available_tools: list[Tool]) -> None:
        """Emit warnings for allowed tool names that are not exposed by the server.

        Warnings are deduplicated - each unknown tool is only warned about once per session.

        Args:
            allowed_tools: Configured whitelist of tool names, or None for no restriction.
            available_tools: Tools currently exposed by the server.
        """
        if not allowed_tools or not available_tools:
            return

        available_names = {tool.name for tool in available_tools}
        unknown = [tool_name for tool_name in allowed_tools if tool_name not in available_names]
        for tool_name in unknown:
            # Only warn once per tool name
            if tool_name not in self._warned_unknown_tools:
                self._warned_unknown_tools.add(tool_name)
                logger.warning(
                    f"[{self.server_name}] Tool '{tool_name}' not found in available tools but specified in allowed_tools"
                )
