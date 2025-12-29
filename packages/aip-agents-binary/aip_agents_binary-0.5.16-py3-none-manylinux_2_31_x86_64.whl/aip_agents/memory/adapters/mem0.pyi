from aip_agents.memory.adapters.base_adapter import BaseMemoryAdapter as BaseMemoryAdapter
from aip_agents.memory.constants import MemoryDefaults as MemoryDefaults
from typing import Any

MemoryManager = Any

class Mem0Memory(BaseMemoryAdapter):
    """Mem0-backed long-term memory adapter using the gllm_memory SDK."""
    def __init__(self, *, agent_id: str, namespace: str | None = None, limit: int = ..., max_chars: int = ..., host: str | None = None, instruction: str | None = None) -> None:
        """Initialize the Mem0 memory adapter.

        Args:
            agent_id: Unique identifier for the agent using this memory.
            namespace: Optional namespace for organizing memories.
            limit: Maximum number of memories to retrieve in search operations.
            max_chars: Maximum character length for text content.
            host: Optional host URL for the Mem0 service.
            instruction: Optional instruction text for memory operations.
        """
    @classmethod
    def validate_env(cls) -> None:
        """Ensure the Mem0 API key is available."""
