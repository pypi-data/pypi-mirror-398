"""Example A2A server for a LangGraphAgent Weather Service.

This server instantiates a LangGraphAgent with weather lookup capabilities and serves it
via the A2A protocol using the proper A2A server setup with LangGraphA2AExecutor.

To run this server:
    python examples/hello_world_a2a_langgraph_server.py

It will listen on http://localhost:8001 by default.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.image_artifact_tool import ImageArtifactTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_AGENT_NAME = "ArtifactAgent"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8999, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the LangGraph Artifact Generation A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="An agent that can generate data tables and images as downloadable artifacts.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="table_generation",
                name="Table Generation",
                description="Generates data tables and provides them as downloadable CSV files.",
                examples=["Generate a data table with 5 rows and 3 columns", "Create a table with customer data"],
                tags=["table", "data", "csv"],
            ),
            AgentSkill(
                id="image_generation",
                name="Image Generation",
                description="Creates simple images and provides them as downloadable PNG files.",
                examples=["Create an image", "Generate a simple graphic"],
                tags=["image", "graphics", "png"],
            ),
        ],
        tags=["artifacts", "files", "generation"],
    )

    table_tool = TableGeneratorTool()
    image_tool = ImageArtifactTool()
    tools = [table_tool, image_tool]

    langgraph_agent = LangGraphAgent(
        name=SERVER_AGENT_NAME,
        instruction=(
            "You are a helpful assistant that can generate data tables and images. "
            "When users ask for data tables, use the table_generator tool to create both a preview "
            "and a downloadable CSV file. When users ask for images, use the image_generator tool "
            "to create visual content. Always provide clear descriptions of what you're generating."
            "Format your responses clearly and professionally."
        ),
        model="openai/gpt-4.1",
        tools=tools,
    )

    app = langgraph_agent.to_a2a(agent_card=agent_card)

    logger.info("A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
