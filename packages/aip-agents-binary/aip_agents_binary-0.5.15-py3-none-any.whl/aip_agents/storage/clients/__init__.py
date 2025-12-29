"""Storage client implementations.

This module contains concrete implementations of object storage clients
for various backends like MinIO, AWS S3, etc.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from aip_agents.storage.clients.minio_client import MinioConfig, MinioObjectStorage

__all__ = ["MinioConfig", "MinioObjectStorage"]
