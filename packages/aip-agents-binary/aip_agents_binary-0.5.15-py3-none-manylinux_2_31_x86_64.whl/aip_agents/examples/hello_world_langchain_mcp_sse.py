"""Example showing LangChain agent with MCP tools integration using SSE transport.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.mcp_configs.configs import mcp_config_sse


async def main():
    """Demonstrates the LangChainAgent with MCP tools via SSE transport."""
    langchain_agent = LangChainAgent(
        name="langchain_mcp_example",
        instruction=(
            "You are a helpful assistant that can browse the web. If you are blocked by captcha, try another website."
        ),
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
    )
    langchain_agent.add_mcp_server(mcp_config_sse)

    response = await langchain_agent.arun(query="What's the rating of the movie 'The Matrix'? browse it")
    print(response["output"])
    print("-" * 50)
    response = await langchain_agent.arun(query="When is the next solar eclipse?, browse it")
    print(response["output"])


if __name__ == "__main__":
    asyncio.run(main())
