from _typeshed import Incomplete
from aip_agents.mcp.client.transports import TransportType as TransportType, create_transport as create_transport
from aip_agents.utils.logger import get_logger as get_logger
from gllm_tools.mcp.client.config import MCPConfiguration
from typing import Any

logger: Incomplete

class MCPConnectionManager:
    """Manages MCP connection lifecycle following mcp-use patterns.

    This connection manager handles the transport connection lifecycle in a background
    task to avoid cancel scope issues during cleanup. It supports automatic transport
    negotiation (HTTP -> SSE fallback) and graceful shutdown. Invalid explicit transports
    are normalized via aliases (e.g., 'streamable_http' -> 'http') or fall back to
    auto-detection with a warning.
    """
    TRANSPORT_ALIASES: Incomplete
    server_name: Incomplete
    config: Incomplete
    transport_type: Incomplete
    max_retries: Incomplete
    initial_retry_delay: Incomplete
    def __init__(self, server_name: str, config: MCPConfiguration) -> None:
        """Initialize connection manager.

        Args:
            server_name (str): Name of the MCP server
            config (MCPConfiguration): MCP server configuration
        """
    async def start(self) -> tuple[Any, Any]:
        """Start connection in background task.

        Returns:
            tuple[Any, Any]: Tuple of (read_stream, write_stream) for ClientSession

        Raises:
            Exception: If connection establishment fails
        """
    async def stop(self) -> None:
        """Stop connection gracefully."""
    @property
    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
