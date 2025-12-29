"""Memory factory for creating memory adapters by backend string.

This module provides a single point of construction for memory backends,
so agent code does not depend on concrete memory implementations.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import importlib
from typing import Any

from aip_agents.memory.base import BaseMemory
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


BACKENDS = {
    # backend_name: "module_path:ClassName"
    "mem0": "aip_agents.memory.adapters.mem0:Mem0Memory",
}


def _import_class(path: str) -> type[BaseMemory]:
    """Import a memory class from a module path string.

    Dynamically imports a memory implementation class from a string path in
    the format "module_path:ClassName".

    Args:
        path: A string in the format "module_path:ClassName" specifying the
            module and class to import.

    Returns:
        type[BaseMemory]: The imported memory class that implements the
            BaseMemory interface.

    Raises:
        ModuleNotFoundError: If the specified module cannot be imported.
        AttributeError: If the specified class does not exist in the module.
        ValueError: If the path format is invalid (does not contain ':').
    """
    module_path, class_name = path.split(":", 1)
    module = importlib.import_module(module_path)
    memory_cls = getattr(module, class_name)
    return memory_cls


class MemoryFactory:
    """Factory to build concrete memory adapters by backend name."""

    @staticmethod
    def create(backend: str, **kwargs: Any) -> BaseMemory:
        """Create a memory adapter instance.

        Args:
            backend: Backend identifier (e.g., "mem0").
            **kwargs: Keyword args passed to adapter constructor (e.g., limit, max_chars, namespace).

        Returns:
            BaseMemory: A constructed memory adapter instance.

        Raises:
            ValueError: If backend is unknown or adapter can't be constructed.
        """
        if backend not in BACKENDS:
            raise ValueError(f"Unknown memory backend: {backend}")

        cls_path = BACKENDS[backend]
        memory_cls = _import_class(cls_path)

        # Validate environment (adapter may raise)
        try:
            if hasattr(memory_cls, "validate_env"):
                memory_cls.validate_env()  # type: ignore[misc]
        except Exception as e:  # noqa: BLE001
            logger.error(f"MemoryFactory: environment validation failed for '{backend}': {e}")
            raise

        try:
            instance = memory_cls(**kwargs)
            return instance
        except Exception as e:  # noqa: BLE001
            logger.error(f"MemoryFactory: failed to create memory adapter '{backend}': {e}")
            raise
