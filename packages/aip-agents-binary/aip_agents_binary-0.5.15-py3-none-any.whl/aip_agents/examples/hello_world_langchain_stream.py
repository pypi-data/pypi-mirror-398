"""Minimal LangChain agent example demonstrating streaming capabilities.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)

"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers


async def langchain_stream_example():
    """Demonstrates the LangChainAgent's arun_stream method with async execution."""
    agent = LangChainAgent(
        name="LangChainStreamingCalculator",
        instruction="You are a helpful calculator assistant that can add numbers. "
        "When asked to add numbers, use the add_numbers tool. "
        "Explain your steps clearly for streaming demonstration.",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
        tools=[add_numbers],
    )

    # Stream the response chunks
    async for chunk in agent.arun_stream(
        query="What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    ):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(langchain_stream_example())
