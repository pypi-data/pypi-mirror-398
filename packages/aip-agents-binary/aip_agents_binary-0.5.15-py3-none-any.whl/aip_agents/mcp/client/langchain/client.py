"""Langchain MCP Adapter for MCP Client with Session Persistence.

Authors:
    Samuel Lusandi (samuel.lusandi@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import base64
from typing import Any

from gllm_tools.mcp.client.config import MCPConfiguration
from gllm_tools.mcp.client.resource import MCPResource
from gllm_tools.mcp.client.tool import MCPTool
from langchain_core.documents.base import Blob
from langchain_core.tools import StructuredTool, ToolException
from mcp.types import (
    BlobResourceContents,
    CallToolResult,
    EmbeddedResource,
    ImageContent,
    TextContent,
    TextResourceContents,
)
from pydantic import AnyUrl

from aip_agents.mcp.client.base_mcp_client import BaseMCPClient
from aip_agents.utils.logger import get_logger

NonTextContent = ImageContent | EmbeddedResource

logger = get_logger(__name__)


class LangchainMCPClient(BaseMCPClient):
    """Langchain MCP Client with Session Persistence.

    This client extends BaseMCPClient to provide LangChain-specific tool conversion
    while maintaining persistent MCP sessions and connection reuse across tool calls.
    """

    RESOURCE_FETCH_TIMEOUT = 10

    def __init__(self, servers: dict[str, MCPConfiguration]):
        """Initialize LangChain MCP client.

        Args:
            servers (dict[str, MCPConfiguration]): Dictionary of MCP server configurations
        """
        super().__init__(servers)
        # Cache converted LangChain tools for better performance on repeated access
        self._langchain_tools_cache: dict[str | None, list[StructuredTool]] = {}

    async def initialize(self) -> None:
        """Initialize all sessions for LangChain client.

        This method initializes the base MCP sessions and prepares for tool caching.

        Raises:
            Exception: If base initialization fails
        """
        # Call base class initialization - this caches raw MCP tools
        await super().initialize()

        logger.info(f"LangchainMCPClient initialized with {self.get_tools_count()} MCP tools available for conversion")

    def _process_tool(self, tool: MCPTool, server_name: str) -> StructuredTool:
        """Converts an MCP tool into a Langchain StructuredTool.

        Args:
            tool (MCPTool): The tool to convert.
            server_name (str): The name of the MCP server.

        Returns:
            StructuredTool: The converted tool.
        """
        # Store the original MCP tool name for the actual server call
        original_tool_name = tool.name

        async def call_mcp_tool(
            **arguments: dict[str, Any],
        ) -> tuple[str | list[str], list[NonTextContent] | None]:
            """Invoke the underlying MCP tool and normalize its response.

            Args:
                **arguments: Structured arguments expected by the MCP tool.

            Returns:
                tuple: Textual response (string or list of strings) and optional non-text artifacts.
            """
            # Use the original MCP tool name for the server call, not the sanitized name
            call_tool_result = await self.call_tool(server_name, original_tool_name, arguments)
            return self._convert_call_tool_result(call_tool_result)

        return StructuredTool(
            name=tool.name,
            description=tool.description or "",
            args_schema=tool.inputSchema,
            coroutine=call_mcp_tool,
            response_format="content_and_artifact",
            metadata=tool.annotations.model_dump() if tool.annotations else None,
        )

    async def get_tools(self, server: str | None = None) -> list[StructuredTool]:
        """Get LangChain StructuredTools with smart caching.

        Converts MCP tools to LangChain format and caches them for better performance
        on repeated access. Cache is keyed by server parameter.

        Args:
            server (str | None): Optional server name to filter tools. If None, returns all tools.

        Returns:
            list[StructuredTool]: List of cached LangChain StructuredTool instances
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

            logger.debug(f"Retrieved {len(all_tools)} total LangChain tools from {len(self.servers)} servers")
            return all_tools

    async def _get_server_tools_cached(self, server_name: str) -> list[StructuredTool]:
        """Get tools for a specific server with caching.

        This method centralizes caching logic and ensures tools are only converted once per server.

        Args:
            server_name (str): Name of the MCP server

        Returns:
            list[StructuredTool]: List of cached StructuredTool instances for the server
        """
        # Check cache first
        if server_name in self._langchain_tools_cache:
            logger.debug(f"Using cached LangChain tools for server '{server_name}'")
            return self._langchain_tools_cache[server_name]

        # Convert and cache tools for this server
        logger.info(f"Converting and caching tools for server '{server_name}'")
        mcp_tools = await self.get_raw_mcp_tools(server_name)
        langchain_tools = []

        for mcp_tool in mcp_tools:
            langchain_tool = self._process_tool(mcp_tool, server_name)
            langchain_tools.append(langchain_tool)
            logger.info(
                f"Converted MCP tool '{mcp_tool.name}' "
                f"to LangChain tool '{langchain_tool.name}' "
                f"for server '{server_name}'"
            )

        # Cache the converted tools
        self._langchain_tools_cache[server_name] = langchain_tools
        logger.debug(f"Cached {len(langchain_tools)} LangChain tools for server '{server_name}'")

        return langchain_tools

    async def _process_resource(self, resource: MCPResource) -> Any:
        """Converts an MCP resource into a Langchain Resource using persistent session.

        Args:
            resource (MCPResource): The resource to convert.

        Returns:
            Blob: The converted resource.
        """
        # Determine server name from resource URI or use first available server
        server_name = self._determine_server_name_for_resource(resource)

        async def read_resource(uri: AnyUrl) -> str:
            """Read the actual content of the MCP resource using persistent session.

            Note: This function is async for consistency with MCP operations, even though
            the uri parameter is a synchronous AnyUrl object.

            Args:
                uri (AnyUrl): The URI of the resource to read.

            Returns:
                str: The content of the resource as a string.
            """
            try:
                # Use base class method for persistent session resource access
                resource_result = await self.read_resource(server_name, str(uri))

                if not resource_result.contents:
                    raise ValueError(f"No contents found for resource {uri}")

                contents = resource_result.contents[0]
                if isinstance(contents, TextResourceContents):
                    return contents.text
                elif isinstance(contents, BlobResourceContents):
                    return base64.b64decode(contents.blob)
                else:
                    raise ValueError(f"Unsupported content type for URI {uri}")
            except Exception as e:
                logger.error(f"Failed to read MCP resource {uri}: {e}")
                raise

        return Blob.from_data(
            await asyncio.wait_for(read_resource(resource.uri), timeout=self.RESOURCE_FETCH_TIMEOUT),
            mime_type=resource.mime_type,
            path=str(resource.uri),
            metadata={"uri": resource.uri},
        )

    async def cleanup(self) -> None:
        """Cleanup LangChain MCP resources.

        This method extends base class cleanup and clears the LangChain tool cache.
        """
        logger.info("Cleaning up LangchainMCPClient resources")
        try:
            await super().cleanup()
        except Exception as e:
            logger.error(f"Error during base LangchainMCPClient cleanup: {e}", exc_info=True)
        finally:
            # Always clear the LangChain tools cache
            self._langchain_tools_cache.clear()
            logger.info("LangchainMCPClient cleanup complete")

    def _convert_call_tool_result(
        self,
        call_tool_result: CallToolResult,
    ) -> tuple[str | list[str], list[NonTextContent] | None]:
        """Converts an MCP call tool result into a tuple of text and non-text contents.

        Args:
            call_tool_result (CallToolResult): The call tool result to convert.

        Returns:
            tuple[str | list[str], list[NonTextContent] | None]: The converted call tool result.
        """
        text_contents: list[TextContent] = []
        non_text_contents = []
        for content in call_tool_result.content:
            if isinstance(content, TextContent):
                text_contents.append(content)
            else:
                non_text_contents.append(content)

        tool_content: str | list[str] = [content.text for content in text_contents]
        if not text_contents:
            tool_content = ""
        elif len(text_contents) == 1:
            tool_content = tool_content[0]

        if call_tool_result.isError:
            raise ToolException(tool_content)

        return tool_content, non_text_contents if non_text_contents else None
