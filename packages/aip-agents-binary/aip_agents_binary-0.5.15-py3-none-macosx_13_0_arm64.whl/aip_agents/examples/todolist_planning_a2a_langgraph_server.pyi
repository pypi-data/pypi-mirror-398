from _typeshed import Incomplete
from aip_agents.agent import LangGraphReactAgent as LangGraphReactAgent
from aip_agents.examples.tools.serper_tool import MockGoogleSerperTool as MockGoogleSerperTool
from aip_agents.examples.tools.stock_tools import get_stock_price as get_stock_price
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int) -> None:
    """Run an A2A server with a planning-enabled LangGraphReactAgent.

    The agent has TodoListMiddleware attached via planning=True and will
    expose the write_todos_tool over A2A with token streaming enabled.

    Args:
        host: The host to bind the server to.
        port: The port to bind the server to.
    """
