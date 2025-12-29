"""Backward-compatible shim for the memory search tool module.

The actual implementations now live under ``aip_agents.tools.memory_search``.
Importing from this module continues to work for existing callers.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from aip_agents.tools.memory_search import (
    MEMORY_SEARCH_TOOL_NAME,
    LongTermMemorySearchInput,
    LongTermMemorySearchTool,
    Mem0SearchInput,
    Mem0SearchTool,
    MemoryConfig,
)

__all__ = [
    "MemoryConfig",
    "LongTermMemorySearchInput",
    "LongTermMemorySearchTool",
    "Mem0SearchInput",
    "Mem0SearchTool",
    "MEMORY_SEARCH_TOOL_NAME",
]
