"""Multi-agent example using Google ADK with a coordinator agent.

This example demonstrates a coordinator agent that can delegate tasks to specialized agents.
"""

import asyncio

import nest_asyncio

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.tools.adk_arithmetic_tools import sum_numbers
from aip_agents.examples.tools.adk_weather_tool import get_weather

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


async def multi_agent_example():
    """Demonstrates multi-agent coordination with GoogleADKAgent."""
    # Create specialized agents
    weather_agent = GoogleADKAgent(
        name="WeatherAgent",
        instruction=(
            "You are a weather expert. You must use the weather_tool "
            "to find weather information for a given city. "
            "Always include the city name in your response."
        ),
        model="gemini-2.0-flash",
        tools=[get_weather],  # Use the get_weather function directly
        max_iterations=3,
    )

    math_agent = GoogleADKAgent(
        name="MathAgent",
        instruction=(
            "You are a math expert. You must use the sum_numbers tool to perform addition. "
            "The tool takes two integer arguments: 'a' and 'b'. "
            "For example, to add 5 and 7, you would call sum_numbers(a=5, b=7). "
            "Always state the numbers you're adding in your response."
        ),
        model="gemini-2.0-flash",
        tools=[sum_numbers],
        max_iterations=3,
    )

    # Create coordinator agent with access to specialized agents
    coordinator_agent = GoogleADKAgent(
        name="CoordinatorAgent",
        instruction=(
            "You are a helpful assistant that coordinates between specialized agents.\n"
            "When asked about weather, delegate to WeatherAgent.\n"
            "When asked to do math, delegate to MathAgent.\n"
            "If asked multiple questions, break them down and handle each one separately.\n"
            "Always be concise and helpful in your responses."
        ),
        model="gemini-2.0-flash",
        agents=[weather_agent, math_agent],
        max_iterations=3,
    )

    # Test weather query
    weather_query = "What is the weather in Tokyo?"
    print(f"\n--- Running query 1: {weather_query} ---")
    weather_response = await coordinator_agent.arun(query=weather_query)
    print(f"Weather Response: {weather_response.get('output')}")

    # Test math query
    math_query = "What is 5 + 7?"
    print(f"\n--- Running query 2: {math_query} ---")
    math_response = await coordinator_agent.arun(query=math_query)
    print(f"Math Response: {math_response.get('output')}")


if __name__ == "__main__":
    asyncio.run(multi_agent_example())
