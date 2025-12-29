"""Example showing LangChain agent with MCP tools integration and streaming capabilities using stdio transport.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_stdio


async def main():
    """Demonstrates the LangChainAgent with MCP tools via stdio transport and streaming capabilities."""
    langchain_agent = LangChainAgent(
        name="langchain_mcp_stream_example",
        instruction="""You are a helpful assistant that can provide weather forecasts.
        For weather, specify the day in lowercase (e.g., 'monday').""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
    )
    langchain_agent.add_mcp_server(mcp_config_stdio)

    full_response = ""
    async for chunk in langchain_agent.arun_stream(
        query="What's the weather forecast for monday?",
    ):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
            full_response += chunk
        elif isinstance(chunk, dict) and "messages" in chunk:
            print("\n(Stream finished with final state object)")
        elif isinstance(chunk, dict):
            pass

    print(full_response)


if __name__ == "__main__":
    asyncio.run(main())
