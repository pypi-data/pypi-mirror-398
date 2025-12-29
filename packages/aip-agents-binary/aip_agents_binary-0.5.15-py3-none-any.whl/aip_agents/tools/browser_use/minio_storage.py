"""MinIO Storage Handler for Steel Session Recording.

This module provides MinIO cloud storage functionality for uploading and managing
video files from Steel session recordings. It handles file uploads, bucket management,
and presigned URL generation for secure file access.

The module supports:
- Automatic bucket creation and validation
- Secure file uploads with proper content types
- Presigned URL generation for temporary file access
- Directory prefix support for organized storage
- Comprehensive error handling and logging

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

import os

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

OBJECT_NAME_PREFIX = "steel-recordings/"


class MinIOStorage:
    """Handles MinIO cloud storage operations for video files.

    This class provides a complete interface for MinIO operations including:
    - Connection management with authentication
    - Bucket existence validation and creation
    - File upload with proper metadata
    - Presigned URL generation for secure access

    Attributes:
        endpoint: MinIO server endpoint URL.
        access_key: MinIO access key for authentication.
        secret_key: MinIO secret key for authentication.
        secure: Whether to use HTTPS/TLS for connections.
        bucket_name: Target bucket for file storage.
        directory_prefix: Optional directory prefix for organized storage.
        client: MinIO client instance for API operations.
    """

    def __init__(self):
        """Initialize MinIO storage with configuration from environment variables.

        Reads configuration from the following environment variables:
        - OBJECT_STORAGE_URL: MinIO server endpoint
        - OBJECT_STORAGE_USER: MinIO access key
        - OBJECT_STORAGE_PASSWORD: MinIO secret key
        - OBJECT_STORAGE_SECURE: Whether to use HTTPS (default: False)
        - OBJECT_STORAGE_BUCKET: Target bucket name
        - OBJECT_STORAGE_DIRECTORY_PREFIX: Optional directory prefix

        Raises:
            ValueError: If required environment variables are missing.
            Exception: If bucket creation or validation fails.

        Note:
            The method automatically ensures the target bucket exists,
            creating it if necessary.
        """
        self.endpoint = os.getenv("OBJECT_STORAGE_URL")
        self.access_key = os.getenv("OBJECT_STORAGE_USER")
        self.secret_key = os.getenv("OBJECT_STORAGE_PASSWORD")
        self.secure = os.getenv("OBJECT_STORAGE_SECURE", "False").lower() == "true"
        self.bucket_name = os.getenv("OBJECT_STORAGE_BUCKET")
        self.directory_prefix = os.getenv("OBJECT_STORAGE_DIRECTORY_PREFIX")

        if not all([self.endpoint, self.access_key, self.secret_key, self.bucket_name]):
            raise ValueError(
                "MinIO configuration incomplete. Set OBJECT_STORAGE_URL, OBJECT_STORAGE_USER, OBJECT_STORAGE_PASSWORD,"
                "and OBJECT_STORAGE_BUCKET."
            )

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the configured bucket exists, create if it doesn't.

        This method checks if the target bucket exists and creates it if necessary.
        It's called during initialization to ensure the storage is ready for use.

        Raises:
            Exception: If bucket creation or validation fails.

        Note:
            Bucket creation failures are logged as warnings but don't prevent
            the class from being usable (existing buckets can still be accessed).
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise Exception(f"Warning: Could not ensure bucket exists: {e}") from e

    def get_object_name(self, object_name: str) -> str:
        """Get the object name with the directory prefix.

        This method constructs the full object path by combining the directory
        prefix with the base object name. It ensures consistent path structure
        for all stored files.

        Args:
            object_name: Name of the object in MinIO.

        Returns:
            str: Object name with the directory prefix and steel-recordings subdirectory.
                Format: {prefix}/steel-recordings/{object_name} or steel-recordings/{object_name}

        Note:
            The method automatically adds a "steel-recordings" subdirectory to
            organize video files separately from other content.
        """
        object_name = f"{OBJECT_NAME_PREFIX}{object_name}"
        if self.directory_prefix:
            return f"{self.directory_prefix}/{object_name}"
        return object_name

    def upload_file(self, file_path: str, object_name: str) -> None:
        """Upload a file to MinIO bucket.

        This method handles the complete file upload process including:
        - File existence validation
        - Proper content type setting for video files
        - Error handling and logging
        - Structured object naming with prefixes

        Args:
            file_path: Local path to the file to upload.
            object_name: Name to use for the object in MinIO.

        Raises:
            Exception: If the file doesn't exist or upload fails.
                Specific S3Error details are included in the exception message.

        Note:
            The method automatically sets the content type to "video/webm"
            for proper video file handling in browsers and applications.
        """
        try:
            if not os.path.exists(file_path):
                raise Exception(f"File not found: {file_path}")

            # Upload the file
            self.client.fput_object(
                self.bucket_name,
                self.get_object_name(object_name),
                file_path,
                content_type="video/webm",
            )

        except S3Error as e:
            raise Exception(f"Error uploading to MinIO: {e}") from e
        except Exception as e:
            raise Exception(f"Unexpected error during upload: {e}") from e

    def get_file_url(self, object_name: str) -> str:
        """Generate a presigned URL for accessing the uploaded file.

        This method creates a temporary, secure URL that allows access to the
        uploaded file without requiring MinIO credentials. The URL is valid
        for a limited time and provides secure, direct access to the file.

        Args:
            object_name: Name of the object in MinIO.

        Returns:
            str: Presigned URL for secure file access.
                The URL includes authentication tokens and is valid for a limited time.

        Raises:
            Exception: If presigned URL generation fails.
                S3Error details are included in the exception message.

        Note:
            Presigned URLs are useful for sharing files temporarily without
            exposing MinIO credentials or requiring users to have storage access.
        """
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                self.get_object_name(object_name),
            )
        except S3Error as e:
            raise Exception(f"Error generating presigned URL: {e}") from e
