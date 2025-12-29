from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel

logger: Incomplete

class GoogleSerperInput(BaseModel):
    """Input schema for the GoogleSerperTool."""
    query: str

class GoogleSerperTool(BaseTool):
    """Tool to search Google Serper API."""
    name: str
    description: str
    save_output_history: bool
    args_schema: type[BaseModel]
    api_wrapper: GoogleSerperAPIWrapper
