from aip_agents.agent.langflow_agent import LangflowAgent as LangflowAgent
from aip_agents.clients.langflow import LangflowApiClient as LangflowApiClient

async def fetch_flow_id() -> tuple[str, str]:
    """Fetch available flows and return the first flow ID and name."""
async def create_agent(flow_id: str, flow_name: str) -> LangflowAgent:
    """Create and configure the Langflow agent.

    Args:
        flow_id (str): The flow ID to use for the agent.
        flow_name (str): The name of the flow.

    Returns:
        LangflowAgent: The configured Langflow agent.
    """
async def demonstrate_regular_execution(agent: LangflowAgent) -> None:
    """Demonstrate regular execution.

    Args:
        agent (LangflowAgent): The Langflow agent to demonstrate with.
    """
async def demonstrate_streaming(agent: LangflowAgent) -> None:
    """Demonstrate streaming execution.

    Args:
        agent (LangflowAgent): The Langflow agent to demonstrate with.
    """
async def demonstrate_session_management(agent: LangflowAgent) -> None:
    """Demonstrate session management.

    Args:
        agent (LangflowAgent): The Langflow agent to demonstrate with.
    """
async def main() -> None:
    """Demonstrate basic Langflow agent usage."""
