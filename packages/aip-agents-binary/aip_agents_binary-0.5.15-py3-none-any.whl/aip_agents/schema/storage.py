"""Schema definitions for storage configuration."""

import os
from dataclasses import dataclass
from enum import StrEnum

__all__ = ["OBJECT_STORAGE_PREFIX", "StorageType", "StorageConfig"]

OBJECT_STORAGE_PREFIX = "tool_outputs/"


class StorageType(StrEnum):
    """Supported storage types."""

    MEMORY = "memory"
    OBJECT_STORAGE = "object_storage"


@dataclass
class StorageConfig:
    """Configuration for storage providers."""

    storage_type: StorageType = StorageType.MEMORY
    object_prefix: str = OBJECT_STORAGE_PREFIX
    object_use_json: bool = False

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """Create StorageConfig from environment variables."""
        storage_type_str = os.getenv("TOOL_OUTPUT_STORAGE_TYPE", StorageType.MEMORY.value).lower()
        if storage_type_str == StorageType.MEMORY.value:
            storage_type = StorageType.MEMORY
        else:
            storage_type = StorageType.OBJECT_STORAGE

        object_prefix = os.getenv("TOOL_OUTPUT_OBJECT_PREFIX", OBJECT_STORAGE_PREFIX)
        use_json_str = os.getenv("TOOL_OUTPUT_USE_JSON", "false").lower()
        use_json = use_json_str in ("true", "1", "yes", "on")

        return cls(storage_type=storage_type, object_prefix=object_prefix, object_use_json=use_json)
