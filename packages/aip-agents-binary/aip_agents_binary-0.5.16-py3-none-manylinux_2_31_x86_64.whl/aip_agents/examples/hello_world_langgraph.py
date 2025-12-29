"""Minimal LangGraph agent example demonstrating asynchronous run."""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers


async def langgraph_example():
    """Demonstrates the LangGraphAgent's arun method."""
    model = ChatOpenAI(model="gpt-4.1", temperature=0)
    tools = [add_numbers]
    agent_name = "LangGraphArithmeticAgent"

    langgraph_agent = LangGraphAgent(
        name=agent_name,
        instruction="You are a helpful assistant that can add two numbers using the add_numbers tool.",
        model=model,
        tools=tools,
    )

    query = "What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun...")
    response = await langgraph_agent.arun(
        query=query,
        configurable={"configurable": {"thread_id": "lgraph_arith_example_arun"}},
    )
    print(f"[arun] Final Response: {response['output']}")
    print("--- End of LangGraph Example ---")


if __name__ == "__main__":
    # OPENAI_API_KEY should be set in the environment.
    asyncio.run(langgraph_example())
