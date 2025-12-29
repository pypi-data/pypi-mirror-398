"""Simple mock tool that returns references for testing reference propagation.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from gllm_core.schema import Chunk
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class MockRetrievalInput(BaseModel):
    """Input schema for the MockRetrievalTool."""

    query: str = Field(..., description="Search query")


class MockRetrievalTool(BaseTool):
    """Mock tool that returns hardcoded references for testing."""

    name: str = "mock_retrieval"
    description: str = "Mock retrieval tool that returns sample references for testing reference propagation."
    args_schema: type[BaseModel] = MockRetrievalInput
    save_output_history: bool = True

    def _run(self, query: str) -> str:
        """Return a simple mock response.

        Args:
            query (str): The search query to process.

        Returns:
            str: Mock retrieval result for the query.
        """
        return f"Mock retrieval result for: {query}"

    def _format_agent_reference(self, tool_output: str) -> list[Chunk]:
        """Return hardcoded references for testing.

        Args:
            tool_output (str): The tool output to format as references.

        Returns:
            list[Chunk]: List of formatted chunks for the query.
        """
        query = tool_output.split(":")[-1].strip()
        return [
            Chunk(
                content=f"Mock reference 1 for query: {query}",
                metadata={"tool_name": "mock_retrieval", "source": "Mock Database", "title": "Mock Reference 1"},
            ),
            Chunk(
                content=f"Mock reference 2 for query: {query}",
                metadata={"tool_name": "mock_retrieval", "source": "Mock Database", "title": "Mock Reference 2"},
            ),
        ]
