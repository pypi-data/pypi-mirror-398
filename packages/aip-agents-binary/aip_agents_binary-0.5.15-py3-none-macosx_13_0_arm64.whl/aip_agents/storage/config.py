"""Storage configuration system.

This module keeps factory logic while delegating data schemas to ``aip_agents.schema.storage``.
"""

from aip_agents.schema.storage import OBJECT_STORAGE_PREFIX, StorageConfig, StorageType
from aip_agents.storage.base import BaseObjectStorageClient
from aip_agents.storage.clients.minio_client import MinioConfig, MinioObjectStorage
from aip_agents.storage.providers.base import BaseStorageProvider
from aip_agents.storage.providers.memory import InMemoryStorageProvider
from aip_agents.storage.providers.object_storage import ObjectStorageProvider

__all__ = ["OBJECT_STORAGE_PREFIX", "StorageConfig", "StorageType", "StorageProviderFactory"]


class StorageProviderFactory:
    """Factory for creating storage providers based on configuration."""

    @staticmethod
    def create(
        config: StorageConfig, object_storage_client: BaseObjectStorageClient | None = None
    ) -> BaseStorageProvider:
        """Create storage provider based on configuration.

        Args:
            config (StorageConfig): Storage configuration object.
            object_storage_client (BaseObjectStorageClient | None, optional): Optional object storage client for object storage type.

        Returns:
            BaseStorageProvider: The created storage provider instance.
        """
        if config.storage_type == StorageType.MEMORY:
            return InMemoryStorageProvider()

        if config.storage_type == StorageType.OBJECT_STORAGE:
            if object_storage_client is None:
                try:
                    minio_config = MinioConfig.from_env()
                    object_storage_client = MinioObjectStorage(minio_config)
                except ValueError as exc:
                    raise ValueError(
                        f"Object storage client required but not provided and cannot create from env: {exc}"
                    ) from exc

            return ObjectStorageProvider(
                client=object_storage_client, prefix=config.object_prefix, use_json=config.object_use_json
            )

        raise ValueError(f"Unknown storage type: {config.storage_type}")

    @staticmethod
    def create_from_env(object_storage_client: BaseObjectStorageClient | None = None) -> BaseStorageProvider:
        """Create storage provider from environment variables.

        Args:
            object_storage_client (BaseObjectStorageClient | None, optional): Optional object storage client for object storage type.

        Returns:
            BaseStorageProvider: The created storage provider instance.
        """
        config = StorageConfig.from_env()
        return StorageProviderFactory.create(config, object_storage_client)
