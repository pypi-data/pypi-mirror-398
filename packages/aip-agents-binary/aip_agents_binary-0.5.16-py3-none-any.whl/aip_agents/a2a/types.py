"""Type definitions and constants for A2A artifact generation.

This module provides common MIME types, artifact types, and other constants
used in A2A artifact generation to ensure consistency across the codebase.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import base64
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MimeType(StrEnum):
    """Common MIME types for A2A artifacts.

    This class provides constants for commonly used MIME types in artifact generation,
    ensuring consistency and reducing typos across the codebase.
    """

    # Text formats
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSS = "text/css"
    TEXT_JAVASCRIPT = "text/javascript"
    TEXT_CSV = "text/csv"
    TEXT_XML = "text/xml"
    TEXT_MARKDOWN = "text/markdown"

    # Application formats
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    APPLICATION_PDF = "application/pdf"
    APPLICATION_ZIP = "application/zip"
    APPLICATION_GZIP = "application/gzip"
    APPLICATION_TAR = "application/x-tar"
    APPLICATION_OCTET_STREAM = "application/octet-stream"

    # Microsoft Office formats
    APPLICATION_MSWORD = "application/msword"
    APPLICATION_EXCEL = "application/vnd.ms-excel"
    APPLICATION_POWERPOINT = "application/vnd.ms-powerpoint"
    APPLICATION_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    APPLICATION_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    APPLICATION_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    # Image formats
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    IMAGE_SVG = "image/svg+xml"
    IMAGE_BMP = "image/bmp"
    IMAGE_TIFF = "image/tiff"
    IMAGE_ICO = "image/x-icon"

    # Audio formats
    AUDIO_MP3 = "audio/mpeg"
    AUDIO_WAV = "audio/wav"
    AUDIO_OGG = "audio/ogg"
    AUDIO_AAC = "audio/aac"
    AUDIO_FLAC = "audio/flac"

    # Video formats
    VIDEO_MP4 = "video/mp4"
    VIDEO_AVI = "video/x-msvideo"
    VIDEO_MOV = "video/quicktime"
    VIDEO_WMV = "video/x-ms-wmv"
    VIDEO_WEBM = "video/webm"
    VIDEO_MKV = "video/x-matroska"

    # Font formats
    FONT_TTF = "font/ttf"
    FONT_OTF = "font/otf"
    FONT_WOFF = "font/woff"
    FONT_WOFF2 = "font/woff2"


class ArtifactType(StrEnum):
    """Common artifact types for A2A artifacts.

    This class provides constants for artifact types used in the A2A protocol.
    """

    FILE = "file"
    DATA = "data"
    TEXT = "text"


# Common file extension to MIME type mappings
EXTENSION_TO_MIME_TYPE = {
    # Text files
    ".txt": MimeType.TEXT_PLAIN,
    ".html": MimeType.TEXT_HTML,
    ".htm": MimeType.TEXT_HTML,
    ".css": MimeType.TEXT_CSS,
    ".js": MimeType.TEXT_JAVASCRIPT,
    ".csv": MimeType.TEXT_CSV,
    ".xml": MimeType.TEXT_XML,
    ".md": MimeType.TEXT_MARKDOWN,
    ".markdown": MimeType.TEXT_MARKDOWN,
    # Application files
    ".json": MimeType.APPLICATION_JSON,
    ".pdf": MimeType.APPLICATION_PDF,
    ".zip": MimeType.APPLICATION_ZIP,
    ".gz": MimeType.APPLICATION_GZIP,
    ".tar": MimeType.APPLICATION_TAR,
    # Microsoft Office
    ".doc": MimeType.APPLICATION_MSWORD,
    ".xls": MimeType.APPLICATION_EXCEL,
    ".ppt": MimeType.APPLICATION_POWERPOINT,
    ".docx": MimeType.APPLICATION_DOCX,
    ".xlsx": MimeType.APPLICATION_XLSX,
    ".pptx": MimeType.APPLICATION_PPTX,
    # Images
    ".jpg": MimeType.IMAGE_JPEG,
    ".jpeg": MimeType.IMAGE_JPEG,
    ".png": MimeType.IMAGE_PNG,
    ".gif": MimeType.IMAGE_GIF,
    ".webp": MimeType.IMAGE_WEBP,
    ".svg": MimeType.IMAGE_SVG,
    ".bmp": MimeType.IMAGE_BMP,
    ".tiff": MimeType.IMAGE_TIFF,
    ".tif": MimeType.IMAGE_TIFF,
    ".ico": MimeType.IMAGE_ICO,
    # Audio
    ".mp3": MimeType.AUDIO_MP3,
    ".wav": MimeType.AUDIO_WAV,
    ".ogg": MimeType.AUDIO_OGG,
    ".aac": MimeType.AUDIO_AAC,
    ".flac": MimeType.AUDIO_FLAC,
    # Video
    ".mp4": MimeType.VIDEO_MP4,
    ".avi": MimeType.VIDEO_AVI,
    ".mov": MimeType.VIDEO_MOV,
    ".wmv": MimeType.VIDEO_WMV,
    ".webm": MimeType.VIDEO_WEBM,
    ".mkv": MimeType.VIDEO_MKV,
    # Fonts
    ".ttf": MimeType.FONT_TTF,
    ".otf": MimeType.FONT_OTF,
    ".woff": MimeType.FONT_WOFF,
    ".woff2": MimeType.FONT_WOFF2,
}
MIME_TYPE_TO_EXTENSION = {v: k for k, v in EXTENSION_TO_MIME_TYPE.items()}


def get_mime_type_from_filename(filename: str) -> str:
    """Get MIME type from filename extension.

    Args:
        filename: The filename to get the MIME type for.

    Returns:
        The MIME type string, or application/octet-stream if unknown.

    Example:
        >>> get_mime_type_from_filename("data.csv")
        'text/csv'
        >>> get_mime_type_from_filename("image.png")
        'image/png'
        >>> get_mime_type_from_filename("unknown.xyz")
        'application/octet-stream'
    """
    if "." not in filename:
        return MimeType.APPLICATION_OCTET_STREAM

    extension = "." + filename.split(".")[-1].lower()
    return EXTENSION_TO_MIME_TYPE.get(extension, MimeType.APPLICATION_OCTET_STREAM)


def get_extension_from_mime_type(mime_type: str) -> str | None:
    """Get file extension from MIME type.

    Args:
        mime_type: The MIME type to get the extension for.

    Returns:
        The file extension (with dot) or None if not found.

    Example:
        >>> get_extension_from_mime_type("text/csv")
        '.csv'
        >>> get_extension_from_mime_type("image/png")
        '.png'
        >>> get_extension_from_mime_type("unknown/type")
        None
    """
    return MIME_TYPE_TO_EXTENSION.get(mime_type)


class Artifact(BaseModel):
    """Represents an artifact payload used by A2A helpers and executors.

    This model standardizes the structure for artifacts generated by tools and
    passed through the A2A pipeline.

    Attributes:
        artifact_type (ArtifactType): The type of artifact. Defaults to FILE.
        data (str): Base64-encoded content of the artifact.
        name (str): Display name or filename of the artifact.
        description (str): Optional description for the artifact. Defaults to empty string.
        mime_type (str): MIME type of the artifact content.
        metadata (dict[str, Any] | None): Optional per-artifact metadata to pass through.
    """

    artifact_type: ArtifactType = Field(default=ArtifactType.FILE)
    data: str
    name: str
    description: str = ""
    mime_type: str
    metadata: dict[str, Any] | None = None

    @field_validator("data")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate that 'data' is a valid base64 string.

        Args:
            v (str): The base64 string to validate.

        Returns:
            str: The validated base64 string if valid.
        """
        try:
            base64.b64decode(v, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Artifact.data must be a valid base64-encoded string") from exc
        return v
