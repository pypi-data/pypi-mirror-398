"""Mem0-specific adapter built on top of the BaseMemoryAdapter.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
from typing import Any

try:
    from gllm_memory import MemoryManager

    _HAS_GLLM_MEMORY = True
except ImportError:  # pragma: no cover
    MemoryManager = Any  # type: ignore[assignment]
    _HAS_GLLM_MEMORY = False

from aip_agents.memory.adapters.base_adapter import BaseMemoryAdapter
from aip_agents.memory.constants import MemoryDefaults


class Mem0Memory(BaseMemoryAdapter):
    """Mem0-backed long-term memory adapter using the gllm_memory SDK."""

    def __init__(
        self,
        *,
        agent_id: str,
        namespace: str | None = None,
        limit: int = MemoryDefaults.RETRIEVAL_LIMIT,
        max_chars: int = MemoryDefaults.MAX_CHARS,
        host: str | None = None,
        instruction: str | None = None,
    ) -> None:
        """Initialize the Mem0 memory adapter.

        Args:
            agent_id: Unique identifier for the agent using this memory.
            namespace: Optional namespace for organizing memories.
            limit: Maximum number of memories to retrieve in search operations.
            max_chars: Maximum character length for text content.
            host: Optional host URL for the Mem0 service.
            instruction: Optional instruction text for memory operations.
        """
        if not _HAS_GLLM_MEMORY:
            raise ImportError("optional dependency 'gllm-memory' is required for Mem0Memory")

        manager = self._initialize_manager(host=host, instruction=instruction)
        super().__init__(
            agent_id=agent_id,
            manager=manager,
            namespace=namespace,
            limit=limit,
            max_chars=max_chars,
        )

    @classmethod
    def validate_env(cls) -> None:
        """Ensure the Mem0 API key is available."""
        cls._resolve_api_key()

    @staticmethod
    def _resolve_api_key() -> str:
        api_key = os.getenv("MEM0_API_KEY") or os.getenv("GLLM_MEMORY_API_KEY")
        if not api_key:
            raise ValueError("MEM0_API_KEY (or GLLM_MEMORY_API_KEY) must be configured for Mem0 access.")
        return api_key

    def _initialize_manager(self, host: str | None, instruction: str | None) -> MemoryManager:
        """Create a MemoryManager tailored for the Mem0 backend.

        Args:
            host: Optional host URL for the Mem0 service.
            instruction: Optional instruction text for memory operations.

        Returns:
            Configured MemoryManager instance for Mem0.
        """
        api_key = self._resolve_api_key()
        resolved_host = host or os.getenv("MEM0_HOST") or os.getenv("GLLM_MEMORY_HOST")
        resolved_instruction = instruction or os.getenv("GLLM_MEMORY_INSTRUCTION")
        return MemoryManager(api_key=api_key, host=resolved_host, instruction=resolved_instruction)
