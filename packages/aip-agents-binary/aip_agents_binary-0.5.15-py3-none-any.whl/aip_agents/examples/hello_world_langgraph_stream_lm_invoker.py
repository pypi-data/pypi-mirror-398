"""Minimal LangChain agent example demonstrating streaming capabilities.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio

import dotenv

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers

dotenv.load_dotenv(override=True)


async def main():
    """Demonstrates the LangChainAgent's arun_stream method with async execution."""
    agent = LangChainAgent(
        name="LangChainStreamingCalculator",
        instruction="You are a helpful calculator assistant that can add numbers. "
        "When asked to add numbers, use the add_numbers tool. "
        "Explain your steps clearly for streaming demonstration.",
        model="openai/gpt-4.1",
        tools=[add_numbers],
    )

    # Stream the response chunks
    async for chunk in agent.arun_stream(
        query="What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    ):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
