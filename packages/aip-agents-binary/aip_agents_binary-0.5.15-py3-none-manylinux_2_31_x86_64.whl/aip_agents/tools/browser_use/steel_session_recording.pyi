from _typeshed import Incomplete
from aip_agents.tools.browser_use.minio_storage import MinIOStorage as MinIOStorage
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
VIDEO_FILE_NAME_PREFIX: str
MANIFEST_TEMP_SUFFIX: str

class SteelSessionRecorder:
    """High-level helper to export Steel sessions via their HLS manifests.

    This class provides a high-level interface for exporting Steel sessions via their HLS manifests.
    It provides methods for sanitizing session IDs, building safe filenames, and generating video filenames.
    It also provides methods for downloading and merging HLS manifests, and uploading videos to MinIO.
    """
    @staticmethod
    def safe_session_id(session_id: str) -> str:
        """Sanitize a session ID for filename usage.

        Args:
            session_id: The session ID to sanitize.

        Returns:
            str: The sanitized session ID.
        """
    @staticmethod
    def safe_session_filename(session_id: str, extension: str) -> str:
        """Build a safe filename for a session recording.

        Args:
            session_id: The session ID to build a filename for.
            extension: The extension of the filename.

        Returns:
            str: The safe filename.
        """
    @staticmethod
    def generate_video_filename(session_id: str, extension: str = '.mp4') -> str:
        """Generate a filename for a session recording.

        Args:
            session_id: The session ID to generate a filename for.
            extension: The extension of the filename.

        Returns:
            str: The generated filename.
        """
    base_url: Incomplete
    api_key: Incomplete
    minio_storage: Incomplete
    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize the recorder.

        Args:
            base_url: Steel API base URL.
            api_key: Steel API key for authentication.
        """
    async def record_session_to_video(self, session_id: str) -> None:
        """Download the HLS manifest and upload the merged video to MinIO.

        Args:
            session_id: The session ID to record.
        """
