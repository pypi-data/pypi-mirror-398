"""Example A2A server for a Google ADK Weather Service.

This server instantiates a Google ADK agent with weather lookup capabilities and serves it
via the A2A protocol using GoogleADKAgent's to_a2a method.

To run this server:
    python examples/hello_world_a2a_google_adk_server.py

It will listen on http://localhost:8002 by default.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.examples.tools.adk_weather_tool import weather_tool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_AGENT_NAME = "GoogleADKWeatherAgent"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8002, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the Google ADK Weather A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A weather agent based on Google ADK that provides weather information for cities.",
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

    # Create a Google ADK agent
    agent = GoogleADKAgent(
        model="gemini-2.0-flash",
        name=SERVER_AGENT_NAME,
        description="A weather agent that provides weather information for cities.",
        instruction="""You are a weather agent that provides weather information for cities.
        Always use the weather_tool for looking up weather data. Format your responses clearly and professionally.""",
        tools=[weather_tool],
    )

    # Convert the agent to an A2A server directly
    app = agent.to_a2a(agent_card=agent_card)

    uvicorn.run(app, host=host, port=port)
    logger.info("A2A application configured. Starting Uvicorn server...")


if __name__ == "__main__":
    main()
