from _typeshed import Incomplete
from aip_agents.agent import LangChainAgent as LangChainAgent
from aip_agents.examples.tools.langgraph_streaming_tool import LangGraphStreamingTool as LangGraphStreamingTool
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int):
    """Runs the LangGraph Agent Wrapper A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
