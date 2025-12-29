"""Example A2A server for a LangChainAgent Weather Service.

This server instantiates a LangChainAgent with weather lookup capabilities and serves it
via the A2A protocol using the to_a2a convenience method.

To run this server:
    python examples/a2a/langchain_server_example.py

It will listen on http://localhost:8001 by default.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from aip_agents.agent import LangGraphReactAgent
from aip_agents.examples.hello_world_a2a_langchain_server import SERVER_AGENT_NAME
from aip_agents.examples.tools.langchain_currency_exchange_tool import CurrencyExchangeTool
from aip_agents.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8885, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the LangChain Currency Exchange A2A server.

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
                id="currency_exchange",
                name="Currency Exchange",
                description="Provides current currency exchange information for cities.",
                examples=["What's the currency exchange in Tokyo?", "Get currency exchange for London"],
                tags=["currency_exchange"],
            )
        ],
        tags=["currency_exchange"],
    )

    agent = LangGraphReactAgent(
        name="CurrencyAgent",
        instruction="You are a currency exchange agent. Use the currency_exchange tool for conversions.",
        model="openai/gpt-4o-mini",
        tools=[CurrencyExchangeTool()],
        tool_configs={"currency_exchange": {"tenant_id": "premium_corp", "auth_key": "premium_key_123"}},
    )

    app = agent.to_a2a(
        agent_card=agent_card,
    )

    uvicorn.run(app, host=host, port=port)
    logger.info("A2A application configured. Starting Uvicorn server...")


if __name__ == "__main__":
    main()
