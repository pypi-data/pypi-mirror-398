"""Minimal LangGraph agent example demonstrating streaming capabilities."""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers


async def langgraph_stream_example():
    """Demonstrates the LangGraphAgent's arun_stream method."""
    model = ChatOpenAI(model="gpt-4.1", temperature=0)
    tools = [add_numbers]
    agent_name = "LangGraphArithmeticStreamAgent"

    langgraph_agent = LangGraphAgent(
        name=agent_name,
        instruction="""You are a helpful assistant that can add two numbers using the add_numbers tool
        and stream the results.""",
        model=model,
        tools=tools,
    )

    # Use the same query as in the non-streaming LangGraph example
    query = "What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun_stream...")
    stream_thread_id = "lgraph_arith_stream_example"
    async for chunk in langgraph_agent.arun_stream(
        query=query, configurable={"configurable": {"thread_id": stream_thread_id}}
    ):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)  # AI message parts, print live

    print("\n\n--- End of LangGraph Stream Example ---")


if __name__ == "__main__":
    # OPENAI_API_KEY should be set in the environment.
    asyncio.run(langgraph_stream_example())
