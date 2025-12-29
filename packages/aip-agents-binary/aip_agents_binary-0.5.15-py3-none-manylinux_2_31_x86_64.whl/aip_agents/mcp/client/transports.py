"""MCP Transport Handlers.

This module provides abstract and concrete transport classes for STDIO, SSE, and streamable HTTP.
Each transport handles connection establishment specific to its protocol.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Any, Protocol

from gllm_tools.mcp.client.config import MCPConfiguration
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from aip_agents.utils.logger import get_logger


class TransportContext(Protocol):
    """Protocol defining the interface for async context managers used in MCP transport connections."""

    async def __aenter__(self):
        """Enter the async context, establishing the connection and returning read/write streams."""
        ...

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Exit the async context, performing cleanup and closing the connection.

        Args:
            _exc_type: Exception type if an exception occurred.
            _exc_val: Exception value if an exception occurred.
            _exc_tb: Exception traceback if an exception occurred.
        """
        ...


logger = get_logger(__name__)


DEFAULT_TIMEOUT: float = 30.0
"""Default connection timeout in seconds."""


class TransportType(StrEnum):
    """Enum for supported MCP transport types."""

    HTTP = "http"
    SSE = "sse"
    STDIO = "stdio"


class Transport(ABC):
    """Abstract base class for MCP transports."""

    def __init__(self, server_name: str, config: MCPConfiguration) -> None:
        """Initialize the transport.

        Args:
            server_name (str): Name of the MCP server.
            config (MCPConfiguration): Configuration for the transport.
        """
        self.server_name = server_name
        self.config = config
        self.ctx: Any = None

    @abstractmethod
    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Establish connection and return read/write streams and context manager.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]:
                (read_stream, write_stream, ctx)
            Where:
                - read_stream: AsyncIterator[bytes] for reading from the server.
                - write_stream: AsyncIterator[bytes] for writing to the server.
                - ctx: The async context manager instance for cleanup via __aexit__.

        Raises:
            ValueError: If required config (e.g., URL or command) is missing.
            ConnectionError: If connection establishment fails.
        """
        pass

    async def close(self) -> None:
        """Clean up the transport connection."""
        if self.ctx:
            try:
                await self.ctx.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error during transport cleanup for {self.server_name}: {e}")


class SSETransport(Transport):
    """SSE transport handler."""

    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Connect using SSE transport.

        Builds SSE URL from config, initializes client with timeout, and enters context.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]: (read_stream, write_stream, ctx)

        Raises:
            ValueError: If URL is missing.
            ConnectionError: If SSE connection fails.
        """
        base_url = self.config.get("url", "").rstrip("/")
        if not base_url:
            raise ValueError("URL is required for SSE transport")

        url = f"{base_url}/sse" if not base_url.endswith("/sse") else base_url
        timeout = self.config.get("timeout", DEFAULT_TIMEOUT)
        headers = self.config.get("headers", {})
        logger.debug(f"Attempting SSE connection to {url} with headers: {list(headers.keys())}")
        try:
            self.ctx = sse_client(url=url, timeout=timeout, sse_read_timeout=300.0, headers=headers)
            read_stream, write_stream = await self.ctx.__aenter__()
            logger.info(f"Connected to {self.server_name} via SSE")
            return read_stream, write_stream, self.ctx
        except Exception as e:
            raise ConnectionError(f"SSE connection failed for {self.server_name}: {str(e)}") from e


class HTTPTransport(Transport):
    """Streamable HTTP transport handler."""

    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Connect using streamable HTTP transport.

        Builds MCP URL from config, initializes client with timeout, and enters context.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]: (read_stream, write_stream, ctx)

        Raises:
            ValueError: If URL is missing.
            ConnectionError: If HTTP connection fails.
        """
        base_url = self.config.get("url", "").rstrip("/")
        if not base_url:
            raise ValueError("URL is required for HTTP transport")

        url = f"{base_url}/mcp" if not base_url.endswith("/mcp") else base_url
        timeout = self.config.get("timeout", DEFAULT_TIMEOUT)
        headers = self.config.get("headers", {})
        logger.debug(f"Attempting streamable HTTP connection to {url} with headers: {list(headers.keys())}")
        try:
            self.ctx = streamablehttp_client(url=url, timeout=timeout, headers=headers)
            read_stream, write_stream, _ = await self.ctx.__aenter__()
            logger.info(f"Connected to {self.server_name} via HTTP")
            return read_stream, write_stream, self.ctx
        except Exception as e:
            raise ConnectionError(f"HTTP connection failed for {self.server_name}: {str(e)}") from e


class StdioTransport(Transport):
    """STDIO transport handler."""

    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Connect using STDIO transport.

        Initializes stdio client from command/args/env in config and enters context.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]: (read_stream, write_stream, ctx)

        Raises:
            ValueError: If command is missing.
            ConnectionError: If STDIO connection fails.
        """
        command = self.config.get("command")
        args = self.config.get("args", [])
        env = self.config.get("env")

        if not command:
            raise ValueError("Command is required for stdio transport")

        logger.debug(f"Attempting stdio connection with command: {command}, args: {args}")
        try:
            stdio_params = StdioServerParameters(command=command, args=args, env=env)
            self.ctx = stdio_client(stdio_params)
            read_stream, write_stream = await self.ctx.__aenter__()
            logger.info(f"Connected to {self.server_name} via STDIO")
            return read_stream, write_stream, self.ctx
        except Exception as e:
            raise ConnectionError(f"STDIO connection failed for {self.server_name}: {str(e)}") from e


def create_transport(server_name: str, config: MCPConfiguration, transport_type: TransportType | str) -> Transport:
    """Factory to create the appropriate transport instance.

    Args:
        server_name (str): Server name
        config (MCPConfiguration): Config
        transport_type (str): Transport type ('http', 'sse', 'stdio')

    Returns:
        Transport: Concrete transport instance

    Raises:
        ValueError: If transport_type is unsupported.
    """
    if transport_type == TransportType.HTTP:
        return HTTPTransport(server_name, config)
    elif transport_type == TransportType.SSE:
        return SSETransport(server_name, config)
    elif transport_type == TransportType.STDIO:
        return StdioTransport(server_name, config)
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")
