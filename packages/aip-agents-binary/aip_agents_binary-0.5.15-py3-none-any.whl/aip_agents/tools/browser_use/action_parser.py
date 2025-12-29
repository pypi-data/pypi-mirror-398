"""Helper utilities for parsing browser-use agent actions.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from typing import Any

from browser_use.agent.views import ActionResult, AgentOutput
from browser_use.controller.registry.views import ActionModel

from aip_agents.tools.browser_use.types import ToolCallInfo
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class ActionParser:
    """Dedicated class for parsing agent actions with improved error handling."""

    @staticmethod
    def extract_actions(
        model_output: AgentOutput | None, last_result: list[ActionResult] | None = None
    ) -> list[ToolCallInfo]:
        """Extract action information from model output.

        Args:
            model_output: The model output containing action information.
            last_result: The last result from the agent state for output extraction.

        Returns:
            list[ToolCallInfo]: Structured action information.
        """
        if model_output is None or getattr(model_output, "action", None) is None:
            return []

        actions = model_output.action
        outputs = ActionParser._extract_outputs_from_result(last_result)

        return [ActionParser._parse_single_action(action_model, outputs, i) for i, action_model in enumerate(actions)]

    @staticmethod
    def _extract_outputs_from_result(last_result: list[ActionResult] | None) -> list[str]:
        """Extract output strings from agent result.

        Args:
            last_result: The last result from the agent state for output extraction.

        Returns:
            list[str]: List of output strings.
        """
        if not last_result:
            return []

        outputs: list[str] = []
        for result in last_result:
            if result.extracted_content:
                outputs.append(result.extracted_content)
            elif result.error:
                outputs.append(f"Error: {result.error}")
            else:
                outputs.append("")

        return outputs

    @staticmethod
    def _parse_single_action(action_model: ActionModel, outputs: list[str], index: int) -> ToolCallInfo:
        """Parse a single action model into ToolCallInfo.

        Args:
            action_model: The action model to parse.
            outputs: List of output strings.
            index: Index of the action in the outputs list.

        Returns:
            ToolCallInfo: Parsed action information.
        """
        try:
            specific_action = action_model.root
            action_data: dict[str, Any] = specific_action.model_dump(exclude_unset=True)

            tool_name = list(action_data.keys())[0]
            tool_args = action_data[tool_name]

            if not isinstance(tool_args, dict):
                tool_args = {"value": tool_args}

            output = outputs[index] if index < len(outputs) else ""

            return ToolCallInfo(name=tool_name, args=tool_args, output=output)

        except Exception as exc:
            logger.warning("Error parsing action structure: %s", exc)
            return ToolCallInfo(
                name="parsing_error",
                args={"error": str(exc)},
                output=outputs[index] if index < len(outputs) else "",
            )


__all__ = ["ActionParser"]
