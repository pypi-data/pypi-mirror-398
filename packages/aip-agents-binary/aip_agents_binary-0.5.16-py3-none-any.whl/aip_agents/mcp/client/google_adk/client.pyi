from _typeshed import Incomplete
from aip_agents.mcp.client.base_mcp_client import BaseMCPClient as BaseMCPClient
from aip_agents.utils.logger import get_logger as get_logger
from gllm_tools.mcp.client.config import MCPConfiguration as MCPConfiguration
from google.adk.tools import FunctionTool
from mcp.types import EmbeddedResource, ImageContent

NonTextContent = ImageContent | EmbeddedResource
logger: Incomplete

class GoogleADKMCPClient(BaseMCPClient):
    '''Google ADK MCP Client with Persistent Sessions.

    This client extends BaseMCPClient to provide Google ADK-specific tool conversion
    while maintaining persistent MCP sessions and connection reuse across tool calls.
    It converts MCP tools into ADK FunctionTool instances for seamless integration.

    The client handles:
    - Converting MCP tools to ADK FunctionTool instances using persistent sessions
    - Managing MCP server connections with automatic reconnection
    - Converting MCP resources to ADK-compatible formats
    - Handling tool execution with proper error formatting for ADK agents

    Example:
        ```python
        from aip_agents.mcp.client.google_adk.client import GoogleADKMCPClient
        from gllm_tools.mcp.client.config import MCPConfiguration

        servers = {
            "filesystem": MCPConfiguration(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"]
            )
        }

        client = GoogleADKMCPClient(servers)
        await client.initialize()  # Initialize persistent sessions
        tools = await client.get_tools()  # Returns list of ADK FunctionTool instances
        ```
    '''
    RESOURCE_FETCH_TIMEOUT: int
    def __init__(self, servers: dict[str, MCPConfiguration]) -> None:
        """Initialize Google ADK MCP client.

        Args:
            servers (dict[str, MCPConfiguration]): Dictionary of MCP server configurations
        """
    async def initialize(self) -> None:
        """Initialize persistent MCP sessions for Google ADK integration.

        This method ensures all MCP servers are connected with persistent sessions
        and prepares the client for ADK tool conversion.

        Raises:
            Exception: If session initialization fails
        """
    async def get_tools(self, server: str | None = None) -> list[FunctionTool]:
        """Get ADK-compatible FunctionTool instances with smart caching.

        Converts MCP tools to ADK format and caches them for better performance
        on repeated access. Cache is keyed by server parameter.

        Args:
            server (str | None): Optional server name to filter tools from a specific server.
                    If None, returns tools from all configured servers.

        Returns:
            list[FunctionTool]: List of cached ADK FunctionTool instances.
        """
    async def cleanup(self) -> None:
        """Clean up Google ADK MCP client resources.

        This method ensures all persistent sessions are properly closed and
        ADK-specific resources are cleaned up.
        """
