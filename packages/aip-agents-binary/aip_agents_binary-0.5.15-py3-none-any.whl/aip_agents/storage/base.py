"""Base class for object storage clients.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from abc import ABC, abstractmethod
from typing import BinaryIO


class BaseObjectStorageClient(ABC):
    """Abstract base class for object storage clients."""

    @abstractmethod
    def object_exists(self, object_key: str) -> bool:
        """Check if an object exists in the storage.

        Args:
            object_key: The key of the object to check.

        Returns:
            True if the object exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def upload(
        self,
        object_key: str,
        file_stream: bytes | BinaryIO,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload data to object storage.

        Args:
            object_key: The key of the object in the storage
            file_stream: The binary data to upload
            filename: The name of the file
            content_type: The content type of the file
            metadata: Additional metadata to store with the object

        Returns:
            The key of the uploaded object
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, object_key: str) -> bytes:
        """Get data from object storage.

        Args:
            object_key: The key of the object in the storage

        Returns:
            The binary data of the object
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, object_key: str) -> None:
        """Delete data from object storage.

        Args:
            object_key: The key of the object in the storage
        """
        raise NotImplementedError

    @abstractmethod
    def generate_presigned_url(
        self, object_key: str, expires: int = 24, response_headers: dict[str, str] | None = None
    ) -> str:
        """Generate a presigned URL for accessing the object.

        Args:
            object_key: The key of the object in the storage
            expires: The number of hours the URL is valid for
            response_headers: Additional headers to include in the response

        Returns:
            The presigned URL
        """
        raise NotImplementedError
