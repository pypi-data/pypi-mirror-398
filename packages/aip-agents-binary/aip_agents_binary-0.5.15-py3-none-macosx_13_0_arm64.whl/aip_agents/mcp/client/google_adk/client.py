"""Google ADK MCP Adapter for MCP Client with Session Persistence.

This module contains the GoogleADKMCPClient class, which extends the BaseMCPClient
to integrate persistent MCP tools with Google's Agent Development Kit (ADK).

The GoogleADKMCPClient adapts MCP tools into ADK FunctionTool instances that can
be used seamlessly with ADK agents while maintaining session persistence across
multiple tool calls.

Authors:
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import base64
from typing import Any

from gllm_tools.mcp.client.config import MCPConfiguration
from gllm_tools.mcp.client.resource import MCPResource
from gllm_tools.mcp.client.tool import MCPTool
from mcp.types import (
    BlobResourceContents,
    CallToolResult,
    EmbeddedResource,
    ImageContent,
    TextContent,
    TextResourceContents,
)

from aip_agents.utils.logger import get_logger

try:
    from google.adk.tools import FunctionTool
    from google.genai.types import Part
except ImportError as e:
    raise ImportError("Google ADK is required to use GoogleADKMCPClient. Install with: pip install google-adk") from e

from aip_agents.mcp.client.base_mcp_client import BaseMCPClient

NonTextContent = ImageContent | EmbeddedResource

logger = get_logger(__name__)


class GoogleADKMCPClient(BaseMCPClient):
    """Google ADK MCP Client with Persistent Sessions.

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
    """

    RESOURCE_FETCH_TIMEOUT = 10

    def __init__(self, servers: dict[str, MCPConfiguration]):
        """Initialize Google ADK MCP client.

        Args:
            servers (dict[str, MCPConfiguration]): Dictionary of MCP server configurations
        """
        super().__init__(servers)
        # Cache converted ADK tools for consistent pattern with LangChain client
        self._adk_tools_cache: dict[str | None, list[FunctionTool]] = {}

    async def initialize(self) -> None:
        """Initialize persistent MCP sessions for Google ADK integration.

        This method ensures all MCP servers are connected with persistent sessions
        and prepares the client for ADK tool conversion.

        Raises:
            Exception: If session initialization fails
        """
        await super().initialize()
        logger.info(f"GoogleADKMCPClient initialized with {self.get_tools_count()} MCP tools ready for ADK conversion")

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
        if not self.is_initialized:
            await self.initialize()

        if server:
            # Get tools from specific server with caching
            server_tools = await self._get_server_tools_cached(server)
            return server_tools.copy()
        else:
            # Get tools from all servers with efficient caching
            all_tools = []
            for server_name in self.servers.keys():
                try:
                    server_tools = await self._get_server_tools_cached(server_name)
                    all_tools.extend(server_tools)
                except Exception as e:
                    logger.warning(f"Failed to get tools from server '{server_name}': {e}")

            logger.debug(f"Retrieved {len(all_tools)} total ADK FunctionTools from {len(self.servers)} servers")
            return all_tools

    async def _get_server_tools_cached(self, server_name: str) -> list[FunctionTool]:
        """Get tools for a specific server with caching.

        This method centralizes caching logic and ensures tools are only converted once per server.

        Args:
            server_name (str): Name of the MCP server

        Returns:
            list[FunctionTool]: List of cached FunctionTool instances for the server
        """
        # Check cache first
        if server_name in self._adk_tools_cache:
            logger.debug(f"Using cached ADK tools for server '{server_name}'")
            return self._adk_tools_cache[server_name]

        # Convert and cache tools for this server
        logger.info(f"Converting and caching tools for server '{server_name}'")
        mcp_tools = await self.get_raw_mcp_tools(server_name)
        adk_tools = []

        for mcp_tool in mcp_tools:
            adk_tool = self._process_tool(mcp_tool, server_name)
            adk_tools.append(adk_tool)
            logger.info(f"Converted MCP tool '{mcp_tool.name}' to ADK FunctionTool for server '{server_name}'")

        # Cache the converted tools
        self._adk_tools_cache[server_name] = adk_tools
        logger.debug(f"Cached {len(adk_tools)} ADK FunctionTools for server '{server_name}'")

        return adk_tools

    def _process_tool(self, tool: MCPTool, server_name: str | None = None) -> FunctionTool:
        """Converts an MCP tool into an ADK FunctionTool using persistent session.

        This method creates a dynamic function that wraps the MCP tool execution
        using the base class's persistent session management, and converts the
        response format to be compatible with ADK's expectations.

        Args:
            tool (MCPTool): The MCP tool to convert.
            server_name (str | None): The server name for routing tool calls.

        Returns:
            FunctionTool: An ADK FunctionTool instance that wraps the MCP tool
                          with persistent session support.
        """
        # Store the original MCP tool name for the actual server call
        original_tool_name = tool.name

        # Create the dynamic function that will be wrapped by FunctionTool
        async def mcp_tool_function(**arguments: dict[str, Any]) -> dict[str, Any]:
            """Dynamic function that executes the MCP tool with persistent session.

            This function uses the base class's call_tool method which handles
            server routing and persistent session management automatically.

            Args:
                **arguments (dict[str, Any]): Keyword arguments for the MCP tool execution.

            Returns:
                dict[str, Any]: The tool execution result.
            """
            try:
                # Determine server to route the call to
                resolved_server = server_name or next(iter(self.servers.keys()), None)
                if not resolved_server:
                    raise RuntimeError("No MCP servers configured for executing tool")

                # Use the original MCP tool name for the server call, not the sanitized name
                call_tool_result = await self.call_tool(resolved_server, original_tool_name, arguments)
                return self._convert_call_tool_result(call_tool_result)
            except Exception as e:
                logger.error(f"MCP tool '{original_tool_name}' execution failed: {e}")
                return {"status": "error", "message": str(e)}

        # Set function metadata for ADK introspection (will be sanitized later by agent)
        mcp_tool_function.__name__ = tool.name
        mcp_tool_function.__doc__ = tool.description or f"MCP tool: {tool.name} (from server: {server_name})"

        # Create and return the ADK FunctionTool
        return FunctionTool(func=mcp_tool_function)

    async def _process_resource(self, resource: MCPResource) -> dict[str, Any]:
        """Converts an MCP resource into an ADK-compatible format using persistent session.

        Args:
            resource (MCPResource): The MCP resource to convert.

        Returns:
            dict[str, Any]: A dictionary containing resource metadata and accessor function.
        """
        # Determine server name from resource URI or use first available server
        server_name = self._determine_server_name_for_resource(resource)

        async def read_resource_content() -> Part:
            """Reads the actual content of the MCP resource using persistent session."""
            try:
                # Use base class method for persistent session resource access
                resource_result = await self.read_resource(server_name, str(resource.uri))

                contents = resource_result.contents[0]
                if isinstance(contents, TextResourceContents):
                    return Part.from_text(contents.text)
                elif isinstance(contents, BlobResourceContents):
                    data = base64.b64decode(contents.blob)
                    return Part.from_bytes(data=data, mime_type=resource.mime_type)
                else:
                    raise ValueError(f"Unsupported content type for URI {resource.uri}")
            except Exception as e:
                # Do not break callers; return a safe textual Part describing the error
                logger.error(f"Failed to read MCP resource {resource.uri}: {e}")
                try:
                    return Part.from_text(f"Error reading resource {resource.uri}: {e}")
                except Exception as part_error:
                    logger.error(f"Failed to create error Part for resource {resource.uri}: {part_error}")
                    raise ValueError(f"Cannot create ADK Part for error response: {part_error}") from part_error

        return {
            "uri": str(resource.uri),
            "name": resource.name,
            "description": resource.description,
            "mime_type": resource.mime_type,
            "read_content": read_resource_content,
            "metadata": {
                "uri": resource.uri,
                "annotations": resource.annotations.model_dump() if resource.annotations else None,
            },
        }

    async def cleanup(self) -> None:
        """Clean up Google ADK MCP client resources.

        This method ensures all persistent sessions are properly closed and
        ADK-specific resources are cleaned up.
        """
        logger.info("Cleaning up GoogleADKMCPClient resources")
        try:
            await super().cleanup()
        except Exception as e:
            logger.error(f"Error during base GoogleADKMCPClient cleanup: {e}", exc_info=True)
        finally:
            # Always clear the ADK tools cache
            self._adk_tools_cache.clear()
            logger.info("GoogleADKMCPClient cleanup completed")

    def _convert_call_tool_result(self, call_tool_result: CallToolResult) -> dict[str, Any]:
        """Converts an MCP call tool result into an ADK-compatible format.

        ADK tools should return dictionaries with meaningful keys. This method
        extracts text content and formats it appropriately for ADK agents.

        Args:
            call_tool_result (CallToolResult): The MCP tool execution result.

        Returns:
            dict[str, Any]: ADK-compatible result dictionary.

        Raises:
            Exception: If the tool execution resulted in an error.
        """
        text_contents, non_text_contents = self._separate_contents(call_tool_result.content)

        if call_tool_result.isError:
            error_message = self._format_error_message(text_contents)
            raise RuntimeError(f"MCP tool execution failed: {error_message}")

        result = {"status": "success"}
        if text_contents:
            result["result"] = (
                text_contents[0].text if len(text_contents) == 1 else [content.text for content in text_contents]
            )
        else:
            result["result"] = "Tool executed successfully"

        artifacts = [a for a in (self._format_artifact(c) for c in non_text_contents) if a]
        if artifacts:
            result["artifacts"] = artifacts

        return result

    @staticmethod
    def _separate_contents(contents) -> tuple[list[TextContent], list[NonTextContent]]:
        """Separates a list of content objects into text and non-text content.

        This helper method processes a list of content objects and categorizes them
        into text content (TextContent) and other content types for further processing.

        Args:
            contents (list[Any]): List of content objects to be separated.

        Returns:
            tuple[list[TextContent], list[NonTextContent]]: A tuple containing two lists:
                - First: TextContent objects
                - Second: All other content types.
        """
        text_contents = []
        non_text_contents = []
        for content in contents:
            if isinstance(content, TextContent):
                text_contents.append(content)
            else:
                non_text_contents.append(content)
        return text_contents, non_text_contents

    @staticmethod
    def _format_artifact(content: NonTextContent) -> dict[str, Any] | None:
        """Formats non-text content into ADK-compatible artifact dictionaries.

        Converts different types of content objects (images, embedded resources) into
        a standardized dictionary format expected by ADK agents.

        Args:
            content (NonTextContent): The content object to be formatted. Can be either ImageContent
                or EmbeddedResource.

        Returns:
            dict[str, Any] | None: A dictionary containing the formatted content with appropriate type-specific
            fields, or None if the content type is not supported.
        """
        if isinstance(content, ImageContent):
            return {
                "type": "image",
                "data": content.data,
                "mime_type": content.mimeType,
            }
        if isinstance(content, EmbeddedResource):
            return {
                "type": "resource",
                "uri": str(content.resource.uri),
                "text": getattr(content.resource, "text", None),
            }
        return None

    @staticmethod
    def _format_error_message(text_contents: list[TextContent]) -> str:
        """Formats a list of text contents into a single error message string.

        Combines multiple text content objects into a single string, typically
        used for creating human-readable error messages from tool execution results.

        Args:
            text_contents (list[TextContent]): List of TextContent objects containing error message parts.

        Returns:
            str: A single string containing all text contents joined by spaces,
            or an empty string if the input list is empty.
        """
        return " ".join(content.text for content in text_contents) if text_contents else ""
