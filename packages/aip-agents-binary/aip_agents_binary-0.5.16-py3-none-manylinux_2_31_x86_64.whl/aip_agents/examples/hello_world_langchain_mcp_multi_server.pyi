from aip_agents.agent import LangChainAgent as LangChainAgent
from aip_agents.examples.mcp_configs.configs import mcp_tool_whitelisting_demo as mcp_tool_whitelisting_demo
from aip_agents.schema.a2a import A2AStreamEventType as A2AStreamEventType
from aip_agents.utils.logger import logger_manager as logger_manager

async def process_query(agent, query: str, is_allowed: bool = True) -> bool:
    """Process a single query and report if tools were called.

    Args:
        agent: The LangChain agent to run.
        query: The query to process.
        is_allowed: Whether this query should use allowed tools.

    Returns:
        True if at least one tool was called while processing the query, False otherwise.
    """
async def main() -> None:
    """Demo allowed_tools filtering with 3 MCP servers (STDIO, SSE, HTTP)."""
