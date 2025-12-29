from _typeshed import Incomplete
from aip_agents.agent import LangChainAgent as LangChainAgent
from aip_agents.examples.tools import google_serper_tool as google_serper_tool, mock_retrieval_tool as mock_retrieval_tool, time_tool as time_tool
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int):
    """Runs the LangChain Mock Retrieval and Google Search A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
