from aip_agents.tools.browser_use.types import ToolCallInfo
from browser_use.agent.views import ActionResult, AgentOutput

__all__ = ['ActionParser']

class ActionParser:
    """Dedicated class for parsing agent actions with improved error handling."""
    @staticmethod
    def extract_actions(model_output: AgentOutput | None, last_result: list[ActionResult] | None = None) -> list[ToolCallInfo]:
        """Extract action information from model output.

        Args:
            model_output: The model output containing action information.
            last_result: The last result from the agent state for output extraction.

        Returns:
            list[ToolCallInfo]: Structured action information.
        """
