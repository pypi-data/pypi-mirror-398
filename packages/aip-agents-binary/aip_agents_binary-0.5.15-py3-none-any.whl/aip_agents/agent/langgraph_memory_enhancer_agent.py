"""LangGraph Memory Enhancer Agent.

This module implements the ``LangGraphMemoryEnhancerAgent``, a dedicated LangGraph helper agent
that automatically augments user queries with relevant memories before the primary agent runs.
It replaces manual memory tool invocation with a consistent preprocessing layer.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import json
import textwrap
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from aip_agents.agent.langgraph_react_agent import LangGraphReactAgent
from aip_agents.agent.system_instruction_context import get_current_date_context
from aip_agents.memory.guidance import MEM0_MEMORY_RECALL_GUIDANCE
from aip_agents.tools.memory_search_tool import (
    MEMORY_SEARCH_TOOL_NAME,
    LongTermMemorySearchTool,
    Mem0SearchTool,
)
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class LangGraphMemoryEnhancerAgent(LangGraphReactAgent):
    """Simplified mini-agent for automatic memory retrieval and query enhancement.

    This agent has a simple 2-node LangGraph (agent + tools) and uses existing memory
    infrastructure to enhance user queries with relevant context. It acts as a
    preprocessing layer that automatically attempts memory retrieval for every query.

    Key features:
    - Uses runtime `memory_user_id` provided via call arguments (no static storage)
    - Uses simplified instruction reusing existing guidance
    - Standard 2-node LangGraph pattern (agent -> tools -> agent)
    - Automatically enhances queries with memory context when available
    - Returns original query unchanged if no relevant memories found
    """

    def __init__(self, memory, **kwargs) -> None:
        """Initialize the LangGraphMemoryEnhancerAgent with memory backend and configuration.

        Args:
            memory: Memory backend instance (Mem0Memory or compatible)
            **kwargs: Additional arguments passed to BaseLangGraphAgent, including:
                - memory_agent_id: Fallback user ID for memory operations
                - model: LLM model to use for memory decisions
                - Other BaseLangGraphAgent parameters
        """
        memory_tool: LongTermMemorySearchTool = Mem0SearchTool(
            memory=memory,
            default_user_id=kwargs.get("memory_agent_id"),
            user_id_provider=None,
        )
        kwargs["save_interaction_to_memory"] = False
        super().__init__(
            name="LangGraphMemoryEnhancerAgent",
            instruction=self._build_simple_instruction(),
            tools=[memory_tool],
            **kwargs,
        )

    def _build_simple_instruction(self) -> str:
        """Build simplified memory recall instruction reusing existing components.

        Returns:
            str: Complete instruction including date context and memory guidance
        """
        date_context = get_current_date_context()

        instruction = textwrap.dedent(f"""
        {date_context}

        You are a Memory Recall Agent that ONLY decides whether and how to call a memory search tool.

        Important: You WILL NOT see the tool results. The system will append any retrieved memory
        to the user input after your turn. Your sole responsibility is to trigger the correct tool
        calls with concise arguments based on the user's message.

        What to do:
        1. Read the user's message as-is (do not rephrase it).
        2. Call the tool `built_in_mem0_search` with minimal, relevant args. Prefer a single call,
           but you MAY make multiple calls when clearly needed (e.g., separate topics or distinct
           time ranges). Avoid duplicate or redundant calls.
           - If the user implies a time frame (e.g., "yesterday", "last week"), set `time_period`.
           - If the user implies a precise range, set `start_date`/`end_date` (YYYY-MM-DD).
           - If the user mentions a topic, set a concise `query` (few words or at most a sentence).
           - Adjust `limit` to higher number to allow more memory to be retrieved if needed.
           - Default when uncertain: omit dates, set a concise `query` derived from the message,
             and set `limit=10`.
        3. Do NOT answer the user's question. Do NOT summarize. Do NOT format output. The system will handle it.

        Constraints:
        - Keep tool arguments succinct and precise; avoid verbose or speculative queries.
        - Never invent facts. If unsure about time ranges, prefer omitting dates rather than fabricating.
        - Do not include any preambles or explanations in your messages.
         - Make one or more tool calls as needed; avoid duplicates or redundant calls.

        Reference guidance:
        {MEM0_MEMORY_RECALL_GUIDANCE}
        """).strip()

        return instruction

    async def _memory_retrieval_node(self, state: dict, config: dict | None = None) -> dict:
        """Execute memory retrieval using explicit tool calls or synthesized defaults.

        Args:
            state: LangGraph state containing the conversation `messages` history.
            config: Optional LangGraph configuration forwarded to the memory tool.

        Returns:
            dict: State update whose `messages` list contains `ToolMessage` outputs.
        """
        messages = state.get("messages", [])
        tool_calls = self._extract_mem0_tool_calls(messages)

        if tool_calls:
            tool_messages = await self._execute_mem0_tool_calls(tool_calls, state, config)
            return {"messages": tool_messages}

        default_query = self._extract_last_human_query(messages)
        tool_messages = await self._execute_default_retrieval(default_query, state, config)
        return {"messages": tool_messages}

    def _extract_mem0_tool_calls(self, messages: list) -> list[dict[str, Any]]:
        """Return all Mem0 tool calls from the last message if present.

        Args:
            messages: Ordered list of LangChain message objects representing the state.

        Returns:
            List of tool call dictionaries filtered for the Mem0 search tool.
        """
        if not messages:
            return []

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None)
        if not tool_calls:
            return []

        return [tc for tc in tool_calls if tc.get("name") == MEMORY_SEARCH_TOOL_NAME]

    async def _execute_mem0_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        state: dict,
        config: dict | None,
    ) -> list[ToolMessage]:
        """Execute the provided Mem0 tool calls and return their messages.

        Args:
            tool_calls: Tool call dictionaries emitted by the LLM.
            state: LangGraph state containing messages and metadata.
            config: Optional runnable configuration forwarded to the tool.

        Returns:
            List of `ToolMessage` objects describing each execution result.
        """
        tool_messages: list[ToolMessage] = []
        for index, tool_call in enumerate(tool_calls):
            logger.info("Executing memory search tool call #%s with args: %s", index, tool_call.get("args", {}))
            tool_messages.append(await self._execute_mem0_call(tool_call.get("args", {}), state, config))
        return tool_messages

    async def _execute_default_retrieval(
        self,
        default_query: str | None,
        state: dict,
        config: dict | None,
    ) -> list[ToolMessage]:
        """Perform a default retrieval when the LLM does not request tools.

        Args:
            default_query: Latest human utterance content or ``None`` if unavailable.
            state: LangGraph state with message history and metadata.
            config: Optional runnable configuration forwarded to the tool.

        Returns:
            Single-item list containing the resulting `ToolMessage`.
        """
        args = self._build_default_mem0_args(default_query)
        tool_message = await self._execute_mem0_call(args, state, config)
        return [tool_message]

    def _build_default_mem0_args(self, query: str | None) -> dict[str, Any]:
        """Create safe default arguments for the Mem0 search tool.

        Args:
            query: Latest human utterance used to derive the search query.

        Returns:
            Dictionary of keyword arguments passed to the Mem0 search tool.
        """
        if query:
            trimmed_query = query[:128]
        else:
            trimmed_query = None

        return {"query": trimmed_query, "limit": 10}

    async def _execute_mem0_call(
        self,
        args: dict[str, Any],
        state: dict,
        config: dict | None,
    ) -> ToolMessage:
        """Execute a single Mem0 tool call with metadata resolution.

        Args:
            args: Base arguments supplied by the LLM or synthesized defaults.
            state: LangGraph state that may include additional metadata.
            config: Optional runnable configuration forwarded to the tool.

        Returns:
            `ToolMessage` containing raw tool output or an error description.
        """
        args_with_metadata = self._merge_metadata(args, state)
        tool_config = self._create_tool_config(config, state, tool_name=MEMORY_SEARCH_TOOL_NAME)
        mem0_tool = self.resolved_tools[0]

        try:
            result = await mem0_tool.ainvoke(args_with_metadata, config=tool_config)
            content = str(result)
        except Exception as exc:
            content = f"Error executing memory search: {exc}"

        return ToolMessage(content=content, tool_call_id=args.get("id", ""))

    def _merge_metadata(self, args: dict[str, Any], state: dict) -> dict[str, Any]:
        """Merge resolved metadata into tool arguments.

        Args:
            args: Tool arguments that may already include metadata.
            state: LangGraph state providing globally resolved metadata values.

        Returns:
            Copy of ``args`` containing merged metadata entries.
        """
        args_with_metadata = dict(args)
        effective_metadata = self._resolve_effective_metadata(state)
        if not effective_metadata:
            return args_with_metadata

        existing_metadata = args_with_metadata.get("metadata")
        if isinstance(existing_metadata, dict):
            merged_metadata = {**effective_metadata, **existing_metadata}
        else:
            merged_metadata = effective_metadata

        args_with_metadata["metadata"] = merged_metadata
        return args_with_metadata

    def _resolve_effective_metadata(self, state: dict) -> dict[str, Any] | None:
        """Resolve metadata for the Mem0 tool, swallowing resolution errors.

        Args:
            state: LangGraph state whose ``metadata`` key may include overrides.

        Returns:
            Resolved metadata dictionary or ``None`` if not available.
        """
        raw_metadata = state.get("metadata")
        if not isinstance(raw_metadata, dict):
            return None

        try:
            return self._resolve_tool_metadata(MEMORY_SEARCH_TOOL_NAME, raw_metadata)
        except Exception:
            return None

    def _extract_last_human_query(self, messages: list) -> str | None:
        """Return the content of the most recent `HumanMessage` if available.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            Text content of the last human message or ``None``.
        """
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                if isinstance(message.content, str):
                    return message.content
                return str(message.content)
        return None

    def _finalize_node(self, state: dict) -> dict:
        """Assemble the enhanced query returned by the memory recall agent.

        Collects raw memory results from all tool calls, deduplicates by memory ID,
        formats the unique memories, and combines with the original user query.

        Args:
            state: LangGraph state containing the original conversation messages and the
                tool outputs generated by `_memory_retrieval_node`.

        Returns:
            dict: State update with a single `AIMessage` that concatenates the original user
                query and any deduplicated memory context.
        """
        messages = state.get("messages", [])
        original_query = self._extract_last_human_query(messages) or self._fallback_query(messages)
        memories = self._collect_unique_memories(messages)
        tagged_memory = self._format_memories(memories)

        final_text = (f"{original_query}\n\n" + tagged_memory).strip()
        return {"messages": [AIMessage(content=final_text)]}

    def _fallback_query(self, messages: list) -> str:
        """Fallback to the last message content when no human message is present.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            The string representation of the last message content.
        """
        if not messages:
            return ""
        last_message = messages[-1]
        content = getattr(last_message, "content", "")
        return content if isinstance(content, str) else str(content)

    def _collect_unique_memories(self, messages: list) -> list[dict[str, Any]]:
        """Collect and deduplicate memory hits from tool messages.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            List of memory dictionaries with unique memory identifiers.
        """
        unique_memories: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for message in messages:
            for memory in self._extract_memories_from_message(message):
                memory_id = memory.get("id")
                if not memory_id or memory_id in seen_ids:
                    continue

                seen_ids.add(memory_id)
                unique_memories.append(memory)

        return unique_memories

    def _extract_memories_from_message(self, message: Any) -> list[dict[str, Any]]:
        """Return parsed memory dictionaries contained in a tool message.

        Args:
            message: Message instance that may contain memory tool output.

        Returns:
            List of memory dictionaries or an empty list when no memories are present.
        """
        if not isinstance(message, ToolMessage):
            return []

        raw_results = self._parse_tool_message_content(message)
        return [memory for memory in raw_results if isinstance(memory, dict)]

    def _parse_tool_message_content(self, message: ToolMessage) -> list[Any]:
        """Parse the JSON content of a tool message into a list.

        Args:
            message: Tool message emitted by the memory search tool.

        Returns:
            List extracted from the tool message content or an empty list on failure.
        """
        try:
            raw_results = json.loads(message.content)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning(
                "Failed to parse tool result as JSON: %s, content: %s...",
                exc,
                message.content[:200],
            )
            return []

        if not isinstance(raw_results, list):
            return []

        return raw_results

    def _format_memories(self, memories: list[dict[str, Any]]) -> str:
        """Format memory hits using the underlying tool formatter.

        Args:
            memories: Deduplicated list of memory dictionaries.

        Returns:
            Tagged string representation of the relevant memories.
        """
        if not memories:
            return ""
        return self.resolved_tools[0].format_hits(memories, with_tag=True)

    def define_graph(self, graph_builder: StateGraph) -> CompiledStateGraph:
        """Define the 3-node memory recall LangGraph for this agent.

        This creates a streamlined ReAct-inspired structure that reuses
        `LangGraphReactAgent` helpers for robust LM invocation, token usage tracking,
        error handling, and tool execution.

        Args:
            graph_builder: LangGraph `StateGraph` builder instance used to register nodes and
                edges for compilation.

        Returns:
            CompiledStateGraph: The compiled memory recall graph ready for execution.
        """
        # Reuse parent's robust node implementations
        # Simple 3-step structure for single pass: agent -> memory_retrieval -> finalize -> END
        agent_node = self._create_agent_node()  # Handles LM invoker + LangChain + token usage
        graph_builder.add_node("agent", agent_node)
        graph_builder.add_node("memory_retrieval", self._memory_retrieval_node)
        graph_builder.add_node("finalize", self._finalize_node)
        graph_builder.add_edge("agent", "memory_retrieval")
        graph_builder.add_edge("memory_retrieval", "finalize")
        graph_builder.add_edge("finalize", END)
        graph_builder.set_entry_point("agent")

        return graph_builder.compile(checkpointer=self.checkpointer)
