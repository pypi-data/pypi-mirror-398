"""Example showing Google ADK agent with MCP tools integration.

Transport: Streamable HTTP
Streaming: Yes

This example demonstrates how to create a Google ADK agent that can use tools
from MCP servers via Streamable HTTP transport while streaming the response
in real-time.

Authors:
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_http


async def main():
    """Demonstrates the GoogleADKAgent with MCP tools via Streamable HTTP transport and streaming."""
    agent = GoogleADKAgent(
        name="GoogleADKMCPHTTPStream",
        instruction="""You are a helpful assistant that can use playwright tools to browse the web.
        If a user ask something, you try to answer it by browsing the web via playwright tools
        Do not ask for clarification, just answer to the best of your ability using playwright tools.""",
        model="gemini-2.0-flash",
        max_iterations=5,
    )
    agent.add_mcp_server(mcp_config_http)
    query = (
        "Go to huggingface.co, and then browse to the number 1 trending model page to find the abstract of the model"
    )
    async for chunk in agent.arun_stream(query=query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
