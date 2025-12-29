"""Minimal example demonstrating the GoogleADKAgent with tool usage and async operation.

This example shows how to create a simple calculator agent using Google's ADK
which automatically handles tool calling and conversation flow.
"""

import asyncio

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.tools.adk_arithmetic_tools import sum_numbers


async def google_adk_example():
    """Demonstrates the GoogleADKAgent's arun method."""
    agent_name = "GoogleADKCalculator"

    # Create the agent with simplified instructions and our tool
    agent = GoogleADKAgent(
        name=agent_name,
        instruction="""You are a calculator assistant. When asked math problems,
        extract numbers and call sum_numbers tool to add them.
        For multi-step problems, use multiple tool calls.""",
        model="gemini-2.0-flash",
        tools=[sum_numbers],
        max_iterations=5,  # Allow multiple tool calls if needed
    )

    # Use the same query as in LangGraph example for consistency
    query = "What is the sum of 23 and 47? And then add 10 to that, then add 5 more."
    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun...")
    response = await agent.arun(query=query)
    print(f"[arun] Final Response: {response.get('output')}")
    print("--- End of Google ADK Example ---")


if __name__ == "__main__":
    # GOOGLE_API_KEY should be set in the environment.
    asyncio.run(google_adk_example())
