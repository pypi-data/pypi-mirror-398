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
from aip_agents.examples.tools import google_serper_tool, mock_retrieval_tool, time_tool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


SERVER_AGENT_NAME = "Mock Retrieval Tool and Google Search Tool Server"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8455, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the LangChain Mock Retrieval and Google Search A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A server that provides mock retrieval data and mock google search information",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="mock_retrieval",
                name="Mock Data Retrieval",
                description="Retrieves mock data and returns references for testing.",
                examples=["Retrieve mock data", "Get test information"],
                tags=["retrieval", "mock"],
            ),
            AgentSkill(
                id="google_serper",
                name="Mock Google Search",
                description="Provides mock google search information.",
                examples=["What is NeoAI?", "Get NeoAI"],
                tags=["google serper"],
            ),
        ],
        tags=["retrieval", "mock", "google serper"],
    )

    time_delegate_agent = LangChainAgent(
        name="TimeLookupAgent",
        instruction="""You are a specialized time lookup assistant.
        Always answer user queries by calling the `time_tool` to obtain the most up-to-date information.""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True),
        tools=[time_tool()],
    )

    google_delegate_agent = LangChainAgent(
        name="GoogleSerperAgent",
        instruction="""You are a specialized research assistant that must use the `google_serper_tool`
        for every query. Provide concise summaries using the tool output.""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True),
        tools=[google_serper_tool()],
    )

    langchain_agent = LangChainAgent(
        name=SERVER_AGENT_NAME,
        instruction="""You are a coordinator agent that delegates research tasks to sub-agents but uses
        mock_retrieval_tool directly. For research questions, delegate to `GoogleSerperAgent`.
        For retrieval queries, use the mock_retrieval_tool directly. Synthesize their responses
        and present a clear combined answer.""",
        model=ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True),
        tools=[mock_retrieval_tool()],  # Direct tool usage
        agents=[time_delegate_agent, google_delegate_agent],  # Delegation for others
    )

    app = langchain_agent.to_a2a(
        agent_card=agent_card,
    )

    uvicorn.run(app, host=host, port=port)
    logger.info("A2A application configured. Starting Uvicorn server...")


if __name__ == "__main__":
    main()
