"""Metadata utilities module.

This module contains utilities for creating and handling metadata for A2A communication.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from aip_agents.utils.metadata.activity_metadata_helper import (
    DEFAULT_ACTIVITY_INFO,
    _format_tool_or_subagent_name,
    create_tool_activity_info,
)
from aip_agents.utils.metadata.schemas import Activity, ActivityDataType, Thinking
from aip_agents.utils.metadata.thinking_metadata_helper import (
    FINAL_THINKING_INFO,
)

__all__ = [
    "Activity",
    "ActivityDataType",
    "Thinking",
    "create_tool_activity_info",
    "DEFAULT_ACTIVITY_INFO",
    "_format_tool_or_subagent_name",
    "FINAL_THINKING_INFO",
]
