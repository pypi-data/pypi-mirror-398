from _typeshed import Incomplete
from aip_agents.agent.langflow_agent import LangflowAgent as LangflowAgent
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int):
    """Runs the Langflow A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
