"""Base MCP Client for aip-agents with Session Persistence.

This base class provides persistent session management for MCP connections and serves
as the foundation for SDK-specific MCP clients (LangChain, Google ADK, etc.). It handles
session pooling, initialization, tool discovery, and cleanup while leaving SDK-specific
tool conversion to subclasses.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from gllm_tools.mcp.client.client import MCPClient
from gllm_tools.mcp.client.config import MCPConfiguration
from gllm_tools.mcp.client.resource import MCPResource
from mcp.types import CallToolResult, Tool

from aip_agents.mcp.client.persistent_session import PersistentMCPSession
from aip_agents.mcp.client.session_pool import MCPSessionPool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


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

    def __init__(self, servers: dict[str, MCPConfiguration]):
        """Initialize the base MCP client with session pool.

        Args:
            servers (dict[str, MCPConfiguration]): Dictionary of MCP server configurations by server name
        """
        super().__init__(servers)
        self.session_pool = MCPSessionPool()
        self._tools_cache: list[Tool] = []
        self._initialized = False
        # Guard against concurrent initialization
        self._init_lock: asyncio.Lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize all MCP sessions and cache tools once.

        This method is idempotent and only performs initialization if not already done.
        It establishes persistent connections to all configured MCP servers and caches
        available tools for efficient access.

        Raises:
            Exception: If any session initialization fails
        """
        if self._initialized:
            logger.debug("BaseMCPClient already initialized, skipping")
            return

        # Ensure only one concurrent initializer proceeds
        async with self._init_lock:
            if self._initialized:
                logger.debug("BaseMCPClient already initialized (post-lock), skipping")
                return

            logger.info(f"Initializing BaseMCPClient with {len(self.servers)} MCP servers")

            try:
                # Initialize all persistent sessions concurrently
                await self.session_pool.initialize_all_sessions(self.servers)

                # Cache all available tools from all sessions
                self._tools_cache = await self.session_pool.get_all_tools()

                self._initialized = True
                logger.info(
                    f"BaseMCPClient initialization complete: "
                    f"{len(self._tools_cache)} tools cached from {self.session_pool.session_count} sessions"
                )
            except Exception as e:
                logger.error(f"Failed to initialize BaseMCPClient: {e}", exc_info=True)
                # Cleanup any partially initialized sessions on failure
                await self.cleanup()
                raise

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
        pass  # pragma: no cover  # Abstract method - cannot be executed directly

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
        if not self._initialized:
            await self.initialize()

        if server:
            if server not in self.servers:
                logger.warning(f"Server '{server}' not found in configuration")
                return []

            try:
                session = self.session_pool.get_session(server)
                return await session.list_tools()
            except KeyError:
                logger.warning(f"No active session found for server '{server}'")
                return []
            except Exception as e:
                logger.error(f"Failed to get tools from server '{server}': {e}")
                return []
        else:
            return self._tools_cache.copy()

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
        if not self._initialized:
            return 0

        if server:
            if server not in self.servers:
                return 0
            try:
                session = self.session_pool.get_session(server)
                return session.get_tools_count()
            except KeyError:
                return 0
            except Exception as e:
                logger.error(f"Failed to get tools count from server '{server}': {e}")
                return 0
        else:
            return len(self._tools_cache)

    async def get_session(self, server_name: str) -> PersistentMCPSession:
        """Get a persistent session for a specific server.

        Args:
            server_name (str): The name of the MCP server

        Returns:
            PersistentMCPSession: Persistent MCP session for the specified server

        Raises:
            KeyError: If the server is not configured or no active session exists
        """
        if not self._initialized:
            await self.initialize()

        try:
            return self.session_pool.get_session(server_name)
        except KeyError:
            logger.error(f"Server '{server_name}' not found in configuration")
            raise
        except Exception as e:
            logger.error(f"Failed to get session for server '{server_name}': {e}")
            raise

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
        if not self._initialized:
            await self.initialize()

        try:
            session = self.session_pool.get_session(server_name)
            return await session.call_tool(tool_name, arguments)
        except KeyError:
            logger.error(f"Server '{server_name}' not found in configuration")
            raise
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}' on server '{server_name}': {e}")
            raise

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
        if not self._initialized:
            await self.initialize()

        try:
            session = self.session_pool.get_session(server_name)
            return await session.read_resource(resource_uri)
        except KeyError:
            logger.error(f"Server '{server_name}' not found in configuration")
            raise
        except Exception as e:
            logger.error(f"Failed to read resource '{resource_uri}' from server '{server_name}': {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up all MCP resources and close sessions.

        This method properly closes all persistent sessions and cleans up resources.
        It can be called multiple times safely.
        """
        if self._initialized:
            logger.info("Cleaning up BaseMCPClient resources")
            cleanup_error = None
            try:
                await self.session_pool.close_all_sessions()
            except TimeoutError as e:
                cleanup_error = e
                logger.warning(f"Timeout during BaseMCPClient cleanup: {e}")
            except Exception as e:
                cleanup_error = e
                logger.error(f"Unexpected error during BaseMCPClient cleanup: {e}", exc_info=True)
                # Don't re-raise - cleanup should be best-effort
            finally:
                # Always clear cache and mark as not initialized, even if session cleanup failed
                self._tools_cache.clear()
                self._initialized = False
                if cleanup_error:
                    logger.info("BaseMCPClient cleanup completed (session cleanup had errors)")
                else:
                    logger.info("BaseMCPClient cleanup completed successfully")
        else:
            logger.debug("BaseMCPClient cleanup called but not initialized, skipping")

    @property
    def is_initialized(self) -> bool:
        """Check if the client is fully initialized.

        Returns:
            bool: True if sessions are initialized and tools are cached, False otherwise
        """
        return self._initialized

    @property
    def active_sessions(self) -> dict[str, PersistentMCPSession]:
        """Get all active persistent sessions.

        Returns:
            dict[str, PersistentMCPSession]: Dictionary of active sessions by server name
        """
        if not self._initialized:
            return {}
        return self.session_pool.get_all_active_sessions()

    def get_session_count(self) -> int:
        """Get the number of active MCP sessions.

        Returns:
            Number of active persistent sessions
        """
        return self.session_pool.session_count

    def _get_annotated_server(self, resource: MCPResource) -> str | None:
        """Extract server name from resource annotations if valid.

        Args:
            resource (MCPResource): The MCP resource.

        Returns:
            str | None: Annotated server name if valid and configured, else None.
        """
        if not self.servers:
            return None

        annotations = getattr(resource, "annotations", None)
        if annotations and hasattr(annotations, "server") and annotations.server:
            annotated = annotations.server
            if annotated in self.servers:
                return annotated
            logger.warning(f"Resource annotation requested server '{annotated}' which is not configured; falling back")
        return None

    def _get_default_server(self) -> str:
        """Get the default server name (first configured server).

        Returns:
            str: First server name.

        Raises:
            ValueError: If no servers configured.
        """
        if not self.servers:
            raise ValueError("No MCP servers configured; cannot resolve server for resource")

        server_list = list(self.servers.keys())
        if len(server_list) > 1:
            logger.warning(
                "Multiple MCP servers configured but resource provided no annotation; "
                f"defaulting to first server '{server_list[0]}'"
            )
        return server_list[0]

    def _determine_server_name_for_resource(self, resource: MCPResource) -> str:
        """Determine the server name for an MCP resource.

        Args:
            resource (MCPResource): The MCP resource to determine server for.

        Returns:
            str: Server name string.

        Raises:
            ValueError: If cannot determine server.
        """
        try:
            annotated = self._get_annotated_server(resource)
            if annotated:
                return annotated
            return self._get_default_server()
        except Exception as e:
            error_msg = f"Failed to determine server for resource {resource.uri}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
