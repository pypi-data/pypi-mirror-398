from _typeshed import Incomplete
from aip_agents.agent import LangGraphAgent as LangGraphAgent
from aip_agents.examples.tools.mock_retrieval_tool import MockRetrievalTool as MockRetrievalTool
from aip_agents.examples.tools.pii_demo_tools import get_customer_info as get_customer_info, get_employee_data as get_employee_data, get_user_profile as get_user_profile
from aip_agents.examples.tools.random_chart_tool import RandomChartTool as RandomChartTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool as TableGeneratorTool
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int):
    """Runs the streaming comparison A2A server.

    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
    """
