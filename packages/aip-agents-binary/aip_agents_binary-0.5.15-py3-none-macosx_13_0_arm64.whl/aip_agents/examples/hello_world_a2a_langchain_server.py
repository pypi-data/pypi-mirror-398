"""Example A2A server for a LangChainAgent Weather Service.

This server instantiates a LangChainAgent with weather lookup capabilities and serves it
via the A2A protocol using the to_a2a convenience method.

To run this server:
    python examples/hello_world_a2a_langchain_server.py

It will listen on http://localhost:8001 by default.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.langchain_weather_tool import weather_tool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


SERVER_AGENT_NAME = "Weather Agent LangChain"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8001, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the LangChain Weather A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A weather agent that provides weather information for cities",
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

    langchain_agent = LangChainAgent(
        name=SERVER_AGENT_NAME,
        instruction="""You are a weather agent that provides weather information for cities.
        Always use the weather_tool for looking up weather data. Format your responses clearly and professionally.""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
        tools=[weather_tool],
    )

    app = langchain_agent.to_a2a(
        agent_card=agent_card,
    )

    uvicorn.run(app, host=host, port=port)
    logger.info("A2A application configured. Starting Uvicorn server...")


if __name__ == "__main__":
    main()
