"""Example showing LangChain agent with MCP tools integration and streaming capabilities using SSE transport.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_sse


async def main():
    """Demonstrates the LangChainAgent with MCP tools via SSE transport and streaming capabilities."""
    langchain_agent = LangChainAgent(
        name="langchain_mcp_stream_example",
        instruction="""You are a helpful assistant that can browse the web using playwright tools.""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
    )
    langchain_agent.add_mcp_server(mcp_config_sse)

    full_response = ""
    async for chunk in langchain_agent.arun_stream(
        query="What are the result of Copa Del Rey Final in 2024/2025 season, browse it.",
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
