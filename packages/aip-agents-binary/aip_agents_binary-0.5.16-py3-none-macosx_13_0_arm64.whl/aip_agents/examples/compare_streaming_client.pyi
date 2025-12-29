from _typeshed import Incomplete
from aip_agents.agent import LangGraphAgent as LangGraphAgent
from aip_agents.examples.tools.mock_retrieval_tool import MockRetrievalTool as MockRetrievalTool
from aip_agents.examples.tools.pii_demo_tools import get_customer_info as get_customer_info, get_employee_data as get_employee_data, get_user_profile as get_user_profile
from aip_agents.examples.tools.random_chart_tool import RandomChartTool as RandomChartTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool as TableGeneratorTool
from aip_agents.schema.a2a import A2AStreamEventType as A2AStreamEventType
from aip_agents.schema.agent import A2AClientConfig as A2AClientConfig
from aip_agents.utils.logger import get_logger as get_logger
from typing import Any

logger: Incomplete
SERVER_URL: str

def create_local_agent(enable_token_streaming: bool = False) -> LangGraphAgent:
    """Create a local agent with the same tools as the server.

    Args:
        enable_token_streaming: Whether to enable token streaming for content_chunk events.
    """
def format_chunk_summary(chunk: dict[str, Any], index: int) -> str:
    """Format a chunk for display."""
async def run_direct_streaming(agent: LangGraphAgent, query: str, pii_mapping: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Run arun_sse_stream and collect all chunks."""
async def run_connector_streaming(agent: LangGraphAgent, query: str, pii_mapping: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Run astream_to_agent via A2A connector and collect all chunks."""
def get_chunk_keys(chunks: list[dict[str, Any]]) -> set[str]:
    """Get all unique keys across all chunks."""
def get_field_types(chunks: list[dict[str, Any]], field: str) -> set[str]:
    """Get all types seen for a field across chunks.

    Note: StrEnum values are reported as 'str' since they ARE strings
    and serialize identically over HTTP/SSE.
    """
def group_chunks_by_event_type(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group chunks by their event_type."""
def compare_chunk_structure(chunk1: dict[str, Any], chunk2: dict[str, Any]) -> dict[str, Any]:
    """Compare structure of two chunks and return differences."""
def compare_event_type_groups(direct_groups: dict[str, list[dict[str, Any]]], connector_groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Compare chunks grouped by event type - RAW comparison without filtering."""
def compare_chunks(direct_chunks: list[dict[str, Any]], connector_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare the two chunk lists and produce a comprehensive structural summary."""
def print_event_type_comparison(event_comparison: dict[str, Any]) -> None:
    """Print per-event-type comparison details with exact key/value examples."""
def print_structure_comparison(comparison: dict[str, Any]) -> None:
    """Print detailed structure comparison."""
async def main() -> None:
    """Main comparison workflow."""
