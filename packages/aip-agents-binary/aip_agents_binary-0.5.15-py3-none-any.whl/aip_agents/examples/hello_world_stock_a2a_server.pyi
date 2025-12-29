from _typeshed import Incomplete
from aip_agents.agent import LangGraphAgent as LangGraphAgent
from aip_agents.examples.tools.stock_tools import StockNewsInput as StockNewsInput, StockPriceInput as StockPriceInput, get_stock_news as get_stock_news, get_stock_price as get_stock_price
from aip_agents.utils.logger import get_logger as get_logger
from langchain_core.tools import BaseTool as BaseTool

logger: Incomplete
SERVER_AGENT_NAME: str
stock_tools: list[BaseTool]

def main(host: str, port: int):
    """Runs the StockAgent A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
