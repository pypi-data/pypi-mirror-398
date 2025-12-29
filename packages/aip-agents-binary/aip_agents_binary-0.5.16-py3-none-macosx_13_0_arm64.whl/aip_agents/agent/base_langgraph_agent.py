"""Base class for LangGraph-based agent implementations.

This class provides the core LangGraph machinery including graph compilation,
state handling, and I/O mapping for LangGraph agents.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import copy
import hashlib
import json
import uuid
from abc import abstractmethod
from collections.abc import AsyncGenerator, Sequence
from concurrent.futures import Future
from contextlib import suppress
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Annotated, Any

from a2a.types import AgentCard
from aiostream import stream as astream
from gllm_core.event import EventEmitter
from gllm_core.event.handler import StreamEventHandler
from gllm_core.schema import Chunk
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Checkpointer, StreamWriter
from pydantic import ValidationError
from typing_extensions import TypedDict

from aip_agents.agent.base_agent import BaseAgent
from aip_agents.agent.system_instruction_context import get_current_date_context
from aip_agents.constants import TEXT_PREVIEW_LENGTH
from aip_agents.mcp.client import LangchainMCPClient
from aip_agents.memory import BaseMemory, MemoryFactory, MemoryMethod
from aip_agents.memory.constants import MemoryDefaults
from aip_agents.schema.agent import StreamMode
from aip_agents.schema.hitl import HitlMetadata
from aip_agents.tools.tool_config_injector import (
    CONFIG_SCHEMA_ATTR,
    TOOL_CONFIG_SCHEMA_ATTR,
    inject_config_methods_into_tool,
)
from aip_agents.types import A2AEvent, A2AStreamEventType
from aip_agents.utils import augment_query_with_file_paths, validate_references
from aip_agents.utils.langgraph.tool_managers.a2a_tool_manager import A2AToolManager
from aip_agents.utils.langgraph.tool_managers.delegation_tool_manager import (
    DelegationToolManager,
)
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata.activity_metadata_helper import create_tool_activity_info
from aip_agents.utils.metadata_helper import (
    DefaultStepMessages,
    Kind,
    MetadataFieldKeys,
    Status,
    end_step_counter_scope,
    get_next_step_number,
    start_step_counter_scope,
)
from aip_agents.utils.pii import deanonymize_final_response_content
from aip_agents.utils.sse_chunk_transformer import SSEChunkTransformer
from aip_agents.utils.step_limit_manager import _STEP_LIMIT_CONFIG_CVAR
from aip_agents.utils.token_usage_helper import (
    STEP_USAGE_KEY,
    TOTAL_USAGE_KEY,
    USAGE_METADATA_KEY,
)

logger = get_logger(__name__)

# Context variable to access current thread_id during streaming callbacks
_THREAD_ID_CVAR: ContextVar[str | None] = ContextVar("aip_agents_thread_id", default=None)


# Context variable to track operation mode for dependency tracking
# "parallel" = include all completed steps (default for backward compatibility)
# "sequential" = include only the most recent completed step
_OPERATION_MODE_CVAR: ContextVar[str] = ContextVar("aip_agents_operation_mode", default="parallel")


@dataclass
class _StreamingContext:
    """Context object for managing streaming state and configuration."""

    original_query: str
    graph_input: dict[str, Any]
    config: dict[str, Any]
    memory_user_id: str | None
    current_thread_id: str
    token: Any
    enable_token_streaming: bool

    # Streaming state
    final_event_yielded: bool = False
    pending_artifacts: list | None = None
    seen_artifact_hashes: set | None = None
    processed_message_count: int = 0
    final_state: dict[str, Any] | None = None
    last_final_content: str | None = None
    saved_memory: bool = False
    is_token_streaming: bool = False

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.pending_artifacts is None:
            self.pending_artifacts = []
        if self.seen_artifact_hashes is None:
            self.seen_artifact_hashes = set()
        if self.final_state is None:
            self.final_state = {}


class BaseLangGraphAgent(BaseAgent):
    """Base class for LangGraph-based agents with unified tool approach.

    Provides core LangGraph functionality including:
    - Graph compilation and execution
    - State schema management
    - I/O mapping between user inputs and graph states
    - Event emission support
    - Tool resolution and handling
    - A2A communication capabilities via tools
    - Agent delegation capabilities via tools
    - MCP server integration via tools
    - Enhanced output extraction from various state formats

    Tool Management:
    - regular_tools: Standard LangChain tools provided during initialization
    - mcp_tools: Tools retrieved from MCP servers
    - resolved_tools: Combined collection of all tools for graph execution

    Subclasses must implement:
    - define_graph(): Define the specific graph structure
    - _prepare_graph_input(): Convert user input to graph state
    - _format_graph_output(): Convert final graph state to user output
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        instruction: str,
        description: str | None = None,
        model: Any | None = None,
        tools: Sequence[BaseTool] | None = None,
        state_schema: type | None = None,
        thread_id_key: str = "thread_id",
        event_emitter: EventEmitter | None = None,
        checkpointer: Checkpointer | None = None,
        enable_a2a_token_streaming: bool = False,
        **kwargs: Any,
    ):
        """Initialize the BaseLangGraphAgent.

        Args:
            name: The name of the agent.
            instruction: The system instruction for the agent.
            description: Human-readable description of the agent.
            model: The model to use (lm_invoker, LangChain model, string, etc.).
            tools: Sequence of regular LangChain tools (not A2A or delegation tools).
            state_schema: The state schema for the LangGraph. Defaults to basic message state.
            thread_id_key: Key for thread ID in configuration.
            event_emitter: Optional event emitter for streaming updates.
            checkpointer: Optional checkpointer for conversation persistence.
            enable_a2a_token_streaming: Enable token-level streaming for A2A responses.
                - False (default): Stream message-level events only
                - True: Stream individual tokens plus message-level events
            **kwargs: Additional keyword arguments passed to BaseAgent (including tool_configs and memory settings).
                Memory settings include:
                - memory_backend: Memory backend (e.g., "mem0")
                - agent_id: Agent identifier for memory scoping
                - memory_namespace: Memory namespace
                - save_interaction_to_memory: Whether to save interactions (default True)
        """
        super().__init__(
            name=name,
            instruction=instruction,
            description=description,
            model=model,
            tools=list(tools) if tools else [],
            **kwargs,
        )

        self._add_system_date_context()

        self.state_schema = state_schema
        self.thread_id_key = thread_id_key
        self.enable_a2a_token_streaming = enable_a2a_token_streaming
        self.event_emitter = event_emitter
        self.checkpointer = checkpointer

        self._mem0_client: Any | None = None
        self.memory: BaseMemory | None = None
        self._initialize_memory_from_kwargs(name, kwargs)

        self.a2a_tool_manager = A2AToolManager()
        self.delegation_tool_manager = DelegationToolManager(parent_agent=self)

        self.regular_tools: list[BaseTool] = self._resolve_and_validate_tools()
        self.mcp_tools: list[BaseTool] = []
        self.resolved_tools: list[BaseTool] = self.regular_tools.copy()

        self._compiled_graph = self._build_and_compile_graph()

        self._tool_parent_map_by_thread: dict[str, dict[str, str]] = {}
        self._completed_tool_steps_by_thread: dict[str, list[str]] = {}
        self._last_status_step_id_by_thread: dict[str, str] = {}
        self._coordinator_completed_tool_steps_by_thread: dict[str, list[str]] = {}
        self._emitted_tool_calls_by_thread: dict[str, set[str]] = {}

    def _create_default_event_emitter(self) -> EventEmitter:
        """Create default event emitter for token streaming.

        Returns:
            EventEmitter with StreamEventHandler configured for token streaming.
        """
        stream_handler = StreamEventHandler(name=f"{self.name}_A2AStreamHandler")
        logger.info(f"Agent '{self.name}': Auto-created event emitter for token streaming")
        return EventEmitter(handlers=[stream_handler])

    def _log_streaming_event_debug(self, source: str, event: dict[str, Any]) -> None:
        """Log the raw streaming event for debugging purposes.

        Args:
            source: A short label describing where the event originated.
            event: The event payload emitted by the streaming pipeline.
        """
        try:
            logger.info("Streaming event (%s): %s", source, event)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to log streaming event: %s", exc, exc_info=True)

    def _record_emitted_tool_calls(self, tool_calls_details: list[dict[str, Any]]) -> None:
        """Track tool call IDs that have already been emitted to avoid duplicates.

        Args:
            tool_calls_details: Tool call metadata emitted by the tool_call event.
        """
        thread_id = _THREAD_ID_CVAR.get()
        if not thread_id or not tool_calls_details:
            return

        emitted = self._emitted_tool_calls_by_thread.setdefault(thread_id, set())
        for details in tool_calls_details:
            call_id = details.get("id")
            if isinstance(call_id, str) and call_id:
                emitted.add(call_id)
                logger.info(
                    "Registered tool call event: agent=%s thread=%s call_id=%s payload=%s",
                    self.name,
                    thread_id,
                    call_id,
                    details,
                )

    def _discard_emitted_tool_call(self, tool_call_id: str | None) -> None:
        """Remove a tool call ID from the emitted tracker.

        Args:
            tool_call_id: Identifier of the tool call to remove from cache.
        """
        if not tool_call_id:
            return
        thread_id = _THREAD_ID_CVAR.get()
        if not thread_id:
            return
        emitted = self._emitted_tool_calls_by_thread.get(thread_id)
        if emitted:
            emitted.discard(tool_call_id)
            logger.info(
                "Cleared recorded tool call: agent=%s thread=%s call_id=%s",
                self.name,
                thread_id,
                tool_call_id,
            )

    def _get_stream_handler(self) -> StreamEventHandler | None:
        """Get StreamEventHandler from event_emitter if available.

        Returns:
            StreamEventHandler instance if found, None otherwise.
        """
        if not self.event_emitter or not self.event_emitter.handlers:
            return None

        for handler in self.event_emitter.handlers:
            if isinstance(handler, StreamEventHandler):
                return handler
        return None

    def _add_system_date_context(self):
        """Prepend the current date context to the agent's system instruction.

        The `get_current_date_context()` helper returns a short natural-language phrase
        describing "today" (e.g., "Today is DD MMM YYYY"). By prepending this
        snippet the agent gains up-to-date temporal grounding for each run,
        which is especially important for prompts that reason about recency or compute
        relative dates.
        """
        date_context = get_current_date_context()
        self.instruction = date_context + "\n\n" + self.instruction
        logger.info(f"Agent '{self.name}': Prepended current date context to system instruction")

    def set_operation_mode(self, mode: str) -> None:
        """Set the operation mode for dependency tracking.

        Args:
            mode: Operation mode - "parallel" (default) or "sequential"
        """
        if mode not in ["parallel", "sequential"]:
            raise ValueError(f"Invalid operation mode: {mode}. Must be 'parallel' or 'sequential'")
        _OPERATION_MODE_CVAR.set(mode)

    def _default_memory_agent_id(self, name: str) -> str:
        """Create a stable identifier for memory scoping.

        Args:
            name: The agent's human-readable name.

        Returns:
            str: A deterministic ID derived from the class and name, suitable for scoping memory per agent.
        """
        base = f"{self.__class__.__name__}:{name}"
        return f"{MemoryDefaults.AGENT_ID_PREFIX}{hashlib.sha256(base.encode()).hexdigest()}"

    @staticmethod
    def _parse_bool_value(value: Any) -> bool:
        """Parse a value to boolean with string handling for "true"/"false".

        Treats string "false" as False, "true" as True.
        For other values, uses standard bool() conversion.

        Args:
            value: The value to parse.

        Returns:
            bool: The parsed boolean value.
        """
        if isinstance(value, str):
            lower_value = value.lower().strip()
            if lower_value == "false":
                return False
            elif lower_value == "true":
                return True
        return bool(value)

    def _memory_enabled(self) -> bool:
        """Check whether memory is enabled for this agent.

        Returns:
            bool: True when a memory adapter is set.
        """
        return self.memory is not None

    def _has_lm_invoker(self) -> bool:
        """Check whether lm_invoker is available for this agent.

        Returns:
            bool: True when lm_invoker attribute exists and is not None.
        """
        return self.lm_invoker is not None

    def _memory_search(self, query: str, override_user_id: str | None = None) -> list[dict[str, Any]]:
        """Search for relevant memories using the configured adapter.

        Args:
            query: The user query to retrieve relevant memories for.
            override_user_id: Optional per-call override for the memory scope.

        Returns:
            list[dict[str, Any]]: Memory hits; empty list on failure or when disabled.
        """
        if not (self._memory_enabled() and isinstance(query, str)):
            return []
        try:
            user_id = override_user_id or self.memory_agent_id
            if hasattr(self.memory, MemoryMethod.SEARCH):
                results = self.memory.search(query=query, user_id=user_id, limit=self.memory_retrieval_limit)  # type: ignore[attr-defined]
                return results if isinstance(results, list) else []
            else:
                return []
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Memory: search ignored error: {e}")
        return []

    def _memory_save_interaction(self, user_text: str, ai_text: str, memory_user_id: str | None = None) -> None:
        """Persist the user/assistant pair using the configured adapter (best-effort).

        Args:
            user_text: The user input text.
            ai_text: The assistant output text.
            memory_user_id: Optional per-call memory scope override.
        """
        if not (self.save_interaction_to_memory and self._memory_enabled() and user_text and ai_text):
            logger.debug("Memory: Skipping save_interaction - saving disabled, memory disabled, or empty text")
            return
        try:
            user_id = memory_user_id or self.memory_agent_id
            logger.info(
                f"Memory: Saving interaction for user_id='{user_id}' - "
                f"User: '{user_text[:TEXT_PREVIEW_LENGTH]}{'...' if len(user_text) > TEXT_PREVIEW_LENGTH else ''}' "
                f"AI: '{ai_text[:TEXT_PREVIEW_LENGTH]}{'...' if len(ai_text) > TEXT_PREVIEW_LENGTH else ''}'"
            )
            save_async = getattr(self.memory, "save_interaction_async", None)
            if callable(save_async):
                future = save_async(user_text=str(user_text), ai_text=str(ai_text), user_id=user_id)
                self._watch_memory_future(future, user_id)
            elif hasattr(self.memory, MemoryMethod.SAVE_INTERACTION):
                self.memory.save_interaction(user_text=str(user_text), ai_text=str(ai_text), user_id=user_id)  # type: ignore[attr-defined]
            else:
                logger.warning(
                    "Memory: save_interaction method NOT available on memory adapter "
                    f"(type: {type(self.memory).__name__})"
                )
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Memory: save_interaction ignored error: {e}")

    @staticmethod
    def _watch_memory_future(future: Any, user_id: str) -> None:
        """Attach logging to asynchronous memory writes.

        Args:
            future: The Future object to monitor for completion.
            user_id: User identifier for logging context.
        """
        if not isinstance(future, Future):
            return

        def _log_completion(done: Future) -> None:
            """Log memory save completion or failure.

            Args:
                done: Future object that has completed.
            """
            exc = done.exception()
            if exc:
                logger.warning("Memory: async save failed for user_id='%s': %s", user_id, exc)

        future.add_done_callback(_log_completion)

    def _resolve_and_validate_tools(self) -> list[BaseTool]:
        """Resolve and validate regular tools for LangGraph usage.

        Also configures tools with injected configuration capabilities
        from agent-level tool_configs.

        Returns:
            List of resolved LangChain BaseTool instances.
        """
        resolved = []
        for tool in self.tools:
            if isinstance(tool, BaseTool):
                self._configure_injected_tool(tool)
                resolved.append(tool)
            else:
                logger.warning(f"Agent '{self.name}': Tool {tool} is not a LangChain BaseTool, skipping")

        logger.info(f"Agent '{self.name}': Resolved {len(resolved)} regular tools for LangGraph")
        return resolved

    def _initialize_memory_from_kwargs(self, agent_name: str, kwargs: dict[str, Any]) -> None:
        """Initialize memory-related settings and adapter.

        Extracts known memory kwargs, sets defaults, and initializes the adapter when enabled.
        Keeps ``__init__`` concise and improves DX.

        Args:
            agent_name: The name of the agent, used to derive a default memory id.
            kwargs: Keyword arguments from the agent constructor; consumed keys are removed.
                Supported memory kwargs:
                - memory_backend: str - Memory backend to use (e.g., "mem0")
                - agent_id: str - Agent identifier for memory scoping
                - memory_namespace: str - Memory namespace
                - memory_retrieval_limit: int - Max memories to retrieve
                - memory_max_chars: int - Max characters per memory
                - save_interaction_to_memory: bool (default True) - Whether to save interactions to memory
        """
        # Initialize memory configuration settings
        self.memory_backend: str | None = kwargs.pop("memory_backend", None)
        self.memory_agent_id: str = str(kwargs.pop("agent_id", self._default_memory_agent_id(agent_name)))
        self.memory_namespace: str | None = kwargs.pop("memory_namespace", None)
        self.memory_retrieval_limit: int = int(kwargs.pop("memory_retrieval_limit", MemoryDefaults.RETRIEVAL_LIMIT))
        self.memory_max_chars: int = int(kwargs.pop("memory_max_chars", MemoryDefaults.MAX_CHARS))

        # Initialize memory interaction saving flag with proper bool conversion
        save_raw = kwargs.pop("save_interaction_to_memory", True)
        self.save_interaction_to_memory: bool = self._parse_bool_value(save_raw)

        if self.memory_backend:
            memory_kwargs = {
                "limit": self.memory_retrieval_limit,
                "max_chars": self.memory_max_chars,
                "agent_id": self.memory_agent_id,
            }
            if self.memory_namespace:
                memory_kwargs["namespace"] = self.memory_namespace

            self._mem0_client = MemoryFactory.create(
                self.memory_backend,
                **memory_kwargs,
            )
            self.memory = self._mem0_client

    def _configure_injected_tool(self, tool: BaseTool) -> None:
        """Configure a tool with automatic configuration injection using agent-level defaults.

        Args:
            tool: The tool instance to configure.
        """
        if self._should_auto_inject_config(tool):
            self._auto_inject_config_capabilities(tool)
            self._apply_agent_config_to_tool(tool)

    def _should_auto_inject_config(self, tool: BaseTool) -> bool:
        """Check if tool needs auto-injection of configuration capabilities.

        Args:
            tool: The tool instance to check.

        Returns:
            True if tool needs auto-injection of configuration capabilities, False otherwise.
        """
        return (
            hasattr(tool, TOOL_CONFIG_SCHEMA_ATTR)
            and getattr(tool, TOOL_CONFIG_SCHEMA_ATTR) is not None
            and not hasattr(tool, CONFIG_SCHEMA_ATTR)
        )

    def _auto_inject_config_capabilities(self, tool: BaseTool) -> None:
        """Inject configuration capabilities into a tool with tool_config_schema.

        Args:
            tool: The tool instance to configure.
        """
        try:
            tool_config_schema = getattr(tool, TOOL_CONFIG_SCHEMA_ATTR)
            inject_config_methods_into_tool(tool, tool_config_schema)
            logger.info(f"Agent '{self.name}': Auto-injected config capabilities into tool '{tool.name}'")
        except Exception as e:
            logger.warning(f"Agent '{self.name}': Failed to auto-inject config into tool '{tool.name}': {e}")

    def _apply_agent_config_to_tool(self, tool: BaseTool) -> None:
        """Apply agent-level configuration to a tool.

        Args:
            tool: The tool instance to configure.
        """
        tool_config_data = self._get_agent_config_for_tool(tool.name)

        if tool_config_data is None:
            return

        try:
            tool.set_tool_config(tool_config_data)
            logger.info(f"Agent '{self.name}': Configured tool '{tool.name}' with agent defaults: {tool_config_data}")
        except Exception as e:
            logger.warning(f"Agent '{self.name}': Failed to configure tool '{tool.name}': {e}")

    def _get_agent_config_for_tool(self, tool_name: str) -> dict[str, Any] | None:
        """Get agent-level configuration data for a specific tool.

        This method intentionally returns only per-tool configuration and does NOT include
        global agent configuration. Global configuration merging is handled separately
        in the metadata resolution process during tool execution.

        Args:
            tool_name: The name of the tool to get configuration for.

        Returns:
            The configuration data for the tool, or None if no configuration is found.
        """
        if not isinstance(self.tool_configs, dict):
            return None

        return self.tool_configs.get(tool_name)

    def _sanitize_tool_names(self):
        """Correct resolved_tools' names that will be used for the agent according to the model provider's rules."""
        for tool in self.resolved_tools:
            sanitized_name = self.name_preprocessor.sanitize_tool_name(tool.name)
            tool.name = sanitized_name

    def _build_and_compile_graph(self) -> CompiledStateGraph:
        """Build and compile the LangGraph while ensuring tool names are valid.

        Returns:
            Compiled LangGraph ready for execution.
        """
        self._sanitize_tool_names()
        try:
            if self.state_schema:
                graph_builder = StateGraph(self.state_schema)
            else:

                class DefaultAgentState(TypedDict):
                    messages: Annotated[list[BaseMessage], add_messages]

                graph_builder = StateGraph(DefaultAgentState)

            compiled_graph = self.define_graph(graph_builder)
            logger.info(
                f"Agent '{self.name}': Successfully compiled LangGraph with {len(self.resolved_tools)} total tools"
            )
            return compiled_graph

        except Exception as e:
            logger.error(f"Agent '{self.name}': Failed to build LangGraph: {e}")
            raise RuntimeError(f"Failed to build LangGraph for agent '{self.name}': {e}") from e

    @abstractmethod
    def define_graph(self, graph_builder: StateGraph) -> CompiledStateGraph:
        """Define the specific graph structure for this agent type.

        Subclasses must implement this method to:
        1. Add nodes to the graph_builder
        2. Add edges and conditional edges
        3. Set entry points
        4. Return the compiled graph

        Args:
            graph_builder: The StateGraph builder to define nodes and edges on.

        Returns:
            The compiled graph ready for execution.
        """
        raise NotImplementedError(f"Agent '{self.name}': Subclasses must implement define_graph method")

    @abstractmethod
    def _prepare_graph_input(self, input_data: Any, **kwargs: Any) -> dict[str, Any]:
        """Convert user input to graph state format.

        Args:
            input_data: The user's input (query string, structured data, etc.).
            **kwargs: Additional keyword arguments from the user.

        Returns:
            Dictionary representing the initial graph state.
        """
        raise NotImplementedError(f"Agent '{self.name}': Subclasses must implement _prepare_graph_input method")

    @abstractmethod
    def _format_graph_output(self, final_state_result: dict[str, Any]) -> Any:
        """Convert final graph state to user-friendly output.

        Args:
            final_state_result: The final state from graph execution.

        Returns:
            Formatted output for the user.
        """
        raise NotImplementedError(f"Agent '{self.name}': Subclasses must implement _format_graph_output method")

    def _extract_metadata_from_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Extract metadata from kwargs for agent implementations.

        Supports both flat and mixed metadata schemas:
        - Flat dict (legacy): all keys applied to all tools and model calls
        - Mixed dict (new): top-level keys applied to all tools, 'tool_configs' section per-tool

        Args:
            **kwargs: Keyword arguments that may contain metadata.

        Returns:
            dict[str, Any]: The metadata dictionary, or an empty dict if no metadata was provided.
        """
        return kwargs.get("metadata", {})

    def _extract_output_from_dict_state(self, dict_state: dict[str, Any]) -> str | None:
        """Extract output from a dictionary state (migrated from BaseLangChainAgent).

        Args:
            dict_state: A dictionary containing agent state information.

        Returns:
            The extracted output string or None if no valid output found.
        """
        output_content: str | None = None
        messages = dict_state.get("messages")
        if messages and isinstance(messages, list) and messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                candidate_content = getattr(last_message, "content", None)
                if not candidate_content:
                    output_content = ""
                else:
                    output_content = candidate_content
            elif hasattr(last_message, "content"):
                output_content = getattr(last_message, "content", None)
        if output_content is None:
            candidate_output_from_key = dict_state.get("output")
            if isinstance(candidate_output_from_key, str):
                output_content = candidate_output_from_key
        return output_content

    def _extract_output_from_list_state(self, list_state: list[Any]) -> str | None:
        """Extract output from a list state (migrated from BaseLangChainAgent).

        Args:
            list_state: A list containing agent state information.

        Returns:
            The extracted output string or None if no valid output found.
        """
        output_content: str | None = None
        if not list_state:
            return None
        last_item = list_state[-1]
        if isinstance(last_item, AIMessage) and getattr(last_item, "content", None) is not None:
            output_content = last_item.content
        elif isinstance(last_item, str):
            output_content = last_item
        return output_content

    def _extract_output_from_final_state(self, final_state_result: Any) -> str:
        """Enhanced output extraction from final state (migrated from BaseLangChainAgent).

        Args:
            final_state_result: The final state from graph execution.

        Returns:
            Extracted text content.
        """
        output_content: str | None = None
        if isinstance(final_state_result, dict):
            output_content = self._extract_output_from_dict_state(final_state_result)
        elif isinstance(final_state_result, str):
            output_content = final_state_result
        elif isinstance(final_state_result, list):
            output_content = self._extract_output_from_list_state(final_state_result)

        if output_content is None:
            return "Error: Could not extract output from agent's final state."
        return output_content

    def register_a2a_agents(self, agent_cards: list[AgentCard]) -> None:
        """Register A2A communication capabilities using the A2A tool manager.

        Args:
            agent_cards (list[AgentCard]): List of AgentCard instances for external communication.
        """
        if not agent_cards:
            logger.info(f"Agent '{self.name}': No A2A agents to register")
            return

        a2a_tools = self.a2a_tool_manager.register_resources(agent_cards)
        self.resolved_tools.extend(a2a_tools)

        logger.info(f"Agent '{self.name}': Registered {len(agent_cards)} A2A agents as tools")
        self._rebuild_graph()

    def register_delegation_agents(self, agents: list[BaseAgent]) -> None:
        """Register internal agent delegation capabilities using the delegation tool manager.

        Args:
            agents: List of BaseAgent instances for internal task delegation.
        """
        if not agents:
            logger.info(f"Agent '{self.name}': No delegation agents to register")
            return

        delegation_tools = self.delegation_tool_manager.register_resources(agents)
        self.resolved_tools.extend(delegation_tools)
        logger.info(f"Agent '{self.name}': Registered {len(agents)} delegation agents as streaming tools")

        self._rebuild_graph()

    def update_regular_tools(self, new_tools: list[BaseTool], rebuild_graph: bool | None = None) -> None:
        """Update regular tools (not capabilities).

        Args:
            new_tools: New list of regular tools to use.
            rebuild_graph: Whether to rebuild graph. If None, uses auto_rebuild_graph setting.
        """
        logger.info(f"Agent '{self.name}': Updating regular tools from {len(self.tools)} to {len(new_tools)}")

        self.tools = list(new_tools)
        old_resolved_count = len(self.regular_tools)
        self.regular_tools = self._resolve_and_validate_tools()

        logger.info(
            f"Agent '{self.name}': Regular tools changed from {old_resolved_count} to {len(self.regular_tools)}"
        )

        self._rebuild_resolved_tools()

        should_rebuild = rebuild_graph if rebuild_graph is not None else True
        if should_rebuild:
            try:
                logger.info(f"Agent '{self.name}': Rebuilding graph with updated tools")
                self._compiled_graph = self._build_and_compile_graph()
            except Exception as e:
                logger.error(f"Agent '{self.name}': Failed to rebuild graph after tool update: {e}")
                raise

    def _rebuild_resolved_tools(self) -> None:
        """Rebuild resolved tools combining regular tools with capability tools."""
        self.resolved_tools = self.regular_tools.copy()

        if self.a2a_tool_manager:
            a2a_tools = self.a2a_tool_manager.get_tools()
            self.resolved_tools.extend(a2a_tools)
            logger.info(f"Agent '{self.name}': Added {len(a2a_tools)} A2A tools")

        if self.delegation_tool_manager:
            delegation_tools = self.delegation_tool_manager.get_tools()
            self.resolved_tools.extend(delegation_tools)
            logger.info(f"Agent '{self.name}': Added {len(delegation_tools)} delegation tools")

        if self.mcp_tools:
            self.resolved_tools.extend(self.mcp_tools)
            logger.info(f"Agent '{self.name}': Added {len(self.mcp_tools)} MCP tools")

        logger.info(f"Agent '{self.name}': Rebuilt resolved tools: {len(self.resolved_tools)} total tools")

    def _rebuild_graph(self) -> None:
        """Rebuilds and recompiles the graph using the current set of tools.

        Raises:
            RuntimeError: If the graph rebuilding or compilation process fails.
        """
        try:
            self._rebuild_resolved_tools()
            self._compiled_graph = self._build_and_compile_graph()
            logger.info(f"Agent '{self.name}': Successfully rebuilt graph")
        except Exception as e:
            logger.error(f"Agent '{self.name}': Failed to rebuild graph: {e}")
            raise RuntimeError(f"Failed to rebuild graph for agent '{self.name}': {e}") from e

    def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Synchronously run the LangGraph agent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Returns:
            Dictionary containing the agent's response.
        """
        try:
            return asyncio.run(self.arun(query, **kwargs))
        except RuntimeError as e:
            raise RuntimeError(f"Agent '{self.name}': Error in sync 'run'. Original: {e}") from e

    async def arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Asynchronously run the LangGraph agent with lazy MCP initialization.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments including configurable for LangGraph.

        Returns:
            Dictionary containing the agent's response and full final state.
        """
        await self._ensure_mcp_tools_initialized()
        return await self._arun(query, **kwargs)

    async def _arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Internal implementation of arun without MCP handling.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments including configurable for LangGraph.

        Returns:
            Dictionary containing the agent's response and full final state.
        """
        memory_user_id: str | None = kwargs.get("memory_user_id")

        # Create config first to ensure thread_id is generated
        config = self._create_graph_config(**kwargs)
        thread_id = self._get_thread_id_from_config(config)

        graph_input = self._prepare_graph_input(query, thread_id=thread_id, **kwargs)

        try:
            final_state_result = await self._compiled_graph.ainvoke(graph_input, config=config)
            formatted_output = self._format_graph_output(final_state_result)

            try:
                self._memory_save_interaction(user_text=query, ai_text=formatted_output, memory_user_id=memory_user_id)
            except Exception:
                pass

            return {"output": formatted_output, "full_final_state": final_state_result}

        except Exception as e:
            logger.error(f"Agent '{self.name}': Error during graph execution: {e}")
            raise RuntimeError(f"Agent '{self.name}': Graph execution failed: {e}") from e

    async def _stream_with_lm_invoker(self, query: str, **kwargs: Any) -> AsyncGenerator[str | dict[str, Any], None]:
        """Handle streaming for LM Invoker using StreamEventHandler.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Chunks of output (strings or dicts) from the streaming response.
        """
        stream_handler = StreamEventHandler(name=f"{self.name}_StreamHandler")
        event_emitter = EventEmitter(handlers=[stream_handler])

        async def run_and_cleanup():
            """Runs the agent and ensures event emitter cleanup."""
            try:
                await self.arun(
                    query=query,
                    event_emitter=event_emitter,
                    **kwargs,
                )
            finally:
                await event_emitter.close()

        execution_task = asyncio.create_task(run_and_cleanup())

        try:
            async for event in stream_handler.stream():
                chunk_data = json.loads(event)
                chunk_value = chunk_data.get("value", "")
                if not chunk_value:
                    continue
                if isinstance(chunk_value, str) or isinstance(chunk_value, dict):
                    yield chunk_value

            await execution_task

        except asyncio.CancelledError:
            execution_task.cancel()
            await event_emitter.close()
            with suppress(asyncio.CancelledError):
                await execution_task
            raise
        except Exception as e:
            execution_task.cancel()
            await event_emitter.close()
            with suppress(asyncio.CancelledError):
                await execution_task
            logger.error(f"Agent '{self.name}': Error during LM Invoker streaming: {e}")
            yield {"error": f"Streaming failed: {e}"}

    def _create_graph_config(self, **kwargs: Any) -> dict[str, Any]:
        """Create standardized graph configuration with thread ID handling.

        Guarantees a thread identifier is present in the returned config. The key used
        is `self.thread_id_key` when set, otherwise the default key `"thread_id"`.

        Args:
            **kwargs: Additional keyword arguments including configurable, metadata, and pii_mapping.

        Returns:
            Dictionary containing the graph configuration with a guaranteed thread ID
            and metadata (including pii_mapping) if provided.
        """
        configurable = kwargs.get("configurable", {}).copy()

        key = self.thread_id_key or "thread_id"
        if key not in configurable:
            configurable[key] = str(uuid.uuid4())
            logger.info(f"Agent '{self.name}': Generated new thread ID: {configurable[key]}")

        config: dict[str, Any] = {"configurable": configurable}

        # Include metadata in config to preserve pii_mapping and other metadata
        # This ensures parity between direct SSE streaming and A2A executor paths
        metadata = kwargs.get("metadata")
        pii_mapping = kwargs.get("pii_mapping")

        if metadata or pii_mapping:
            config_metadata: dict[str, Any] = dict(metadata) if metadata else {}
            if pii_mapping and "pii_mapping" not in config_metadata:
                config_metadata["pii_mapping"] = pii_mapping
            config["metadata"] = config_metadata

        return config

    def _get_thread_id_from_config(self, config: dict[str, Any]) -> str | None:
        """Extract thread_id from graph configuration.

        Args:
            config: Graph configuration dict with 'configurable' key.

        Returns:
            The thread_id value or None if not found.
        """
        configurable = config.get("configurable", {})
        key = self.thread_id_key or "thread_id"
        return configurable.get(key)

    def _process_langgraph_event(self, event: dict[str, Any]) -> str | dict[str, Any] | None:
        """Process a single LangGraph streaming event.

        Args:
            event: Event from LangGraph's astream_events.

        Returns:
            Processed output or None if event should be skipped.
        """
        event_type = event.get("event")
        event_data = event.get("data")

        if event_type == "on_chat_model_stream" and event_data:
            chunk = event_data.get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                return chunk.content

        elif event_type == "on_tool_end" and event_data:
            output = event_data.get("output")
            if output:
                return {"tool_output": str(output)}

        return None

    def _should_yield_a2a_event(self, event_data: A2AEvent) -> bool:
        """Check if A2A event should be yielded based on event type.

        Args:
            event_data: A2AEvent with semantic type information.

        Returns:
            True if event should be yielded, False otherwise.
        """
        event_type = event_data.get("event_type")

        if event_type in {
            A2AStreamEventType.TOOL_CALL,
            A2AStreamEventType.TOOL_RESULT,
            A2AStreamEventType.CONTENT_CHUNK,
            A2AStreamEventType.FINAL_RESPONSE,
            A2AStreamEventType.ERROR,
        }:
            return True

        if event_type == A2AStreamEventType.STATUS_UPDATE:
            content = event_data.get("content", "")
            return bool(content.strip())

        return True

    async def _stream_with_langgraph(self, query: str, **kwargs: Any) -> AsyncGenerator[str | dict[str, Any], None]:
        """Handle streaming for LangChain models using LangGraph's native streaming.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Chunks of output (strings or dicts) from the streaming response.
        """
        # Create config first to ensure thread_id is generated
        config = self._create_graph_config(**kwargs)
        thread_id = self._get_thread_id_from_config(config)

        graph_input = self._prepare_graph_input(query, thread_id=thread_id, **kwargs)

        try:
            async for event in self._compiled_graph.astream_events(graph_input, config=config, version="v2"):
                processed_output = self._process_langgraph_event(event)
                if processed_output is not None:
                    yield processed_output

        except Exception as e:
            logger.error(f"Agent '{self.name}': Error during graph streaming: {e}")
            yield {"error": f"Streaming failed: {e}"}

    async def arun_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[str | dict[str, Any], None]:
        """Asynchronously stream the LangGraph agent's response.

        If MCP configuration exists, connects to the MCP server and registers tools before streaming.
        This method properly handles both LM Invoker and LangChain model streaming:
        - For LM Invoker: Uses StreamEventHandler to capture streaming events
        - For LangChain models: Uses LangGraph's native streaming implementation

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Chunks of output (strings or dicts) from the streaming response.
        """
        await self._ensure_mcp_tools_initialized()
        async for chunk in self._arun_stream(query, **kwargs):
            yield chunk

    async def _arun_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[str | dict[str, Any], None]:
        """Internal implementation of arun_stream without MCP handling.

        This method properly handles both LM Invoker and LangChain model streaming:
        - For LM Invoker: Uses StreamEventHandler to capture streaming events
        - For LangChain models: Uses LangGraph's native streaming implementation

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Chunks of output (strings or dicts) from the streaming response.
        """
        if self._has_lm_invoker():
            async for chunk in self._stream_with_lm_invoker(query, **kwargs):
                yield chunk
        else:
            async for chunk in self._stream_with_langgraph(query, **kwargs):
                yield chunk

    def _initialize_mcp_client(self) -> None:
        """Initialize/recreate MCP client with current config safely disposing previous.

        This method creates a new LangchainMCPClient if MCP configuration exists,
        and safely disposes of any existing client before setting the new one.
        """
        new_client = LangchainMCPClient(self.mcp_config) if self.mcp_config else None
        self._set_mcp_client_safely(new_client)

    async def _register_mcp_tools(self) -> None:
        """Initialize MCP tools once during agent setup using persistent sessions.

        This method connects to MCP servers, retrieves available tools, and integrates
        them into the agent's tool collection. It includes timeout handling to prevent
        hanging operations.

        Raises:
            RuntimeError: If MCP initialization times out after 30 seconds.
            Exception: If MCP tool initialization fails for other reasons.
        """
        try:
            logger.info(f"Agent '{self.name}': Initializing MCP tools with persistent sessions.")

            # Add timeout for initialization to prevent hanging
            await asyncio.wait_for(self.mcp_client.initialize(), timeout=30.0)

            mcp_tools = await self.mcp_client.get_tools()

            if not mcp_tools:
                logger.warning(f"Agent '{self.name}': No MCP tools retrieved from configured servers.")
                return

            self.mcp_tools.extend(mcp_tools)
            logger.info(f"Agent '{self.name}': Added {len(mcp_tools)} persistent MCP tools to graph.")
            self._rebuild_graph()

        except TimeoutError as err:
            logger.error(f"Agent '{self.name}': MCP initialization timed out")
            raise RuntimeError(f"Agent '{self.name}': MCP initialization timed out after 30 seconds") from err
        except Exception as e:
            logger.error(f"Agent '{self.name}': Failed to initialize persistent MCP tools: {e}", exc_info=True)
            raise

    async def cleanup(self) -> None:
        """Cleanup MCP resources including persistent sessions.

        This method performs best-effort cleanup of MCP client resources.
        Errors during cleanup are logged but do not raise exceptions to ensure
        the cleanup process completes gracefully.
        """
        if hasattr(self, "mcp_client") and self.mcp_client:
            try:
                await self.mcp_client.cleanup()
                logger.debug(f"Agent '{self.name}': MCP client cleanup completed")
            except Exception as e:
                logger.warning(f"Agent '{self.name}': Error during MCP client cleanup: {e}")
                # Don't re-raise - cleanup should be best-effort

    async def arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronously streams the agent's response in A2A format.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Dictionaries with "status" and "content" keys.
            Possible statuses: "working", "completed", "failed", "canceled".
        """
        await self._ensure_mcp_tools_initialized()
        async for chunk in self._arun_a2a_stream(query, **kwargs):
            yield chunk

    async def arun_sse_stream(
        self,
        query: str,
        task_id: str | None = None,
        context_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream agent response as SSE-compatible chunks.

        This method wraps arun_a2a_stream and transforms output to the normalized
        dict format matching A2AConnector.astream_to_agent output, enabling direct
        streaming without A2A server overhead.

        Args:
            query: The input query for the agent.
            task_id: Optional task identifier for the stream.
            context_id: Optional context identifier for the stream.
            **kwargs: Additional arguments passed to arun_a2a_stream.

        Yields:
            SSEChunk dicts with normalized structure:
            - status: "success" | "error"
            - task_state: "working" | "completed" | "failed" | "canceled"
            - content: Text content or None
            - event_type: Always string (never enum)
            - final: True for terminal events
            - metadata: Normalized metadata dict
            - artifacts: Only present when non-empty
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        if context_id is None:
            context_id = str(uuid.uuid4())

        # Extract pii_mapping from kwargs to pass to transformer (matching A2A executor behavior)
        pii_mapping = kwargs.get("pii_mapping")
        transformer = SSEChunkTransformer(task_id=task_id, context_id=context_id, pii_mapping=pii_mapping)
        try:
            async for chunk in transformer.transform_stream(self.arun_a2a_stream(query, **kwargs)):
                yield chunk
        except Exception as e:
            logger.error(f"Agent '{self.name}': Error in arun_sse_stream: {e}", exc_info=True)
            yield SSEChunkTransformer._create_error_chunk(f"Error during streaming: {e}")

    def _get_tool_processing_content(self, tool_names: list[str]) -> str:
        """Generate appropriate content prefix for tool processing messages.

        Args:
            tool_names: List of tool names to process.

        Returns:
            Formatted content string with appropriate prefix.
        """
        unique_tool_names = list(dict.fromkeys(tool_names))
        has_delegation_tools = any(name.startswith("delegate_to") for name in unique_tool_names)
        content_prefix = "Processing with sub-agents:" if has_delegation_tools else "Processing with tools:"
        return f"{content_prefix} {', '.join(unique_tool_names)}"

    def _get_tool_completion_content(self, tool_names: list[str]) -> str:
        """Generate completion message for finished tool executions.

        Args:
            tool_names: List of tool names to summarize.

        Returns:
            Content string indicating completion.
        """
        unique_tool_names = list(dict.fromkeys(tool_names))
        has_delegation_tools = any(name.startswith("delegate_to") for name in unique_tool_names)
        content_prefix = "Completed sub-agents:" if has_delegation_tools else "Completed tools:"
        return f"{content_prefix} {', '.join(unique_tool_names)}"

    def _parse_a2a_stream_message(
        self, message: BaseMessage, state: dict[str, Any] | None = None
    ) -> tuple[A2AEvent | None, bool]:
        """Parse LangChain messages into semantically meaningful A2A events.

        This method converts LangChain message types (AIMessage, ToolMessage) into
        structured A2AEvent objects that preserve semantic information and eliminate
        the need for string parsing downstream.

        Args:
            message: The LangChain message to parse (AIMessage, ToolMessage, etc.).
            state: Optional state dictionary containing pii_mapping and other data.

        Returns:
            A tuple containing:
            - A2AEvent | None: The parsed A2A event, or None if message should be skipped.
            - bool: True if this is a final event that should terminate the stream.
        """
        if isinstance(message, AIMessage) and message.tool_calls:
            return self._create_tool_call_event(message), False

        elif isinstance(message, ToolMessage):
            return self._create_tool_result_event(message), False

        elif isinstance(message, AIMessage) and message.content:
            return self._create_ai_message_event(message, state)

        return None, False

    def _link_tool_call_to_previous_status(self, event: A2AEvent) -> None:
        """Link the tool call event to completed tool steps or the most recent status step.

        Supports both parallel and sequential operation modes:
        - "parallel": Links to ALL completed tool steps (default for backward compatibility)
        - "sequential": Links to only the most recent completed tool step

        Args:
            event: The A2AEvent to link to previous step.
        """
        try:
            thread_id = _THREAD_ID_CVAR.get()
            if thread_id:
                metadata = event.get("metadata", {})
                existing_step_ids = metadata.get("previous_step_ids") or []

                if existing_step_ids:
                    return

                operation_mode = _OPERATION_MODE_CVAR.get() or "parallel"

                coord_completed_steps = self._coordinator_completed_tool_steps_by_thread.get(thread_id, [])
                completed_steps = coord_completed_steps or self._completed_tool_steps_by_thread.get(thread_id, [])
                if completed_steps:
                    if operation_mode == "sequential":
                        metadata["previous_step_ids"] = [completed_steps[-1]]
                    else:
                        metadata["previous_step_ids"] = completed_steps
                    event["metadata"] = metadata
                    return

                last_status_id = self._last_status_step_id_by_thread.get(thread_id)
                if last_status_id:
                    metadata["previous_step_ids"] = [last_status_id]
                    event["metadata"] = metadata
        except Exception as e:
            logger.warning("Failed linking tool call to previous step: %s", e, exc_info=True)

    def _register_tool_call_parent_steps(self, event: A2AEvent, tool_calls_details: list[dict]) -> None:
        """Register parent step IDs for each tool call ID.

        Args:
            event: The A2AEvent containing the parent step.
            tool_calls_details: List of tool call details.
        """
        try:
            thread_id = _THREAD_ID_CVAR.get()
            if thread_id:
                parent_step_id = event["metadata"].get("step_id")
                if parent_step_id:
                    parent_map = self._tool_parent_map_by_thread.setdefault(thread_id, {})
                    for tool_call in tool_calls_details:
                        tool_call_id = tool_call.get("id")
                        if tool_call_id:
                            parent_map[str(tool_call_id)] = str(parent_step_id)
        except Exception as e:
            logger.warning("Registering tool call parent steps failed: %s", e, exc_info=True)

    def _create_tool_call_event(self, message: AIMessage) -> A2AEvent:
        """Create an A2AEvent for tool invocation from AIMessage.

        Args:
            message: AIMessage containing tool calls.

        Returns:
            A2AEvent with TOOL_CALL event type and structured tool information.
        """
        tool_calls_details = [
            {
                "id": tool_call.get("id"),
                "name": tool_call["name"],
                "args": tool_call["args"],
            }
            for tool_call in message.tool_calls
        ]
        tool_names = [details["name"] for details in tool_calls_details]

        event = self._create_a2a_event(
            event_type=A2AStreamEventType.TOOL_CALL,
            content=self._get_tool_processing_content(tool_names),
            tool_info={"tool_calls": tool_calls_details, "status": "running"},
            metadata={"status": Status.RUNNING},
            is_final=False,
            step_usage=message.usage_metadata,
        )

        self._record_emitted_tool_calls(tool_calls_details)

        self._link_tool_call_to_previous_status(event)
        self._register_tool_call_parent_steps(event, tool_calls_details)

        return event

    def _get_sub_agent_previous_steps(self, message: ToolMessage) -> list[str] | None:
        """Extract previous step IDs from sub-agent response metadata.

        Args:
            message: ToolMessage containing response metadata.

        Returns:
            List of previous step IDs or None if not available.
        """
        try:
            if not hasattr(message, "response_metadata") or not isinstance(message.response_metadata, dict):
                return None

            sub_prev = message.response_metadata.get("previous_step_ids")
            if isinstance(sub_prev, list) and sub_prev:
                return [str(x) for x in sub_prev if isinstance(x, str | int)]
            return None
        except Exception as e:
            logger.warning("Failed extracting sub-agent previous steps: %s", e, exc_info=True)
            return None

    def _determine_previous_step_ids(self, message: ToolMessage, sub_prev: list[str] | None) -> list[str]:
        """Determine which previous step IDs to use for the event.

        Args:
            message: ToolMessage for the tool call.
            sub_prev: Previous step IDs from sub-agent, if available.

        Returns:
            List of previous step IDs to use.
        """
        if sub_prev:
            return sub_prev

        try:
            thread_id = _THREAD_ID_CVAR.get()
            if thread_id:
                parent_map = self._tool_parent_map_by_thread.get(thread_id, {})
                parent_step = parent_map.get(str(message.tool_call_id))
                if parent_step:
                    return [parent_step]
        except Exception as e:
            logger.warning("Determining previous step IDs failed: %s", e, exc_info=True)

        return []

    def _record_tool_completion(self, message: ToolMessage, event: A2AEvent) -> None:
        """Record tool completion for final event dependency tracking.

        Args:
            message: ToolMessage for the completed tool.
            event: The A2AEvent for the tool result.
        """
        try:
            thread_id = _THREAD_ID_CVAR.get()
            if not thread_id:
                return

            completed_list = self._completed_tool_steps_by_thread.setdefault(thread_id, [])
            coord_completed_list = self._coordinator_completed_tool_steps_by_thread.setdefault(thread_id, [])

            event_sid = (event.get("metadata") or {}).get("step_id")
            if isinstance(event_sid, str) and event_sid:
                completed_list.append(event_sid)
                coord_completed_list.append(event_sid)

            sub_prev = self._get_sub_agent_previous_steps(message) or []
            completed_list.extend(step_id for step_id in sub_prev if isinstance(step_id, str) and step_id)

            self._completed_tool_steps_by_thread[thread_id] = list(dict.fromkeys(completed_list))
            self._coordinator_completed_tool_steps_by_thread[thread_id] = list(dict.fromkeys(coord_completed_list))
        except Exception as e:
            logger.warning("Recording tool completion failed: %s", e, exc_info=True)

    def _create_tool_result_event(self, message: ToolMessage) -> A2AEvent:
        """Create an A2AEvent for tool completion from ToolMessage.

        Args:
            message: ToolMessage containing tool execution results.

        Returns:
            A2AEvent with TOOL_RESULT event type and execution details.
        """
        tool_info = self._extract_tool_info_from_message(message)
        previous_ids = self._determine_previous_step_ids(
            message,
            self._get_sub_agent_previous_steps(message),
        )

        event = self._create_a2a_event(
            event_type=A2AStreamEventType.TOOL_RESULT,
            content=self._build_tool_event_content(tool_info["name"], tool_info["output"], message),
            tool_info={
                "id": message.tool_call_id,
                "name": tool_info["name"],
                "args": tool_info["args"],
                "output": tool_info["output"],
                "execution_time": tool_info["execution_time"],
            },
            metadata=self._build_tool_event_metadata(tool_info["execution_time"], previous_ids),
            is_final=False,
            step_usage=message.response_metadata.get(USAGE_METADATA_KEY),
        )

        self._propagate_hitl_metadata(message, event)
        self._record_tool_completion(message, event)
        self._discard_emitted_tool_call(getattr(message, "tool_call_id", None))

        return event

    def _extract_tool_info_from_message(self, message: ToolMessage) -> dict[str, Any]:
        """Extract tool details from a ToolMessage.

        Args:
            message: The ToolMessage to extract information from.

        Returns:
            Dictionary containing tool name, args, output, and execution time.
        """
        tool_call_info = getattr(message, "tool_calls", {})
        tool_name = getattr(message, "name", None) or tool_call_info.get("name", "unknown")
        return {
            "name": tool_name,
            "args": tool_call_info.get("args", {}),
            "output": tool_call_info.get("output", message.content),
            "execution_time": tool_call_info.get("time"),
        }

    def _build_tool_event_content(self, tool_name: str, tool_output: Any, message: ToolMessage) -> str:
        """Determine event content for a tool result.

        Args:
            tool_name: Name of the tool that was executed.
            tool_output: The output returned by the tool.
            message: The ToolMessage containing response metadata and tool call information.

        Returns:
            String content for the tool result event.
        """
        response_metadata = getattr(message, "response_metadata", None) or {}
        hitl_meta = response_metadata.get(MetadataFieldKeys.HITL) if isinstance(response_metadata, dict) else None

        if hitl_meta and hitl_meta.get("required"):
            return str(tool_output) if tool_output else self._get_tool_processing_content([tool_name])

        return self._get_tool_completion_content([tool_name])

    def _build_tool_event_metadata(
        self,
        execution_time: Any,
        previous_ids: list[str] | None,
    ) -> dict[str, Any]:
        """Build metadata payload for tool result events.

        Args:
            execution_time: Time taken to execute the tool.
            previous_ids: Optional list of previous step IDs this tool depends on.

        Returns:
            Dictionary containing status, execution time, and previous step IDs.
        """
        return {
            "status": Status.FINISHED,
            "time": execution_time,
            "previous_step_ids": previous_ids,
        }

    def _propagate_hitl_metadata(self, message: ToolMessage, event: A2AEvent) -> None:
        """Copy HITL metadata from ToolMessage into the event if available.

        Args:
            message: The ToolMessage containing response metadata with HITL information.
            event: The A2AEvent to update with HITL metadata if present.
        """
        response_metadata = getattr(message, "response_metadata", None)
        if not isinstance(response_metadata, dict):
            return

        hitl_meta = response_metadata.get(MetadataFieldKeys.HITL)
        if hitl_meta is None:
            return

        try:
            hitl_model = HitlMetadata.model_validate(hitl_meta)
        except ValidationError as exc:
            raise ValueError("Invalid HITL metadata payload encountered") from exc

        metadata = event.get("metadata")
        if isinstance(metadata, dict):
            try:
                metadata[MetadataFieldKeys.HITL] = hitl_model.as_payload()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to propagate HITL metadata to event: %s", exc)

    def _create_ai_message_event(
        self, message: AIMessage, state: dict[str, Any] | None = None
    ) -> tuple[A2AEvent, bool]:
        """Create an A2AEvent for AI-generated content from AIMessage.

        Args:
            message: AIMessage containing AI-generated content.
            state: Optional state dictionary containing pii_mapping and other data.

        Returns:
            A tuple containing:
            - A2AEvent: Either CONTENT_CHUNK or FINAL_RESPONSE event.
            - bool: True if this is a final response, False for streaming content.
        """
        is_final_response = self._is_final_response(message)
        metadata = self._build_metadata_for_final_response(is_final_response, state)
        content = deanonymize_final_response_content(
            content=message.content,
            is_final_response=is_final_response,
            metadata=metadata,
        )
        event = self._create_a2a_event(
            event_type=A2AStreamEventType.FINAL_RESPONSE if is_final_response else A2AStreamEventType.CONTENT_CHUNK,
            content=content,
            tool_info=None,
            metadata=metadata,
            is_final=is_final_response,
            step_usage=message.usage_metadata,
        )
        return event, is_final_response

    def _is_final_response(self, message: AIMessage) -> bool:
        """Check if the message represents a final response.

        Args:
            message: AIMessage to check.

        Returns:
            True if this is a final response, False otherwise.
        """
        return bool(message.response_metadata) and message.response_metadata.get("finish_reason") == "stop"

    def _build_metadata_for_final_response(
        self, is_final_response: bool, state: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build metadata for final response including previous_step_ids and pii_mapping.

        Args:
            is_final_response: Whether this is a final response.
            state: Optional state dictionary containing pii_mapping and other data.

        Returns:
            Metadata dictionary with previous_step_ids and pii_mapping if applicable.
        """
        metadata: dict[str, Any] = {}

        if not is_final_response:
            return metadata

        try:
            previous_step_ids = self._get_previous_step_ids()
            if previous_step_ids:
                metadata["previous_step_ids"] = previous_step_ids
        except Exception as e:
            logger.warning("Attaching previous_step_ids to final response failed: %s", e, exc_info=True)

        # Add PII mapping if present in state or nested metadata
        if state:
            pii_mapping = state.get("pii_mapping") or state.get("metadata", {}).get("pii_mapping")
            if pii_mapping:
                metadata[MetadataFieldKeys.PII_MAPPING] = pii_mapping

        return metadata

    def _get_previous_step_ids(self) -> list[str] | None:
        """Get the list of previous step IDs based on thread context and operation mode.

        Returns:
            List of step IDs or None if no thread context or steps found.
        """
        thread_id = _THREAD_ID_CVAR.get()
        if not thread_id:
            return None

        operation_mode = _OPERATION_MODE_CVAR.get() or "parallel"

        coord_ids = self._coordinator_completed_tool_steps_by_thread.get(thread_id, [])
        if coord_ids:
            return self._filter_step_ids_by_mode(coord_ids, operation_mode)

        completed_ids = self._completed_tool_steps_by_thread.get(thread_id, [])
        if completed_ids:
            return self._filter_step_ids_by_mode(completed_ids, operation_mode)

        return None

    def _filter_step_ids_by_mode(self, step_ids: list[str], operation_mode: str) -> list[str]:
        """Filter step IDs based on operation mode.

        Args:
            step_ids: List of step IDs to filter.
            operation_mode: Either "sequential" or "parallel".

        Returns:
            Filtered list of step IDs.
        """
        if operation_mode == "sequential":
            return [step_ids[-1]] if step_ids else []
        else:
            return step_ids

    def _process_artifacts(
        self,
        item: dict[str, Any],
        pending_artifacts: list,
        seen_artifact_hashes: set,
    ) -> None:
        """Process artifacts from a graph stream item.

        Args:
            item: The event item from the graph stream.
            pending_artifacts: A list of artifacts waiting to be attached to a message.
            seen_artifact_hashes: A set of hashes of artifacts already processed.
        """
        if "artifacts" not in item or not item["artifacts"]:
            return

        logger.info(f"Agent '{self.name}': Artifacts: {len(item['artifacts'])}")
        for artifact in item["artifacts"]:
            artifact_data = str(artifact.get("data", ""))
            artifact_name = artifact.get("name", "")
            artifact_hash = hashlib.sha256(f"{artifact_data}:{artifact_name}".encode()).hexdigest()

            if artifact_hash not in seen_artifact_hashes:
                pending_artifacts.append(artifact)
                seen_artifact_hashes.add(artifact_hash)

    def _process_a2a_stream_item(
        self,
        item: dict[str, Any],
        pending_artifacts: list,
        seen_artifact_hashes: set,
        processed_message_count: int,
    ) -> tuple[list[A2AEvent], bool, int]:
        """Process a single item from the graph stream, handling artifacts and messages.

        This method processes LangGraph stream items and converts them into A2AEvent objects
        with proper metadata merging, artifact attachment, and reference handling.

        Args:
            item: The event item from the graph stream containing messages and metadata.
            pending_artifacts: List of artifacts waiting to be attached to messages.
            seen_artifact_hashes: Set of hashes of artifacts already processed.
            processed_message_count: Number of messages already processed from the stream.

        Returns:
            A tuple containing:
            - list[A2AEvent]: List of A2A events to yield to the executor.
            - bool: True if a final event was encountered.
            - int: Updated count of processed messages.
        """
        events_to_yield = []
        is_final_event = False

        self._process_artifacts(item, pending_artifacts, seen_artifact_hashes)
        references = item.get("references", [])

        if "messages" not in item or not item["messages"]:
            return [], False, processed_message_count

        new_messages = item["messages"][processed_message_count:]
        updated_message_count = len(item["messages"])
        for message in new_messages:
            event_data, is_final = self._parse_a2a_stream_message(message, item)

            if event_data and self._should_yield_a2a_event(event_data):
                self._enhance_event_with_context(event_data, item, pending_artifacts, references, is_final)
                events_to_yield.append(event_data)

            if is_final:
                is_final_event = True

        return events_to_yield, is_final_event, updated_message_count

    def _enhance_event_with_context(
        self,
        event_data: A2AEvent,
        stream_item: dict[str, Any],
        pending_artifacts: list,
        references: list[Any],
        is_final: bool,
    ) -> None:
        """Enhance A2AEvent with context from the stream item.

        This method adds metadata, artifacts, and references to the A2AEvent
        based on the current stream item context.

        Args:
            event_data: The A2AEvent to enhance.
            stream_item: The stream item containing context information.
            pending_artifacts: List of artifacts to attach to the event.
            references: List of references to attach to final events.
            is_final: Whether this is a final event.
        """
        self._merge_event_metadata(event_data, stream_item)
        self._attach_pending_artifacts(event_data, pending_artifacts)

        if is_final and references:
            self._attach_references_to_final_event(event_data, references)

        if is_final and stream_item.get(TOTAL_USAGE_KEY):
            event_data[TOTAL_USAGE_KEY] = stream_item[TOTAL_USAGE_KEY]

    def _merge_previous_step_ids(
        self,
        state_prev: list[str | int | None] | None,
        event_prev: list[str | int | None] | None,
    ) -> list[str | int] | None:
        """Merge previous_step_ids from state and event metadata.

        Args:
            state_prev: Previous step IDs from state metadata.
            event_prev: Previous step IDs from event metadata.

        Returns:
            Combined list of previous step IDs, or None if no lists to merge.
        """
        if (state_prev is None and event_prev is None) or (
            not isinstance(state_prev, list)
            and state_prev is not None
            and not isinstance(event_prev, list)
            and event_prev is not None
        ):
            return None

        state_list = state_prev if isinstance(state_prev, list) else []
        event_list = event_prev if isinstance(event_prev, list) else []

        combined: list[Any] = []

        for step_id in event_list:
            if step_id is not None and step_id not in combined:
                combined.append(step_id)

        for step_id in state_list:
            if step_id is not None and step_id not in combined:
                combined.append(step_id)

        return combined

    def _merge_event_metadata(self, event_data: A2AEvent, stream_item: dict[str, Any]) -> None:
        """Merge metadata from stream item into the A2AEvent.

        Args:
            event_data: The A2AEvent to update with merged metadata.
            stream_item: The stream item containing state metadata.
        """
        state_metadata = stream_item.get("metadata", {})
        existing_metadata = event_data.get("metadata", {})
        if isinstance(existing_metadata, dict) and isinstance(state_metadata, dict):
            merged_metadata = {**state_metadata, **existing_metadata}

            state_prev = state_metadata.get("previous_step_ids") or []
            event_prev = existing_metadata.get("previous_step_ids") or []
            combined_ids = self._merge_previous_step_ids(state_prev, event_prev)
            if combined_ids is not None:
                merged_metadata["previous_step_ids"] = combined_ids
        else:
            merged_metadata = state_metadata or existing_metadata

        event_data["metadata"] = merged_metadata

    def _attach_pending_artifacts(self, event_data: A2AEvent, pending_artifacts: list) -> None:
        """Attach pending artifacts to the A2AEvent and clear the pending list.

        Args:
            event_data: The A2AEvent to attach artifacts to.
            pending_artifacts: List of artifacts to attach and clear.
        """
        if pending_artifacts:
            event_data["artifacts"] = pending_artifacts.copy()
            pending_artifacts.clear()

    def _attach_references_to_final_event(self, event_data: A2AEvent, references: list[Any]) -> None:
        """Attach references to final events.

        Args:
            event_data: The final A2AEvent to attach references to.
            references: List of references to attach.
        """
        if references:
            event_data["references"] = references

    def _setup_thread_context(self, config: dict[str, Any]) -> tuple[str | None, Any]:
        """Set up thread context for step linkage during streaming.

        Args:
            config: Graph configuration

        Returns:
            Tuple of (thread_id, context_token)
        """
        current_thread_id: str | None = None
        try:
            configurable = config.get("configurable", {})  # type: ignore[assignment]
            thread_key = self.thread_id_key or "thread_id"
            current_thread_id = str(configurable.get(thread_key)) if configurable.get(thread_key) else None
        except Exception:
            current_thread_id = None

        token = None

        try:
            start_step_counter_scope()
        except Exception as exc:
            logger.debug("Starting step counter scope failed: %s", exc)

        if current_thread_id:
            token = _THREAD_ID_CVAR.set(current_thread_id)
            self._tool_parent_map_by_thread[current_thread_id] = {}
            self._completed_tool_steps_by_thread[current_thread_id] = []
            self._emitted_tool_calls_by_thread[current_thread_id] = set()

        return current_thread_id, token

    def _cleanup_thread_context(self, current_thread_id: str | None, token: Any) -> None:
        """Clean up thread context and reset context variables.

        Args:
            current_thread_id: The thread ID to clean up
            token: The context token to reset
        """
        try:
            end_step_counter_scope()
        except Exception as exc:
            logger.debug("Ending step counter scope failed: %s", exc)

        if current_thread_id:
            self._tool_parent_map_by_thread.pop(current_thread_id, None)
            self._completed_tool_steps_by_thread.pop(current_thread_id, None)
            self._last_status_step_id_by_thread.pop(current_thread_id, None)
            self._emitted_tool_calls_by_thread.pop(current_thread_id, None)

        if token is not None:
            try:
                _THREAD_ID_CVAR.reset(token)
            except ValueError as e:
                logger.debug("Context variable token from different context, skipping reset: %s", e)
            except Exception as e:
                logger.error("Resetting _THREAD_ID_CVAR failed: %s", e, exc_info=True)
        try:
            _STEP_LIMIT_CONFIG_CVAR.set(None)
        except Exception:
            logger.debug("Failed to reset step limit config context; continuing cleanup.")

    def _handle_stream_item(
        self, item: tuple, pending_artifacts: list, seen_artifact_hashes: set, processed_message_count: int
    ) -> tuple[list[A2AEvent], bool, int]:
        """Handle a single stream item.

        Args:
            item: Stream item tuple (mode, data)
            pending_artifacts: List of pending artifacts
            seen_artifact_hashes: Set of seen artifact hashes
            processed_message_count: Current message count

        Returns:
            Tuple of (events_to_yield, is_final, updated_message_count)
        """
        mode, data = item

        if mode == StreamMode.CUSTOM:
            delegation_event: A2AEvent = data
            if self._should_yield_a2a_event(delegation_event):
                return [delegation_event], False, processed_message_count
            return [], False, processed_message_count
        elif mode == StreamMode.VALUES:
            stream_data = data
        else:
            return [], False, processed_message_count

        events, is_final, updated_message_count = self._process_a2a_stream_item(
            stream_data, pending_artifacts, seen_artifact_hashes, processed_message_count
        )
        return events, is_final, updated_message_count

    async def _arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        """Internal implementation of arun_a2a_stream without MCP handling.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Dictionaries with "status" and "content" keys for status events.
            Status events may include "artifacts" field when tools generate artifacts.
            Possible statuses: "working", "completed", "failed", "canceled".
        """
        context = self._initialize_streaming_context(query, **kwargs)

        try:
            async for event in self._handle_streaming_process(context):
                yield event

            self._persist_memory_if_needed(context)

            async for event in self._ensure_final_completion(context):
                yield event

        except Exception as e:
            async for event in self._handle_streaming_error(context, e):
                yield event
        finally:
            self._cleanup_thread_context(context.current_thread_id, context.token)

    def _initialize_streaming_context(self, query: str, **kwargs: Any) -> "_StreamingContext":
        """Initialize the streaming context with all necessary setup.

        Args:
            query: The user's input query to process.
            **kwargs: Additional keyword arguments including optional metadata and configuration.

        Returns:
            Configured _StreamingContext object ready for streaming execution.
        """
        files = kwargs.pop("files", [])
        if files is None:
            files = []

        memory_user_id: str | None = kwargs.get("memory_user_id")

        # Create config first to ensure thread_id is generated
        config = self._create_graph_config(**kwargs)
        thread_id = self._get_thread_id_from_config(config)

        augmented_query = augment_query_with_file_paths(query=query, files=files)
        graph_input = self._prepare_graph_input(augmented_query, thread_id=thread_id, **kwargs)

        current_thread_id, token = self._setup_thread_context(config)

        if self.enable_a2a_token_streaming and self.model:
            self.model.disable_streaming = False

        return _StreamingContext(
            original_query=query,
            graph_input=graph_input,
            config=config,
            memory_user_id=memory_user_id,
            current_thread_id=current_thread_id,
            token=token,
            enable_token_streaming=self.enable_a2a_token_streaming,
        )

    async def _handle_streaming_process(self, context: "_StreamingContext") -> AsyncGenerator[dict[str, Any], None]:
        """Handle the main streaming process including initial status and event processing.

        Args:
            context: The streaming context containing query, config, and thread information.

        Yields:
            Streaming events including initial status and processed streaming items.
        """
        initial_status_event = self._create_initial_status_event()
        self._log_streaming_event_debug("initial_status", initial_status_event)
        yield initial_status_event

        async for event in self._process_streaming_items(context):
            self._log_streaming_event_debug("process_stream_item", event)
            yield event

    def _create_initial_status_event(self) -> dict[str, Any]:
        """Create and setup the initial status event."""
        initial_status_event = self._create_a2a_event(
            event_type=A2AStreamEventType.STATUS_UPDATE, content=DefaultStepMessages.EN.value
        )

        try:
            thread_id = _THREAD_ID_CVAR.get()
            if thread_id:
                step_id = initial_status_event.get("metadata", {}).get("step_id")
                if step_id:
                    self._last_status_step_id_by_thread[thread_id] = str(step_id)
        except Exception:
            pass

        return initial_status_event

    async def _process_streaming_items(self, context: "_StreamingContext") -> AsyncGenerator[dict[str, Any], None]:
        """Process individual streaming items from the LangGraph execution.

        Handles the core streaming logic by iterating through items produced by
        the compiled LangGraph, processing both VALUES and CUSTOM stream modes,
        and managing final event generation.

        Args:
            context: The streaming context containing graph input, configuration,
                and state tracking information.

        Yields:
            dict[str, Any]: A2A events generated from the stream processing,
                including status updates, final responses, and completion events.
        """
        if context.enable_token_streaming:
            if self.event_emitter is None:
                self.event_emitter = self._create_default_event_emitter()
            elif not self._get_stream_handler():
                logger.warning(
                    "Agent '%s': No StreamEventHandler found in event_emitter. "
                    "Reinitializing event_emitter using default emitter.",
                    self.name,
                )
                self.event_emitter = self._create_default_event_emitter()

            async for event in self._process_a2a_streaming_with_tokens(context):
                yield event
        else:
            enhanced_input = context.graph_input
            async for event in self._create_graph_stream_events(enhanced_input, context):
                yield event

    async def _process_a2a_streaming_with_tokens(
        self, context: "_StreamingContext"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process A2A streaming with token streaming support using aiostream.

        Supports both LM Invoker and LangChain models by detecting the appropriate
        token source and merging with graph events.

        Uses aiostream to merge token streaming and graph execution streams,
        yielding events in real-time order as they arrive.

        Args:
            context: The streaming context containing graph input, configuration,
                and state tracking information.

        Yields:
            dict[str, Any]: A2A events generated from the stream processing,
                including status updates, final responses, and completion events.

        Raises:
            RuntimeError: If token streaming is requested but event_emitter is not available.
        """
        if not self.event_emitter:
            raise RuntimeError(f"Agent '{self.name}': Event emitter required for token streaming")
        if astream is None:
            raise RuntimeError(
                "aiostream is required for token streaming support. "
                "Install the 'aiostream' dependency or disable token streaming."
            )

        try:
            if self._has_lm_invoker():
                token_stream, enhanced_input = self._create_token_stream(context)
                graph_stream = self._create_graph_stream_events(enhanced_input, context)

                merged = astream.merge(token_stream, graph_stream)
                async with merged.stream() as merged_stream:
                    async for event in merged_stream:
                        yield event
            else:
                _, enhanced_input = self._create_token_stream(context)
                async for event in self._create_graph_stream_events(enhanced_input, context):
                    yield event

        except Exception as e:
            if self.event_emitter is not None:
                await self.event_emitter.close()
            logger.error(f"Agent '{self.name}': Error during A2A token streaming: {e}")
            raise

    async def _create_lm_invoker_token_stream(self) -> AsyncGenerator[dict[str, Any], None]:
        """Generate A2A events from LM Invoker token stream.

        Uses StreamEventHandler to capture tokens emitted by LM Invoker.

        Yields:
            A2A events generated from LM Invoker token stream.

        Raises:
            RuntimeError: If no StreamEventHandler is found in event_emitter.
        """
        stream_handler = self._get_stream_handler()

        try:
            async for event in stream_handler.stream():
                if event is None:
                    break

                token_event = self._convert_raw_token_to_a2a_event(event)
                if token_event:
                    yield token_event
        except Exception as e:
            logger.error(f"Agent '{self.name}': LM Invoker token stream error: {e}")

    def _create_token_stream(
        self,
        context: "_StreamingContext",
    ) -> tuple[AsyncGenerator[dict[str, Any], None], dict[str, Any]]:
        """Create appropriate token stream and enhanced input for the active model backend.

        Args:
            context: Streaming context containing graph input and configuration.

        Returns:
            Tuple of (token_stream, enhanced_input) where token_stream yields A2A token
            events and enhanced_input is the graph input dictionary (augmented with event
            emitter when required by LM Invoker backends).
        """
        if self._has_lm_invoker():
            token_stream = self._create_lm_invoker_token_stream()
            enhanced_input = {**context.graph_input, "event_emitter": self.event_emitter}
        else:
            token_stream = None
            enhanced_input = context.graph_input

        return token_stream, enhanced_input

    async def _create_graph_stream_events(
        self, enhanced_input: dict[str, Any], context: "_StreamingContext"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generate A2A events from graph execution.

        Args:
            enhanced_input: The enhanced input for the graph execution.
            context: The streaming context containing state tracking information.

        Yields:
            A2A events generated from graph execution.
        """
        try:
            stream_modes = self._get_stream_modes(context)
            graph_execution = self._compiled_graph.astream(
                enhanced_input, config=context.config, stream_mode=stream_modes
            )

            async for item in graph_execution:
                stream_mode, stream_data = item

                if stream_mode == StreamMode.MESSAGES:
                    async for token_event in self._process_message_stream_item(stream_data):
                        yield token_event
                    continue

                async for event in self._process_graph_stream_item(item, stream_mode, stream_data, context):
                    yield event
        except Exception as e:
            logger.error(f"Agent '{self.name}': Graph processing error: {e}")
            raise

    def _get_stream_modes(self, context: "_StreamingContext") -> list[str]:
        """Determine stream modes based on token streaming configuration.

        Args:
            context: Streaming context containing token streaming configuration.

        Returns:
            List of stream modes to use for graph execution.
        """
        stream_modes = [StreamMode.VALUES, StreamMode.CUSTOM]

        if context.enable_token_streaming and not self._has_lm_invoker():
            stream_modes.append(StreamMode.MESSAGES)

        return stream_modes

    async def _process_graph_stream_item(
        self,
        item: tuple[str, Any],
        stream_mode: str,
        stream_data: Any,
        context: "_StreamingContext",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process a single graph stream item and yield A2A events.

        Args:
            item: The stream item tuple (mode, data).
            stream_mode: The stream mode of this item.
            stream_data: The data from the stream item.
            context: Streaming context for state tracking.

        Yields:
            A2A events generated from the stream item.
        """
        context.final_state = copy.copy(stream_data) if stream_mode == StreamMode.VALUES else context.final_state

        events, is_final, context.processed_message_count = self._handle_stream_item(
            item, context.pending_artifacts, context.seen_artifact_hashes, context.processed_message_count
        )

        if is_final:
            context.final_event_yielded = True

        for event in events:
            self._capture_final_content_if_needed(context, event)
            processed_event = self._update_final_response_for_streaming(context, event)
            yield processed_event

    async def _process_message_stream_item(
        self, message_data: tuple[Any, dict[str, Any]]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process message stream items to extract token events.

        The "messages" stream mode yields tuples of (AIMessageChunk, metadata).
        This method extracts token content from AIMessageChunk and converts it
        to A2A CONTENT_CHUNK events with TOKEN kind.

        Args:
            message_data: Tuple of (message_chunk, metadata) from messages stream

        Yields:
            A2A CONTENT_CHUNK events with TOKEN kind
        """
        try:
            message_chunk, _ = message_data

            # Filter out events with response_metadata.finish_reason attribute
            # since it is a response from subagent
            if hasattr(message_chunk, "response_metadata") and message_chunk.response_metadata:
                if "finish_reason" in message_chunk.response_metadata:
                    return

            is_tool_call_event = hasattr(message_chunk, "tool_calls") and message_chunk.tool_calls
            is_has_content_event = hasattr(message_chunk, "content") and message_chunk.content

            if is_has_content_event and not is_tool_call_event:
                token_content = message_chunk.content
                token_event = self._create_a2a_event(
                    event_type=A2AStreamEventType.CONTENT_CHUNK,
                    content=token_content,
                    metadata={MetadataFieldKeys.KIND: Kind.TOKEN},
                )
                yield token_event

        except Exception as e:
            logger.error(f"Agent '{self.name}': Error processing message stream item: {e}")

    def _update_final_response_for_streaming(
        self, context: "_StreamingContext", event: dict[str, Any]
    ) -> dict[str, Any]:
        """Update final response events with appropriate streaming configuration.

        For FINAL_RESPONSE events, this method updates the metadata and optionally clears
        the content when token streaming is active to prevent sending duplicate content.

        Args:
            context: The streaming context containing streaming configuration
            event: The event dictionary to process

        Returns:
            The processed event dictionary with updated metadata and content
        """
        if event.get("event_type") == A2AStreamEventType.FINAL_RESPONSE:
            event["metadata"][MetadataFieldKeys.TOKEN_STREAMING] = False
            if context.enable_token_streaming:
                event["content"] = ""
                event["metadata"][MetadataFieldKeys.TOKEN_STREAMING] = True
        return event

    def _convert_raw_token_to_a2a_event(self, raw_event: str) -> dict[str, Any] | None:
        """Parse raw token event into A2A event.

        Args:
            raw_event: The raw event containing the raw event.

        Returns:
            dict[str, Any]: A2A event generated from the stream processing,
                including status updates, final responses, and completion events.
        """
        try:
            event_data = json.loads(raw_event)
            content = event_data.get("value", "")
            if content:
                return self._create_a2a_event(
                    event_type=A2AStreamEventType.CONTENT_CHUNK,
                    content=content,
                    metadata={MetadataFieldKeys.KIND: Kind.TOKEN},
                )
        except Exception as e:
            logger.debug(f"Agent '{self.name}': Error parsing token event: {e}")
        return None

    def _capture_final_content_if_needed(self, context: "_StreamingContext", event: dict[str, Any]) -> None:
        """Capture final content from A2A events for memory persistence.

        Monitors A2A events for final response content and triggers early memory
        persistence to ensure conversation content is saved even if consumers
        stop reading the stream after receiving the final response.

        Args:
            context: The streaming context containing memory state and user
                identification information.
            event: The A2A event dictionary that may contain final response content.
        """
        try:
            if isinstance(event, dict) and event.get("event_type") == A2AStreamEventType.FINAL_RESPONSE:
                context.last_final_content = event.get("content")
                should_save_early = (
                    self._memory_enabled()
                    and (not context.saved_memory)
                    and isinstance(context.last_final_content, str)
                    and context.last_final_content
                )
                if should_save_early:
                    try:
                        logger.info(
                            "Agent '%s': A2A persisting memory early (len=%d) for user_id='%s'",
                            self.name,
                            len(context.last_final_content),
                            context.memory_user_id or self.memory_agent_id,
                        )
                    except Exception:
                        pass
                    try:
                        self._memory_save_interaction(
                            user_text=context.original_query,
                            ai_text=context.last_final_content,
                            memory_user_id=context.memory_user_id,
                        )
                        context.saved_memory = True
                    except Exception:
                        pass
        except Exception:
            pass

    def _persist_memory_if_needed(self, context: "_StreamingContext") -> None:
        """Persist memory using the final state output (best-effort).

        Attempts to save the conversation to memory using the best available
        content source, first trying captured final content, then falling back
        to extracting content from the final state.

        Args:
            context: The streaming context containing the final state, captured
                content, and memory persistence state.
        """
        try:
            if context.last_final_content is not None:
                final_text = context.last_final_content
            elif isinstance(context.final_state, dict):
                final_text = self._extract_output_from_final_state(context.final_state)
            else:
                final_text = ""
            if (not context.saved_memory) and isinstance(final_text, str) and final_text:
                try:
                    logger.info(
                        "Agent '%s': A2A persisting memory after stream (len=%d) for user_id='%s'",
                        self.name,
                        len(final_text),
                        context.memory_user_id or self.memory_agent_id,
                    )
                except Exception:
                    pass
                self._memory_save_interaction(
                    user_text=context.original_query, ai_text=final_text, memory_user_id=context.memory_user_id
                )
                context.saved_memory = True
        except Exception:
            pass

    async def _ensure_final_completion(self, context: "_StreamingContext") -> AsyncGenerator[dict[str, Any], None]:
        """Ensure final completion events are yielded if not already done.

        Args:
            context: The streaming context containing pending artifacts and
                other state information.

        Yields:
            dict[str, Any]: The final completion event.
        """
        if not context.final_event_yielded:
            completion_event = self._create_completion_event(context.pending_artifacts, context.final_state)
            self._log_streaming_event_debug("final_completion", completion_event)
            yield completion_event

    async def _handle_streaming_error(
        self,
        context: "_StreamingContext",
        error: Exception,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Handle streaming errors gracefully.

        Provides error handling for the A2A streaming process, ensuring errors
        are properly logged and communicated to the client while preserving
        any pending artifacts generated before the error occurred.

        Args:
            context: The streaming context containing pending artifacts and
                other state information.
            error: The exception that occurred during streaming.

        Yields:
            dict[str, Any]: An error event containing the failure status and
                error message, optionally including any pending artifacts.
        """
        logger.error(f"Error in agent stream: {error}", exc_info=True)
        error_event = {"status": "failed", "content": f"Error: {str(error)}"}

        if context.pending_artifacts:
            error_event["artifacts"] = context.pending_artifacts

        self._log_streaming_event_debug("error_event", error_event)
        yield error_event

    def _extract_references_from_state(self, final_state: dict[str, Any] | None) -> list[Chunk] | None:
        """Extract and validate references from final state.

        Args:
            final_state: The final state of the agent.

        Returns:
            Validated references or None if not available.
        """
        if final_state and isinstance(final_state, dict) and final_state.get("references"):
            try:
                return validate_references(final_state["references"])
            except Exception:
                pass
        return None

    def _extract_total_usage_from_state(self, final_state: dict[str, Any] | None) -> dict[str, Any] | None:
        """Extract total usage from final state.

        Args:
            final_state: The final state of the agent.

        Returns:
            Total usage metadata or None if not available.
        """
        if final_state and isinstance(final_state, dict) and final_state.get(TOTAL_USAGE_KEY):
            return final_state[TOTAL_USAGE_KEY]
        return None

    def _build_completion_metadata(self, final_state: dict[str, Any] | None) -> dict[str, Any]:
        """Build metadata for completion event.

        Args:
            final_state: The final state of the agent.

        Returns:
            Metadata dictionary with previous_step_ids and pii_mapping if available.
        """
        metadata: dict[str, Any] = {}

        # Add previous step IDs if available
        try:
            thread_id = _THREAD_ID_CVAR.get()
            if thread_id and thread_id in self._completed_tool_steps_by_thread:
                completed_ids = self._completed_tool_steps_by_thread[thread_id]
                if completed_ids:
                    metadata["previous_step_ids"] = list(completed_ids)
        except Exception as e:
            logger.warning("Attaching previous_step_ids to completion event failed: %s", e, exc_info=True)

        return metadata

    def _create_completion_event(self, pending_artifacts: list, final_state: dict[str, Any]):
        """Helper to create the completion event with artifacts and references if available.

        This method is used to create the completion event with artifacts and references if available.

        Args:
            pending_artifacts: List of artifacts waiting to be attached to a message.
            final_state: The final state of the agent.

        Returns:
            A dictionary with "status" and "content" keys
            Additional keys may include "artifacts" and "references" if available
        """
        artifacts = pending_artifacts if pending_artifacts else None
        references = self._extract_references_from_state(final_state)
        total_usage = self._extract_total_usage_from_state(final_state)
        metadata = self._build_completion_metadata(final_state)

        return self._create_a2a_event(
            event_type=A2AStreamEventType.FINAL_RESPONSE,
            content="Stream finished.",
            tool_info=None,
            metadata=metadata,
            is_final=True,
            artifacts=artifacts,
            references=references,
            step_usage=None,
            total_usage=total_usage,
        )

    def _extract_tool_name_prefix(self, tool_name: str) -> str:
        """Extract a meaningful prefix from a tool name.

        Args:
            tool_name: The name of the tool.

        Returns:
            A meaningful prefix.
        """
        if tool_name.startswith("delegate_to_"):
            agent_name = tool_name[12:]
            if agent_name.endswith("Agent"):
                agent_name = agent_name[:-5]
            return agent_name.lower()[:4]

        if "_" in tool_name:
            parts = tool_name.split("_")
            for part in parts:
                if part not in ["tool", "generator", "calculator", "forecast"]:
                    return part[:4]
            return parts[0][:4]
        else:
            return tool_name[:4]

    def _generate_tool_call_step_id(self, tool_info: dict[str, Any], counter: int) -> str:
        """Generate step_id for tool call events.

        Args:
            tool_info: Tool information
            counter: Step counter

        Returns:
            Generated step_id
        """
        if not tool_info or not tool_info.get("tool_calls"):
            return f"tool_start_{counter:03d}"

        tool_calls = tool_info["tool_calls"]
        if not tool_calls:
            return f"tool_start_{counter:03d}"

        prefixes = [self._extract_tool_name_prefix(tc.get("name", "")) or "unkn" for tc in tool_calls]
        delegation_flags = self._get_delegation_info_from_tool_calls(tool_calls)

        if len(tool_calls) == 1:
            category = "agent" if delegation_flags[0] else "tool"
            return f"{category}_{prefixes[0]}_start_{counter:03d}"

        combined_name = "".join(prefixes).strip()[:6]
        combined_name = combined_name or "multi"

        if all(delegation_flags):
            category = "agent"
        elif any(delegation_flags):
            category = "mixed"
        else:
            category = "tool"

        return f"{category}_{combined_name}_parent_{counter:03d}"

    def _generate_tool_result_step_id(self, tool_info: dict[str, Any], counter: int) -> str:
        """Generate step_id for tool result events.

        Args:
            tool_info: Tool information
            counter: Step counter

        Returns:
            Generated step_id
        """
        if not tool_info:
            return f"tool_done_{counter:03d}"

        tool_name = tool_info.get("name", "")
        prefix = self._extract_tool_name_prefix(tool_name) or "unkn"
        category = "agent" if self._is_delegation_tool_from_info(tool_info) else "tool"
        return f"{category}_{prefix}_done_{counter:03d}"

    @staticmethod
    def _is_delegation_tool_name(tool_name: str) -> bool:
        """Check if a tool name corresponds to a delegation (sub-agent) tool.

        This method maintains backward compatibility by checking the tool name pattern.
        For new tools created by DelegationToolManager, use _is_delegation_tool() instead.

        Args:
            tool_name: The name of the tool to check.

        Returns:
            bool: True if the tool name indicates a delegation tool.
        """
        return isinstance(tool_name, str) and tool_name.startswith("delegate_to_")

    @staticmethod
    def _is_delegation_tool(tool_instance: Any) -> bool:
        """Check delegation status based on metadata when available.

        Args:
            tool_instance: The tool instance to check for delegation metadata.

        Returns:
            True if the tool is marked as a delegation tool, False otherwise.
        """
        metadata = getattr(tool_instance, "metadata", None)
        if not metadata or not hasattr(metadata, "get"):
            return False

        return bool(metadata.get("is_delegation_tool"))

    def _get_delegation_info_from_tool_calls(self, tool_calls: list[dict[str, Any]] | None) -> list[bool]:
        """Return delegation flags for each tool call using hybrid detection.

        Args:
            tool_calls: List of tool call dictionaries containing tool information.

        Returns:
            List of boolean flags indicating delegation status for each tool call.
        """
        if not tool_calls:
            return []

        delegation_flags: list[bool] = []
        for tc in tool_calls:
            if not isinstance(tc, dict):
                logger.warning("Unexpected tool call payload type: %s", type(tc))
                delegation_flags.append(False)
                continue

            delegation_flags.append(self._is_delegation_tool_from_info(tc))

        return delegation_flags

    def _is_delegation_tool_from_info(self, tool_info: dict[str, Any] | None) -> bool:
        """Check delegation status from tool metadata, fallback to name pattern.

        Args:
            tool_info: Dictionary containing tool information including name and instance.

        Returns:
            True if the tool is identified as a delegation tool, False otherwise.
        """
        if not isinstance(tool_info, dict):
            logger.warning("Unexpected tool info payload type: %s", type(tool_info))
            return False

        tool_instance = tool_info.get("tool_instance")
        if tool_instance and self._is_delegation_tool(tool_instance):
            return True

        return self._is_delegation_tool_name(tool_info.get("name", ""))

    def _generate_meaningful_step_id(
        self, event_type: A2AStreamEventType, tool_info: dict[str, Any] | None = None
    ) -> str:
        """Generate a meaningful step_id based on event type and tool information.

        Args:
            event_type: The type of event (tool_call, tool_result, final_response, etc.)
            tool_info: Tool information containing tool names and IDs

        Returns:
            A meaningful step_id string
        """
        try:
            counter = get_next_step_number()

            step_id_generators = {
                A2AStreamEventType.TOOL_CALL: lambda: self._generate_tool_call_step_id(tool_info, counter),
                A2AStreamEventType.TOOL_RESULT: lambda: self._generate_tool_result_step_id(tool_info, counter),
                A2AStreamEventType.FINAL_RESPONSE: lambda: f"final_{counter:03d}",
                A2AStreamEventType.CONTENT_CHUNK: lambda: f"content_{counter:03d}",
            }

            generator = step_id_generators.get(event_type)
            if generator:
                return generator()

            event_value = event_type.value if hasattr(event_type, "value") else str(event_type)
            return f"{event_value}_{counter:03d}"

        except Exception:
            return f"stp_{uuid.uuid4().hex[:8]}"

    def _create_a2a_event(  # noqa: PLR0913
        self,
        event_type: A2AStreamEventType,
        content: str,
        metadata: dict[str, Any] | None = None,
        tool_info: dict[str, Any] | None = None,
        thinking_and_activity_info: dict[str, Any] | None = None,
        is_final: bool = False,
        artifacts: list | None = None,
        references: list | None = None,
        step_usage: dict[str, Any] | None = None,
        total_usage: dict[str, Any] | None = None,
    ) -> A2AEvent:
        """Create a structured A2AEvent dictionary.

        Args:
            event_type: The semantic type of the event.
            content: The main text content of the event.
            metadata: Additional metadata.
            tool_info: Tool-specific information.
            thinking_and_activity_info: Thinking and activity info from the model.
            is_final: Whether this is a final event.
            artifacts: List of artifacts to attach to the event.
            references: List of references to attach to the event.
            step_usage: Step-level token usage information.
            total_usage: Total token usage information.

        Returns:
            A dictionary conforming to the A2AEvent TypedDict.
        """
        enriched_metadata: dict[str, Any] = metadata.copy() if isinstance(metadata, dict) else {}
        if "agent_name" not in enriched_metadata:
            enriched_metadata["agent_name"] = self.name
        if "step_id" not in enriched_metadata:
            enriched_metadata["step_id"] = self._generate_meaningful_step_id(event_type, tool_info)
        if "previous_step_ids" not in enriched_metadata:
            enriched_metadata["previous_step_ids"] = []

        # Inject cumulative time since the first STATUS_UPDATE for this thread
        # Do not set cumulative time here; server executor enforces it for all SSE events

        event = {
            "event_type": event_type,
            "content": content,
            "metadata": enriched_metadata,
            "tool_info": tool_info,
            "is_final": is_final,
            "artifacts": artifacts,
            "references": references,
            STEP_USAGE_KEY: step_usage,
            TOTAL_USAGE_KEY: total_usage,
        }

        if thinking_and_activity_info is not None:
            event["thinking_and_activity_info"] = thinking_and_activity_info

        try:
            content_preview = content if isinstance(content, str) else str(content)
            logger.info(
                "A2A emitting event: type=%s step_id=%s final=%s preview=%s",
                getattr(event_type, "value", event_type),
                enriched_metadata.get("step_id"),
                is_final,
                content_preview[:120].replace("\n", " "),
            )
        except Exception:
            logger.debug("A2A emitting event (logging preview failed)", exc_info=True)

        return event

    def _resolve_tool_event_type(self, event_type_raw: Any) -> A2AStreamEventType | None:
        """Normalize a raw event type to ``A2AStreamEventType``.

        Args:
            event_type_raw: Raw ``event_type`` value from a streaming chunk.

        Returns:
            The resolved ``A2AStreamEventType`` when supported, otherwise ``None``.
        """
        if isinstance(event_type_raw, A2AStreamEventType):
            return event_type_raw
        if isinstance(event_type_raw, str):
            try:
                return A2AStreamEventType(event_type_raw)
            except ValueError:
                return None
        return None

    @staticmethod
    def _is_supported_tool_event(event_type: A2AStreamEventType) -> bool:
        """Return True when the event type is a tool-related streaming event.

        Args:
            event_type: Candidate event type to evaluate.

        Returns:
            True when the event type should be forwarded to the client.
        """
        return event_type in {
            A2AStreamEventType.TOOL_CALL,
            A2AStreamEventType.TOOL_RESULT,
            A2AStreamEventType.STATUS_UPDATE,
        }

    def _build_tool_activity_payload(
        self,
        event_type: A2AStreamEventType,
        metadata: dict[str, Any] | None,
        tool_info: dict[str, Any] | None,
        activity_info: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Ensure tool events carry activity payloads per the streaming contract.

        Args:
            event_type: Stream event type emitted by the tool.
            metadata: Optional metadata accompanying the chunk.
            tool_info: Tool details provided by the emitting runner.
            activity_info: Pre-built activity payload to reuse when present.

        Returns:
            Activity dictionary ready to be serialized with the tool chunk.
        """
        if event_type not in (A2AStreamEventType.TOOL_CALL, A2AStreamEventType.TOOL_RESULT):
            return activity_info

        if activity_info:
            return activity_info

        activity_context = self._compose_tool_activity_context(metadata, tool_info)
        return create_tool_activity_info(activity_context)

    def _compose_tool_activity_context(
        self,
        metadata: dict[str, Any] | None,
        tool_info: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Create a context dictionary for downstream activity message generation.

        Args:
            metadata: Metadata payload extracted from the streaming chunk.
            tool_info: Tool descriptor containing ids and display names.

        Returns:
            A merged context dictionary or None when no data was provided.
        """
        activity_context: dict[str, Any] | None = None
        if isinstance(metadata, dict):
            activity_context = metadata.copy()
        if isinstance(tool_info, dict):
            if activity_context is None:
                activity_context = {"tool_info": tool_info}
            else:
                activity_context.setdefault("tool_info", tool_info)
        return activity_context

    def _create_tool_streaming_event(self, chunk: dict[str, Any], writer: StreamWriter, tool_name: str) -> None:
        """Create and emit tool streaming events.

        Only processes TOOL_CALL and TOOL_RESULT event types.

        Args:
            chunk: Streaming chunk from the tool.
            writer: Stream writer to emit events.
            tool_name: Name of the tool producing the chunk.
        """
        event_type = self._resolve_tool_event_type(chunk.get("event_type"))
        if not event_type or not self._is_supported_tool_event(event_type):
            return

        tool_info = chunk.get("tool_info")
        metadata = chunk.get("metadata")

        if (
            event_type == A2AStreamEventType.TOOL_RESULT
            and isinstance(tool_info, dict)
            and not tool_info.get("id")
            and isinstance(tool_info.get("tool_calls"), list)
            and tool_info.get("tool_calls")
        ):
            logger.info(
                "A2A skipping streaming tool_result without id (tool=%s)",
                tool_info.get("name"),
            )
            return

        activity_info = self._build_tool_activity_payload(
            event_type,
            metadata if isinstance(metadata, dict) else None,
            tool_info if isinstance(tool_info, dict) else None,
            chunk.get("thinking_and_activity_info"),
        )

        a2a_event = self._create_a2a_event(
            event_type=event_type,
            content=chunk.get("content", f"Processing with tools: {tool_name}"),
            metadata=metadata,
            tool_info=tool_info,
            thinking_and_activity_info=activity_info,
        )
        writer(a2a_event)
