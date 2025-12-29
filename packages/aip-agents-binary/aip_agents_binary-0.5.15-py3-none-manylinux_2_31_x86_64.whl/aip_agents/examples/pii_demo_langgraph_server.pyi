from _typeshed import Incomplete
from aip_agents.agent import LangChainAgent as LangChainAgent
from aip_agents.examples.tools.pii_demo_tools import get_customer_info as get_customer_info, get_employee_data as get_employee_data, get_user_profile as get_user_profile
from aip_agents.utils.logger import LoggerManager as LoggerManager

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int):
    """Runs the PII Demo LangGraph A2A server.

    This server demonstrates PII handling capabilities including:
    - Automatic anonymization of sensitive data in tool outputs
    - Deanonymization of PII for tool inputs
    - Collision detection and resolution in parallel tool execution

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
