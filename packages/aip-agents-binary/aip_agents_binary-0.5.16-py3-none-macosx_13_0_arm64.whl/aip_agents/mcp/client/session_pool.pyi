from _typeshed import Incomplete
from aip_agents.mcp.client.persistent_session import PersistentMCPSession as PersistentMCPSession
from aip_agents.mcp.utils.config_validator import validate_allowed_tools_config as validate_allowed_tools_config, validate_allowed_tools_list as validate_allowed_tools_list
from aip_agents.utils.logger import get_logger as get_logger
from gllm_tools.mcp.client.config import MCPConfiguration
from mcp.types import Tool as Tool

logger: Incomplete

class MCPSessionPool:
    """Manages pool of persistent MCP sessions.

    This pool provides centralized management of MCP sessions, including
    initialization, tool collection, and resource cleanup. Sessions are
    reused across the agent lifecycle.
    """
    sessions: dict[str, PersistentMCPSession]
    def __init__(self) -> None:
        """Initialize empty session pool."""
    async def get_or_create_session(self, server_name: str, config: MCPConfiguration, allowed_tools: list[str] | None = None) -> PersistentMCPSession:
        """Get existing session or create new one.

        Args:
            server_name (str): Name of the MCP server
            config (MCPConfiguration): MCP server configuration
            allowed_tools (list[str] | None): Optional list of tool names to allow. None means all tools allowed.

        Returns:
            PersistentMCPSession: Persistent MCP session

        Raises:
            Exception: If session creation fails
        """
    async def initialize_all_sessions(self, server_configs: dict[str, MCPConfiguration]) -> None:
        """Initialize all sessions and cache tools.

        This method initializes all configured MCP servers concurrently
        for better performance.

        Args:
            server_configs (dict[str, MCPConfiguration]): Dictionary of server configurations

        Raises:
            Exception: If any session initialization fails
        """
    def get_all_active_sessions(self) -> dict[str, PersistentMCPSession]:
        """Get all active sessions.

        Returns:
            dict[str, PersistentMCPSession]: Dictionary of active sessions by server name
        """
    @property
    def active_sessions(self) -> list[str]:
        """Get list of active session names.

        Returns:
            list[str]: List of active session names
        """
    async def get_all_tools(self) -> list[Tool]:
        """Get all cached tools from all active sessions.

        Returns:
            list[Tool]: List of all available tools across all sessions
        """
    async def close_session(self, server_name: str) -> None:
        """Close specific session.

        Args:
            server_name (str): Name of the server session to close
        """
    async def close_all_sessions(self) -> None:
        """Close all sessions gracefully.

        This method ensures all resources are cleaned up properly.
        """
    @property
    def is_initialized(self) -> bool:
        """Check if session pool is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
    @property
    def session_count(self) -> int:
        """Get number of active sessions.

        Returns:
            int: Number of active sessions
        """
    def get_session(self, server_name: str) -> PersistentMCPSession:
        """Get specific session by name.

        Args:
            server_name (str): Name of the server

        Returns:
            PersistentMCPSession: The requested session

        Raises:
            KeyError: If session doesn't exist
        """
