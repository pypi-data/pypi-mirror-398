"""Example showing Google ADK agent with MCP tools integration using stdio transport and streaming capabilities.

This example demonstrates how to create a Google ADK agent that can use tools
from MCP servers via stdio (standard input/output) transport while streaming the response
in real-time. The MCP server runs as a subprocess.

Authors:
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_stdio


async def main():
    """Demonstrates the GoogleADKAgent with MCP tools via stdio transport and streaming."""
    agent_name = "GoogleADKMCPStdioStream"

    agent = GoogleADKAgent(
        name=agent_name,
        instruction="""You are a helpful assistant that can provide weather forecasts.
        For weather, specify the day in lowercase (e.g., 'monday').
        Explain your steps clearly for streaming demonstration.""",
        model="gemini-2.0-flash",
        tools=[],
        max_iterations=5,
    )
    agent.add_mcp_server(mcp_config_stdio)

    query = "What's the weather forecast for monday?"  # Uses MCP weather tool

    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun_stream with MCP stdio tools...")
    print("Streaming response:")

    async for chunk in agent.arun_stream(query=query):
        print(chunk, end="", flush=True)

    print("\n--- End of Google ADK MCP Stdio Streaming Example ---")


if __name__ == "__main__":
    asyncio.run(main())
