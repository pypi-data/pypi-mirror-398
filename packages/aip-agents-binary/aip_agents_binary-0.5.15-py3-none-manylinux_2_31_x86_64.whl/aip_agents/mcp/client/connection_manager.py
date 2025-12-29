"""MCP Connection Manager for persistent connection lifecycle management.

This module implements the connection manager pattern inspired by mcp-use library
to avoid cancel scope issues and provide persistent connections.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import inspect
from typing import Any

from gllm_tools.mcp.client.config import MCPConfiguration

from aip_agents.mcp.client.transports import TransportType, create_transport
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class MCPConnectionManager:
    """Manages MCP connection lifecycle following mcp-use patterns.

    This connection manager handles the transport connection lifecycle in a background
    task to avoid cancel scope issues during cleanup. It supports automatic transport
    negotiation (HTTP -> SSE fallback) and graceful shutdown. Invalid explicit transports
    are normalized via aliases (e.g., 'streamable_http' -> 'http') or fall back to
    auto-detection with a warning.
    """

    TRANSPORT_ALIASES = {
        "http": TransportType.HTTP,
        "streamable-http": TransportType.HTTP,
        "sse": TransportType.SSE,
        "stdio": TransportType.STDIO,
    }

    def __init__(self, server_name: str, config: MCPConfiguration):
        """Initialize connection manager.

        Args:
            server_name (str): Name of the MCP server
            config (MCPConfiguration): MCP server configuration
        """
        self.server_name = server_name
        self.config = config
        self._task = None
        self._connection = None
        self._transport = None
        self._stop_event = asyncio.Event()
        self._ready_event = asyncio.Event()
        self._done_event = asyncio.Event()
        self._exception = None
        self.transport_type = None
        # Configurable retry settings (MCP-specific, defaults to reasonable values)
        self.max_retries = config.get("max_retries", 3)
        self.initial_retry_delay = config.get("initial_retry_delay", 1.0)

    async def start(self) -> tuple[Any, Any]:
        """Start connection in background task.

        Returns:
            tuple[Any, Any]: Tuple of (read_stream, write_stream) for ClientSession

        Raises:
            Exception: If connection establishment fails
        """
        logger.debug(f"Starting connection manager for {self.server_name}")
        self._task = asyncio.create_task(self._connection_task())
        await self._ready_event.wait()

        if self._exception:
            raise self._exception

        return self._connection

    async def stop(self) -> None:
        """Stop connection gracefully."""
        logger.debug(f"Stopping connection manager for {self.server_name}")
        if self._task and not self._task.done():
            self._stop_event.set()
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except TimeoutError:
                logger.warning(f"Connection manager for {self.server_name} did not stop gracefully")
                self._task.cancel()
        await self._done_event.wait()

    @property
    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
        return (
            self._connection is not None
            and self._task is not None
            and not self._task.done()
            and not self._stop_event.is_set()
        )

    def _auto_detect_transport_type(self) -> TransportType:
        """Auto-detect transport type based on configuration.

        Returns:
            TransportType: Detected transport type
        """
        if "command" in self.config:
            return TransportType.STDIO
        elif "url" in self.config:
            url = self.config["url"]
            if url.endswith("/sse"):
                return TransportType.SSE
            else:
                return TransportType.HTTP
        else:
            return TransportType.STDIO

    def _get_transport_type(self) -> TransportType:
        """Determine the transport type to use, prioritizing explicit config with aliases.

        Returns:
            TransportType: Transport type enum

        Notes:
            Invalid explicit transports trigger a warning and fallback to auto-detection; no exception raised.
        """
        explicit_transport = self.config.get("transport", "").lower().replace("_", "-")
        if explicit_transport in self.TRANSPORT_ALIASES:
            return self.TRANSPORT_ALIASES[explicit_transport]

        if explicit_transport:
            logger.warning(f"Unknown explicit transport '{explicit_transport}'. Falling back to auto-detection.")

        return self._auto_detect_transport_type()

    async def _establish_connection(self) -> None:
        """Establish connection based on transport preference with fallback.

        Uses configurable retries with exponential backoff for transient failures.

        Raises:
            ConnectionError: If all connection attempts fail
        """
        self.transport_type = self._get_transport_type()
        details = f"URL: {self.config.get('url', 'N/A')}, Command: {self.config.get('command', 'N/A')}"
        logger.info(f"Establishing connection to {self.server_name} via {self.transport_type} ({details})")

        retry_delay = self.initial_retry_delay
        for attempt in range(self.max_retries):
            self._transport = create_transport(self.server_name, self.config, self.transport_type)
            try:
                read_stream, write_stream, _ = await self._transport.connect()
                self._connection = (read_stream, write_stream)
                logger.info(f"Connection established on attempt {attempt + 1}")
                return
            except ValueError:
                # Config validation errors should not be retried
                raise
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise ConnectionError(
                        f"Failed to establish connection to {self.server_name} "
                        f"after {self.max_retries} attempts: {str(e)}"
                    ) from e

    async def _connection_task(self) -> None:
        """Background task that manages the connection lifecycle."""
        try:
            await self._establish_connection()
            self._ready_event.set()
            await self._stop_event.wait()
        except Exception as e:
            logger.error(f"Connection failed for {self.server_name}: {e}", exc_info=True)
            self._exception = e
            self._ready_event.set()
        finally:
            if self._transport:
                try:
                    close_result = self._transport.close()
                    if inspect.isawaitable(close_result):
                        await close_result
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Failed to close transport cleanly for %s: %s", self.server_name, exc)
            self._connection = None
            self._done_event.set()
            logger.debug(f"Connection manager cleanup complete for {self.server_name}")
