from _typeshed import Incomplete
from aip_agents.agent import LangGraphAgent as LangGraphAgent
from aip_agents.examples.tools.image_artifact_tool import ImageArtifactTool as ImageArtifactTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool as TableGeneratorTool
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SERVER_AGENT_NAME: str

def main(host: str, port: int):
    """Runs the LangGraph Artifact Generation A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
