"""Steel session recording helper built on Steel's HLS exports.

This module downloads Steel session HLS manifests, merges the associated
segments into a single MP4 file, and uploads the result to MinIO storage.
It replaces the earlier rrweb + Playwright conversion pipeline.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

import asyncio
import re
import shutil
import tempfile
import time
from io import BufferedWriter
from pathlib import Path
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

from aip_agents.tools.browser_use.minio_storage import MinIOStorage
from aip_agents.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

VIDEO_FILE_NAME_PREFIX = "session_"
MANIFEST_TEMP_SUFFIX = ".m3u8"


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
        return "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))

    @staticmethod
    def safe_session_filename(session_id: str, extension: str) -> str:
        """Build a safe filename for a session recording.

        Args:
            session_id: The session ID to build a filename for.
            extension: The extension of the filename.

        Returns:
            str: The safe filename.
        """
        safe_id = SteelSessionRecorder.safe_session_id(session_id)
        return f"{VIDEO_FILE_NAME_PREFIX}{safe_id}{extension}"

    @staticmethod
    def generate_video_filename(session_id: str, extension: str = ".mp4") -> str:
        """Generate a filename for a session recording.

        Args:
            session_id: The session ID to generate a filename for.
            extension: The extension of the filename.

        Returns:
            str: The generated filename.
        """
        normalized_extension = extension if extension.startswith(".") else f".{extension}"
        return SteelSessionRecorder.safe_session_filename(session_id, normalized_extension)

    @staticmethod
    def _parse_manifest_entries(manifest_text: str, manifest_url: str) -> tuple[str | None, list[str]]:
        """Parse manifest lines into init segment and media segment URLs.

        Args:
            manifest_text: The text of the manifest.
            manifest_url: The URL of the manifest.

        Returns:
            tuple[str | None, list[str]]: The init segment URL and the list of media segment URLs.
        """
        init_url = None
        segments: list[str] = []

        for line in manifest_text.splitlines():
            line = line.strip()
            if not line:
                continue

            if not line.startswith("#"):
                segments.append(urljoin(manifest_url, line))
                continue

            if line.startswith("#EXT-X-MAP"):
                match = re.search(r'URI="([^"]+)"', line)
                if match:
                    init_url = match.group(1)

        if init_url:
            init_url = urljoin(manifest_url, init_url)

        return init_url, segments

    @staticmethod
    def _stream_url(session: requests.Session, url: str, headers: dict[str, str], output_file: BufferedWriter) -> None:
        """Stream data from a URL into a buffered writer.

        Args:
            session: The requests session to use.
            url: The URL to stream from.
            headers: The headers to use.
            output_file: The buffered writer to write the data to.
        """
        with session.get(url, headers=headers, stream=True, timeout=120) as resp:
            resp.raise_for_status()

            # Validate content type
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith(("video/", "application/octet-stream")):
                logger.warning("Unexpected content type: %s", content_type)
                return

            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    output_file.write(chunk)

    @staticmethod
    def _cleanup_temp_directory(video_dir: str) -> None:
        """Clean up the temporary directory.

        Args:
            video_dir: The directory to clean up.
        """
        try:
            shutil.rmtree(video_dir)
        except OSError:
            pass

    def __init__(self, base_url: str, api_key: str):
        """Initialize the recorder.

        Args:
            base_url: Steel API base URL.
            api_key: Steel API key for authentication.
        """
        self.base_url = base_url
        self.api_key = api_key

        self._manifest_poll_timeout_minutes = 1
        self._manifest_poll_interval_seconds = 2

        try:
            self.minio_storage = MinIOStorage()
        except Exception as exc:
            logger.warning("Failed to initialize MinIO storage: %s", exc)
            self.minio_storage = None

    def _download_manifest(self, session_id: str, dest: Path) -> str | None:
        """Download the Steel HLS manifest for a session.

        Args:
            session_id: The session ID to download the manifest for.
            dest: The destination path to save the manifest to.

        Returns:
            str | None: The URL of the manifest, or None if the base URL or API key is not set.

        Raises:
            requests.exceptions.RequestException: If the manifest is not ready after the timeout.
        """
        if not self.base_url or not self.api_key:
            logger.warning("Base URL or API key not set, skipping download for session %s", session_id)
            return None

        url = f"{self.base_url.rstrip('/')}/v1/sessions/{session_id}/hls"
        headers = {"steel-api-key": self.api_key}

        deadline = time.monotonic() + (self._manifest_poll_timeout_minutes * 60)
        attempt = 0
        while True:
            response = requests.get(url, headers=headers, timeout=60)
            if response.ok:
                dest.write_text(response.text)
                return response.url

            pollable = response.status_code in {404, 408, 429, 503}
            attempt += 1
            if not pollable or time.monotonic() >= deadline:
                logger.warning(
                    "Manifest not ready for session %s after %.1f minutes, last status %d",
                    session_id,
                    self._manifest_poll_timeout_minutes,
                    response.status_code,
                )
                response.raise_for_status()

            logger.debug(
                "Manifest not ready for session %s (attempt %d, status %d); waiting %.1f seconds",
                session_id,
                attempt,
                response.status_code,
                self._manifest_poll_interval_seconds,
            )
            time.sleep(self._manifest_poll_interval_seconds)

    def _merge_segments(self, manifest_path: Path, manifest_url: str, output_path: Path) -> bool:
        """Merge HLS segments defined in a manifest into a single video file.

        Args:
            manifest_path: The path to the manifest.
            manifest_url: The URL of the manifest.
            output_path: The path to save the merged video to.

        Returns:
            bool: True if the segments were merged successfully, False otherwise.
        """
        if not self.api_key:
            logger.warning("API key not set, skipping merge for session %s", manifest_url)
            return False

        headers = {"steel-api-key": self.api_key}
        manifest_text = manifest_path.read_text()
        init_url, segments = SteelSessionRecorder._parse_manifest_entries(manifest_text, manifest_url)

        if not init_url or not segments:
            logger.warning("No media segments found in manifest.")
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with requests.Session() as session, open(output_path, "wb") as output_file:
            if init_url:
                SteelSessionRecorder._stream_url(session, init_url, headers, output_file)

            for segment_url in segments:
                SteelSessionRecorder._stream_url(session, segment_url, headers, output_file)

        return True

    async def _download_and_merge_manifest(self, session_id: str, output_path: Path) -> bool:
        """Download and merge the Steel HLS manifest into a single file.

        Args:
            session_id: The session ID to download the manifest for.
            output_path: The path to save the merged video to.

        Returns:
            bool: True if the manifest was downloaded and merged successfully, False otherwise.
        """
        manifest_path = Path(tempfile.NamedTemporaryFile(suffix=MANIFEST_TEMP_SUFFIX, delete=False).name)

        try:
            manifest_url = await asyncio.to_thread(self._download_manifest, session_id, manifest_path)
            if not manifest_url:
                logger.warning("Failed to download manifest for session %s", session_id)
                return False

            merged = await asyncio.to_thread(self._merge_segments, manifest_path, manifest_url, output_path)
            if not merged:
                logger.warning("Failed to merge segments for session %s", session_id)
                return False

            return True
        except Exception as exc:
            logger.warning(
                "Failed to generate video from HLS manifest for session %s: %s", session_id, exc, exc_info=True
            )
            return False
        finally:
            manifest_path.unlink(missing_ok=True)

    async def _upload_video_to_minio(self, video_path: Path, video_filename: str) -> None:
        """Upload a video file to MinIO storage.

        Args:
            video_path: The path to the video file to upload.
            video_filename: The filename of the video to upload.
        """
        if not video_path.exists():
            logger.warning("Video file not found: %s", video_path)
            return

        await asyncio.to_thread(self.minio_storage.upload_file, str(video_path), video_filename)

    async def record_session_to_video(self, session_id: str) -> None:
        """Download the HLS manifest and upload the merged video to MinIO.

        Args:
            session_id: The session ID to record.
        """
        if not self.minio_storage:
            logger.warning("MinIO storage not available, skipping recording for %s", session_id)
            return

        video_dir = tempfile.mkdtemp()
        try:
            video_filename = SteelSessionRecorder.generate_video_filename(session_id, extension=".mp4")
            output_path = Path(video_dir) / video_filename
            merged = await self._download_and_merge_manifest(session_id, output_path)
            if not merged:
                logger.warning("Skipping upload because manifest merge failed for session %s", session_id)
                return

            await self._upload_video_to_minio(output_path, video_filename)
        finally:
            SteelSessionRecorder._cleanup_temp_directory(video_dir)
