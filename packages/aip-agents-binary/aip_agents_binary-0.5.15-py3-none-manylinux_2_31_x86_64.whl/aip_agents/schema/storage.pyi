from dataclasses import dataclass
from enum import StrEnum

__all__ = ['OBJECT_STORAGE_PREFIX', 'StorageType', 'StorageConfig']

OBJECT_STORAGE_PREFIX: str

class StorageType(StrEnum):
    """Supported storage types."""
    MEMORY: str
    OBJECT_STORAGE: str

@dataclass
class StorageConfig:
    """Configuration for storage providers."""
    storage_type: StorageType = ...
    object_prefix: str = ...
    object_use_json: bool = ...
    @classmethod
    def from_env(cls) -> StorageConfig:
        """Create StorageConfig from environment variables."""
