from _typeshed import Incomplete
from aip_agents.mcp.client.connection_manager import MCPConnectionManager as MCPConnectionManager
from aip_agents.mcp.utils.config_validator import validate_allowed_tools_list as validate_allowed_tools_list
from aip_agents.utils.logger import get_logger as get_logger
from gllm_tools.mcp.client.config import MCPConfiguration
from mcp import ClientSession
from mcp.types import CallToolResult, Tool as Tool
from typing import Any

logger: Incomplete

class PersistentMCPSession:
    """Persistent MCP session that reuses connections.

    This session wrapper manages the connection lifecycle and caches tools
    to avoid repeated initialization overhead. It provides automatic reconnection
    and thread-safe operations.

    Tool Filtering:
        When allowed_tools is configured, tools are filtered inline during list_tools()
        and permission checked in call_tool() using set lookup.
    """
    server_name: Incomplete
    config: Incomplete
    connection_manager: Incomplete
    client_session: ClientSession | None
    tools: list[Tool]
    def __init__(self, server_name: str, config: MCPConfiguration, allowed_tools: list[str] | None = None) -> None:
        """Initialize persistent session.

        Args:
            server_name: Name of the MCP server
            config: MCP server configuration
            allowed_tools: Optional list of tool names to allow. None or empty means all tools allowed.
        """
    async def initialize(self) -> None:
        """Initialize session once and cache tools.

        This method is idempotent and can be called multiple times safely.

        Raises:
            Exception: If session initialization fails
        """
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
    async def read_resource(self, uri: str) -> Any:
        """Read an MCP resource using persistent session.

        Args:
            uri (str): The URI of the resource to read

        Returns:
            Any: The resource content

        Raises:
            Exception: If resource reading fails
        """
    async def list_tools(self) -> list[Tool]:
        """Get cached tools list with allowed tools filtering applied.

        Returns:
            list[Tool]: a copy of list of available tools, filtered to only allowed tools if configured
        """
    def get_tools_count(self) -> int:
        """Get count of allowed tools.

        Returns:
            Count of allowed tools
        """
    async def ensure_connected(self) -> None:
        """Ensure connection is healthy, reconnect if needed.

        This method provides automatic reconnection capability.

        Raises:
            Exception: If reconnection fails
        """
    async def disconnect(self) -> None:
        """Disconnect session gracefully.

        This method cleans up all resources and connections.
        """
    @property
    def is_initialized(self) -> bool:
        """Check if session is initialized.

        Returns:
            bool: True if initialized and connected, False otherwise
        """
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
