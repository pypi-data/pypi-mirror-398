from dataclasses import dataclass
from gllm_core.schema import Chunk
from langchain_core.messages import ToolMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.tools import BaseTool
from typing import Any

__all__ = ['ToolCallResult', 'ToolStorageParams']

@dataclass
class ToolCallResult:
    """Container for the results of a single tool call execution."""
    messages: list[ToolMessage]
    artifacts: list[dict[str, Any]]
    metadata_delta: dict[str, Any]
    references: list[Chunk]
    step_usage: UsageMetadata | None
    pii_mapping: dict[str, str] | None = ...

@dataclass
class ToolStorageParams:
    """Parameters required for automatically storing tool outputs."""
    tool: BaseTool
    tool_output: Any
    tool_call: dict[str, Any]
    tool_call_id: str
    resolved_args: dict[str, Any]
    state: dict[str, Any]
