"""Minio object storage implementation.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import datetime
import io
import os
from dataclasses import dataclass
from typing import BinaryIO

from minio import Minio, S3Error
from urllib3.exceptions import HTTPError

from aip_agents.storage.base import BaseObjectStorageClient

S3_ERR_NO_SUCH_KEY = "NoSuchKey"
S3_ERR_NO_SUCH_BUCKET = "NoSuchBucket"
S3_ERR_ACCESS_DENIED = "AccessDenied"


@dataclass
class MinioConfig:
    """Configuration for MinIO object storage client.

    Attributes:
        endpoint: MinIO server endpoint URL
        access_key: Access key for authentication
        secret_key: Secret key for authentication
        bucket: Bucket name to use for storage
        secure: Whether to use HTTPS (defaults to True)
    """

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = True

    @classmethod
    def from_env(cls) -> "MinioConfig":
        """Create MinioConfig from environment variables.

        Expected environment variables:
        - OBJECT_STORAGE_URL
        - OBJECT_STORAGE_USER
        - OBJECT_STORAGE_PASSWORD
        - OBJECT_STORAGE_BUCKET
        - OBJECT_STORAGE_SECURE (optional, defaults to True)

        Returns:
            MinioConfig instance

        Raises:
            ValueError: If required environment variables are not set
        """
        endpoint = os.getenv("OBJECT_STORAGE_URL")
        access_key = os.getenv("OBJECT_STORAGE_USER")
        secret_key = os.getenv("OBJECT_STORAGE_PASSWORD")
        bucket = os.getenv("OBJECT_STORAGE_BUCKET")
        secure_str = os.getenv("OBJECT_STORAGE_SECURE")

        if not all([endpoint, access_key, secret_key, bucket]):
            raise ValueError(
                "MinIO configuration incomplete. Required environment variables: "
                "OBJECT_STORAGE_URL, OBJECT_STORAGE_USER, "
                "OBJECT_STORAGE_PASSWORD, OBJECT_STORAGE_BUCKET"
            )

        secure = secure_str.lower() in ("true", "1", "yes", "on")

        return cls(endpoint=endpoint, access_key=access_key, secret_key=secret_key, bucket=bucket, secure=secure)


class MinioObjectStorage(BaseObjectStorageClient):
    """Implementation of ObjectStorageInterface using Minio."""

    def __init__(self, config: MinioConfig | None = None, ensure_bucket: bool = True):
        """Initialize MinioObjectStorage with configuration.

        Args:
            config: MinioConfig instance. If None, will attempt to load from environment variables.
            ensure_bucket: Whether to ensure bucket exists during initialization (optional). Defaults to True.

        Raises:
            ValueError: If configuration is invalid or incomplete
        """
        if config is None:
            config = MinioConfig.from_env()

        self.config = config
        self.client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )
        self.bucket = config.bucket
        self._bucket_exists = None

        if ensure_bucket:
            self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists, creating it if necessary.

        Uses caching to avoid repeated bucket existence checks.

        Raises:
            PermissionError: If user lacks permission to create the bucket
            ConnectionError: If there's a network/connection issue creating the bucket
        """
        if self._bucket_exists is None:
            try:
                self._bucket_exists = self.client.bucket_exists(self.bucket)
                if not self._bucket_exists:
                    self.client.make_bucket(self.bucket)
                    self._bucket_exists = True
            except S3Error as e:
                if e.code == S3_ERR_ACCESS_DENIED:  # pragma: no cover - difficult to test with mocks
                    raise PermissionError(
                        f"Access denied: Insufficient permissions to create bucket '{self.bucket}'. "
                        f"Please check your AWS/MinIO user permissions."
                    ) from e
                else:
                    raise ConnectionError(f"Failed to create bucket '{self.bucket}': {str(e)}") from e

    def _prepare_file_stream(self, file_stream: bytes | BinaryIO) -> tuple[BinaryIO, int]:
        """Prepare file stream for upload and validate its content.

        Args:
            file_stream: The file stream to prepare (bytes or file-like object)

        Returns:
            Tuple containing:
                - Prepared file stream
                - Length of the file content

        Raises:
            ValueError: If the file stream is empty or invalid
        """
        if isinstance(file_stream, bytes):
            file_stream = io.BytesIO(file_stream)
            file_length = len(file_stream.getvalue())
        else:
            # For file-like objects, seek to end to get size, then reset
            try:
                current_pos = file_stream.tell()
                file_stream.seek(0, 2)  # Seek to end
                file_length = file_stream.tell()
                file_stream.seek(current_pos)
            except (OSError, AttributeError) as e:
                raise ValueError(f"Invalid file stream: {str(e)}") from e

        if file_length == 0:
            raise ValueError("File stream is empty.")

        return file_stream, file_length

    def upload(
        self,
        object_key: str,
        file_stream: bytes | BinaryIO,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload data to Minio object storage.

        Args:
            object_key: The key to store the object under
            file_stream: The data to upload (bytes or file-like object)
            filename: The filename of the data (optional)
            content_type: The content type of the data (optional)
            metadata: Additional metadata to store with the object (optional)

        Returns:
            The object key of the uploaded data

        Raises:
            ValueError: If the file stream is empty or invalid
            ConnectionError: If there's an issue connecting to Minio
            Exception: For other unexpected errors during upload
        """
        if self._bucket_exists is None:
            self._ensure_bucket_exists()
        prepared_stream, file_length = self._prepare_file_stream(file_stream)

        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_key,
                data=prepared_stream,
                length=file_length,
                content_type=content_type,
                metadata=metadata,
            )
        except S3Error as e:
            raise ConnectionError(f"Failed to upload object '{object_key}' to Minio: {str(e)}") from e
        except HTTPError as e:
            raise ConnectionError(f"A network error occurred during object upload: {str(e)}") from e

        return object_key

    def get(self, object_key: str) -> bytes:
        """Get data from Minio object storage.

        Args:
            object_key: The key of the object to retrieve

        Returns:
            The object data as bytes

        Raises:
            KeyError: If the object is not found
            ConnectionError: If there's a network or connection issue
        """
        try:
            with self.client.get_object(bucket_name=self.bucket, object_name=object_key) as response:
                return response.read()
        except S3Error as e:
            if e.code == S3_ERR_NO_SUCH_KEY:
                raise KeyError(f"Object with key '{object_key}' not found") from e
            raise ConnectionError(f"Failed to get object '{object_key}': {str(e)}") from e
        except HTTPError as e:
            raise ConnectionError(f"A network error occurred during object retrieval: {str(e)}") from e

    def delete(self, object_key: str) -> None:
        """Delete data from Minio object storage.

        Args:
            object_key: The key of the object to delete

        Raises:
            ConnectionError: If there's a network or connection issue
        """
        try:
            self.client.remove_object(bucket_name=self.bucket, object_name=object_key)
        except S3Error as e:
            if e.code != S3_ERR_NO_SUCH_KEY:  # Don't raise error if object doesn't exist
                raise ConnectionError(f"Failed to delete object '{object_key}': {str(e)}") from e
        except HTTPError as e:
            raise ConnectionError(f"A network error occurred during file deletion: {str(e)}") from e

    def object_exists(self, object_key: str) -> bool:
        """Check if an object exists in the MinIO bucket.

        Args:
            object_key: The key of the object to check.

        Returns:
            True if the object exists, False otherwise.

        Raises:
            ConnectionError: If there's a network or connection issue (excluding not found errors)
        """
        try:
            self.client.stat_object(self.bucket, object_key)
            return True
        except S3Error as e:
            if e.code in (S3_ERR_NO_SUCH_KEY, S3_ERR_NO_SUCH_BUCKET):
                return False
            raise ConnectionError(f"Failed to check object existence '{object_key}': {str(e)}") from e
        except HTTPError as e:
            raise ConnectionError(f"A network error occurred while checking object existence: {str(e)}") from e

    def list_objects(self, prefix: str = "") -> list[str]:
        """List objects in the bucket with optional prefix filter.

        Args:
            prefix: Optional prefix to filter objects

        Returns:
            List of object keys

        Raises:
            ConnectionError: If there's an issue listing objects
        """
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise ConnectionError(f"Failed to list objects in bucket '{self.bucket}': {str(e)}") from e
        except HTTPError as e:
            raise ConnectionError(f"A network error occurred while listing objects: {str(e)}") from e

    def generate_presigned_url(
        self, object_key: str, expires: int = 24, response_headers: dict[str, str] | None = None
    ) -> str:
        """Generate a presigned URL for accessing the object.

        Args:
            object_key: The key of the object
            expires: Expiration time in hours (defaults to 24)
            response_headers: Additional response headers (optional)

        Returns:
            A presigned URL

        Raises:
            ValueError: If expiration time is not positive
            ConnectionError: If there's an issue generating the URL
        """
        if expires <= 0:
            raise ValueError("Expiration time must be positive")

        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_key,
                expires=datetime.timedelta(hours=expires),
                response_headers=response_headers,
            )
        except S3Error as e:
            raise ConnectionError(f"Failed to generate presigned URL for '{object_key}': {str(e)}") from e
        except HTTPError as e:
            raise ConnectionError(f"A network error occurred while generating presigned URL: {str(e)}") from e
