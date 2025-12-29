"""Example A2A server for a LangflowAgent.

This server instantiates a LangflowAgent and serves it via the A2A protocol
using the proper A2A server setup.

To run this server:
    python examples/hello_world_a2a_langflow_server.py

It will listen on http://localhost:8787 by default.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from aip_agents.agent.langflow_agent import LangflowAgent
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_AGENT_NAME = "LangflowA2AServer"
load_dotenv()


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8787, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the Langflow A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A Langflow agent that provides AI assistance through A2A protocol",
        url=f"http://{host}:{port}",
        version="1.0.0",
        author="AIP Agents SDK",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="general_assistance",
                name="General Assistance",
                description="Provides general AI assistance through Langflow",
                examples=[
                    "Answer questions about any topic",
                    "Help with writing and editing",
                    "Provide explanations and analysis",
                    "Creative content generation",
                ],
                tags=["ai", "assistant", "langflow", "chat"],
            )
        ],
        tags=["langflow", "ai", "assistant"],
    )

    # Create the Langflow agent
    langflow_agent = LangflowAgent(
        name=SERVER_AGENT_NAME,
        flow_id="6dd45ac0-5c05-44c1-9825-66c6c6e516f7",
        description="A Langflow agent that provides AI assistance through A2A protocol",
        base_url="https://langflow.obrol.id",
    )

    app = langflow_agent.to_a2a(agent_card=agent_card)

    logger.info("A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
