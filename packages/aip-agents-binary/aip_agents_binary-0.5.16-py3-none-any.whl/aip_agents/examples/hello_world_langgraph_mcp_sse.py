"""Example showing LangGraph agent with MCP tools integration.

Authors:
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_sse


async def main():
    """Demonstrates the LangGraphAgent with MCP tools via SSE transport."""
    langgraph_agent = LangGraphAgent(
        name="langgraph_mcp_example",
        instruction="""You are a helpful assistant that can provide weather forecasts.
        For weather, specify the day in lowercase (e.g., 'monday').""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
        tools=[],
    )
    langgraph_agent.add_mcp_server(mcp_config_sse)

    query = "What's the weather forecast for monday?"  # Uses MCP weather tool

    print(f"\nQuery: {query}")
    response = await langgraph_agent.arun(query=query)
    print(f"Response: {response['output']}")


if __name__ == "__main__":
    asyncio.run(main())
