from _typeshed import Incomplete
from abc import ABC, abstractmethod
from aip_agents.utils.logger import get_logger as get_logger
from collections.abc import AsyncIterator as AsyncIterator
from enum import StrEnum
from gllm_tools.mcp.client.config import MCPConfiguration
from typing import Any, Protocol

class TransportContext(Protocol):
    """Protocol defining the interface for async context managers used in MCP transport connections."""
    async def __aenter__(self) -> None:
        """Enter the async context, establishing the connection and returning read/write streams."""
    async def __aexit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Exit the async context, performing cleanup and closing the connection.

        Args:
            _exc_type: Exception type if an exception occurred.
            _exc_val: Exception value if an exception occurred.
            _exc_tb: Exception traceback if an exception occurred.
        """

logger: Incomplete
DEFAULT_TIMEOUT: float

class TransportType(StrEnum):
    """Enum for supported MCP transport types."""
    HTTP: str
    SSE: str
    STDIO: str

class Transport(ABC):
    """Abstract base class for MCP transports."""
    server_name: Incomplete
    config: Incomplete
    ctx: Any
    def __init__(self, server_name: str, config: MCPConfiguration) -> None:
        """Initialize the transport.

        Args:
            server_name (str): Name of the MCP server.
            config (MCPConfiguration): Configuration for the transport.
        """
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
    async def close(self) -> None:
        """Clean up the transport connection."""

class SSETransport(Transport):
    """SSE transport handler."""
    ctx: Incomplete
    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Connect using SSE transport.

        Builds SSE URL from config, initializes client with timeout, and enters context.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]: (read_stream, write_stream, ctx)

        Raises:
            ValueError: If URL is missing.
            ConnectionError: If SSE connection fails.
        """

class HTTPTransport(Transport):
    """Streamable HTTP transport handler."""
    ctx: Incomplete
    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Connect using streamable HTTP transport.

        Builds MCP URL from config, initializes client with timeout, and enters context.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]: (read_stream, write_stream, ctx)

        Raises:
            ValueError: If URL is missing.
            ConnectionError: If HTTP connection fails.
        """

class StdioTransport(Transport):
    """STDIO transport handler."""
    ctx: Incomplete
    async def connect(self) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes], TransportContext]:
        """Connect using STDIO transport.

        Initializes stdio client from command/args/env in config and enters context.

        Returns:
            tuple[AsyncIterator[bytes], AsyncIterator[bytes], Any]: (read_stream, write_stream, ctx)

        Raises:
            ValueError: If command is missing.
            ConnectionError: If STDIO connection fails.
        """

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
