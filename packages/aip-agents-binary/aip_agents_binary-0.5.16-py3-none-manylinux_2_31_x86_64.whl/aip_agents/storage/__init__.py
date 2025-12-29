"""Storage module for aip_agents.

This module provides comprehensive storage functionality including object storage
clients, storage providers for tool outputs, and configuration management.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

# Object storage clients
from aip_agents.storage.base import BaseObjectStorageClient
from aip_agents.storage.clients.minio_client import MinioConfig, MinioObjectStorage

# Configuration and factory
from aip_agents.storage.config import (
    StorageConfig,
    StorageProviderFactory,
    StorageType,
)

# Storage providers
from aip_agents.storage.providers.base import BaseStorageProvider, StorageError
from aip_agents.storage.providers.memory import InMemoryStorageProvider
from aip_agents.storage.providers.object_storage import ObjectStorageProvider

__all__ = [
    # Object storage
    "BaseObjectStorageClient",
    "MinioConfig",
    "MinioObjectStorage",
    # Storage providers
    "BaseStorageProvider",
    "StorageError",
    "InMemoryStorageProvider",
    "ObjectStorageProvider",
    # Configuration
    "StorageConfig",
    "StorageType",
    "StorageProviderFactory",
]
