"""Thinking metadata helper utilities.

Provides helpers to build thinking messages.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from aip_agents.utils.metadata.schemas.thinking_schema import Thinking, ThinkingDataType


def _create_thinking_info(
    message: str,
    top_level_id: str = "default_thinking_id",
    data_type: ThinkingDataType = "thinking",
) -> dict[str, str]:
    r"""Create thinking info payload with a customizable ID, data_type, and message.

    Args:
        message: The message content for the thinking info.
        top_level_id: The ID for the thinking info. Defaults to "default_thinking_id".
        data_type: The type of the data. Defaults to "thinking".

    Returns a dict with top-level id and data_value as JSON string:
      {
        "data_type": "thinking",
        "id": "<id>",
        "data_value": "**title**\n\n..."
      }
    """
    thinking = Thinking(data_type=data_type, id=top_level_id, data_value=message)
    return thinking.model_dump()


# Exported default/terminal thinking info
FINAL_THINKING_INFO = _create_thinking_info(
    "**All process has finished**\n\nThe tasks have been finished.", "default_thinking_id"
)
