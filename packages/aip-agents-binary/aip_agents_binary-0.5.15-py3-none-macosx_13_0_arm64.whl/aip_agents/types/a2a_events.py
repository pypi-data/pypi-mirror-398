"""Backward-compatible exports for A2A event schema.

Prefer importing from ``aip_agents.schema.a2a`` in new code.
"""

from aip_agents.schema.a2a import A2AEvent, A2AStreamEventType, ToolCallInfo, ToolResultInfo

__all__ = [
    "A2AStreamEventType",
    "A2AEvent",
    "ToolCallInfo",
    "ToolResultInfo",
]
