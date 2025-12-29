"""Demo: LangChain agent with allowed_tools whitelist filtering.

Shows how allowed_tools restricts tool access across 3 MCP servers:
- STDIO: only get_current_time allowed (not generate_uuid or get_weather_forecast)
- SSE: only get_random_quote allowed (not word_count or get_weather_forecast)
- HTTP: only get_random_fact allowed (not convert_to_base64 or get_weather_forecast)

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import logging
from typing import Any

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.examples.mcp_configs.configs import mcp_tool_whitelisting_demo
from aip_agents.schema.a2a import A2AStreamEventType
from aip_agents.utils.logger import logger_manager


def _normalize_event_type(raw_value: Any) -> A2AStreamEventType | None:
    """Convert raw event_type payloads (enum or string) into A2AStreamEventType.

    Args:
        raw_value: Event type payload emitted by the agent stream (enum or string).

    Returns:
        Parsed A2AStreamEventType value, or None when the payload is unrecognized.
    """
    if isinstance(raw_value, A2AStreamEventType):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return A2AStreamEventType(raw_value.lower())
        except ValueError:
            return None
    return None


def _log_tool_call(event: dict[str, Any], is_allowed: bool) -> bool:
    """Log tool call events and return True if at least one call existed.

    Args:
        event: A2A event payload containing tool_call metadata.
        is_allowed: Whether the current query is expected to hit an allowed tool.

    Returns:
        True when at least one tool call entry is present; False otherwise.
    """
    tool_info = event.get("tool_info") or {}
    tool_calls = tool_info.get("tool_calls") or []
    if not tool_calls:
        print("⚠️ Tool call event received without tool_calls payload")
        return False

    first_call = tool_calls[0]
    tool_name = first_call.get("name", "unknown")
    icon = "⚠️" if not is_allowed else "✅"
    print(f"{icon} Tool called: {tool_name}")
    return True


async def process_query(agent, query: str, is_allowed: bool = True) -> bool:
    """Process a single query and report if tools were called.

    Args:
        agent: The LangChain agent to run.
        query: The query to process.
        is_allowed: Whether this query should use allowed tools.

    Returns:
        True if at least one tool was called while processing the query, False otherwise.
    """
    print(f"\nQuery: {query}")
    tool_called = False
    final_response = None
    try:
        async for event in agent.arun_a2a_stream(query=query):
            event_type = _normalize_event_type(event.get("event_type"))
            if event_type is None:
                print(f"⚠️ Unknown event type payload: {event.get('event_type')!r}")
                continue

            if event_type is A2AStreamEventType.TOOL_CALL:
                tool_called = _log_tool_call(event, is_allowed) or tool_called
                continue

            if event_type is A2AStreamEventType.FINAL_RESPONSE:
                final_response = event.get("content")
                break
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return False
    if final_response:
        print(f"🧠 LLM response: {final_response}")
    if not tool_called:
        print("✅ No tool called (blocked or LLM answered directly)")
    return tool_called


async def main():
    """Demo allowed_tools filtering with 3 MCP servers (STDIO, SSE, HTTP)."""
    logger_manager.set_level(logging.WARNING)

    agent = LangChainAgent(
        name="allowed_tools_demo",
        instruction=(
            "You are a helpful assistant with access to tools from 3 MCP servers.\n"
            "Use the available tools to answer questions.\n"
            "Note: Each server has specific tools whitelisted via allowed_tools."
        ),
        model=ChatOpenAI(model="gpt-4.1-mini"),
    )
    agent.add_mcp_server(mcp_tool_whitelisting_demo)

    all_allowed_queries_called_tools = True
    any_disallowed_query_called_tools = False

    print("\n=== ALLOWED TOOLS (should work) ===")
    allowed_queries = [
        "Get the current time for me",
        "Tell me an inspirational quote",
        "Share a fun fact with me",
    ]
    for query in allowed_queries:
        called = await process_query(agent, query, is_allowed=True)
        all_allowed_queries_called_tools = all_allowed_queries_called_tools and called

    print("\n\n=== DISALLOWED TOOLS (should fail or skip) ===")
    disallowed_queries = [
        "Generate a UUID for me",  # Not allowed from STDIO
        "Get the weather forecast for Jakarta",  # Not allowed from any server
        "Count words in 'hello world'",  # Not allowed from SSE
    ]
    for query in disallowed_queries:
        called = await process_query(agent, query, is_allowed=False)
        any_disallowed_query_called_tools = any_disallowed_query_called_tools or called

    print("\n=== SUMMARY: allowed_tools vs disabled_tools behavior ===")
    if all_allowed_queries_called_tools:
        print("✅ allowed_tools: All allowed queries called tools as expected.")
    else:
        print("❌ allowed_tools: Some allowed queries did not call any tools.")

    if any_disallowed_query_called_tools:
        print("❌ disabled_tools: Some disallowed queries still called tools.")
    else:
        print("✅ disabled_tools: No tools were called for any disallowed queries.")


if __name__ == "__main__":
    asyncio.run(main())
