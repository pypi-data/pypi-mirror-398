from _typeshed import Incomplete
from aip_agents.agent import LangChainAgent as LangChainAgent
from aip_agents.schema.agent import AgentConfig as AgentConfig

DEEPINFRA_URL: str
MODEL_IDS: Incomplete
MODEL_CONFIGS: Incomplete

def make_agent(model_id):
    """Makes an agent with the given model id.

    Args:
        model_id: The model identifier to use for the agent.

    Returns:
        LangChainAgent: The configured agent instance.
    """
def print_help() -> None:
    """Prints available commands and their descriptions."""
def handle_switch_model(current_model):
    """Handles model switching. Returns (new_model, new_agent).

    Args:
        current_model: The currently active model identifier.

    Returns:
        tuple: (new_model, new_agent) where new_model is the selected model ID and new_agent is the configured agent instance.
    """
def main() -> None:
    """Runs the Hello World Model Switch CLI."""
