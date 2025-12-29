"""Example demonstrating a multi-agent setup with a CoordinatorAgent.

This example showcases:
1. How to define multiple specialized agents (WeatherAgent, MathAgent).
2. How to set up a CoordinatorAgent that can delegate to these specialized agents.
3. How the CoordinatorAgent uses dynamically created tools to call sub-agents.
4. How the CoordinatorAgent can delegate tasks to the appropriate sub-agents.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from dotenv import load_dotenv

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools import weather_tool_langchain as weather_tool
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers

load_dotenv(override=True)


async def main():
    """Main function demonstrating the multi-agent setup with Lang."""
    # llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    llm = "openai/gpt-4o"

    # --- Agent Definitions (tools and sub_agents inlined) ---
    weather_agent = LangGraphAgent(
        name="WeatherAgent",
        instruction="You are a weather expert. You must use the get_weather tool to find weather information.",
        model=llm,
        tools=[weather_tool],
    )

    math_agent = LangGraphAgent(
        name="MathAgent",
        instruction=(
            "You are a math expert. You must use the 'add_numbers' tool to perform addition. "
            "The tool takes two integer arguments: 'a' and 'b'.\n"
            "For example, to add 5 and 7, you would call add_numbers(a=5, b=7)."
        ),
        model=llm,
        tools=[add_numbers],
    )

    coordinator_agent = LangGraphAgent(
        name="CoordinatorAgent",
        instruction=(
            "You are a coordinator agent. Your primary role is to delegate tasks to specialized agents. "
            "Based on the user's query, decide which agent (WeatherAgent or MathAgent) is best suited. "
            "If a query involves multiple aspects, delegate accordingly. Synthesize their responses."
        ),
        model=llm,
        agents=[weather_agent, math_agent],
    )

    print("--- Agents Initialized ---")

    query = "What is the weather in Tokyo and what is 5 + 7?"
    print(f"\n--- Running query: {query} ---")
    response = await coordinator_agent.arun(query=query)
    print(f"Response: {response.get('output')}")


if __name__ == "__main__":
    asyncio.run(main())
