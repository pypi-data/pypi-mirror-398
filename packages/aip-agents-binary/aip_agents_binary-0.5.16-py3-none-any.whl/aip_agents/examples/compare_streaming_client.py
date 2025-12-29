"""Client script to compare direct SSE streaming vs A2A connector streaming.

This script demonstrates:
1. Creating an agent with the same tools as the server
2. Running arun_sse_stream (direct) and recording the SSE chunks
3. Using A2AConnector.astream_to_agent (connector) to get chunks from the server
4. Comparing both outputs side-by-side

Prerequisites:
    Start the server first:
        poetry run python -m aip_agents.examples.compare_streaming_server

Then run this client:
    poetry run python -m aip_agents.examples.compare_streaming_client

Authors:
    AI Agent Platform Team
"""

import asyncio
import base64
import json
from copy import deepcopy
from typing import Any

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.mock_retrieval_tool import MockRetrievalTool
from aip_agents.examples.tools.pii_demo_tools import (
    get_customer_info,
    get_employee_data,
    get_user_profile,
)
from aip_agents.examples.tools.random_chart_tool import RandomChartTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool
from aip_agents.schema.a2a import A2AStreamEventType
from aip_agents.schema.agent import A2AClientConfig
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_URL = "http://localhost:18999"


def create_local_agent(enable_token_streaming: bool = False) -> LangGraphAgent:
    """Create a local agent with the same tools as the server.

    Args:
        enable_token_streaming: Whether to enable token streaming for content_chunk events.
    """
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, streaming=enable_token_streaming)
    table_tool = TableGeneratorTool()
    mock_retrieval_tool = MockRetrievalTool()
    random_chart_tool = RandomChartTool()

    visualization_agent = LangGraphAgent(
        name="RandomChartAgent",
        instruction=(
            "You are a visualization specialist. Whenever someone asks for a chart, visualization, "
            "image, or snapshot of insights, you MUST call the random_chart_tool to generate a bar chart artifact. "
            "Always explain what the generated chart represents."
        ),
        model=llm,
        tools=[random_chart_tool],
    )

    agent = LangGraphAgent(
        name="LocalComparisonAgent",
        instruction=(
            "You are a helpful assistant for testing streaming comparison. "
            "When asked for a table, use the table_generator tool. "
            "When asked to search or retrieve, use the mock_retrieval tool. "
            "When asked for customer information, use the get_customer_info tool. "
            "When asked for employee data, use the get_employee_data tool. "
            "When asked for user profile, use the get_user_profile tool. "
            "IMPORTANT: When you receive PII placeholders like <PERSON_1>, pass them WITH the angle brackets <> "
            "to the tools - they are required for the PII system to work correctly. "
            "Always use the tools when relevant to demonstrate artifacts, references, and PII masking."
        ),
        model=llm,
        tools=[table_tool, mock_retrieval_tool, get_customer_info, get_employee_data, get_user_profile],
        agents=[visualization_agent],
        enable_a2a_token_streaming=False,
    )
    return agent


def format_chunk_summary(chunk: dict[str, Any], index: int) -> str:
    """Format a chunk for display."""
    lines = [f"  [{index}] event_type={chunk.get('event_type')}, task_state={chunk.get('task_state')}"]

    content = chunk.get("content")
    if content:
        preview = content[:80].replace("\n", "\\n")
        if len(content) > 80:
            preview += "..."
        lines.append(f"       content: {preview}")

    if chunk.get("artifacts"):
        for art in chunk["artifacts"]:
            lines.append(f"       artifact: {art.get('name', art.get('artifact_name', 'unknown'))}")

    metadata = chunk.get("metadata", {})
    if metadata.get("references"):
        lines.append(f"       references: {len(metadata['references'])} items")
    if metadata.get("tool_info"):
        tool_info = metadata["tool_info"]
        # Handle tool_call events (array of tools) vs tool_result events (single tool)
        if "tool_calls" in tool_info:
            tool_names = [tc.get("name", "?") for tc in tool_info.get("tool_calls", [])]
            lines.append(f"       tool_info: [{', '.join(tool_names)}]")
        else:
            tool_name = tool_info.get("name", "unknown")
            lines.append(f"       tool_info: {tool_name}")

    lines.append(f"       final={chunk.get('final')}, status={chunk.get('status')}")
    return "\n".join(lines)


async def run_direct_streaming(
    agent: LangGraphAgent, query: str, pii_mapping: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    """Run arun_sse_stream and collect all chunks."""
    print("Running direct SSE streaming (arun_sse_stream)...")
    chunks = []

    try:
        async for chunk in agent.arun_sse_stream(
            query, task_id="direct-task", context_id="direct-ctx", pii_mapping=pii_mapping
        ):
            chunks.append(chunk)
    except Exception as e:
        logger.error(f"Error in direct streaming: {e}")
        chunks.append({"status": "error", "content": str(e), "event_type": "error", "final": True})

    return chunks


async def run_connector_streaming(
    agent: LangGraphAgent, query: str, pii_mapping: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    """Run astream_to_agent via A2A connector and collect all chunks."""
    print("Running connector streaming (astream_to_agent)...")
    chunks = []

    # Discover agents from the server
    client_a2a_config = A2AClientConfig(discovery_urls=[SERVER_URL])
    agent_cards = agent.discover_agents(client_a2a_config)

    if not agent_cards:
        logger.error("No agents discovered from server!")
        return [{"status": "error", "content": "No agents discovered", "event_type": "error", "final": True}]

    agent_card = agent_cards[0]
    print(f"Discovered agent: {agent_card.name}")

    try:
        async for chunk in agent.astream_to_agent(agent_card=agent_card, message=query, pii_mapping=pii_mapping):
            chunks.append(chunk)
    except Exception as e:
        logger.error(f"Error in connector streaming: {e}")
        chunks.append({"status": "error", "content": str(e), "event_type": "error", "final": True})

    return chunks


def get_chunk_keys(chunks: list[dict[str, Any]]) -> set[str]:
    """Get all unique keys across all chunks."""
    keys: set[str] = set()
    for chunk in chunks:
        # Convert keys to str to handle StrEnum keys (they are strings but type shows differently)
        keys.update(str(k) for k in chunk.keys())
        # Also get metadata keys
        if "metadata" in chunk and isinstance(chunk["metadata"], dict):
            keys.update(f"metadata.{str(k)}" for k in chunk["metadata"].keys())
    return keys


def get_field_types(chunks: list[dict[str, Any]], field: str) -> set[str]:
    """Get all types seen for a field across chunks.

    Note: StrEnum values are reported as 'str' since they ARE strings
    and serialize identically over HTTP/SSE.
    """
    types: set[str] = set()
    for chunk in chunks:
        if "." in field:
            parent, child = field.split(".", 1)
            value = chunk.get(parent, {}).get(child) if isinstance(chunk.get(parent), dict) else None
        else:
            value = chunk.get(field)
        if value is not None:
            # StrEnum IS a string - report as 'str' for comparison purposes
            # since they serialize identically over HTTP/SSE
            if isinstance(value, str):
                types.add("str")
            else:
                types.add(type(value).__name__)
    return types


def group_chunks_by_event_type(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group chunks by their event_type."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        # Ensure the grouping key is always a non-empty string
        raw_type = chunk.get("event_type")
        event_type = str(raw_type) if raw_type else "unknown"
        groups.setdefault(event_type, []).append(chunk)
    return groups


def _is_empty_payload_chunk(chunk: dict[str, Any]) -> bool:
    return chunk.get("content") in (None, "") and chunk.get("reason") == "empty_payload"


def _is_base64_payload(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if len(candidate) < 24:
        return False
    if len(candidate) % 4 != 0:
        return False
    try:
        base64.b64decode(candidate, validate=True)
    except Exception:
        return False
    return True


def _filter_chunks_for_comparison(event_type: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter out known non-equivalent chunks so comparisons match semantic parity.

    - A2A connector can emit placeholder status updates with content=None and reason=empty_payload.
      These should not be compared against the real status_update chunk.
    - A2A connector can emit an artifact payload chunk (base64 content) as a tool_result with
      missing tool_info metadata. This is not equivalent to the tool_result completion message.
    """
    if event_type == A2AStreamEventType.STATUS_UPDATE.value:
        meaningful = [c for c in chunks if not _is_empty_payload_chunk(c)]
        return meaningful if meaningful else chunks

    if event_type == A2AStreamEventType.TOOL_RESULT.value:
        filtered: list[dict[str, Any]] = []
        for c in chunks:
            md = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            has_tool_info = isinstance(md, dict) and md.get("tool_info") is not None
            if not has_tool_info and c.get("artifacts") and _is_base64_payload(c.get("content")):
                continue
            filtered.append(c)
        return filtered if filtered else chunks

    return chunks


def compare_chunk_structure(chunk1: dict[str, Any], chunk2: dict[str, Any]) -> dict[str, Any]:
    """Compare structure of two chunks and return differences."""
    keys1 = {str(k) for k in chunk1.keys()}
    keys2 = {str(k) for k in chunk2.keys()}

    # Add metadata keys
    if "metadata" in chunk1 and isinstance(chunk1["metadata"], dict):
        keys1.update(f"metadata.{str(k)}" for k in chunk1["metadata"].keys())
    if "metadata" in chunk2 and isinstance(chunk2["metadata"], dict):
        keys2.update(f"metadata.{str(k)}" for k in chunk2["metadata"].keys())

    differences = {
        "keys_only_in_first": sorted(keys1 - keys2),
        "keys_only_in_second": sorted(keys2 - keys1),
        "keys_in_both": sorted(keys1 & keys2),
        "type_differences": [],
    }

    # Check type differences for common keys
    for key in sorted(keys1 & keys2):
        if key.startswith("metadata."):
            parent, child = key.split(".", 1)
            val1 = chunk1.get(parent, {}).get(child)
            val2 = chunk2.get(parent, {}).get(child)
        else:
            val1 = chunk1.get(key)
            val2 = chunk2.get(key)

        if val1 is not None and val2 is not None:
            type1 = "str" if isinstance(val1, str) else type(val1).__name__
            type2 = "str" if isinstance(val2, str) else type(val2).__name__
            if type1 != type2:
                differences["type_differences"].append(
                    {
                        "field": key,
                        "type1": type1,
                        "type2": type2,
                    }
                )

    return differences


def _get_chunk_keys_flat(chunk: dict[str, Any]) -> set[str]:
    """Get all keys from a single chunk, flattening metadata."""
    keys: set[str] = set()
    for k in chunk.keys():
        keys.add(str(k))
    if "metadata" in chunk and isinstance(chunk["metadata"], dict):
        for mk in chunk["metadata"].keys():
            keys.add(f"metadata.{str(mk)}")
    return keys


def _get_chunk_value(chunk: dict[str, Any], key: str) -> Any:
    """Get value for a key, handling metadata.* keys."""
    if key.startswith("metadata."):
        _, child = key.split(".", 1)
        meta = chunk.get("metadata")
        if isinstance(meta, dict):
            return meta.get(child)
        return None
    return chunk.get(key)


def _normalize_type(val: Any) -> str:
    """Get normalized type name. StrEnum and str are treated as 'str'."""
    if val is None:
        return "NoneType"
    if isinstance(val, str):
        return "str"
    return type(val).__name__


def _compare_common_keys_across_chunks(
    direct_chunks: list[dict[str, Any]],
    connector_chunks: list[dict[str, Any]],
    common_keys: set[str],
) -> dict[str, Any]:
    """Compare values for common keys: check None vs non-None and type consistency."""
    value_issues: list[dict[str, Any]] = []
    type_issues: list[dict[str, Any]] = []

    for key in sorted(common_keys):
        # Collect all values for this key from both sides
        direct_vals = [_get_chunk_value(c, key) for c in direct_chunks]
        connector_vals = [_get_chunk_value(c, key) for c in connector_chunks]

        direct_has_value = any(v is not None for v in direct_vals)
        connector_has_value = any(v is not None for v in connector_vals)

        # Check None vs non-None mismatch
        if direct_has_value != connector_has_value:
            direct_example = next((v for v in direct_vals if v is not None), None)
            connector_example = next((v for v in connector_vals if v is not None), None)
            value_issues.append(
                {
                    "key": key,
                    "direct_has_value": direct_has_value,
                    "connector_has_value": connector_has_value,
                    "direct_example": str(direct_example)[:150] if direct_example else None,
                    "connector_example": str(connector_example)[:150] if connector_example else None,
                }
            )

        # Check type consistency (only for non-None values)
        direct_types = {_normalize_type(v) for v in direct_vals if v is not None}
        connector_types = {_normalize_type(v) for v in connector_vals if v is not None}

        if direct_types and connector_types and direct_types != connector_types:
            direct_example = next((v for v in direct_vals if v is not None), None)
            connector_example = next((v for v in connector_vals if v is not None), None)
            type_issues.append(
                {
                    "key": key,
                    "direct_types": sorted(direct_types),
                    "connector_types": sorted(connector_types),
                    "direct_example": str(direct_example)[:150] if direct_example else None,
                    "connector_example": str(connector_example)[:150] if connector_example else None,
                }
            )

    return {"value_issues": value_issues, "type_issues": type_issues}


def compare_event_type_groups(
    direct_groups: dict[str, list[dict[str, Any]]],
    connector_groups: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Compare chunks grouped by event type - RAW comparison without filtering."""
    all_event_types = set(direct_groups.keys()) | set(connector_groups.keys())

    canonical_types = {
        A2AStreamEventType.STATUS_UPDATE.value,
        A2AStreamEventType.CONTENT_CHUNK.value,
        A2AStreamEventType.TOOL_CALL.value,
        A2AStreamEventType.TOOL_RESULT.value,
        A2AStreamEventType.FINAL_RESPONSE.value,
        A2AStreamEventType.ERROR.value,
    }

    event_comparisons = {}
    for event_type in sorted(all_event_types):
        direct_chunks = direct_groups.get(event_type, [])
        connector_chunks = connector_groups.get(event_type, [])

        # Collect ALL keys seen across ALL chunks of this event type
        direct_all_keys: set[str] = set()
        connector_all_keys: set[str] = set()
        for c in direct_chunks:
            direct_all_keys.update(_get_chunk_keys_flat(c))
        for c in connector_chunks:
            connector_all_keys.update(_get_chunk_keys_flat(c))

        keys_only_direct = sorted(direct_all_keys - connector_all_keys)
        keys_only_connector = sorted(connector_all_keys - direct_all_keys)
        common_keys = direct_all_keys & connector_all_keys

        # For keys that differ, find example chunks and values
        direct_extra_examples: list[dict[str, Any]] = []
        for key in keys_only_direct:
            for idx, c in enumerate(direct_chunks):
                val = _get_chunk_value(c, key)
                if val is not None:
                    direct_extra_examples.append(
                        {
                            "key": key,
                            "chunk_index": idx,
                            "value": val,
                            "chunk_preview": {
                                k: (str(v)[:100] if isinstance(v, str | list | dict) else v)
                                for k, v in c.items()
                                if k != "metadata"
                            },
                        }
                    )
                    break

        connector_extra_examples: list[dict[str, Any]] = []
        for key in keys_only_connector:
            for idx, c in enumerate(connector_chunks):
                val = _get_chunk_value(c, key)
                if val is not None:
                    connector_extra_examples.append(
                        {
                            "key": key,
                            "chunk_index": idx,
                            "value": val,
                            "chunk_preview": {
                                k: (str(v)[:100] if isinstance(v, str | list | dict) else v)
                                for k, v in c.items()
                                if k != "metadata"
                            },
                        }
                    )
                    break

        # Compare common keys for value presence and type consistency
        common_key_comparison = _compare_common_keys_across_chunks(direct_chunks, connector_chunks, common_keys)

        has_issues = (
            keys_only_direct
            or keys_only_connector
            or common_key_comparison["value_issues"]
            or common_key_comparison["type_issues"]
        )

        comparison = {
            "direct_count": len(direct_chunks),
            "connector_count": len(connector_chunks),
            "direct_all_keys": sorted(direct_all_keys),
            "connector_all_keys": sorted(connector_all_keys),
            "keys_only_in_direct": keys_only_direct,
            "keys_only_in_connector": keys_only_connector,
            "direct_extra_examples": direct_extra_examples,
            "connector_extra_examples": connector_extra_examples,
            "common_keys": sorted(common_keys),
            "value_issues": common_key_comparison["value_issues"],
            "type_issues": common_key_comparison["type_issues"],
            "structure_match": not has_issues,
        }

        event_comparisons[event_type] = comparison

    return {
        "event_comparisons": event_comparisons,
        "canonical_types": sorted(canonical_types),
        "tested_types": sorted(all_event_types),
        "missing_types": sorted(canonical_types - all_event_types),
    }


def compare_chunks(direct_chunks: list[dict[str, Any]], connector_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare the two chunk lists and produce a comprehensive structural summary."""
    direct_keys = get_chunk_keys(direct_chunks)
    connector_keys = get_chunk_keys(connector_chunks)

    # Required fields per SSE chunk schema
    required_fields = {"status", "task_state", "event_type", "final", "metadata"}

    # Group by event type for detailed comparison
    direct_groups = group_chunks_by_event_type(direct_chunks)
    connector_groups = group_chunks_by_event_type(connector_chunks)
    event_type_comparison = compare_event_type_groups(direct_groups, connector_groups)

    comparison = {
        # Basic counts
        "direct_count": len(direct_chunks),
        "connector_count": len(connector_chunks),
        # Schema keys
        "direct_keys": sorted(direct_keys),
        "connector_keys": sorted(connector_keys),
        "keys_only_in_direct": sorted(direct_keys - connector_keys),
        "keys_only_in_connector": sorted(connector_keys - direct_keys),
        "keys_in_both": sorted(direct_keys & connector_keys),
        # Required fields check
        "direct_has_required_fields": required_fields.issubset(direct_keys),
        "connector_has_required_fields": required_fields.issubset(connector_keys),
        # Event types
        "direct_event_types": [c.get("event_type") for c in direct_chunks],
        "connector_event_types": [c.get("event_type") for c in connector_chunks],
        # Type consistency
        "direct_all_event_types_string": all(
            isinstance(c.get("event_type"), str) for c in direct_chunks if c.get("event_type")
        ),
        "connector_all_event_types_string": all(
            isinstance(c.get("event_type"), str) for c in connector_chunks if c.get("event_type")
        ),
        # Artifacts and references
        "direct_has_artifacts": any(c.get("artifacts") for c in direct_chunks),
        "connector_has_artifacts": any(c.get("artifacts") for c in connector_chunks),
        "direct_has_references": any(c.get("metadata", {}).get("references") for c in direct_chunks),
        "connector_has_references": any(c.get("metadata", {}).get("references") for c in connector_chunks),
        # Final chunk status
        "direct_final_status": direct_chunks[-1].get("status") if direct_chunks else None,
        "connector_final_status": connector_chunks[-1].get("status") if connector_chunks else None,
        "direct_final_task_state": direct_chunks[-1].get("task_state") if direct_chunks else None,
        "connector_final_task_state": connector_chunks[-1].get("task_state") if connector_chunks else None,
        # Per-event-type comparison
        "event_type_comparison": event_type_comparison,
    }

    # Field type comparison for common keys
    common_keys = direct_keys & connector_keys
    type_mismatches = []
    for key in sorted(common_keys):
        if key.startswith("metadata."):
            continue  # Skip nested for now
        direct_types = get_field_types(direct_chunks, key)
        connector_types = get_field_types(connector_chunks, key)
        if direct_types != connector_types and direct_types and connector_types:
            type_mismatches.append(
                {
                    "field": key,
                    "direct_types": sorted(direct_types),
                    "connector_types": sorted(connector_types),
                }
            )
    comparison["type_mismatches"] = type_mismatches

    return comparison


def print_event_type_comparison(event_comparison: dict[str, Any]) -> None:
    """Print per-event-type comparison details with exact key/value examples."""
    print("\n--- PER-EVENT-TYPE COMPARISON (RAW, NO FILTERING) ---")

    canonical = event_comparison["canonical_types"]
    tested = event_comparison["tested_types"]
    missing = event_comparison["missing_types"]

    print(f"  Canonical event types: {canonical}")
    print(f"  Tested event types:    {tested}")
    if missing:
        print(f"  ⚠️  Missing event types (not tested): {missing}")
    else:
        print("  ✓ All canonical event types tested")

    print("\n  Per-event breakdown:")
    for event_type, comp in sorted(event_comparison["event_comparisons"].items()):
        direct_count = comp["direct_count"]
        connector_count = comp["connector_count"]
        structure_match = comp["structure_match"]

        status_icon = "✓" if structure_match else "⚠️"
        print(f"\n    {status_icon} {event_type}: [direct={direct_count} chunks, connector={connector_count} chunks]")
        print(f"        Direct keys:    {comp['direct_all_keys']}")
        print(f"        Connector keys: {comp['connector_all_keys']}")

        if comp["keys_only_in_direct"]:
            print(f"        ❌ Keys ONLY in direct: {comp['keys_only_in_direct']}")
            for ex in comp.get("direct_extra_examples", []):
                val_preview = str(ex["value"])[:200]
                print(f"           └─ key='{ex['key']}' in chunk[{ex['chunk_index']}]")
                print(f"              value: {val_preview}")
                print(f"              chunk: {ex['chunk_preview']}")

        if comp["keys_only_in_connector"]:
            print(f"        ❌ Keys ONLY in connector: {comp['keys_only_in_connector']}")
            for ex in comp.get("connector_extra_examples", []):
                val_preview = str(ex["value"])[:200]
                print(f"           └─ key='{ex['key']}' in chunk[{ex['chunk_index']}]")
                print(f"              value: {val_preview}")
                print(f"              chunk: {ex['chunk_preview']}")

        # Show value issues (one has value, other is None)
        if comp.get("value_issues"):
            print("        ❌ Value presence mismatch (None vs non-None):")
            for issue in comp["value_issues"]:
                print(f"           └─ key='{issue['key']}'")
                print(f"              direct has value: {issue['direct_has_value']} -> {issue['direct_example']}")
                print(
                    f"              connector has value: {issue['connector_has_value']} -> {issue['connector_example']}"
                )

        # Show type issues
        if comp.get("type_issues"):
            print("        ❌ Type mismatch (str/StrEnum treated same):")
            for issue in comp["type_issues"]:
                print(f"           └─ key='{issue['key']}'")
                print(f"              direct types: {issue['direct_types']} -> {issue['direct_example']}")
                print(f"              connector types: {issue['connector_types']} -> {issue['connector_example']}")

        if structure_match:
            print("        ✓ Keys, values, and types match between direct and connector")


def print_structure_comparison(comparison: dict[str, Any]) -> None:
    """Print detailed structure comparison."""
    print("\n--- SCHEMA STRUCTURE ---")
    print(f"  Direct keys:    {comparison['direct_keys']}")
    print(f"  Connector keys: {comparison['connector_keys']}")

    if comparison["keys_only_in_direct"]:
        print(f"  ⚠️  Keys ONLY in direct:    {comparison['keys_only_in_direct']}")
    if comparison["keys_only_in_connector"]:
        print(f"  ⚠️  Keys ONLY in connector: {comparison['keys_only_in_connector']}")

    print("\n--- REQUIRED FIELDS CHECK ---")
    print(
        f"  Direct has required fields (status, task_state, event_type, final, metadata): {comparison['direct_has_required_fields']}"
    )
    print(f"  Connector has required fields: {comparison['connector_has_required_fields']}")

    print("\n--- TYPE CONSISTENCY ---")
    print(f"  Direct event_type always string:    {comparison['direct_all_event_types_string']}")
    print(f"  Connector event_type always string: {comparison['connector_all_event_types_string']}")

    if comparison["type_mismatches"]:
        print("\n  ⚠️  Type mismatches found:")
        for mismatch in comparison["type_mismatches"]:
            print(
                f"      {mismatch['field']}: direct={mismatch['direct_types']}, connector={mismatch['connector_types']}"
            )
    else:
        print("  ✓ No type mismatches in common fields")

    # Per-event-type comparison
    if "event_type_comparison" in comparison:
        print_event_type_comparison(comparison["event_type_comparison"])

    print("\n--- CONTENT COMPARISON ---")
    print(f"  Direct chunk count:     {comparison['direct_count']}")
    print(f"  Connector chunk count:  {comparison['connector_count']}")
    print(f"  Direct has artifacts:     {comparison['direct_has_artifacts']}")
    print(f"  Connector has artifacts:  {comparison['connector_has_artifacts']}")
    print(f"  Direct has references:    {comparison['direct_has_references']}")
    print(f"  Connector has references: {comparison['connector_has_references']}")

    print("\n--- FINAL CHUNK ---")
    print(
        f"  Direct final:    status={comparison['direct_final_status']}, task_state={comparison['direct_final_task_state']}"
    )
    print(
        f"  Connector final: status={comparison['connector_final_status']}, task_state={comparison['connector_final_task_state']}"
    )

    # Overall parity verdict
    print("\n--- PARITY VERDICT ---")
    schema_match = not comparison["keys_only_in_direct"] and not comparison["keys_only_in_connector"]
    type_match = not comparison["type_mismatches"]
    required_match = comparison["direct_has_required_fields"] and comparison["connector_has_required_fields"]
    event_type_match = comparison["direct_all_event_types_string"] and comparison["connector_all_event_types_string"]

    # Check per-event-type parity
    event_parity = True
    if "event_type_comparison" in comparison:
        event_comp = comparison["event_type_comparison"]
        for et_comp in event_comp["event_comparisons"].values():
            if not et_comp["structure_match"]:
                event_parity = False
                break

    if schema_match and type_match and required_match and event_type_match and event_parity:
        print("  ✓ PARITY ACHIEVED: Direct SSE stream output matches connector output structure!")
    else:
        print("  ⚠️  PARITY ISSUES DETECTED:")
        if not schema_match:
            print("      - Schema keys differ")
        if not type_match:
            print("      - Field types differ")
        if not required_match:
            print("      - Missing required fields")
        if not event_type_match:
            print("      - event_type not consistently string")
        if not event_parity:
            print("      - Per-event-type structure differs")


async def main():
    """Main comparison workflow."""
    print("=" * 80)
    print("DIRECT vs CONNECTOR STREAMING COMPARISON")
    print("=" * 80)

    # Query that exercises table, retrieval, visualization (via sub-agent), and PII tool
    # NOTE: The <> angle brackets in <PERSON_1> are required - they're part of the PII tag format
    # that the system recognizes for replacement. Without them, "PERSON_1" won't be detected.
    query = (
        "Generate a small table with 2 rows, search for 'test data', call the RandomChartAgent to produce a "
        "random visualization image, and can you get me information about customers <PERSON_1> and <PERSON_2>?"
    )
    # The pii_mapping keys MUST include the <> brackets to match the tags in the query
    pii_mapping_original = {"<PERSON_1>": "C001", "<PERSON_2>": "C002"}

    # Create local agent (token streaming disabled for now)
    print("\n[1] Creating local agent with artifact and reference tools...")
    agent = create_local_agent(enable_token_streaming=False)
    print(f"    Agent: {agent.name}")
    print(
        "    Tools: table_generator, mock_retrieval, customer_info, employee_data, user_profile (PII), random_chart (sub-agent)"
    )
    print("    Token streaming: disabled (will compare later)")
    # Run direct streaming (local agent, no A2A)
    print("\n[2] Running DIRECT streaming (arun_sse_stream on local agent)...")
    print(f"    Query: {query}")
    pii_mapping_direct = deepcopy(pii_mapping_original)
    direct_chunks = await run_direct_streaming(agent, query, pii_mapping=pii_mapping_direct)
    print(f"    Collected {len(direct_chunks)} chunks")

    # Run connector streaming (via A2A to server)
    print(f"\n[3] Running CONNECTOR streaming (astream_to_agent to {SERVER_URL})...")
    print(f"    Query: {query}")
    pii_mapping_connector = deepcopy(pii_mapping_original)
    connector_chunks = await run_connector_streaming(agent, query, pii_mapping=pii_mapping_connector)
    print(f"    Collected {len(connector_chunks)} chunks")

    # Display results
    print("\n" + "=" * 80)
    print("DIRECT STREAMING CHUNKS (arun_sse_stream)")
    print("=" * 80)
    for i, chunk in enumerate(direct_chunks):
        print(format_chunk_summary(chunk, i))

    print("\n" + "=" * 80)
    print("CONNECTOR STREAMING CHUNKS (astream_to_agent)")
    print("=" * 80)
    for i, chunk in enumerate(connector_chunks):
        print(format_chunk_summary(chunk, i))

    # Comprehensive structure comparison
    print("\n" + "=" * 80)
    print("STRUCTURE COMPARISON (SSE Stream vs A2A Connector)")
    print("=" * 80)
    comparison = compare_chunks(direct_chunks, connector_chunks)
    print_structure_comparison(comparison)

    # Save full output for inspection
    output_file = "streaming_comparison_output.json"
    output_data = {
        "query": query,
        "direct_chunks": direct_chunks,
        "connector_chunks": connector_chunks,
        "comparison": comparison,
    }
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    print(f"\n  Full output saved to: {output_file}")

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
