"""Example A2A server for a LangGraph Agent Wrapper Service.

This server instantiates a LangChainAgent with the LangGraph agent wrapper tool that provides
time and weather forecast capabilities, and serves it via the A2A protocol with streaming support.

The agent can handle time queries and weather forecast requests for any day of the week.

To run this server:
    python examples/hello_world_a2a_langgraph_server_tool_streaming.py

It will listen on http://localhost:8003 by default.

Environment Variables Required:
    OPENAI_API_KEY: OpenAI API key for the LLM

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.langgraph_streaming_tool import LangGraphStreamingTool
from aip_agents.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

SERVER_AGENT_NAME = "TimeWeatherAgentLangGraph"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8003, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the LangGraph Agent Wrapper A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    # ruff: noqa: E501
    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A time and weather agent that can provide current time information and weather data for specific cities",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="time_queries",
                name="Time Information",
                description="Provides current time and date information in various formats.",
                examples=[
                    "What time is it now?",
                    "Get the current date and time",
                    "Show me the time in ISO format",
                    "What's the current timestamp?",
                ],
                tags=["time", "date", "timestamp"],
            ),
            AgentSkill(
                id="weather_info",
                name="Weather Information",
                description="Provides weather information for specific cities.",
                examples=[
                    "What's the weather in Jakarta?",
                    "Weather in Tokyo and Singapore",
                    "Check weather for New York",
                    "Get weather for London",
                ],
                tags=["weather", "city", "location"],
            ),
            AgentSkill(
                id="combined_queries",
                name="Time and Weather Combined",
                description="Handles queries that combine both time and weather information.",
                examples=[
                    "What time is it and what's the weather in Jakarta?",
                    "Current time and weather in Tokyo",
                    "Tell me the time and weather for Singapore",
                ],
                tags=["time", "weather", "combined"],
            ),
        ],
        tags=["time", "weather", "assistant"],
    )

    # Create the LangGraph streaming tool instance
    streaming_tool = LangGraphStreamingTool()

    langchain_agent = LangChainAgent(
        name=SERVER_AGENT_NAME,
        instruction="""You are a helpful time and weather assistant.

You can provide current time information and weather forecasts.

You have access to a specialized LangGraph agent that can:
- Get the current time and date in various formats
- Provide weather information for specific cities (Jakarta, Singapore, Tokyo, London, New York)
- Handle combined time and weather queries

When given a task:
1. Use the langgraph_streaming_tool to execute time and weather queries
2. Be specific about what information is requested
3. Provide clear, formatted responses about the time or weather information
4. For weather queries, specify the city name clearly

Always use the agent wrapper tool for time and weather requests. Format your responses clearly and professionally.""",
        model="openai/gpt-4.1",
        tools=[streaming_tool],
        tool_configs={"langgraph_streaming_tool": {"time_format": "%d-%m-%Y %H:%M:%S"}},
    )

    app = langchain_agent.to_a2a(
        agent_card=agent_card,
    )

    uvicorn.run(app, host=host, port=port)
    logger.info("A2A application configured. Starting Uvicorn server...")


if __name__ == "__main__":
    main()
