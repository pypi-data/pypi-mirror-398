"""Minimal example demonstrating the GoogleADKAgent's streaming capabilities with async execution.

This example shows how to use the arun_stream method to process responses in real-time
with Google's Agent Development Kit (ADK).
"""

import asyncio

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.tools.adk_arithmetic_tools import add_numbers


async def google_adk_example_stream():
    """Demonstrates the GoogleADKAgent's arun_stream method."""
    agent_name = "GoogleADKStreamingCalculator"

    # Create the agent with simplified instructions for streaming
    agent = GoogleADKAgent(
        name=agent_name,
        instruction="""You are a calculator assistant. When asked math problems,
        extract numbers and call add_numbers tool to add them.
        Explain your steps clearly for streaming demonstration.""",
        model="gemini-2.0-flash",
        tools=[add_numbers],
        max_iterations=5,  # Allow multiple tool calls if needed
    )

    # Use the same query as in LangGraph example for consistency
    query = "What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun_stream...")
    print("Streaming response:")

    # Stream the response chunks
    async for chunk in agent.arun_stream(query=query):
        print(chunk, end="", flush=True)

    print("\n--- End of Google ADK Streaming Example ---")


if __name__ == "__main__":
    asyncio.run(google_adk_example_stream())
