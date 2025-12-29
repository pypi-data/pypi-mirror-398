from _typeshed import Incomplete
from aip_agents.memory.base import BaseMemory as BaseMemory
from aip_agents.utils.logger import get_logger as get_logger
from typing import Any

logger: Incomplete
BACKENDS: Incomplete

class MemoryFactory:
    """Factory to build concrete memory adapters by backend name."""
    @staticmethod
    def create(backend: str, **kwargs: Any) -> BaseMemory:
        '''Create a memory adapter instance.

        Args:
            backend: Backend identifier (e.g., "mem0").
            **kwargs: Keyword args passed to adapter constructor (e.g., limit, max_chars, namespace).

        Returns:
            BaseMemory: A constructed memory adapter instance.

        Raises:
            ValueError: If backend is unknown or adapter can\'t be constructed.
        '''
