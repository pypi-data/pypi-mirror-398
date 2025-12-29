"""Example A2A server demonstrating tool output management.

This server provides data generation and visualization capabilities,
demonstrating how tools can store and reference each other's outputs.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from aip_agents.agent import LangGraphReactAgent
from aip_agents.examples.tools.data_generator_tool import DataGeneratorTool
from aip_agents.examples.tools.data_visualization_tool import DataVisualizerTool
from aip_agents.storage.clients.minio_client import MinioConfig, MinioObjectStorage
from aip_agents.storage.providers.object_storage import ObjectStorageProvider
from aip_agents.utils.langgraph.tool_output_management import ToolOutputConfig, ToolOutputManager
from aip_agents.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

SERVER_AGENT_NAME = "DataVisualizationAgent"


@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=8885, help="Port to bind the server to")
def main(host: str, port: int):
    """Run the Data Visualization A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    # Create agent card
    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="Agent that generates and visualizes data with tool output references",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="data_generation",
                name="Data Generation",
                description="Generate sample datasets (sales, scores, growth)",
                examples=[
                    "Generate sales data with 5 points",
                    "Create test scores for 3 students",
                ],
                tags=["data"],
            ),
            AgentSkill(
                id="data_visualization",
                name="Data Visualization",
                description="Create charts from data (supports tool output references)",
                examples=[
                    "Create a bar chart from the sales data",
                    "Visualize test scores as a line chart",
                ],
                tags=["visualization"],
            ),
        ],
        tags=["data", "visualization"],
    )

    # Use environment-based MinIO configuration
    minio_config = MinioConfig.from_env()
    minio_client = MinioObjectStorage(minio_config)
    object_storage_provider = ObjectStorageProvider(
        client=minio_client,
        prefix="test_prefix",  # Unique test prefix
    )
    tool_output_config = ToolOutputConfig(
        storage_provider=object_storage_provider,
    )

    # Create agent with tool output management
    tool_output_manager = ToolOutputManager(tool_output_config)
    agent = LangGraphReactAgent(
        name=SERVER_AGENT_NAME,
        instruction="""You are a data visualization agent that can generate and visualize data.

You have access to these tools:
1. data_generator: Creates sample datasets (sales, scores, growth data)
2. data_visualizer: Creates charts from data, supporting tool output references

Always be explicit about what data you're generating and visualizing.""",
        model="openai/gpt-4.1",
        tools=[
            DataGeneratorTool(),
            DataVisualizerTool(),
        ],
        tool_output_manager=tool_output_manager,
    )

    # Create A2A app
    app = agent.to_a2a(agent_card=agent_card)

    # Run server
    uvicorn.run(app, host=host, port=port)
    logger.info("A2A application configured. Starting Uvicorn server...")


if __name__ == "__main__":
    main()
