from aip_agents.schema.storage import OBJECT_STORAGE_PREFIX as OBJECT_STORAGE_PREFIX, StorageConfig as StorageConfig, StorageType as StorageType
from aip_agents.storage.base import BaseObjectStorageClient
from aip_agents.storage.providers.base import BaseStorageProvider

__all__ = ['OBJECT_STORAGE_PREFIX', 'StorageConfig', 'StorageType', 'StorageProviderFactory']

class StorageProviderFactory:
    """Factory for creating storage providers based on configuration."""
    @staticmethod
    def create(config: StorageConfig, object_storage_client: BaseObjectStorageClient | None = None) -> BaseStorageProvider:
        """Create storage provider based on configuration.

        Args:
            config (StorageConfig): Storage configuration object.
            object_storage_client (BaseObjectStorageClient | None, optional): Optional object storage client for object storage type.

        Returns:
            BaseStorageProvider: The created storage provider instance.
        """
    @staticmethod
    def create_from_env(object_storage_client: BaseObjectStorageClient | None = None) -> BaseStorageProvider:
        """Create storage provider from environment variables.

        Args:
            object_storage_client (BaseObjectStorageClient | None, optional): Optional object storage client for object storage type.

        Returns:
            BaseStorageProvider: The created storage provider instance.
        """
