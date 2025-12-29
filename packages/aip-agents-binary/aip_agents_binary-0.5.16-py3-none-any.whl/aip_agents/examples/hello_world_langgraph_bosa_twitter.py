"""Minimal LangGraph agent with bosa support example demonstrating asynchronous run.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.tools import BOSA_AUTOMATED_TOOLS


async def langgraph_bosa_example():
    """Demonstrates the LangGraphAgent's arun method."""
    model = ChatOpenAI(model="gpt-4.1", temperature=0)
    agent_name = "BOSAConnectorTwitterAgent"

    langgraph_agent = LangGraphAgent(
        name=agent_name,
        instruction="You are a helpful assistant that use BOSA connector to connect with Twitter API.",
        model=model,
        tools=BOSA_AUTOMATED_TOOLS["twitter"],
    )

    query = "Get 3 tweets about the latest Air India Incident"
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
    asyncio.run(langgraph_bosa_example())
