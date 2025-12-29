from _typeshed import Incomplete
from aip_agents.a2a.types import get_mime_type_from_filename as get_mime_type_from_filename
from aip_agents.tools.code_sandbox.constant import DATA_FILE_NAME as DATA_FILE_NAME
from aip_agents.tools.code_sandbox.e2b_cloud_sandbox_extended import MyE2BCloudSandbox as MyE2BCloudSandbox
from aip_agents.utils.artifact_helpers import ArtifactHandler as ArtifactHandler, create_multiple_artifacts_response as create_multiple_artifacts_response
from aip_agents.utils.logger import get_logger as get_logger
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from typing import Any

logger: Incomplete

class E2BCodeSandboxInput(BaseModel):
    """Input schema for the E2BCodeSandboxTool."""
    code: str
    data_source: str | list[dict[str, Any]] | None
    timeout: int
    language: str
    additional_packages: list[str] | None

class E2BCodeSandboxTool(BaseTool):
    """Tool to execute Python code in E2B Cloud Sandbox."""
    name: str
    description: str
    save_output_history: bool
    args_schema: type[BaseModel]
    api_key: str
    default_additional_packages: list[str]
    store_final_output: bool
