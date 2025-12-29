"""Minimal LangChain agent example demonstrating asynchronous run."""

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.langchain_weather_tool import weather_tool

if __name__ == "__main__":
    langchain_agent = LangChainAgent(
        name="LangChainWeatherAgent",
        instruction="You are a helpful assistant that can get the weather in a given city using the get_weather tool.",
        model="openai/gpt-4o",
        tools=[weather_tool],
    )

    response = langchain_agent.run(query="What is the weather in Tokyo?")
    print(response["output"])
