from _typeshed import Incomplete
from aip_agents.agent.langflow_agent import LangflowAgent as LangflowAgent
from aip_agents.schema.agent import A2AClientConfig as A2AClientConfig
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete

async def main() -> None:
    """Main function demonstrating the Langflow client with streaming A2A capabilities."""
