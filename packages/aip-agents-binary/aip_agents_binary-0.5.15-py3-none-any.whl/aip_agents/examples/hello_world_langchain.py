"""Minimal LangChain agent example demonstrating asynchronous run."""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers


async def langchain_example():
    """Demonstrates the LangChainAgent's arun method."""
    langchain_agent = LangChainAgent(
        name="LangChainArithmeticAgent",
        instruction="You are a helpful assistant that can add two numbers using the add_numbers tool.",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
        tools=[add_numbers],
    )

    response = await langchain_agent.arun(
        query="What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    )
    print(response["output"])


if __name__ == "__main__":
    # OPENAI_API_KEY should be set in the environment.
    asyncio.run(langchain_example())
