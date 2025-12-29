"""Example showing LangChain agent with MCP tools integration.

Transport: Streamable HTTP
Streaming: Yes

This example demonstrates how to create a LangChain agent that can use tools
from MCP servers via Streamable HTTP transport while streaming the response
in real-time.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_http


async def main():
    """Demonstrates the LangChainAgent with MCP tools via Streamable HTTP transport and streaming capabilities."""
    langchain_agent = LangChainAgent(
        name="langchain_mcp_stream_example",
        instruction="""You are a helpful assistant that can browse the web.""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
    )
    langchain_agent.add_mcp_server(mcp_config_http)

    async for chunk in langchain_agent.arun_stream(query="What's the latest news about FC Barcelona?"):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)

    # run again to make sure it use persistent session
    async for chunk in langchain_agent.arun_stream(query="What's the latest news about UEFA Champions League?"):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
