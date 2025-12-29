"""In-memory storage provider implementation.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import sys
from typing import Any

from aip_agents.storage.providers.base import BaseStorageProvider, StorageError


class InMemoryStorageProvider(BaseStorageProvider):
    """In-memory storage provider for fast access to small data.

    This provider stores all data in memory, providing the fastest
    access times but limited by available RAM.

    Best for:
    - Small to medium datasets
    - Temporary storage
    - Development and testing
    - High-frequency access patterns
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: dict[str, Any] = {}

    def store(self, key: str, data: Any) -> None:
        """Store data in memory.

        Args:
            key: Unique identifier for the data
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        try:
            self._storage[key] = data
        except Exception as e:
            raise StorageError(f"Failed to store data in memory: {e}") from e

    def retrieve(self, key: str) -> Any:
        """Retrieve data from memory.

        Args:
            key: Unique identifier for the data

        Returns:
            The stored data

        Raises:
            KeyError: If key not found
        """
        if key not in self._storage:
            raise KeyError(f"Key '{key}' not found in memory storage")
        return self._storage[key]

    def exists(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Unique identifier to check

        Returns:
            True if key exists, False otherwise
        """
        return key in self._storage

    def delete(self, key: str) -> None:
        """Delete data from memory.

        Args:
            key: Unique identifier for the data
        """
        self._storage.pop(key, None)

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        if prefix:
            return [k for k in self._storage.keys() if k.startswith(prefix)]
        return list(self._storage.keys())

    def clear(self) -> None:
        """Clear all data from memory."""
        self._storage.clear()

    @property
    def size_bytes(self) -> int:
        """Get approximate memory usage in bytes.

        Returns:
            Approximate memory usage in bytes
        """
        return sum(sys.getsizeof(v) for v in self._storage.values())

    @property
    def count(self) -> int:
        """Get number of stored items.

        Returns:
            Number of items in storage
        """
        return len(self._storage)
