"""Example showing Google ADK agent with MCP tools integration using SSE transport and streaming capabilities.

This example demonstrates how to create a Google ADK agent that can use tools
from MCP servers via Server-Sent Events (SSE) transport while streaming the response
in real-time.

Authors:
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_sse


async def main():
    """Demonstrates the GoogleADKAgent with MCP tools via SSE transport and streaming."""
    agent_name = "GoogleADKMCPSSEStream"

    agent = GoogleADKAgent(
        name=agent_name,
        instruction="""You are a helpful assistant that can use playwright tools to browse the web.
        If a user ask something, you try to answer it by browsing the web via playwright tools
        Do not ask for clarification, just answer to the best of your ability using playwright tools.""",
        model="gemini-2.0-flash",
        tools=[],
        max_iterations=5,
    )
    agent.add_mcp_server(mcp_config_sse)

    query = "How many trophies did FC Barcelona win in 2024/2025 season?"

    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun_stream with MCP SSE tools...")
    print("Streaming response:")

    async for chunk in agent.arun_stream(query=query):
        print(chunk, end="", flush=True)

    print("\n--- End of Google ADK MCP SSE Streaming Example ---")


if __name__ == "__main__":
    asyncio.run(main())
