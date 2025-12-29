from _typeshed import Incomplete
from aip_agents.agent import LangGraphReactAgent as LangGraphReactAgent
from aip_agents.examples.hello_world_a2a_langchain_server import SERVER_AGENT_NAME as SERVER_AGENT_NAME
from aip_agents.examples.tools.langchain_currency_exchange_tool import CurrencyExchangeTool as CurrencyExchangeTool
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete

def main(host: str, port: int):
    """Runs the LangChain Currency Exchange A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
