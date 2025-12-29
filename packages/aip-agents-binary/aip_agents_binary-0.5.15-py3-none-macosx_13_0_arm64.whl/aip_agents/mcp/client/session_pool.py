"""MCP Session Pool for centralized session management.

This module manages a pool of persistent MCP sessions, providing centralized
initialization, tool collection, and cleanup.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from gllm_tools.mcp.client.config import MCPConfiguration
from mcp.types import Tool

from aip_agents.mcp.client.persistent_session import PersistentMCPSession
from aip_agents.mcp.utils.config_validator import validate_allowed_tools_config, validate_allowed_tools_list
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class MCPSessionPool:
    """Manages pool of persistent MCP sessions.

    This pool provides centralized management of MCP sessions, including
    initialization, tool collection, and resource cleanup. Sessions are
    reused across the agent lifecycle.
    """

    def __init__(self):
        """Initialize empty session pool."""
        self.sessions: dict[str, PersistentMCPSession] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def get_or_create_session(
        self,
        server_name: str,
        config: MCPConfiguration,
        allowed_tools: list[str] | None = None,
    ) -> PersistentMCPSession:
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
        async with self._lock:
            if server_name in self.sessions:
                return self._update_existing_session(server_name, allowed_tools)

            return await self._create_and_initialize_session(server_name, config, allowed_tools)

    def _update_existing_session(
        self,
        server_name: str,
        allowed_tools: list[str] | None,
    ) -> PersistentMCPSession:
        """Update existing session's allowed_tools if changed.

        Args:
            server_name (str): Name of the MCP server
            allowed_tools (list[str] | None): Optional list of tool names to allow

        Returns:
            PersistentMCPSession: Updated existing session
        """
        existing_session = self.sessions[server_name]
        if existing_session.update_allowed_tools(allowed_tools):
            logger.debug(f"Reconfigured allowed_tools for {server_name}")
        else:
            logger.debug(f"Reusing existing session for {server_name} (allowed_tools unchanged)")
        return existing_session

    async def _create_and_initialize_session(
        self,
        server_name: str,
        config: MCPConfiguration,
        allowed_tools: list[str] | None,
    ) -> PersistentMCPSession:
        """Create and initialize a new session.

        Args:
            server_name (str): Name of the MCP server
            config (MCPConfiguration): MCP server configuration
            allowed_tools (list[str] | None): Optional list of tool names to allow

        Returns:
            PersistentMCPSession: Newly created and initialized session

        Raises:
            Exception: If session creation or initialization fails
        """
        logger.info(f"Creating new session for {server_name}")
        session = PersistentMCPSession(
            server_name,
            config,
            allowed_tools=allowed_tools,
        )

        # Initialize session first, only store if successful
        try:
            await session.initialize()
            # Only store session after successful initialization
            self.sessions[server_name] = session
            logger.info(f"Session created and cached for {server_name}")
            return session
        except Exception:
            # Clean up session on failure
            await session.disconnect()
            raise

    async def initialize_all_sessions(self, server_configs: dict[str, MCPConfiguration]) -> None:
        """Initialize all sessions and cache tools.

        This method initializes all configured MCP servers concurrently
        for better performance.

        Args:
            server_configs (dict[str, MCPConfiguration]): Dictionary of server configurations

        Raises:
            Exception: If any session initialization fails
        """
        if self._initialized:
            logger.debug("Session pool already initialized")
            return

        logger.info(f"Initializing session pool with {len(server_configs)} servers")

        # Initialize all sessions concurrently
        initialization_tasks = []
        for server_name, config in server_configs.items():
            allowed_tools = self._extract_allowed_tools(server_name, config)
            task = self._initialize_single_session(server_name, config, allowed_tools)
            initialization_tasks.append(task)

        if initialization_tasks:
            try:
                await asyncio.gather(*initialization_tasks)
                self._initialized = True
                logger.info(f"Session pool initialized with {len(self.sessions)} active sessions")
            except Exception as e:
                logger.error(f"Failed to initialize session pool: {e}")
                # Cleanup any partially initialized sessions
                await self.close_all_sessions()
                # Ensure _initialized remains False to allow retrying
                self._initialized = False
                raise
        else:
            self._initialized = True
            logger.info("Session pool initialized (no servers configured)")

    def _extract_allowed_tools(
        self,
        server_name: str,
        config: MCPConfiguration,
    ) -> list[str] | None:
        """Extract allowed_tools from config.

        Args:
            server_name (str): Name of the MCP server
            config (MCPConfiguration): MCP server configuration

        Returns:
            list[str] | None: List of allowed tool names, or None if no restriction

        Raises:
            ValueError: If allowed_tools is not a list of strings
        """
        allowed_tools: list[str] | None = None

        # Try object attribute first (avoids double property call from hasattr+getattr)
        try:
            raw_allowed = config.allowed_tools
            # Use unified validation logic
            allowed_tools = validate_allowed_tools_list(raw_allowed, f"Server '{server_name}'")
        except AttributeError:
            # Check if config is dict-like
            if isinstance(config, dict):
                allowed_tools = validate_allowed_tools_config(config, server_name)

        if allowed_tools:
            logger.debug(f"Server '{server_name}' has {len(allowed_tools)} allowed tools")
        else:
            logger.debug(f"Server '{server_name}' allows all tools (no restriction)")

        return allowed_tools

    async def _initialize_single_session(
        self,
        server_name: str,
        config: MCPConfiguration,
        allowed_tools: list[str] | None = None,
    ) -> None:
        """Initialize a single session (internal method).

        Args:
            server_name (str): Name of the MCP server
            config (MCPConfiguration): MCP server configuration
            allowed_tools (list[str] | None): Optional list of tool names to allow
        """
        try:
            await self.get_or_create_session(server_name, config, allowed_tools)
            logger.debug(f"Session initialized for {server_name}")
        except Exception as e:
            logger.debug(f"Failed to initialize session for {server_name}: {e}")
            raise

    def get_all_active_sessions(self) -> dict[str, PersistentMCPSession]:
        """Get all active sessions.

        Returns:
            dict[str, PersistentMCPSession]: Dictionary of active sessions by server name
        """
        return {name: session for name, session in self.sessions.items() if session.is_initialized}

    @property
    def active_sessions(self) -> list[str]:
        """Get list of active session names.

        Returns:
            list[str]: List of active session names
        """
        return [name for name, session in self.sessions.items() if session.is_initialized]

    async def get_all_tools(self) -> list[Tool]:
        """Get all cached tools from all active sessions.

        Returns:
            list[Tool]: List of all available tools across all sessions
        """
        # Create snapshot of sessions under lock to prevent race conditions
        async with self._lock:
            session_snapshot = dict(self.sessions.items())

        # Prepare tasks for active sessions
        server_names = list(session_snapshot.keys())
        tasks = [session_snapshot[name].list_tools() for name in server_names]

        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_tools: list[Tool] = []
        for server_name, result in zip(server_names, results, strict=False):
            if isinstance(result, Exception):
                logger.warning(f"Failed to get tools from {server_name}: {result}")
            else:
                all_tools.extend(result)
                logger.debug(f"Added {len(result)} tools from {server_name}")

        logger.debug(f"Total tools available: {len(all_tools)}")
        return all_tools

    async def close_session(self, server_name: str) -> None:
        """Close specific session.

        Args:
            server_name (str): Name of the server session to close
        """
        async with self._lock:
            if server_name in self.sessions:
                try:
                    logger.info(f"Closing session for {server_name}")
                    await self.sessions[server_name].disconnect()
                except Exception as e:
                    logger.warning(f"Error closing session {server_name}: {e}")
                finally:
                    del self.sessions[server_name]
                    logger.info(f"Session {server_name} removed from pool")

    async def close_all_sessions(self) -> None:
        """Close all sessions gracefully.

        This method ensures all resources are cleaned up properly.
        """
        async with self._lock:
            logger.info("Closing all sessions in pool")

            # Create list of sessions to close (to avoid modification during iteration)
            sessions_to_close = list(self.sessions.keys())

            # Close sessions concurrently for faster shutdown
            close_tasks = []
            for server_name in sessions_to_close:
                task = self._close_single_session(server_name)
                close_tasks.append(task)

            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)

            # Clear all session data
            self.sessions.clear()
            self._initialized = False

            logger.info("All sessions closed and pool cleared")

    async def _close_single_session(self, server_name: str) -> None:
        """Close a single session (internal method).

        Args:
            server_name (str): Name of the server session to close
        """
        try:
            if server_name in self.sessions:
                await self.sessions[server_name].disconnect()
                logger.debug(f"Session {server_name} closed successfully")
        except Exception as e:
            logger.warning(f"Error closing session {server_name}: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if session pool is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized

    @property
    def session_count(self) -> int:
        """Get number of active sessions.

        Returns:
            int: Number of active sessions
        """
        return len(self.sessions)

    def get_session(self, server_name: str) -> PersistentMCPSession:
        """Get specific session by name.

        Args:
            server_name (str): Name of the server

        Returns:
            PersistentMCPSession: The requested session

        Raises:
            KeyError: If session doesn't exist
        """
        if server_name not in self.sessions:
            raise KeyError(f"Session '{server_name}' not found")
        return self.sessions[server_name]
