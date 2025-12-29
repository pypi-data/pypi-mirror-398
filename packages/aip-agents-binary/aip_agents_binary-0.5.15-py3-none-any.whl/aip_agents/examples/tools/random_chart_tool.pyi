from aip_agents.a2a.types import MimeType as MimeType
from aip_agents.utils.artifact_helpers import create_artifact_command as create_artifact_command
from langchain_core.tools import BaseTool
from pydantic import BaseModel

DEFAULT_RANDOM_CHART_TITLE: str
PIL_AVAILABLE: bool

class RandomChartInput(BaseModel):
    """Input schema for random chart generation."""
    title: str
    num_bars: int
    min_value: int
    max_value: int

class RandomChartTool(BaseTool):
    """Generate random bar chart images without relying on upstream data."""
    name: str
    description: str
    args_schema: type[BaseModel]
