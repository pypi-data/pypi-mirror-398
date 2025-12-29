from langchain_core.tools import BaseTool
from pydantic import BaseModel

class MockRetrievalInput(BaseModel):
    """Input schema for the MockRetrievalTool."""
    query: str

class MockRetrievalTool(BaseTool):
    """Mock tool that returns hardcoded references for testing."""
    name: str
    description: str
    args_schema: type[BaseModel]
    save_output_history: bool
