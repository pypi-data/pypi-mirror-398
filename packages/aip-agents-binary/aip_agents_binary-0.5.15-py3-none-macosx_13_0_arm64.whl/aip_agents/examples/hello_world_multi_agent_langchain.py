"""Example demonstrating a multi-agent setup with a Coordinator Agent.

This example showcases:
1. How to define multiple specialized agents (Weather Agent, Math Agent).
2. How to set up a Coordinator Agent that can delegate to these specialized agents.
3. How the Coordinator Agent uses dynamically created tools to call sub-agents.
4. How the Coordinator Agent can delegate tasks to the appropriate sub-agents.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools import weather_tool_langchain as weather_tool
from aip_agents.examples.tools.langchain_arithmetic_tools import add_numbers


async def main():
    """Main function demonstrating the multi-agent setup with LangChainAgent."""
    model = ChatOpenAI(model="gpt-4.1", temperature=0)

    weather_agent = LangChainAgent(
        name="Weather Agent",
        instruction="You are a weather expert. You must use the get_weather tool to find weather information.",
        model=model,
        tools=[weather_tool],
    )

    math_agent = LangChainAgent(
        name="Math Agent",
        instruction="You are a math expert. Use the 'add_numbers' tool to add two numbers.",
        model=model,
        tools=[add_numbers],
    )

    coordinator_agent = LangChainAgent(
        name="Coordinator Agent",
        instruction="Delegate each query to suitable agent (Weather Agent or Math Agent) and combine their results.",
        model=model,
        agents=[weather_agent, math_agent],
    )

    query = "What is the weather in Tokyo and what is 5 + 7?"
    response = await coordinator_agent.arun(query=query)
    print(f"Response: {response.get('output')}")


if __name__ == "__main__":
    asyncio.run(main())
