from _typeshed import Incomplete
from abc import ABC, abstractmethod
from aip_agents.mcp.client.persistent_session import PersistentMCPSession as PersistentMCPSession
from aip_agents.mcp.client.session_pool import MCPSessionPool as MCPSessionPool
from aip_agents.utils.logger import get_logger as get_logger
from gllm_tools.mcp.client.client import MCPClient
from gllm_tools.mcp.client.config import MCPConfiguration as MCPConfiguration
from mcp.types import CallToolResult, Tool as Tool
from typing import Any

logger: Incomplete

class BaseMCPClient(MCPClient, ABC):
    """Base MCP Client with persistent session management for aip-agents.

    This class provides:
    - Persistent session management across tool calls
    - One-time tool registration and caching
    - Automatic connection health monitoring and reconnection
    - Centralized cleanup of all MCP resources
    - Generic tool discovery from all configured MCP servers

    Subclasses should implement SDK-specific tool conversion in _process_tool() method.
    """
    session_pool: Incomplete
    def __init__(self, servers: dict[str, MCPConfiguration]) -> None:
        """Initialize the base MCP client with session pool.

        Args:
            servers (dict[str, MCPConfiguration]): Dictionary of MCP server configurations by server name
        """
    async def initialize(self) -> None:
        """Initialize all MCP sessions and cache tools once.

        This method is idempotent and only performs initialization if not already done.
        It establishes persistent connections to all configured MCP servers and caches
        available tools for efficient access.

        Raises:
            Exception: If any session initialization fails
        """
    @abstractmethod
    async def get_tools(self, server: str | None = None) -> list[Any]:
        """Get framework-specific tools from MCP servers.

        This method must be implemented by subclasses to provide framework-specific
        tool conversion (e.g., StructuredTool for LangChain, FunctionTool for Google ADK).

        Args:
            server (str | None): Optional server name to filter tools from a specific server.
                    If None, returns tools from all configured servers.

        Returns:
            list[Any]: List of framework-specific tool objects.
        """
    async def get_raw_mcp_tools(self, server: str | None = None) -> list[Tool]:
        """Get raw MCP tools - for subclasses to perform framework-specific conversions.

        This method provides access to the cached raw MCP Tool objects.
        Subclasses use this to convert to framework-specific tools.

        Args:
            server (str | None): Optional server name to filter tools from a specific server.
                    If None, returns tools from all configured servers.

        Returns:
            list[Tool]: List of raw MCP Tool objects. Empty list if not initialized or no tools available.
        """
    def get_tools_count(self, server: str | None = None) -> int:
        """Get count of raw MCP tools without expensive copying.

        This is an efficient way to get tool counts for logging/metrics
        without the overhead of copying tool lists.

        Args:
            server (str | None): Optional server name to filter tools from a specific server.
                    If None, returns count from all configured servers.

        Returns:
            int: Count of raw MCP tools available.
        """
    async def get_session(self, server_name: str) -> PersistentMCPSession:
        """Get a persistent session for a specific server.

        Args:
            server_name (str): The name of the MCP server

        Returns:
            PersistentMCPSession: Persistent MCP session for the specified server

        Raises:
            KeyError: If the server is not configured or no active session exists
        """
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Execute a tool on a specific MCP server using persistent session.

        Args:
            server_name (str): The MCP server to execute the tool on
            tool_name (str): The name of the tool to execute
            arguments (dict[str, Any]): Arguments for the tool execution

        Returns:
            CallToolResult: The result of the tool execution

        Raises:
            KeyError: If the server doesn't exist
            Exception: If tool execution fails
        """
    async def read_resource(self, server_name: str, resource_uri: str):
        """Read an MCP resource from a specific server using persistent session.

        Args:
            server_name (str): The MCP server to read the resource from
            resource_uri (str): The URI of the resource to read

        Returns:
            Any: The resource content

        Raises:
            KeyError: If the server doesn't exist
            Exception: If resource reading fails
        """
    async def cleanup(self) -> None:
        """Clean up all MCP resources and close sessions.

        This method properly closes all persistent sessions and cleans up resources.
        It can be called multiple times safely.
        """
    @property
    def is_initialized(self) -> bool:
        """Check if the client is fully initialized.

        Returns:
            bool: True if sessions are initialized and tools are cached, False otherwise
        """
    @property
    def active_sessions(self) -> dict[str, PersistentMCPSession]:
        """Get all active persistent sessions.

        Returns:
            dict[str, PersistentMCPSession]: Dictionary of active sessions by server name
        """
    def get_session_count(self) -> int:
        """Get the number of active MCP sessions.

        Returns:
            Number of active persistent sessions
        """
