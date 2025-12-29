"""Tool for E2B Cloud Sandbox code execution.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Komang Elang Surya Prawira (komang.e.s.prawira@gdplabs.id)
"""

import asyncio
import json
import os
from typing import Any

import pandas as pd
from gllm_inference.schema import Attachment
from gllm_tools.code_interpreter.code_sandbox.e2b_cloud_sandbox import E2BCloudSandbox
from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import BaseModel, Field

from aip_agents.a2a.types import get_mime_type_from_filename
from aip_agents.tools.code_sandbox.constant import DATA_FILE_NAME
from aip_agents.tools.code_sandbox.e2b_cloud_sandbox_extended import MyE2BCloudSandbox
from aip_agents.utils.artifact_helpers import (
    ArtifactHandler,
    create_multiple_artifacts_response,
)
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class E2BCodeSandboxInput(BaseModel):
    """Input schema for the E2BCodeSandboxTool."""

    code: str = Field(
        ...,
        description=(
            "Python code to execute in the sandbox. "
            "If `data_source` is provided, the data will be automatically pre-loaded into "
            "the sandbox as a Pandas DataFrame. "
            "You can access the data directly via a variable named `df`. "
            "The final result must be printed to stdout."
        ),
        min_length=1,
    )
    data_source: str | list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "The data source used during code execution. "
            "It can be a tool output reference (using $tool_output) or  raw data. "
            "If the code requires a data source, this field should not be left empty. "
            "When an output reference is available, prioritize the output reference over raw data."
        ),
    )
    timeout: int = Field(default=30, description="Maximum execution time in seconds", ge=1, le=300)
    language: str = Field(default="python", description="Programming language for the sandbox")
    additional_packages: list[str] | None = Field(
        default=None,
        description="Additional Python packages to install before execution",
    )


class E2BCodeSandboxTool(BaseTool):
    """Tool to execute Python code in E2B Cloud Sandbox."""

    name: str = "e2b_sandbox_tool"
    description: str = (
        "Useful for executing Python code in a secure cloud sandbox environment. "
        "Input should include the Python code to execute and optional data source, timeout, and packages. "
        "Returns execution results including stdout, stderr, and any errors. "
        "Automatically downloads all files created during execution as artifacts."
    )
    save_output_history: bool = Field(default=True)
    args_schema: type[BaseModel] = E2BCodeSandboxInput
    api_key: str = Field(
        default_factory=lambda: os.getenv("E2B_API_KEY", ""),
        description="E2B API key for cloud sandbox access",
    )
    default_additional_packages: list[str] = Field(
        default_factory=lambda: [
            pkg.strip() for pkg in os.getenv("E2B_SANDBOX_TOOL_ADDITIONAL_PACKAGES", "").split(",") if pkg.strip()
        ],
        description="Default additional packages from environment variable",
    )
    store_final_output: bool = False

    def _run(
        self,
        code: str,
        data_source: str | list[dict[str, Any]] | None = None,
        timeout: int = 30,
        language: str = "python",
        additional_packages: list[str] | None = None,
    ) -> str | dict[str, Any]:
        """Execute code in E2B Cloud Sandbox and return the result with artifacts.

        This method calls the async _arun method to avoid code duplication.

        Args:
            code (str): The Python code to execute.
            data_source (str | list[dict[str, Any]] | None, optional): Data source to be used during code execution.
                Defaults to None.
            timeout (int, optional): Maximum execution time in seconds. Defaults to 30.
            language (str, optional): Programming language for the sandbox. Defaults to "python".
            additional_packages (list[str] | None, optional): Additional packages to install. Defaults to None.

        Returns:
            str | dict[str, Any]: The execution result as JSON string, or dict with artifacts if files downloaded.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._arun(code, data_source, timeout, language, additional_packages))
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"Error in synchronous execution wrapper: {str(e)}")
            return self._create_error_result(code, str(e))

    def _create_error_result(self, code: str, error_message: str, duration_ms: int = 0) -> str:
        """Create a standardized error result.

        Args:
            code (str): The code that was being executed.
            error_message (str): The error message.
            duration_ms (int, optional): Duration in milliseconds. Defaults to 0.

        Returns:
            str: JSON string of error result.
        """
        error_result = {
            "status": "error",
            "code": code,
            "stdout": "",
            "stderr": "",
            "error": error_message,
            "duration_ms": duration_ms,
        }
        return json.dumps(error_result, indent=2)

    def _prepare_packages(self, additional_packages: list[str] | None) -> list[str]:
        """Prepare the final list of packages by combining defaults with additional packages.

        Args:
            additional_packages (list[str] | None): Additional packages to install.

        Returns:
            list[str]: Deduplicated list of packages.
        """
        all_packages = list(self.default_additional_packages) + (additional_packages or [])
        return list(dict.fromkeys(all_packages))

    def _convert_execution_result_to_dict(self, result) -> dict[str, Any]:
        """Convert execution result to dictionary for JSON serialization.

        Args:
            result: The execution result from sandbox.

        Returns:
            dict[str, Any]: Dictionary representation of the result.
        """
        return {
            "status": (result.status.value if hasattr(result.status, "value") else str(result.status)),
            "code": result.code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": str(result.error) if result.error else "",
            "duration_ms": result.duration_ms,
        }

    async def _arun(
        self,
        code: str,
        data_source: str | list[dict[str, Any]] | None = None,
        timeout: int = 30,
        language: str = "python",
        additional_packages: list[str] | None = None,
    ) -> str | dict[str, Any]:
        """Async version of code execution in E2B Cloud Sandbox.

        Args:
            code (str): The Python code to execute.
            data_source (str | list[dict[str, Any]] | None, optional): Data source to be used during code execution.
                Defaults to None.
            timeout (int, optional): Maximum execution time in seconds. Defaults to 30.
            language (str, optional): Programming language for the sandbox. Defaults to "python".
            additional_packages (list[str] | None, optional): Additional packages to install. Defaults to None.

        Returns:
            str | dict[str, Any]: The execution result as JSON string, or dict with artifacts if files downloaded.
        """
        sandbox = None
        try:
            if isinstance(data_source, str) and data_source.startswith("$tool_output"):
                logger.warning(f"Reference {data_source!r} not resolved! Skipping the code execution.")
                return self._create_error_result(code, f"Reference {data_source!r} not resolved!")

            files = await self._create_files(data_source)
            sandbox = await self._create_sandbox(language, additional_packages)
            result = await sandbox.execute_code(code, timeout=timeout, files=files)
            return await self._process_execution_result(sandbox, result)

        except Exception as e:
            logger.error(f"Error executing code in E2B sandbox: {str(e)}")
            return self._create_error_result(code, str(e))

        finally:
            self._cleanup_sandbox(sandbox)

    async def _create_files(self, data_source: Command | list[dict[str, Any]] | None) -> list[Attachment] | None:
        """Create files from data source.

        This method will convert the data source to a CSV file and return it as an Attachment object,
        as required by the E2B Cloud Sandbox library.

        Args:
            data_source (Command | list[dict[str, Any]] | None): Data source to be used during code execution.

        Returns:
            list[Attachment] | None: List of Attachment objects.

        Note:
        1. Command is the expected data type when this method receives data from the tool output sharing.
        2. The known use cases so far only require a single file, hence the current implementation only accepts
            a single list of dictionaries and creates one file, even though the Sandbox supports multiple files.
        """
        if isinstance(data_source, Command):
            data_source: list[dict[str, Any]] = data_source.update["result"]

        if not (isinstance(data_source, list) and data_source and all(isinstance(row, dict) for row in data_source)):
            if not data_source:
                logger.info("No data source provided. Ignoring the data source.")
            else:
                logger.warning(
                    "Unsupported `data_source` type. Expected a non-empty list of dictionaries. "
                    "Ignoring the data source.",
                )
            return None

        try:
            logger.info("Creating files from data source to upload to the sandbox...")
            df = pd.DataFrame(data_source)
            csv_string = df.to_csv(index=False)
            csv_bytes = csv_string.encode("utf-8")
            return [Attachment.from_bytes(csv_bytes, filename=DATA_FILE_NAME)]
        except Exception as e:
            logger.warning(f"Error creating files from data source: {str(e)}. Ignoring the data source.")
            return None

    async def _create_sandbox(self, language: str, additional_packages: list[str] | None) -> MyE2BCloudSandbox:
        """Create and initialize the E2B Cloud Sandbox.

        Args:
            language (str): Programming language for the sandbox.
            additional_packages (list[str] | None): Additional packages to install.

        Returns:
            MyE2BCloudSandbox: Initialized sandbox instance.
        """
        unique_packages = self._prepare_packages(additional_packages)

        return MyE2BCloudSandbox(
            api_key=self.api_key,
            language=language,
            additional_packages=unique_packages,
        )

    async def _process_execution_result(self, sandbox: MyE2BCloudSandbox, result: Any) -> str | dict[str, Any]:
        """Process the execution result and handle file artifacts.

        Args:
            sandbox (MyE2BCloudSandbox): The sandbox instance.
            result (Any): The execution result from sandbox.

        Returns:
            str | dict[str, Any]: Processed result as JSON or dict with artifacts.
        """
        result_dict = self._convert_execution_result_to_dict(result)
        created_files = sandbox.get_created_files()

        if not created_files:
            result_dict["message"] = "No new files were created during execution"
            return json.dumps(result_dict, indent=2)

        downloaded_artifacts = self._create_artifacts_from_files(sandbox, created_files)

        if downloaded_artifacts:
            execution_summary = self._create_execution_summary(result_dict, created_files)
            return create_multiple_artifacts_response(result=execution_summary, artifacts=downloaded_artifacts)

        logger.warning("Files were detected but could not be downloaded")
        return json.dumps(result_dict, indent=2)

    def _cleanup_sandbox(self, sandbox: MyE2BCloudSandbox | None) -> None:
        """Clean up sandbox resources.

        Args:
            sandbox (MyE2BCloudSandbox | None): The sandbox instance to cleanup.
        """
        if sandbox:
            try:
                sandbox.terminate()
            except Exception as e:
                logger.warning(f"Error terminating sandbox: {str(e)}")

    def _create_artifacts_from_files(self, sandbox: E2BCloudSandbox, file_paths: list[str]) -> list[dict[str, Any]]:
        """Create artifacts from a list of file paths using ArtifactHandler.

        Args:
            sandbox (E2BCloudSandbox): The active sandbox instance.
            file_paths (list[str]): List of file paths to download.

        Returns:
            list[dict[str, Any]]: List of artifact dictionaries.
        """
        artifacts = []

        try:
            for file_path in file_paths:
                logger.debug(f"Processing newly created file: {file_path}")
                artifact_dict = self._download_and_create_artifact(sandbox, file_path)
                if artifact_dict:
                    artifacts.append(artifact_dict)

        except Exception as e:
            logger.error(f"Error creating artifacts from files: {str(e)}")

        return artifacts

    def _create_execution_summary(self, result_dict: dict[str, Any], created_files: list[str]) -> str:
        """Create execution summary with file information.

        Args:
            result_dict (dict[str, Any]): The execution result dictionary.
            created_files (list[str]): List of created file paths.

        Returns:
            str: Formatted execution summary.
        """
        execution_summary = f"Code executed successfully (status: {result_dict['status']}).\n"

        if result_dict["stdout"]:
            execution_summary += f"Output: {result_dict['stdout']}\n"

        execution_summary += f"Downloaded {len(created_files)} file(s) created during execution:\n\n"

        # Add markdown format for each file, especially images
        for file_path in created_files:
            filename = self._extract_filename(file_path)
            mime_type = get_mime_type_from_filename(filename)

            if mime_type.startswith("image/"):
                # Use just the filename for both alt text and display name
                execution_summary += f"- **{filename}** (Image): ![{filename}]({filename})\n"
            else:
                execution_summary += f"- **{filename}** ({mime_type}): `{file_path}`\n"

        return execution_summary

    def _download_and_create_artifact(self, sandbox: E2BCloudSandbox, file_path: str) -> dict[str, Any] | None:
        """Download a single file and create an artifact using ArtifactHandler.

        Args:
            sandbox (E2BCloudSandbox): The active sandbox instance.
            file_path (str): Path to the file in the sandbox.

        Returns:
            dict[str, Any] | None: Artifact dictionary or None if download failed.
        """
        try:
            # Download file content
            file_content = sandbox.download_file(file_path)
            if file_content is None:
                logger.warning(f"Failed to download file: {file_path}")
                return None

            # Extract filename from path
            filename = self._extract_filename(file_path)

            # Create artifact using ArtifactHandler
            artifact_response = ArtifactHandler().create_file_artifact(
                result=f"File created during execution: {file_path}",
                artifact_data=file_content,
                artifact_name=filename,
                artifact_description=f"File created during execution: {file_path}",
                enable_deduplication=False,
            )

            logger.info(f"Successfully downloaded newly created file: {file_path} ({len(file_content)} bytes)")

            # Return just the artifact part (not the response wrapper)
            return artifact_response["artifact"]

        except Exception as e:
            logger.warning(f"Failed to download file {file_path}: {str(e)}")
            return None

    def _extract_filename(self, file_path: str) -> str:
        """Extract filename from file path with fallback.

        Args:
            file_path (str): The file path.

        Returns:
            str: The extracted filename.
        """
        filename = os.path.basename(file_path)
        if not filename:
            filename = f"sandbox_file_{hash(file_path) % 10000}"
        return filename
