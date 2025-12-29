"""Tool for E2B Cloud Sandbox code execution.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Komang Elang Surya Prawira (komang.e.s.prawira@gdplabs.id)
"""

import asyncio
import time
from http import HTTPStatus
from typing import Any

import requests
from gllm_inference.schema import Attachment
from gllm_tools.code_interpreter.code_sandbox.e2b_cloud_sandbox import E2BCloudSandbox
from gllm_tools.code_interpreter.code_sandbox.models import (
    ExecutionResult,
    ExecutionStatus,
)
from gllm_tools.code_interpreter.code_sandbox.utils import calculate_duration_ms

from aip_agents.tools.code_sandbox.constant import DATA_FILE_PATH
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class SandboxFileWatcher:
    """File watcher for monitoring file creation in sandbox environments."""

    def __init__(self, sandbox: Any):
        """Initialize the file watcher with a sandbox instance.

        Args:
            sandbox (Any): The sandbox instance to monitor.
        """
        self.sandbox = sandbox
        self._created_files: list[str] = []
        self._watchers_with_dirs: list[tuple[Any, str]] = []

    def setup_monitoring(self) -> None:
        """Set up filesystem watchers for monitoring file creation.

        Note: /tmp/output is a sandbox-isolated directory, not a shared system /tmp.
        This directory is scoped to the E2B sandbox instance and is safe for use.
        """
        output_dirs = [
            "/tmp/output",  # NOSONAR: python:S5443 - Sandbox-isolated directory, safe for temp outputs
        ]

        self._watchers_with_dirs = []

        for output_dir in output_dirs:
            try:
                # Create the directory if it doesn't exist
                # NOSONAR: python:S5443 - Sandbox-isolated directory, safe for use
                self.sandbox.files.make_dir(output_dir)

                # Watch the directory for new files
                watcher = self.sandbox.files.watch_dir(output_dir, recursive=True)
                self._watchers_with_dirs.append((watcher, output_dir))

                logger.debug(f"Set up file watcher for directory: {output_dir}")

            except Exception as e:
                logger.debug(f"Could not set up watcher for {output_dir}: {str(e)}")
                continue

    def _process_single_event(self, event: Any, output_dir: str) -> None:
        """Process a single filesystem event and add created files to the list.

        Args:
            event: The filesystem event to process.
            output_dir: The directory being watched.
        """
        if not (hasattr(event, "name") and hasattr(event, "type")):
            return

        if str(event.type) != "FilesystemEventType.CREATE":
            logger.debug(f"Ignored filesystem event: {event.type} - {event.name}")
            return

        # Construct full path by combining output_dir with filename
        full_path = f"{output_dir}/{event.name}".replace("//", "/")
        logger.info(f"New file created: {full_path}")
        if full_path not in self._created_files:
            self._created_files.append(full_path)

    def _process_watcher_events(self, watcher: Any, output_dir: str) -> None:
        """Process all events from a single watcher.

        Args:
            watcher: The filesystem watcher instance.
            output_dir: The directory being watched.
        """
        try:
            events = watcher.get_new_events()
            for event in events:
                logger.debug(f"Event: {event}")
                self._process_single_event(event, output_dir)
            watcher.stop()
        except Exception as e:
            logger.debug(f"Error processing watcher events: {str(e)}")

    async def process_events(self) -> None:
        """Process filesystem events from watchers and update created files list."""
        # Poll for file system events (allow time for events to be generated)
        await asyncio.sleep(0.5)

        for watcher, output_dir in self._watchers_with_dirs:
            self._process_watcher_events(watcher, output_dir)

    def reset_created_files(self) -> None:
        """Reset the list of created files."""
        self._created_files = []

    def get_created_files(self) -> list[str]:
        """Get the list of files created during monitoring.

        Returns:
            list[str]: List of file paths that were created.
        """
        return self._created_files.copy()


class MyE2BCloudSandbox(E2BCloudSandbox):
    """Extended E2B Cloud Sandbox with filesystem monitoring capabilities."""

    def __init__(self, *args, **kwargs):
        """Initialize the sandbox with monitoring capabilities.

        Args:
            *args: Positional arguments forwarded to ``E2BCloudSandbox``.
            **kwargs: Keyword arguments forwarded to ``E2BCloudSandbox``.
        """
        super().__init__(*args, **kwargs)
        self.file_watcher: SandboxFileWatcher | None = None

    async def execute_code(
        self,
        code: str,
        timeout: int = 30,
        files: list[Attachment] | None = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute code in the E2B Cloud sandbox with filesystem monitoring.

        This override fixes the Pydantic validation error by ensuring execution.error
        is converted to string. Always enables filesystem monitoring to track
        created files.

        Args:
            code (str): The code to execute.
            timeout (int, optional): Maximum execution time in seconds. Defaults to 30.
            files (list[Attachment] | None, optional): List of Attachment objects with file details. Defaults to None.
            **kwargs (Any): Additional execution parameters.

        Returns:
            ExecutionResult: Structured result of the execution.

        Raises:
            RuntimeError: If sandbox is not initialized.
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox is not initialized")

        start_time = time.time()

        try:
            # Initialize filesystem monitoring
            self.file_watcher = SandboxFileWatcher(self.sandbox)
            self.file_watcher.reset_created_files()
            self.file_watcher.setup_monitoring()

            self._upload_files(files)
            # Pre-populate the variable `df` for direct use in the code
            if files:
                logger.info("Pre-populating the variable `df` with the data from the file.")
                self.sandbox.run_code(f"import pandas as pd; df = pd.read_csv('{DATA_FILE_PATH}')", timeout=timeout)
            execution = self.sandbox.run_code(code, timeout=timeout)
            duration_ms = calculate_duration_ms(start_time)
            status = ExecutionStatus.ERROR if execution.error else ExecutionStatus.SUCCESS

            # Process filesystem events
            if self.file_watcher:
                await self.file_watcher.process_events()
                created_files_count = len(self.file_watcher.get_created_files())
                logger.info(f"File monitoring detected {created_files_count} newly created files")

            # Fix: Convert execution.error to string
            return ExecutionResult.create(
                status=status,
                code=code,
                stdout=(execution.logs.stdout[0] if execution.logs and execution.logs.stdout else ""),
                stderr=(execution.logs.stderr[0] if execution.logs and execution.logs.stderr else ""),
                error=(str(execution.error) if execution.error else ""),  # Convert to string here
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.warning(f"Error executing code in {self.language} sandbox: {str(e)}")
            return ExecutionResult.create(
                status=ExecutionStatus.ERROR,
                code=code,
                error=str(e),
                duration_ms=calculate_duration_ms(start_time),
            )

    def get_created_files(self) -> list[str]:
        """Get the list of files created during the last monitored execution.

        Returns:
            list[str]: List of file paths that were created.
        """
        if self.file_watcher:
            return self.file_watcher.get_created_files()
        return []

    def download_file(self, file_path: str) -> bytes | None:
        """Download file content from the sandbox.

        Uses download_url method to get a direct URL and downloads via HTTP,
        which avoids the binary corruption issue with files.read().

        Args:
            file_path (str): Path to the file in the sandbox.

        Returns:
            bytes | None: File content as bytes, or None if download fails.

        Raises:
            RuntimeError: If sandbox is not initialized.
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox is not initialized")

        try:
            if hasattr(self.sandbox, "download_url"):
                logger.info(f"Downloading {file_path} via download_url method")

                # Get the download URL
                url = self.sandbox.download_url(file_path)
                logger.debug(f"Got download URL: {url}")

                response = requests.get(url, timeout=30)

                if response.status_code == HTTPStatus.OK:
                    content = response.content
                    logger.info(f"Successfully downloaded {len(content)} bytes via URL")
                    return content
                else:
                    logger.warning(f"URL download failed with status {response.status_code}")

            return None

        except Exception as e:
            logger.warning(f"Failed to download file {file_path}: {str(e)}")
            return None
