"""Object storage provider implementation.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import json
import pickle
from typing import Any

from aip_agents.storage.base import BaseObjectStorageClient
from aip_agents.storage.providers.base import BaseStorageProvider, StorageError
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class ObjectStorageProvider(BaseStorageProvider):
    """Object storage provider for S3-compatible storage.

    Works with any S3-compatible storage including AWS S3, MinIO,
    Google Cloud Storage (with S3 compatibility), etc.

    Best for:
    - Very large datasets
    - Distributed systems
    - Cloud deployments
    - Long-term storage
    - Multi-region access
    """

    def __init__(self, client: BaseObjectStorageClient, prefix: str = "", use_json: bool = False):
        """Initialize object storage provider.

        Args:
            client: Object storage client instance
            prefix: Prefix for all keys (like a directory)
            use_json: Use JSON format (True) or pickle (False)
        """
        self.client = client
        self.prefix = prefix.rstrip("/") + "/" if prefix else ""
        self.use_json = use_json

    def _get_object_key(self, key: str) -> str:
        """Get full object key with prefix.

        Args:
            key: Storage key

        Returns:
            Full object key with prefix
        """
        return f"{self.prefix}{key}"

    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data to bytes.

        Args:
            data: Data to serialize

        Returns:
            Serialized data as bytes

        Raises:
            StorageError: If serialization fails
        """
        try:
            if self.use_json:
                return json.dumps(data, default=str).encode("utf-8")
            return pickle.dumps(data)
        except Exception as e:
            raise StorageError(f"Failed to serialize data: {e}") from e

    def _deserialize_data(self, data_bytes: bytes) -> Any:
        """Deserialize data from bytes.

        Args:
            data_bytes: Serialized data

        Returns:
            Deserialized data

        Raises:
            StorageError: If deserialization fails
        """
        try:
            if self.use_json:
                return json.loads(data_bytes.decode("utf-8"))
            return pickle.loads(data_bytes)
        except Exception as e:
            raise StorageError(f"Failed to deserialize data: {e}") from e

    def store(self, key: str, data: Any) -> None:
        """Store data in object storage.

        Args:
            key: Unique identifier for the data
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        object_key = self._get_object_key(key)

        try:
            data_bytes = self._serialize_data(data)

            self.client.upload(
                object_key=object_key,
                file_stream=data_bytes,
                content_type="application/json" if self.use_json else "application/octet-stream",
                metadata={"storage_key": key, "format": "json" if self.use_json else "pickle"},
            )

            logger.debug(f"Stored data to object storage: {object_key}")

        except Exception as e:
            raise StorageError(f"Failed to store data in object storage: {e}") from e

    def retrieve(self, key: str) -> Any:
        """Retrieve data from object storage.

        Args:
            key: Unique identifier for the data

        Returns:
            The stored data

        Raises:
            KeyError: If key not found
            StorageError: If retrieval operation fails
        """
        object_key = self._get_object_key(key)

        try:
            data_bytes = self.client.get(object_key)
            return self._deserialize_data(data_bytes)

        except KeyError as e:
            raise KeyError(f"Key '{key}' not found in object storage: {e}") from e
        except Exception as e:
            raise StorageError(f"Failed to retrieve data from object storage: {e}") from e

    def exists(self, key: str) -> bool:
        """Check if object exists.

        Args:
            key: Unique identifier to check

        Returns:
            True if key exists, False otherwise
        """
        object_key = self._get_object_key(key)

        try:
            return self.client.object_exists(object_key)
        except Exception as e:
            logger.warning(f"Failed to check object existence: {e}")
            return False

    def delete(self, key: str) -> None:
        """Delete object.

        Args:
            key: Unique identifier for the data
        """
        object_key = self._get_object_key(key)

        try:
            self.client.delete(object_key)
            logger.debug(f"Deleted object: {object_key}")
        except Exception as e:
            logger.warning(f"Failed to delete object {object_key}: {e}")

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix.

        Args:
            prefix: Optional prefix to filter keys

        Raises:
            NotImplementedError: list_keys is not implemented
        """
        raise NotImplementedError("list_keys not yet implemented for object storage")

    def clear(self) -> None:
        """Clear all objects with the configured prefix.

        Warning:
            This is a dangerous operation!
        """
        logger.warning("clear() not implemented for object storage - too dangerous")
        raise NotImplementedError("Batch clear not implemented for safety reasons")

    def get_presigned_url(self, key: str, expires_hours: int = 24) -> str | None:
        """Generate presigned URL for direct access.

        Args:
            key: Storage key
            expires_hours: URL expiration in hours

        Returns:
            Presigned URL for direct access

        Raises:
            StorageError: If URL generation fails
        """
        object_key = self._get_object_key(key)

        try:
            return self.client.generate_presigned_url(object_key=object_key, expires=expires_hours)
        except Exception as e:
            raise StorageError(f"Failed to generate presigned URL: {e}") from e
