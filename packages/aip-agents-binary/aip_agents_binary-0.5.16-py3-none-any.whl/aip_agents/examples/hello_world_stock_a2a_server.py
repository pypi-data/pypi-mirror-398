"""Stock Market A2A Server Example.

This server provides stock market information and can be used as an A2A agent.

To run:
    python aip_agents/examples/hello_world_stock_a2a_server.py --port 8002

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.stock_tools import StockNewsInput, StockPriceInput, get_stock_news, get_stock_price
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_AGENT_NAME = "StockAgent"


stock_tools: list[BaseTool] = [get_stock_price, get_stock_news]


@click.command()
@click.option("--host", "host", default="0.0.0.0", help="Host to bind the server to.")
@click.option("--port", "port", default=8002, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the StockAgent A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="Provides stock market information including prices and news.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True, tools=True),
        skills=[
            AgentSkill(
                id="get_stock_price",
                name="Get Stock Price",
                description="Retrieves the current stock price and performance data for a given symbol.",
                examples=["What's the price of AAPL?", "Stock price for MSFT"],
                tags=["finance", "stocks", "price"],
                input_schema=StockPriceInput.model_json_schema(),
            ),
            AgentSkill(
                id="get_stock_news",
                name="Get Stock News",
                description="Fetches recent news articles for a specified stock symbol.",
                examples=[
                    "Latest news for GOOGL",
                    "Stock news for TSLA over last 3 days",
                ],
                tags=["finance", "stocks", "news"],
                input_schema=StockNewsInput.model_json_schema(),
            ),
        ],
        tags=["finance", "stocks"],
    )

    # For A2A, the LLM is used by the *client* agent to decide to call this agent.
    # This agent itself just executes its tools based on the A2A request.
    # However, LangGraphAgent requires an LLM, so we provide a basic one.
    llm = ChatOpenAI(
        model="gpt-4.1",
        temperature=0,
        streaming=True,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    langgraph_agent = LangGraphAgent(
        name=SERVER_AGENT_NAME,
        instruction="You are a Stock Agent. You can get stock prices and news. Use your tools to answer user queries.",
        model=llm,
        tools=stock_tools,
        verbose=True,
    )

    app = langgraph_agent.to_a2a(
        agent_card=agent_card,
    )

    logger.info("A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
