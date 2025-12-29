"""Example A2A server for a LangGraphAgent Weather Service.

This server instantiates a LangGraphAgent with weather lookup capabilities and serves it
via the A2A protocol using the proper A2A server setup with LangGraphA2AExecutor.

To run this server:
    python examples/hello_world_a2a_langgraph_server.py

It will listen on http://localhost:8001 by default.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools import weather_tool_langchain as weather_tool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_AGENT_NAME = "WeatherAgent"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8001, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the LangGraph Weather A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A weather agent that provides weather information for cities.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="weather",
                name="Weather Lookup",
                description="Provides current weather information for cities.",
                examples=["What's the weather in Tokyo?", "Get weather for London"],
                tags=["weather"],
            )
        ],
        tags=["weather"],
    )

    llm = ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True)
    tools = [weather_tool]

    langgraph_agent = LangGraphAgent(
        name=SERVER_AGENT_NAME,
        instruction=(
            "You are a weather agent that provides weather information for cities. "
            "Always use the weather_tool for looking up weather data. "
            "Format your responses clearly and professionally."
        ),
        model=llm,
        tools=tools,
        enable_a2a_token_streaming=True,
    )

    app = langgraph_agent.to_a2a(agent_card=agent_card)

    logger.info("A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
