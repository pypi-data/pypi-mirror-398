"""LangGraph ReAct Agent implementation.

A ReAct agent template built on LangGraph that can use either lm_invoker or LangChain BaseChatModel.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import asdict, dataclass
from functools import reduce
from textwrap import dedent
from typing import Annotated, Any

from deprecated import deprecated
from gllm_core.event import EventEmitter
from gllm_core.schema import Chunk
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.ai import UsageMetadata
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.types import Command, StreamWriter
from typing_extensions import TypedDict

from aip_agents.agent.base_langgraph_agent import _THREAD_ID_CVAR, BaseLangGraphAgent
from aip_agents.agent.hitl.langgraph_hitl_mixin import LangGraphHitLMixin
from aip_agents.agent.hitl.manager import TOOL_EXECUTION_BLOCKING_DECISIONS
from aip_agents.middleware.base import AgentMiddleware, ModelRequest
from aip_agents.middleware.manager import MiddlewareManager
from aip_agents.middleware.todolist import TodoList, TodoListMiddleware
from aip_agents.schema.a2a import A2AStreamEventType
from aip_agents.schema.hitl import ApprovalDecision, HitlMetadata
from aip_agents.schema.langgraph import ToolCallResult, ToolStorageParams
from aip_agents.schema.step_limit import MaxStepsExceededError, StepLimitConfig
from aip_agents.tools.memory_search_tool import MEMORY_SEARCH_TOOL_NAME
from aip_agents.tools.tool_config_injector import TOOL_CONFIGS_KEY
from aip_agents.utils import add_references_chunks
from aip_agents.utils.langgraph import (
    convert_langchain_messages_to_gllm_messages,
    convert_lm_output_to_langchain_message,
)
from aip_agents.utils.langgraph.tool_output_management import (
    StoreOutputParams,
    ToolOutputManager,
    ToolReferenceError,
    ToolReferenceResolver,
)
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata.activity_metadata_helper import create_tool_activity_info
from aip_agents.utils.metadata_helper import Kind, MetadataFieldKeys, Status
from aip_agents.utils.pii import ToolPIIHandler, add_pii_mappings, normalize_enable_pii
from aip_agents.utils.reference_helper import extract_references_from_tool
from aip_agents.utils.step_limit_manager import (
    _DELEGATION_CHAIN_CVAR,
    _DELEGATION_DEPTH_CVAR,
    _REMAINING_STEP_BUDGET_CVAR,
    _STEP_LIMIT_CONFIG_CVAR,
    StepLimitManager,
)
from aip_agents.utils.token_usage_helper import (
    TOTAL_USAGE_KEY,
    USAGE_METADATA_KEY,
    add_usage_metadata,
    extract_and_update_token_usage_from_ai_message,
    extract_token_usage_from_tool_output,
)

logger = get_logger(__name__)

# Default instruction for ReAct agents
DEFAULT_INSTRUCTION = "You are a helpful assistant. Use the available tools to help answer questions."

# Tool method constants
TOOL_RUN_STREAMING_METHOD = "arun_streaming"

# Key Attributes
TOOL_OUTPUT_MANAGER_KEY = "tool_output_manager"
CALL_ID_KEY = "call_id"


@dataclass
class ToolCallContext:
    """Context information for executing a single tool call."""

    config: dict[str, Any] | None
    state: dict[str, Any]
    pending_artifacts: list[dict[str, Any]]
    hitl_decision: ApprovalDecision | None = None


class ReactAgentState(TypedDict):
    """State schema for the ReAct agent.

    Includes messages, step tracking, optional event emission support, artifacts, references,
    metadata, tool output management, and deep agents middleware state (todos, filesystem).
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
    event_emitter: EventEmitter | None
    artifacts: list[dict[str, Any]] | None
    references: Annotated[list[Chunk], add_references_chunks]
    metadata: dict[str, Any] | None
    tool_output_manager: ToolOutputManager | None
    total_usage: Annotated[UsageMetadata | None, add_usage_metadata]
    pii_mapping: Annotated[dict[str, str] | None, add_pii_mappings]
    thread_id: str

    # Deep Agents Middleware State
    todos: TodoList | None  # Planning middleware - task decomposition state

    # Step Limit State (Configurable Maximum Steps Feature)
    current_step: int  # Current step number (incremented after each LLM call or tool execution)
    delegation_depth: int  # Current depth in delegation chain (0 for root)
    delegation_chain: list[str]  # Agent names in delegation chain
    step_limit_config: StepLimitConfig | None  # Step and delegation limit configuration


class LangGraphReactAgent(LangGraphHitLMixin, BaseLangGraphAgent):
    """A ReAct agent template built on LangGraph.

    This agent can use either:
    - An LMInvoker (if self.lm_invoker is set by BaseAgent)
    - A LangChain BaseChatModel (if self.model is set by BaseAgent)

    The graph structure follows the standard ReAct pattern:
    agent -> tools -> agent (loop) -> END
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        instruction: str = DEFAULT_INSTRUCTION,
        model: BaseChatModel | str | Any | None = None,
        tools: Sequence[BaseTool] | None = None,
        agents: Sequence[Any] | None = None,
        description: str | None = None,
        thread_id_key: str = "thread_id",
        event_emitter: EventEmitter | None = None,
        tool_output_manager: ToolOutputManager | None = None,
        planning: bool = False,
        middlewares: Sequence[AgentMiddleware] | None = None,
        step_limit_config: StepLimitConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize the LangGraph ReAct Agent.

        Args:
            name: The name of the agent.
            instruction: The system instruction for the agent.
            model: The model to use (lm_invoker, LangChain model, string, etc.).
            tools: Sequence of LangChain tools available to the agent.
            agents: Optional sequence of sub-agents for delegation (coordinator mode).
            description: Human-readable description of the agent.
            thread_id_key: Key for thread ID in configuration.
            event_emitter: Optional event emitter for streaming updates.
            tool_output_manager: Optional ToolOutputManager instance for tool output management.
                When provided, enables tool output storage, reference resolution, and sharing capabilities.
                This enables multi-agent workflows where agents can access each other's tool outputs.
                If None, tool output management is disabled for this agent.
            planning: Enable planning capabilities with TodoListMiddleware. Defaults to False.
            middlewares: Optional sequence of custom middleware to COMPOSE (not override) with built-in middleware.
                        Execution order: [TodoListMiddleware (if planning=True),
                                         ...custom middlewares in order provided]
                        All middleware hooks execute - this extends capabilities, never replaces them.
            enable_pii: Optional toggle to enable PII handling for tool inputs and outputs.
            step_limit_config: Optional configuration for step limits and delegation depth.
            **kwargs: Additional keyword arguments passed to BaseLangGraphAgent.
        """
        # Use LangGraph's standard AgentState for ReAct
        state_schema = kwargs.pop("state_schema", ReactAgentState)
        enable_pii = kwargs.pop("enable_pii", None)
        enable_pii = normalize_enable_pii(enable_pii)

        super().__init__(
            name=name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            state_schema=state_schema,
            thread_id_key=thread_id_key,
            event_emitter=event_emitter,
            **kwargs,
        )

        # Handle tool output management
        self.tool_output_manager = tool_output_manager
        self._pii_handlers_by_thread: dict[str, ToolPIIHandler] = {}
        self._enable_pii = enable_pii

        # Initialize middleware tools list (populated by _setup_middleware)
        self._middleware_tools: list[BaseTool] = []

        # Setup middleware
        self._middleware_manager = self._setup_middleware(
            planning=planning,
            custom_middlewares=middlewares,
        )

        # Handle delegation agents (coordinator mode) - following legacy pattern
        if agents:
            self.register_delegation_agents(list(agents))

        self.step_limit_config = step_limit_config

    def _setup_middleware(
        self,
        planning: bool,
        custom_middlewares: Sequence[AgentMiddleware] | None,
    ) -> MiddlewareManager | None:
        """Setup middleware based on configuration.

        Creates auto-configured middleware (planning) and composes
        with custom middleware if provided.

        Args:
            planning: Whether to enable TodoListMiddleware.
            custom_middlewares: Optional custom middlewares to append.

        Returns:
            MiddlewareManager if any middleware configured, None otherwise.
        """
        middleware_list: list[AgentMiddleware] = []

        # Auto-configure TodoListMiddleware if planning enabled
        if planning:
            middleware_list.append(TodoListMiddleware())

        # Append custom middlewares
        if custom_middlewares:
            middleware_list.extend(custom_middlewares)

        # Return manager if any middleware configured
        if middleware_list:
            manager = MiddlewareManager(middleware_list)
            # Store middleware tools separately for proper rebuild support
            middleware_tools = manager.get_all_tools()
            if middleware_tools:
                self._middleware_tools = list(middleware_tools)
                # Add to resolved_tools for immediate use
                self.resolved_tools = list(self.resolved_tools) + self._middleware_tools
            # Enhance instruction with middleware prompt additions
            self.instruction = manager.build_system_prompt(self.instruction)
            return manager

        return None

    async def _get_effective_writer(self, writer: StreamWriter | None = None) -> StreamWriter | None:
        """Get the effective stream writer, falling back to ContextVar if needed.

        Args:
            writer: Optional stream writer to use.

        Returns:
            The effective stream writer or None if retrieval fails.
        """
        try:
            return writer or get_stream_writer()
        except Exception:
            return None

    def _get_step_limit_manager(
        self,
        state: dict[str, Any],
        node_type: str,
        writer: StreamWriter | None = None,
        count: int = 1,
        manager: StepLimitManager | None = None,
    ) -> tuple[dict[str, Any] | None, StepLimitManager | None]:
        """Return initialized StepLimitManager or early state update.

        Args:
            state: Current LangGraph state dictionary.
            node_type: `"agent"` or `"tool"`; determines the fallback message format when limits are exceeded.
            writer: Optional LangGraph `StreamWriter` used when limit events need to be emitted in the absence of an event emitter.
            count: Number of steps to check.
            manager: Optional existing manager to reuse.

        Returns:
            Tuple where the first element is a state update dict when execution should stop, and the second element is the active `StepLimitManager` when limits allow the node to proceed.
        """
        limit_error_update, manager = self._check_step_limits_helper(
            state, node_type, writer=writer, count=count, manager=manager
        )
        if limit_error_update:
            return limit_error_update, None
        if manager is None:
            return {}, None
        manager.set_context()
        return None, manager

    def _emit_step_limit_event(
        self,
        event_type: A2AStreamEventType,
        metadata: dict[str, Any],
        writer: StreamWriter | None = None,
    ) -> None:
        """Emit a step limit event via LangGraph stream writer or EventEmitter.

        Args:
            event_type: The type of event to emit.
            metadata: Metadata to include in the event.
            writer: Optional LangGraph `StreamWriter` used when limit events need to be emitted in the absence of an event emitter.
        """
        enriched_metadata = dict(metadata)
        enriched_metadata.setdefault("status", "error")
        enriched_metadata.setdefault("kind", "agent_default")

        event_payload = self._create_a2a_event(
            event_type=event_type,
            content=enriched_metadata.get("message", ""),
            metadata=enriched_metadata,
        )

        try:
            effective_writer = writer or get_stream_writer()
        except Exception:
            effective_writer = None

        if effective_writer:
            effective_writer(event_payload)
            return

        if self.event_emitter:
            self.event_emitter.emit(event_payload["event_type"], event_payload["metadata"])

    def _check_step_limits_helper(
        self,
        state: dict[str, Any],
        node_type: str,
        writer: StreamWriter | None = None,
        count: int = 1,
        manager: StepLimitManager | None = None,
    ) -> tuple[dict[str, Any] | None, StepLimitManager | None]:
        """Check step limits and return state update if limit exceeded.

        Centralized logic to avoid duplication between agent_node and tool_node.

        Args:
            state: Current agent state.
            node_type: Either 'agent' or 'tool' to determine return message types.
            writer: Optional stream writer for emitting custom events if event_emitter is missing.
            count: Number of steps to check.
            manager: Optional existing manager to reuse.

        Returns:
            Tuple of (state update dict if limit exceeded else None, active StepLimitManager instance).
        """
        try:
            if manager is None:
                manager = StepLimitManager.from_state(state)
            manager.check_step_limit(agent_name=self.name, count=count)

            return None, manager

        except MaxStepsExceededError as e:
            logger.warning(f"Agent '{self.name}': {e.error_response.message}")
            metadata = {
                "message": e.error_response.message,
                "agent_name": e.error_response.agent_name,
                "current_value": e.error_response.current_value,
                "configured_limit": e.error_response.configured_limit,
            }
            self._emit_step_limit_event(
                A2AStreamEventType.STEP_LIMIT_EXCEEDED,
                metadata,
                writer,
            )
            if node_type == "tool":
                return (
                    {
                        "messages": [ToolMessage(content=f"⚠️ {e.error_response.message}", tool_call_id="step_limit")],
                    },
                    None,
                )
            return (
                {
                    "messages": [AIMessage(content=f"⚠️ {e.error_response.message}")],
                },
                None,
            )

    def _rebuild_resolved_tools(self) -> None:
        """Rebuild resolved tools including middleware tools.

        Overrides base class to ensure middleware tools are preserved
        when tools are rebuilt (e.g., after update_regular_tools).
        """
        # Call base class to rebuild with regular, a2a, delegation, and mcp tools
        super()._rebuild_resolved_tools()

        # Add middleware tools if present
        if hasattr(self, "_middleware_tools") and self._middleware_tools:
            self.resolved_tools.extend(self._middleware_tools)

    def _handle_tool_artifacts(
        self, tool_output: Any, pending_artifacts: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Handle artifact extraction from tool output.

        Args:
            tool_output: The output from the tool execution.
            pending_artifacts: Current list of pending artifacts.

        Returns:
            Tuple of (agent_result_text, updated_pending_artifacts).
        """
        if isinstance(tool_output, dict) and "artifacts" in tool_output:
            artifacts = tool_output["artifacts"]
            if isinstance(artifacts, list):
                pending_artifacts.extend(artifacts)
            return tool_output.get("result", ""), pending_artifacts
        else:
            return str(tool_output), pending_artifacts

    # ruff: noqa: PLR0915
    def define_graph(self, graph_builder: StateGraph) -> CompiledStateGraph:
        """Define the ReAct agent graph structure.

        Args:
            graph_builder: The StateGraph builder to define the graph structure.

        Returns:
            Compiled LangGraph ready for execution.
        """
        # Create node functions using helper methods
        agent_node = self._create_agent_node()
        tool_node_logic = self._create_tool_node_logic()
        should_continue = self._create_should_continue_logic(END)

        # Add memory node if memory is enabled
        if self._memory_enabled():
            memory_enhancer_agent = self._create_memory_enhancer_agent()
            graph_builder.add_node("memory_enhancer", self._create_memory_node(memory_enhancer_agent))
            graph_builder.set_entry_point("memory_enhancer")
            graph_builder.add_edge("memory_enhancer", "agent")
        else:
            graph_builder.set_entry_point("agent")

        graph_builder.add_node("agent", agent_node)

        if self.resolved_tools:
            graph_builder.add_node("tools", tool_node_logic)
            graph_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
            graph_builder.add_edge("tools", "agent")
        else:
            graph_builder.add_edge("agent", END)

        return graph_builder.compile(
            checkpointer=self.checkpointer,
        )

    def _create_memory_enhancer_agent(self) -> Any:
        """Create dedicated LangGraphMemoryEnhancerAgent instance for memory enhancement.

        Returns:
            LangGraphMemoryEnhancerAgent: Configured mini-agent for automatic memory retrieval.
        """
        # Lazy import to avoid circular dependency: LangGraphReactAgent imports
        # LangGraphMemoryEnhancerAgent which inherits from LangGraphReactAgent.
        from aip_agents.agent.langgraph_memory_enhancer_agent import (  # noqa: PLC0415
            LangGraphMemoryEnhancerAgent,
        )

        model_id = getattr(self.lm_invoker, "model_id", None)
        model = self.model or model_id
        return LangGraphMemoryEnhancerAgent(
            memory=self.memory,
            model=model,
            memory_agent_id=self.memory_agent_id,
            memory_retrieval_limit=self.memory_retrieval_limit,
        )

    def _create_memory_node(self, memory_enhancer_agent: Any) -> Any:
        """Create memory enhancement node that delegates to LangGraphMemoryEnhancerAgent.

        Args:
            memory_enhancer_agent: The LangGraphMemoryEnhancerAgent instance to use for enhancement.

        Returns:
            Callable: Async function that enhances user query with memory context.
        """

        async def memory_node(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
            """Enhance user query with memory context via LangGraphMemoryEnhancerAgent.

            Args:
                state: LangGraph state containing conversation messages.
                config: Optional LangGraph configuration.

            Returns:
                State update with potentially enhanced last message.
            """
            user_query = self._extract_user_query_from_messages(state.get("messages", []))
            if not user_query:
                return {}

            try:
                metadata = state.get("metadata", {})
                enhanced_result = await memory_enhancer_agent.arun(query=user_query, metadata=metadata)
                enhanced_query = enhanced_result.get("output", user_query)

                if enhanced_query == user_query:
                    logger.debug(f"Agent '{self.name}': No memory enhancement needed")
                    return {}

                logger.info(f"Agent '{self.name}': Memory enhancement completed")
                enhanced_message = HumanMessage(content=enhanced_query)
                # Append enhanced message (with add_messages reducer, this creates: original + enhanced)
                return {"messages": [enhanced_message]}

            except Exception as e:
                logger.warning(f"Agent '{self.name}': Memory enhancement failed: {e}")
                return {}

        return memory_node

    def _extract_user_query_from_messages(self, messages: list[Any]) -> str | None:
        """Get latest user query string from a list of messages.

        Args:
            messages: List of LangChain messages to search through.

        Returns:
            The content string from the most recent HumanMessage if valid, None otherwise.
        """
        if not messages:
            return None
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if isinstance(msg, HumanMessage) and hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, str) and content.strip():
                    return content
                return None
        return None

    def _create_agent_node(self) -> Callable[..., Awaitable[dict[str, Any]]]:
        """Create the agent node function for the graph."""

        async def agent_node(
            state: dict[str, Any], config: dict[str, Any] | None = None, *, writer: StreamWriter = None
        ) -> dict[str, Any]:
            """Call the appropriate LLM and return new messages.

            Args:
                state: Current agent state containing messages and conversation context.
                config: Optional configuration containing thread_id and execution parameters.
                writer: Optional stream writer for emitting custom events.

            Returns:
                Updated state dictionary with new AI messages and token usage.
            """
            writer = await self._get_effective_writer(writer)
            limit_error_update, manager = self._get_step_limit_manager(state, "agent", writer=writer)
            if limit_error_update:
                return limit_error_update
            if manager is None:
                return {}

            current_messages = state["messages"]

            # Execute LLM call
            if self.lm_invoker:
                result = await self._handle_lm_invoker_call(current_messages, state, config)
            elif isinstance(self.model, BaseChatModel):
                result = await self._handle_langchain_model_call(current_messages, state, config)
            else:
                raise ValueError(
                    f"Agent '{self.name}': No valid LMInvoker or LangChain model configured for ReAct agent node."
                )

            # Increment step counter after successful execution
            manager.increment_step()
            # Update state with new step count
            result.update(manager.to_state_update())

            return result

        return agent_node

    def _extract_tool_calls_from_state(self, state: dict[str, Any]) -> tuple[AIMessage | None, int]:
        """Extract the last AI message and tool call count from state.

        Args:
            state: Current agent state.

        Returns:
            Tuple of (last AI message or None, count of tool calls).
        """
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        if not self.resolved_tools or not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return None, 0
        return last_message, len(last_message.tool_calls)

    def _check_tool_batch_limits(
        self,
        state: dict[str, Any],
        tool_call_count: int,
        manager: StepLimitManager,
        writer: StreamWriter | None,
    ) -> tuple[dict[str, Any] | None, StepLimitManager | None]:
        """Check if tool batch exceeds limits.

        Args:
            state: Current LangGraph state dictionary.
            tool_call_count: Number of tools in the current batch.
            manager: Initialized StepLimitManager.
            writer: Optional stream writer for events.

        Returns:
            Tuple of (limit update dict or None, manager instance).
        """
        if tool_call_count <= 1:
            return None, manager
        return self._get_step_limit_manager(state, "tool", writer=writer, count=tool_call_count, manager=manager)

    def _create_tool_node_logic(self) -> Callable[..., Awaitable[dict[str, Any]]]:
        """Create the tool node logic function for the graph."""

        async def tool_node_logic(
            state: dict[str, Any],
            config: dict[str, Any] | None = None,
            *,
            writer: StreamWriter = None,
        ) -> dict[str, Any]:
            """Execute tools with artifact payload separation and reference collection.

            Args:
                state: Current agent state.
                config: Optional execution configuration.
                writer: Optional stream writer.

            Returns:
                Updated state dictionary with tool results.
            """
            writer = await self._get_effective_writer(writer)
            limit_error, manager = self._get_step_limit_manager(state, "tool", writer=writer)
            if limit_error or manager is None:
                return limit_error or {}

            last_message, tool_call_count = self._extract_tool_calls_from_state(state)
            if not last_message:
                return {}

            # Re-check step limits with the actual batch count (Spec-3)
            limit_error, manager = self._check_tool_batch_limits(state, tool_call_count, manager, writer)
            if limit_error or manager is None:
                return limit_error or {}

            result = await self._execute_tool_calls(last_message, state, config)

            # Increment step after tool execution
            manager.increment_step(count=tool_call_count)
            result.update(manager.to_state_update())

            return result

        return tool_node_logic

    async def _execute_tool_calls(
        self, last_message: AIMessage, state: dict[str, Any], config: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Execute tool calls and aggregate results.

        Runs multiple tool calls concurrently for better parallelism.

        Args:
            last_message: The AI message containing tool calls to execute.
            state: Current agent state containing messages, artifacts, and metadata.
            config: Optional configuration containing thread_id and other execution context.

        Returns:
            Updated state dictionary with tool execution results including messages,
            artifacts, references, and metadata updates.
        """
        tool_messages: list[ToolMessage] = []
        pending_artifacts: list[dict[str, Any]] = state.get("artifacts") or []
        reference_updates: list[Chunk] = []
        tool_map = {tool.name: tool for tool in self.resolved_tools}
        pii_mapping = {}

        aggregated_metadata_delta: dict[str, Any] = {}
        total_tools_token_usage: list[UsageMetadata] = []

        async def run_tool(tool_call: dict[str, Any]):
            """Run a single tool call asynchronously.

            Args:
                tool_call: Tool call dictionary.

            Returns:
                Tool result from execution.
            """
            return await self._run_single_tool_call(
                tool_map=tool_map,
                tool_call=tool_call,
                context=ToolCallContext(
                    config=config,
                    state=state,
                    pending_artifacts=pending_artifacts,
                ),
            )

        tasks = [asyncio.create_task(run_tool(tc)) for tc in last_message.tool_calls]

        for coro in asyncio.as_completed(tasks):
            tool_result = await coro
            self._accumulate_tool_result(
                tool_result,
                tool_messages,
                pending_artifacts,
                aggregated_metadata_delta,
                reference_updates,
                total_tools_token_usage,
                pii_mapping,
            )

        return self._build_tool_state_updates(
            tool_messages,
            pending_artifacts,
            reference_updates,
            aggregated_metadata_delta,
            total_tools_token_usage,
            pii_mapping,
        )

    def _accumulate_tool_result(  # noqa: PLR0913
        self,
        tool_result: Any,
        tool_messages: list[ToolMessage],
        pending_artifacts: list[dict[str, Any]],
        aggregated_metadata_delta: dict[str, Any],
        reference_updates: list[Chunk],
        total_tools_token_usage: list[UsageMetadata],
        pii_mapping: dict[str, str] | None,
    ) -> None:  # noqa: PLR0913
        """Accumulate results from a single tool call.

        Args:
            tool_result: The result object from a single tool execution containing messages,
                artifacts, metadata_delta, references, usage information, and PII mapping.
            tool_messages: List to accumulate tool messages into.
            pending_artifacts: List to accumulate artifacts into.
            aggregated_metadata_delta: Dictionary to accumulate metadata updates into.
            reference_updates: List to accumulate reference chunks into.
            total_tools_token_usage: List to accumulate token usage metadata into.
            pii_mapping: Dictionary to accumulate PII mappings into (mutated in place).
        """
        if tool_result.messages:
            tool_messages.extend(tool_result.messages)
        if tool_result.artifacts:
            pending_artifacts.extend(tool_result.artifacts)
        if tool_result.metadata_delta:
            aggregated_metadata_delta.update(tool_result.metadata_delta)
        if tool_result.references:
            reference_updates.extend(tool_result.references)
        if tool_result.step_usage:
            total_tools_token_usage.append(tool_result.step_usage)
        if tool_result.pii_mapping:
            pii_mapping.update(tool_result.pii_mapping)

    def _build_tool_state_updates(
        self,
        tool_messages: list[ToolMessage],
        pending_artifacts: list[dict[str, Any]],
        reference_updates: list[Chunk],
        aggregated_metadata_delta: dict[str, Any],
        total_tools_token_usage: list[UsageMetadata],
        pii_mapping: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build state updates from accumulated tool results.

        Args:
            tool_messages: List of tool messages to include in state updates.
            pending_artifacts: List of artifacts to include in state updates.
            reference_updates: List of reference chunks to include in state updates.
            aggregated_metadata_delta: Metadata changes to include in state updates.
            total_tools_token_usage: List of token usage metadata from all tool executions.
            pii_mapping: Current PII mapping to include in state updates.

        Returns:
            Dictionary containing state updates with messages, artifacts, references,
            metadata, token usage, and PII mapping information.
        """
        state_updates: dict[str, Any] = {"messages": tool_messages, "artifacts": pending_artifacts}

        if reference_updates:
            state_updates["references"] = reference_updates

        # Clean metadata delta to avoid leaking linkage-only fields
        if "previous_step_ids" in aggregated_metadata_delta:
            aggregated_metadata_delta = {k: v for k, v in aggregated_metadata_delta.items() if k != "previous_step_ids"}

        if aggregated_metadata_delta:
            state_updates["metadata"] = aggregated_metadata_delta

        # Process accumulated tool usage
        total_tool_usage = self._process_tool_usage(total_tools_token_usage)
        if total_tool_usage:
            state_updates[TOTAL_USAGE_KEY] = total_tool_usage

        # Include PII mapping in state updates if present
        if pii_mapping:
            state_updates["pii_mapping"] = pii_mapping

        return state_updates

    def _create_should_continue_logic(self, end_node: str) -> Callable[[dict[str, Any]], str]:
        """Create the should_continue function for conditional edges.

        Args:
            end_node: The name of the end node to return when execution should stop.

        Returns:
            Function that determines the next node based on the current state.
        """

        def should_continue(state: dict[str, Any]) -> str:
            """Determine whether to continue to tools or end.

            Args:
                state: Current agent state containing messages and execution status.

            Returns:
                Either "tools" to continue tool execution or the end_node to stop execution.
            """
            messages = state.get("messages", [])
            if not messages:
                return end_node

            last_message = messages[-1]

            # Check if this is the last step
            if state.get("is_last_step", False):
                logger.debug(f"Agent '{self.name}': Reached last step, ending execution")
                return end_node

            if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
                return end_node

            return "tools"

        return should_continue

    def _add_usage_metadata_to_tool_message(
        self, messages: list[ToolMessage], usage_metadata: UsageMetadata | None
    ) -> None:
        """Add usage metadata to a tool message's response metadata.

        Args:
            messages: List of tool messages to potentially update.
            usage_metadata: The usage metadata to add to the first tool message, if any.

        Note:
        - Used for streaming purposes only, to show token usage by tool via ToolMessage response_metadata.
        - Tool message that are coming from Command with single message or a dictionary will have exactly 1 message.
        - For those cases, we will add usage_metadata to the response_metadata of the first message.
        """
        if len(messages) == 1 and isinstance(messages[0], ToolMessage) and usage_metadata is not None:
            messages[0].response_metadata[USAGE_METADATA_KEY] = usage_metadata

    def _process_tool_usage(self, total_tools_token_usage: list[UsageMetadata]) -> UsageMetadata | None:
        """Process accumulated tool usage metadata.

        Args:
            total_tools_token_usage: List of UsageMetadata objects to process.

        Returns:
            UsageMetadata: The accumulated token usage metadata.
        """
        if not total_tools_token_usage:
            return None

        # More concise and functional
        return reduce(add_usage_metadata, total_tools_token_usage, None)

    def _process_command_tool_output(
        self,
        tool_output: Command,
        tool_call: dict[str, Any],
        execution_time: float,
    ) -> tuple[list[ToolMessage], list[dict[str, Any]], dict[str, Any]]:
        """Convert a Command tool output into messages, artifacts, and metadata deltas.

        Args:
            tool_output: The Command returned by the tool.
            tool_call: The tool call info (id, name, args) for ToolMessage context.
            execution_time: Execution time to include in ToolMessage tool_calls.

        Returns:
            A tuple of (messages, artifacts, metadata_delta).
        """
        update: dict[str, Any] = getattr(tool_output, "update", {}) or {}

        out_messages: list[ToolMessage] = []
        out_artifacts: list[dict[str, Any]] = []
        metadata_delta: dict[str, Any] = {}

        # Artifacts
        artifacts_update = update.get("artifacts")
        if isinstance(artifacts_update, list):
            out_artifacts.extend(artifacts_update)

        # Metadata
        md_update = update.get("metadata")
        if isinstance(md_update, dict):
            metadata_delta.update(md_update)

        # Messages or fallback to result
        messages_update = update.get("messages")
        if isinstance(messages_update, list):
            out_messages.extend(messages_update)
        else:
            agent_result = str(update.get("result", ""))
            out_messages.append(
                ToolMessage(
                    content=agent_result,
                    tool_call_id=tool_call["id"],
                    tool_calls={
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                        "output": agent_result,
                        "time": execution_time,
                    },
                )
            )

        # If metadata contains linkage info, attach to first ToolMessage response_metadata
        md = update.get("metadata")
        if isinstance(md, dict):
            prev_ids = md.get("previous_step_ids")
            if isinstance(prev_ids, list) and prev_ids and out_messages:
                try:
                    out_messages[0].response_metadata.setdefault("previous_step_ids", [])
                    existing = out_messages[0].response_metadata.get("previous_step_ids", [])
                    combined = list(dict.fromkeys(list(existing) + list(prev_ids)))
                    out_messages[0].response_metadata["previous_step_ids"] = combined
                except Exception:
                    pass

        return out_messages, out_artifacts, metadata_delta

    def _process_simple_tool_output(
        self,
        agent_result_text: str,
        tool_call: dict[str, Any],
        execution_time: float,
    ) -> tuple[list[ToolMessage], list[dict[str, Any]]]:
        """Convert a simple string tool output into messages with no artifacts.

        Args:
            agent_result_text: The string result from tool execution.
            tool_call: The tool call information containing id, name, and args.
            execution_time: Time taken to execute the tool.

        Returns:
            Tuple of (tool_messages, artifacts) where artifacts is always an empty list.
        """
        messages = [
            ToolMessage(
                content=agent_result_text,
                tool_call_id=tool_call["id"],
                tool_calls={
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "output": agent_result_text,
                    "time": execution_time,
                },
            )
        ]
        return messages, []

    @deprecated(version="0.5.0", reason="Use _process_command_tool_output instead")
    def _process_legacy_tool_output(
        self,
        tool_output: dict[str, Any],
        tool_call: dict[str, Any],
        execution_time: float,
        pending_artifacts: list[dict[str, Any]],
    ) -> tuple[list[ToolMessage], list[dict[str, Any]]]:
        """Normalize legacy dict outputs into ToolMessages and artifacts.

        Supports legacy tools that return a mapping possibly containing 'artifacts'
        and 'result' keys.

        Args:
            tool_output: The legacy dict output from tool execution.
            tool_call: The tool call information containing id, name, and args.
            execution_time: Time taken to execute the tool.
            pending_artifacts: Current list of pending artifacts to extend with new ones.

        Returns:
            Tuple of (tool_messages, updated_pending_artifacts).
        """
        if isinstance(tool_output.get("artifacts"), list):
            pending_artifacts.extend(tool_output["artifacts"])

        agent_result = str(tool_output.get("result", tool_output))

        # Extract metadata from tool_output if present
        response_metadata = {}
        if isinstance(tool_output, dict) and isinstance(tool_output.get("metadata"), dict):
            response_metadata.update(tool_output["metadata"])

        messages = [
            ToolMessage(
                content=agent_result,
                tool_call_id=tool_call["id"],
                tool_calls={
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "output": agent_result,
                    "time": execution_time,
                },
                response_metadata=response_metadata,
            )
        ]
        return messages, pending_artifacts

    async def _run_single_tool_call(
        self,
        tool_map: dict[str, BaseTool],
        tool_call: dict[str, Any],
        context: ToolCallContext,
    ) -> ToolCallResult:
        """Execute a single tool call with tool output management and reference resolution.

        This method handles the complete lifecycle of a tool call including:
        - Reference resolution for tool arguments
        - Tool execution with enhanced configuration
        - Automatic and manual tool output storage
        - Error handling for reference and execution failures

        Args:
            tool_map: Mapping of tool name to tool instance.
            tool_call: The tool call information from the AI message.
            context: Tool call context containing config, state, pending artifacts, and HITL decision.

        Returns:
            ToolCallResult containing messages, artifacts, metadata_delta, references, and usage_metadata.
        """
        tool = tool_map.get(tool_call["name"])  # type: ignore[index]
        tool_call_id = tool_call.get("id", f"tool_call_{uuid.uuid4().hex[:8]}")

        # Check for HITL approval if configured
        if context.hitl_decision is None:
            try:
                context.hitl_decision = await self._check_hitl_approval(
                    tool_call=tool_call, tool_name=tool_call["name"], state=context.state
                )

                if context.hitl_decision and context.hitl_decision.decision in TOOL_EXECUTION_BLOCKING_DECISIONS:
                    # Return sentinel result for pending/rejected/skipped tools
                    return self._create_hitl_blocking_result(tool_call, context.hitl_decision)
            except Exception as e:
                # Log HITL failure but continue with normal tool execution
                logger.warning(
                    "HITL approval check failed for tool '%s' (error: %s: %s). Proceeding with tool execution.",
                    tool_call["name"],
                    type(e).__name__,
                    e,
                )

        # Execute tool and handle errors
        tool_output, execution_time, references, updated_pii_mapping = await self._execute_tool_with_management(
            tool=tool,
            tool_call=tool_call,
            tool_call_id=tool_call_id,
            config=context.config,
            state=context.state,
        )

        # Process tool output into messages and artifacts
        messages, artifacts, metadata_delta = self._process_tool_output_result(
            tool_output=tool_output,
            tool_call=tool_call,
            execution_time=execution_time,
            pending_artifacts=context.pending_artifacts,
        )

        # Capture and merge new PII mapping from subagent
        updated_pii_mapping = self._merge_tool_pii_mapping(metadata_delta, updated_pii_mapping)

        # If HITL was required, annotate the first ToolMessage with HITL metadata
        try:
            if context.hitl_decision and messages:
                first_msg = messages[0]
                if isinstance(first_msg, ToolMessage):
                    response_metadata = getattr(first_msg, "response_metadata", None) or {}
                    response_metadata = dict(response_metadata)
                    hitl_model = HitlMetadata.from_decision(context.hitl_decision)
                    response_metadata["hitl"] = hitl_model.as_payload()
                    first_msg.response_metadata = response_metadata
        except Exception as e:
            # Non-fatal: continue even if metadata injection fails
            logger.warning(f"Failed to inject HITL metadata into tool message: {e}")

        # Extract and add usage metadata
        tool_usage_metadata = extract_token_usage_from_tool_output(tool_output)
        self._add_usage_metadata_to_tool_message(messages, tool_usage_metadata)

        return ToolCallResult(
            messages=messages,
            artifacts=artifacts,
            metadata_delta=metadata_delta,
            references=references,
            step_usage=tool_usage_metadata,
            pii_mapping=updated_pii_mapping,
        )

    def _merge_tool_pii_mapping(
        self,
        metadata_delta: dict[str, Any],
        updated_pii_mapping: dict[str, str] | None,
    ) -> dict[str, str] | None:
        """Merge PII mapping from metadata delta into existing mapping.

        Args:
            metadata_delta: Metadata delta returned from tool execution.
            updated_pii_mapping: PII mapping produced during tool execution, if any.

        Returns:
            New merged PII mapping or None if no PII information is present.
        """
        if "pii_mapping" not in metadata_delta:
            return updated_pii_mapping

        metadata_pii_mapping = metadata_delta.get("pii_mapping") or {}
        if not isinstance(metadata_pii_mapping, dict) or not metadata_pii_mapping:
            return updated_pii_mapping

        if updated_pii_mapping:
            return {**updated_pii_mapping, **metadata_pii_mapping}

        return metadata_pii_mapping

    async def _execute_tool_with_management(
        self,
        tool: BaseTool | None,
        tool_call: dict[str, Any],
        tool_call_id: str,
        config: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> tuple[Any, float, list[Chunk], dict[str, str] | None]:
        """Execute tool with output management, reference resolution, and error handling.

        Args:
            tool: The tool instance to execute, or None if not found.
            tool_call: The tool call information from the AI message.
            tool_call_id: Unique identifier for this tool call.
            config: Optional configuration passed down to the tool.
            state: Current agent state containing tool output manager.

        Returns:
            Tuple of (tool_output, execution_time, references, updated_pii_mapping).
        """
        execution_time = 0.0
        references: list[Chunk] = []
        updated_pii_mapping: dict[str, str] | None = None

        if not tool:
            return f"Error: Tool '{tool_call['name']}' not found.", execution_time, references, updated_pii_mapping

        start_time = time.time()
        try:
            # Resolve tool argument references
            resolved_args = self._resolve_tool_arguments(tool_call, state, config)
            predefined_pii_mapping = self._get_predefined_pii_mapping(state, config)

            enable_pii = self._enable_pii
            if enable_pii is False:
                pii_handler = ToolPIIHandler.create_mapping_only(predefined_pii_mapping)
            else:
                pii_handler = self._create_pii_handler(predefined_pii_mapping, config)

            # Deanonymize tool arguments if PII handler is enabled
            resolved_args = self._deanonymize_tool_args(pii_handler, resolved_args)

            # Create enhanced tool configuration with output management
            tool_config = self._create_enhanced_tool_config(config, state, tool_call["name"], tool_call_id)

            arun_streaming_method = getattr(tool, TOOL_RUN_STREAMING_METHOD, None)

            if arun_streaming_method and callable(arun_streaming_method):
                tool_output = await self._execute_tool_with_streaming(tool, tool_call, tool_config)
            else:
                tool_output = await tool.ainvoke(resolved_args, tool_config)

            references = extract_references_from_tool(tool, tool_output)

            # Anonymize tool output if PII handler is enabled
            tool_output, updated_pii_mapping = self._anonymize_tool_output(pii_handler, tool_output)

            # Handle automatic storage if enabled
            self._handle_automatic_tool_storage(
                ToolStorageParams(
                    tool=tool,
                    tool_output=tool_output,
                    tool_call=tool_call,
                    tool_call_id=tool_call_id,
                    resolved_args=resolved_args,
                    state=state,
                ),
                config=config,
            )

            return tool_output, time.time() - start_time, references, updated_pii_mapping

        except ToolReferenceError as ref_error:
            tool_output = f"Reference error in tool '{tool_call['name']}': {str(ref_error)}"
            logger.error(f"Tool reference error: {ref_error}", exc_info=True)
            return tool_output, time.time() - start_time, references, updated_pii_mapping
        except Exception as e:  # noqa: BLE001
            tool_output = f"Error executing tool '{tool_call['name']}': {str(e)}"
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return tool_output, time.time() - start_time, references, updated_pii_mapping

    def _get_predefined_pii_mapping(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None,
    ) -> dict[str, str] | None:
        """Get predefined PII mapping from state or configuration.

        This helper centralizes the logic for resolving an existing PII mapping,
        first checking the agent state metadata, then falling back to the config
        metadata if available.

        Args:
            state: Current LangGraph agent state.
            config: Optional LangGraph configuration dictionary.

        Returns:
            The resolved PII mapping dictionary if found, otherwise None.
        """
        metadata_from_state = state.get("metadata") or {}
        mapping_from_state = metadata_from_state.get("pii_mapping")
        if isinstance(mapping_from_state, dict) and mapping_from_state:
            return mapping_from_state  # type: ignore[return-value]

        if not config:
            return None

        metadata_from_config = config.get("metadata") or {}
        mapping_from_config = metadata_from_config.get("pii_mapping")
        if isinstance(mapping_from_config, dict) and mapping_from_config:
            return mapping_from_config  # type: ignore[return-value]

        return None

    def _create_pii_handler(
        self, predefined_pii_mapping: dict[str, str] | None, config: dict[str, Any] | None
    ) -> ToolPIIHandler | None:
        """Create (or reuse) a PII handler scoped to the current thread.

        Thin wrapper around ToolPIIHandler.create_if_enabled to keep
        _execute_tool_with_management focused on orchestration. The handler can
        operate in mapping-only mode when no NER credentials are configured.

        Args:
            predefined_pii_mapping: Existing PII mapping to seed the handler with.
            config: LangGraph configuration needed to scope handlers per thread.

        Returns:
            A ToolPIIHandler instance when mapping/NER config is available, otherwise None.
        """
        thread_id: str | None = None
        if config:
            try:
                thread_id = self._extract_thread_id_from_config(config)
            except Exception:
                thread_id = None
        if thread_id:
            handler = self._pii_handlers_by_thread.get(thread_id)
            if handler:
                return handler
        handler = ToolPIIHandler.create_if_enabled(predefined_pii_mapping)
        if handler and thread_id:
            self._pii_handlers_by_thread[thread_id] = handler

        return handler

    def _deanonymize_tool_args(
        self,
        pii_handler: ToolPIIHandler | None,
        resolved_args: dict[str, Any],
    ) -> dict[str, Any]:
        """Deanonymize tool arguments using the provided PII handler.

        Args:
            pii_handler: Optional ToolPIIHandler instance.
            resolved_args: Tool arguments after reference resolution.

        Returns:
            Tool arguments with PII tags replaced by real values when a handler
            is available, otherwise the original arguments.
        """
        if not pii_handler:
            return resolved_args
        return pii_handler.deanonymize_tool_args(resolved_args)

    def _anonymize_tool_output(
        self,
        pii_handler: ToolPIIHandler | None,
        tool_output: Any,
    ) -> tuple[Any, dict[str, str] | None]:
        """Anonymize tool output and return updated PII mapping when enabled.

        Args:
            pii_handler: Optional ToolPIIHandler instance.
            tool_output: Raw output returned by the tool.

        Returns:
            Tuple of (possibly anonymized tool_output, updated PII mapping or None).
        """
        if not pii_handler:
            return tool_output, None

        anonymized_output, updated_mapping = pii_handler.anonymize_tool_output(tool_output)
        return anonymized_output, updated_mapping

    def _resolve_tool_arguments(
        self, tool_call: dict[str, Any], state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Resolve tool argument references using the tool output manager.

        Args:
            tool_call: The tool call information containing arguments.
            state: Current agent state containing tool output manager.
            config: Optional configuration containing thread_id information.

        Returns:
            Resolved arguments dictionary.

        Raises:
            ToolReferenceError: If reference resolution fails.
        """
        manager = state.get(TOOL_OUTPUT_MANAGER_KEY)
        resolved_args = tool_call["args"]

        if manager and self.tool_output_manager:
            thread_id = self._extract_thread_id_from_config(config)

            if manager.has_outputs(thread_id):
                resolver = ToolReferenceResolver(self.tool_output_manager.config)
                resolved_args = resolver.resolve_references(resolved_args, manager, thread_id)
                logger.debug(
                    f"Resolved references for tool '{tool_call['name']}' in thread '{thread_id}', "
                    f"Resolved args: {resolved_args}"
                )

        return resolved_args

    def _create_enhanced_tool_config(
        self, config: dict[str, Any] | None, state: dict[str, Any], tool_name: str, tool_call_id: str
    ) -> dict[str, Any]:
        """Create enhanced tool configuration with output management capabilities.

        Args:
            config: Base configuration passed down to the tool.
            state: Current agent state containing tool output manager.
            tool_name: Name of the tool being executed.
            tool_call_id: Unique identifier for this tool call.

        Returns:
            Enhanced tool configuration dictionary.
        """
        tool_config = self._create_tool_config(config, state, tool_name=tool_name)

        # Add tool output management capabilities
        manager = state.get(TOOL_OUTPUT_MANAGER_KEY)
        if manager and self.tool_output_manager:
            tool_config[TOOL_OUTPUT_MANAGER_KEY] = manager
            tool_config[CALL_ID_KEY] = tool_call_id

        # Attach coordinator parent step id so delegated sub-agents can link their start step properly
        try:
            thread_id = self._extract_thread_id_from_config(config)
            parent_map = self._tool_parent_map_by_thread.get(thread_id, {})
            parent_step_id = parent_map.get(str(tool_call_id))
            if parent_step_id:
                tool_config["parent_step_id"] = parent_step_id
                cfg = tool_config.get("configurable")
                if not isinstance(cfg, dict):
                    cfg = {}
                cfg["parent_step_id"] = parent_step_id
                tool_config["configurable"] = cfg
        except Exception:
            pass

        return tool_config

    def _extract_thread_id_from_config(self, config: dict[str, Any] | None) -> str:
        """Extract thread_id from LangGraph configuration.

        Since BaseLangGraphAgent._create_graph_config() guarantees a thread ID is always present,
        this method should always find a valid thread ID. If config is somehow None (which
        should never happen), creates a new UUID.

        Args:
            config: LangGraph configuration dictionary.

        Returns:
            Thread ID string from the configuration.
        """
        # This should never happen since _create_graph_config always creates config
        if not config:
            thread_id = str(uuid.uuid4())
            logger.warning(f"Agent '{self.name}': No config provided, generated new thread_id: {thread_id}")
            return thread_id

        configurable = config["configurable"]
        thread_key = self.thread_id_key or "thread_id"
        return str(configurable[thread_key])

    def _handle_automatic_tool_storage(
        self,
        params: ToolStorageParams,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Handle automatic storage for tools with store_final_output enabled.

        Args:
            params: ToolStorageParams containing all necessary parameters.
            config: Optional configuration containing thread_id information.
        """
        manager = params.state.get(TOOL_OUTPUT_MANAGER_KEY)

        if (
            manager
            and self.tool_output_manager
            and params.tool_output is not None
            and getattr(params.tool, "store_final_output", False)
        ):
            # Extract thread_id from config
            thread_id = self._extract_thread_id_from_config(config)

            storable_data = self._extract_storable_data(params.tool_output)
            store_params = StoreOutputParams(
                call_id=params.tool_call_id,
                tool_name=params.tool_call["name"],
                data=storable_data,
                tool_args=params.resolved_args,
                thread_id=thread_id,
                description=None,  # No automatic description
                tags=None,
                agent_name=self.name,
            )
            manager.store_output(store_params)
            logger.debug(
                f"Auto-stored output for tool '{params.tool_call['name']}' with call_id: {params.tool_call_id} "
                f"in thread: {thread_id}"
            )

    def _process_tool_output_result(
        self,
        tool_output: Any,
        tool_call: dict[str, Any],
        execution_time: float,
        pending_artifacts: list[dict[str, Any]],
    ) -> tuple[list[BaseMessage], list[dict[str, Any]], dict[str, Any]]:
        """Process tool output into messages, artifacts, and metadata.

        Args:
            tool_output: The output returned by the tool.
            tool_call: The tool call information from the AI message.
            execution_time: Time taken to execute the tool.
            pending_artifacts: List of artifacts to be updated with new artifacts from this tool call.

        Returns:
            Tuple of (messages, artifacts, metadata_delta).
        """
        metadata_delta: dict[str, Any] = {}

        # Handle Command outputs
        if isinstance(tool_output, Command):
            return self._handle_command_output(tool_output, tool_call, execution_time, metadata_delta)

        if isinstance(tool_output, dict):
            return self._handle_legacy_output(tool_output, tool_call, execution_time, pending_artifacts, metadata_delta)

        # Handle string outputs, coercing other simple types
        if not isinstance(tool_output, str):
            tool_output = str(tool_output)
        return self._handle_string_output(tool_output, tool_call, execution_time)

    def _handle_command_output(
        self, tool_output: Command, tool_call: dict[str, Any], execution_time: float, metadata_delta: dict[str, Any]
    ) -> tuple[list[BaseMessage], list[dict[str, Any]], dict[str, Any]]:
        """Handle Command type tool outputs.

        Args:
            tool_output: The Command object returned by the tool.
            tool_call: The tool call information containing id, name, and args.
            execution_time: Time taken to execute the tool.
            metadata_delta: Dictionary to accumulate metadata updates into.

        Returns:
            Tuple of (messages, artifacts, updated_metadata_delta).
        """
        messages, artifacts, md_delta = self._process_command_tool_output(
            tool_output=tool_output,
            tool_call=tool_call,
            execution_time=execution_time,
        )
        if md_delta:
            metadata_delta.update(md_delta)

        update: dict[str, Any] = getattr(tool_output, "update", {}) or {}
        pii_mapping = update.get("pii_mapping")
        if isinstance(pii_mapping, dict) and pii_mapping:
            metadata_delta["pii_mapping"] = pii_mapping

        return messages, artifacts, metadata_delta

    def _handle_string_output(
        self, tool_output: str, tool_call: dict[str, Any], execution_time: float
    ) -> tuple[list[BaseMessage], list[dict[str, Any]], dict[str, Any]]:
        """Handle string type tool outputs.

        Args:
            tool_output: The string output from tool execution.
            tool_call: The tool call information containing id, name, and args.
            execution_time: Time taken to execute the tool.

        Returns:
            Tuple of (messages, artifacts, metadata_delta) where artifacts is empty
            and metadata_delta is empty dict.
        """
        messages, artifacts = self._process_simple_tool_output(
            agent_result_text=tool_output,
            tool_call=tool_call,
            execution_time=execution_time,
        )
        return messages, artifacts, {}

    def _handle_legacy_output(
        self,
        tool_output: Any,
        tool_call: dict[str, Any],
        execution_time: float,
        pending_artifacts: list[dict[str, Any]],
        metadata_delta: dict[str, Any],
    ) -> tuple[list[BaseMessage], list[dict[str, Any]], dict[str, Any]]:
        """Handle legacy dict and other tool outputs.

        Args:
            tool_output: The output from tool execution (typically a dict).
            tool_call: The tool call information containing id, name, and args.
            execution_time: Time taken to execute the tool.
            pending_artifacts: Current list of pending artifacts to extend with new ones.
            metadata_delta: Dictionary to accumulate metadata updates into.

        Returns:
            Tuple of (messages, updated_pending_artifacts, updated_metadata_delta).
        """
        messages, artifacts = self._process_legacy_tool_output(
            tool_output=tool_output,  # type: ignore[arg-type]
            tool_call=tool_call,
            execution_time=execution_time,
            pending_artifacts=pending_artifacts,
        )

        # Process metadata from legacy dict outputs
        if isinstance(tool_output, dict):
            self._process_legacy_metadata(tool_output, messages, metadata_delta)

        return messages, artifacts, metadata_delta

    def _process_legacy_metadata(
        self, tool_output: dict[str, Any], messages: list[BaseMessage], metadata_delta: dict[str, Any]
    ) -> None:
        """Process metadata from legacy dict tool outputs.

        Args:
            tool_output: The dict tool output containing metadata
            messages: List of messages to potentially update with metadata
            metadata_delta: Metadata delta to update
        """
        md = tool_output.get("metadata")
        if not isinstance(md, dict):
            return

        prev_ids = md.get("previous_step_ids")
        if isinstance(prev_ids, list):
            metadata_delta["previous_step_ids"] = list(prev_ids)
            self._attach_previous_step_ids_to_message(messages, prev_ids)

    def _attach_previous_step_ids_to_message(self, messages: list[BaseMessage], prev_ids: list[Any]) -> None:
        """Attach previous step IDs to the first ToolMessage's response metadata.

        Args:
            messages: List of messages to update
            prev_ids: Previous step IDs to attach
        """
        if not messages or not isinstance(messages[0], ToolMessage):
            return

        try:
            tool_message = messages[0]
            tool_message.response_metadata.setdefault("previous_step_ids", [])
            existing = tool_message.response_metadata.get("previous_step_ids", [])
            combined = list(dict.fromkeys(list(existing) + list(prev_ids)))
            tool_message.response_metadata["previous_step_ids"] = combined
        except Exception:
            pass

    async def _execute_tool_with_streaming(
        self,
        tool: BaseTool,
        tool_call: dict[str, Any],
        tool_config: dict[str, Any] | None = None,
    ) -> str:
        """Execute a tool with streaming support and emit streaming chunks.

        This method dynamically passes all tool arguments to the streaming method
        using **kwargs, making it flexible for tools with different parameter structures.

        Args:
            tool: The tool instance to execute.
            tool_call: The tool call information from the AI message.
            tool_config: Optional configuration passed down to the tool.

        Returns:
            The final output from the tool execution.
        """
        writer: StreamWriter = get_stream_writer()
        final_output: Any = None
        saw_tool_result = False
        start_time = time.time()

        tool_call_id = tool_call.get("id", f"tool_call_{uuid.uuid4().hex[:8]}")
        tool_name = tool_call.get("name", "")
        tool_args = self._normalize_tool_args(tool_call.get("args"))

        logger.info("Streaming tool start detected: agent=%s tool=%s call_id=%s", self.name, tool_name, tool_call_id)

        try:
            self._emit_default_tool_call_event(writer, tool_name, tool_call_id, tool_args)

            streaming_kwargs = self._build_streaming_kwargs(tool_args, tool_config)

            async for chunk in tool.arun_streaming(**streaming_kwargs):
                final_output, saw_tool_result = self._handle_streaming_chunk(
                    chunk=chunk,
                    writer=writer,
                    tool_name=tool_call["name"],
                    current_output=final_output,
                    saw_tool_result=saw_tool_result,
                )

            final_output = self._finalize_streaming_tool(
                writer=writer,
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                tool_args=tool_args,
                final_output=final_output,
                saw_tool_result=saw_tool_result,
                start_time=start_time,
            )
            logger.info(
                "Streaming tool completed: agent=%s tool=%s call_id=%s",
                self.name,
                tool_name,
                tool_call_id,
            )

        except Exception as e:
            final_output = f"Error during streaming execution of tool '{tool_call['name']}': {str(e)}"
            logger.error(f"Tool streaming error: {final_output}", exc_info=True)
            self._emit_tool_error_event(writer, tool_call["name"], final_output)

        return final_output

    @staticmethod
    def _normalize_tool_args(raw_tool_args: Any) -> dict[str, Any]:
        """Normalize raw tool arguments into a dictionary.

        Args:
            raw_tool_args: The raw tool arguments to normalize.

        Returns:
            A dictionary containing the normalized tool arguments.
        """
        if isinstance(raw_tool_args, dict):
            return raw_tool_args
        if raw_tool_args is None:
            return {}
        return {"value": raw_tool_args}

    @staticmethod
    def _build_streaming_kwargs(tool_args: dict[str, Any], tool_config: dict[str, Any] | None) -> dict[str, Any]:
        """Create kwargs payload for streaming execution.

        Args:
            tool_args: The tool arguments to include in the streaming kwargs.
            tool_config: Optional tool configuration to include.

        Returns:
            A dictionary containing the streaming kwargs.
        """
        streaming_kwargs = tool_args.copy()
        if tool_config:
            streaming_kwargs["config"] = tool_config
        return streaming_kwargs

    def _handle_streaming_chunk(
        self,
        *,
        chunk: Any,
        writer: StreamWriter,
        tool_name: str,
        current_output: Any,
        saw_tool_result: bool,
    ) -> tuple[Any, bool]:
        """Process a single streaming chunk and update output/result flag.

        Args:
            chunk: The streaming chunk to process.
            writer: The stream writer for output.
            tool_name: The name of the tool being executed.
            current_output: The current accumulated output.
            saw_tool_result: Whether a tool result has been seen.

        Returns:
            A tuple of (updated_output, saw_tool_result).
        """
        if not isinstance(chunk, dict):
            return current_output, saw_tool_result

        event_type_raw = chunk.get("event_type")
        event_type = self._resolve_tool_event_type(event_type_raw)
        if event_type == A2AStreamEventType.TOOL_CALL or (
            event_type is None
            and isinstance(event_type_raw, str)
            and event_type_raw.lower() == A2AStreamEventType.TOOL_CALL.value
        ):
            return current_output, saw_tool_result

        self._create_tool_streaming_event(chunk, writer, tool_name)
        new_output = self._extract_output_from_chunk(chunk, current_output)
        if event_type == A2AStreamEventType.STATUS_UPDATE:
            metadata = chunk.get("metadata")
            kind = None
            if isinstance(metadata, dict):
                kind = metadata.get(MetadataFieldKeys.KIND)
            if getattr(kind, "value", kind) == Kind.FINAL_THINKING_STEP.value:
                return new_output, True
        if event_type == A2AStreamEventType.TOOL_RESULT:
            return new_output, True
        return new_output, saw_tool_result

    def _emit_default_tool_call_event(
        self,
        writer: StreamWriter,
        tool_name: str,
        tool_call_id: str,
        tool_args: dict[str, Any],
    ) -> None:
        """Emit a standardized TOOL_CALL event for streaming tools.

        Args:
            writer: The stream writer to emit events to.
            tool_name: Name of the tool being called.
            tool_call_id: Unique identifier for the tool call.
            tool_args: Arguments passed to the tool.
        """
        thread_id = _THREAD_ID_CVAR.get()
        if thread_id:
            emitted = self._emitted_tool_calls_by_thread.get(thread_id, set())
            if tool_call_id in emitted:
                logger.info(
                    "Skipping fallback tool call event: agent=%s tool=%s call_id=%s",
                    self.name,
                    tool_name,
                    tool_call_id,
                )
                return

        tool_call_info = {
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "name": tool_name,
                    "args": tool_args,
                }
            ],
            "status": "running",
        }
        metadata = {
            MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP,
            MetadataFieldKeys.STATUS: Status.RUNNING,
            MetadataFieldKeys.TOOL_INFO: tool_call_info,
        }
        activity_info = create_tool_activity_info({"tool_info": tool_call_info})
        event = {
            "event_type": A2AStreamEventType.TOOL_CALL,
            "content": f"Processing with tools: {tool_name}",
            "metadata": metadata,
            "tool_info": tool_call_info,
            "thinking_and_activity_info": activity_info,
        }
        self._create_tool_streaming_event(event, writer, tool_name)

    @staticmethod
    def _extract_output_from_chunk(chunk: dict[str, Any], current_output: Any) -> Any:
        """Return most recent tool output derived from streaming chunk.

        Args:
            chunk: The streaming chunk containing tool information.
            current_output: The current output value to fall back to.

        Returns:
            The extracted output from the chunk or the current_output if not found.
        """
        tool_info = chunk.get("tool_info")
        if isinstance(tool_info, dict):
            return tool_info.get("output", current_output)
        return current_output

    def _finalize_streaming_tool(
        self,
        *,
        writer: StreamWriter,
        tool_name: str,
        tool_call_id: str,
        tool_args: dict[str, Any],
        final_output: Any,
        saw_tool_result: bool,
        start_time: float,
    ) -> str:
        """Emit final tool event when needed and return final output as string.

        Args:
            writer: The stream writer to emit events to.
            tool_name: Name of the tool being called.
            tool_call_id: Unique identifier for the tool call.
            tool_args: Arguments passed to the tool.
            final_output: The final output from the tool execution.
            saw_tool_result: Whether a TOOL_RESULT event was observed during streaming.
            start_time: Timestamp when the tool execution started.

        Returns:
            The final output as a string.
        """
        output_text = final_output
        if output_text is None:
            output_text = f"Tool '{tool_name}' completed successfully"
        if not isinstance(output_text, str):
            output_text = str(output_text)

        logger.debug(
            "Streaming tool finalize check: agent=%s tool=%s call_id=%s saw_tool_result=%s",
            self.name,
            tool_name,
            tool_call_id,
            saw_tool_result,
        )
        if not saw_tool_result:
            logger.debug(
                "Streaming tool finalize emitting default result: agent=%s tool=%s call_id=%s",
                self.name,
                tool_name,
                tool_call_id,
            )
            self._emit_default_tool_result_event(
                writer=writer,
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                tool_args=tool_args,
                output_text=output_text,
                start_time=start_time,
            )

        return output_text

    def _emit_default_tool_result_event(
        self,
        *,
        writer: StreamWriter,
        tool_name: str,
        tool_call_id: str,
        tool_args: dict[str, Any],
        output_text: str,
        start_time: float,
    ) -> None:
        """Emit a standardized TOOL_RESULT event for streaming tools.

        Args:
            writer: The stream writer to emit events to.
            tool_name: Name of the tool that was executed.
            tool_call_id: Unique identifier for the tool call.
            tool_args: Arguments passed to the tool.
            output_text: The output text from the tool execution.
            start_time: Timestamp when the tool execution started.
        """
        execution_time = time.time() - start_time
        tool_result_info = {
            "name": tool_name,
            "args": tool_args,
            "output": output_text,
            "execution_time": execution_time,
        }
        metadata = {
            MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP,
            MetadataFieldKeys.STATUS: Status.FINISHED,
            MetadataFieldKeys.TOOL_INFO: tool_result_info,
        }
        activity_info = create_tool_activity_info({"tool_info": tool_result_info})
        event = {
            "event_type": A2AStreamEventType.TOOL_RESULT,
            "content": output_text,
            "metadata": metadata,
            "tool_info": tool_result_info,
            "thinking_and_activity_info": activity_info,
        }
        self._create_tool_streaming_event(event, writer, tool_name)

    def _emit_tool_error_event(self, writer: StreamWriter, tool_name: str, error_msg: str) -> None:
        """Emit a tool error event to the stream.

        Args:
            writer: Stream writer to emit events.
            tool_name: Name of the tool that encountered an error.
            error_msg: The error message.
        """
        a2a_event = self._create_a2a_event(
            event_type=A2AStreamEventType.ERROR,
            content=f"Error in {tool_name}: {error_msg}",
            tool_info={
                "name": tool_name,
                "error": error_msg,
            },
        )
        writer(a2a_event)

    def _execute_before_model_hook(self, state: dict[str, Any]) -> None:
        """Execute before_model middleware hook and update state.

        Args:
            state: Current agent state to potentially update.
        """
        if self._middleware_manager:
            try:
                before_updates = self._middleware_manager.before_model(state)
                if before_updates:
                    state.update(before_updates)
            except Exception as e:
                logger.error(f"Agent '{self.name}': Middleware before_model hook failed: {e}")

    def _execute_modify_model_request_hook(
        self, messages: list[Any], enhanced_instruction: str, state: dict[str, Any]
    ) -> tuple[list[Any], str]:
        """Execute modify_model_request middleware hook.

        Args:
            messages: Current messages to potentially modify.
            enhanced_instruction: Current system prompt to potentially modify.
            state: Current agent state for context.

        Returns:
            Tuple of (potentially modified messages, potentially modified system prompt).
        """
        if not self._middleware_manager:
            return messages, enhanced_instruction

        try:
            model_request: ModelRequest = {
                "messages": messages,
                "tools": self.resolved_tools or [],
                "system_prompt": enhanced_instruction,
            }
            model_request = self._middleware_manager.modify_model_request(model_request, state)

            modified_messages = model_request.get("messages", messages)
            modified_prompt = model_request.get("system_prompt", enhanced_instruction)

            return modified_messages, modified_prompt
        except Exception as e:
            logger.error(f"Agent '{self.name}': Middleware modify_model_request hook failed: {e}")
            return messages, enhanced_instruction

    def _execute_after_model_hook(self, state_updates: dict[str, Any], state: dict[str, Any]) -> None:
        """Execute after_model middleware hook and update state_updates.

        Args:
            state_updates: Dictionary to update with middleware changes.
            state: Current agent state for context.
        """
        if self._middleware_manager:
            try:
                after_updates = self._middleware_manager.after_model(state)
                if after_updates:
                    state_updates.update(after_updates)
            except Exception as e:
                logger.error(f"Agent '{self.name}': Middleware after_model hook failed: {e}")

    async def _handle_lm_invoker_call(
        self, current_messages: Sequence[BaseMessage], state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle LMInvoker model calls with bridge conversion and tool output context.

        Args:
            current_messages: The current messages in the agent.
            state: The current state of the agent.
            config: The configuration for the agent.

        Returns:
            dict[str, Any]: A dictionary containing the new messages and updated token usage.
        """
        # Execute before_model middleware hook
        self._execute_before_model_hook(state)

        # Build tool output aware instruction
        enhanced_instruction = self._build_tool_output_aware_instruction(self.instruction, state, config)

        # Execute modify_model_request middleware hook
        _, enhanced_instruction = self._execute_modify_model_request_hook(
            list(current_messages), enhanced_instruction, state
        )

        messages = convert_langchain_messages_to_gllm_messages(list(current_messages), enhanced_instruction)

        effective_event_emitter = state.get("event_emitter") or self.event_emitter

        if self.resolved_tools:
            self.lm_invoker.set_tools(self.resolved_tools)

        # Debug timing for LLM invocation
        _t0 = time.perf_counter()
        logger.info(f"Agent '{self.name}': LLM invoke start (tools={len(self.resolved_tools)})")
        lm_output = await self.lm_invoker.invoke(messages=messages, event_emitter=effective_event_emitter)
        _dt = time.perf_counter() - _t0
        logger.info(f"Agent '{self.name}': LLM invoke finished in {_dt:.3f}s")

        ai_message = convert_lm_output_to_langchain_message(lm_output)

        # Update token usage if available in the message
        state_updates = {"messages": [ai_message]}

        # Extract and accumulate token usage from the message
        token_usage_updates = extract_and_update_token_usage_from_ai_message(ai_message)
        state_updates.update(token_usage_updates)

        # Execute after_model middleware hook
        self._execute_after_model_hook(state_updates, state)

        return state_updates

    async def _handle_langchain_model_call(
        self, current_messages: Sequence[BaseMessage], state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle LangChain BaseChatModel calls with tool output context.

        Args:
            current_messages: The current messages in the agent.
            state: The current state of the agent.
            config: The configuration for the agent.

        Returns:
            dict[str, Any]: A dictionary containing the new messages and updated token usage.
        """
        # Execute before_model middleware hook
        self._execute_before_model_hook(state)

        # Build tool output aware instruction
        enhanced_instruction = self._build_tool_output_aware_instruction(self.instruction, state, config)

        langchain_prompt: list[BaseMessage] = [SystemMessage(content=enhanced_instruction)] + list(current_messages)

        # Execute modify_model_request middleware hook
        langchain_prompt, enhanced_instruction = self._execute_modify_model_request_hook(
            langchain_prompt, enhanced_instruction, state
        )

        # Rebuild prompt if needed (invalid structure or system prompt was modified)
        if (
            not langchain_prompt
            or not isinstance(langchain_prompt[0], SystemMessage)
            or langchain_prompt[0].content != enhanced_instruction
        ):
            langchain_prompt = [SystemMessage(content=enhanced_instruction)] + list(current_messages)

        model_with_tools = self.model.bind_tools(self.resolved_tools) if self.resolved_tools else self.model

        ai_message = await model_with_tools.ainvoke(langchain_prompt, config)

        # Update token usage if available in the message
        state_updates = {"messages": [ai_message]}

        # Extract and accumulate token usage from the message
        token_usage_updates = extract_and_update_token_usage_from_ai_message(ai_message)
        state_updates.update(token_usage_updates)

        # Execute after_model middleware hook
        self._execute_after_model_hook(state_updates, state)

        return state_updates

    def _add_user_id_memory_tool_config(self, metadata: dict[str, Any], memory_user_id: str) -> None:
        """Add user ID to memory tool config.

        Args:
            metadata: The metadata to add the user ID to.
            memory_user_id: The user ID to add.
        """
        try:
            tool_cfgs = metadata.get(TOOL_CONFIGS_KEY, {})
            per_tool_config = tool_cfgs.get(MEMORY_SEARCH_TOOL_NAME)
            if not isinstance(per_tool_config, dict):
                per_tool_config = {}
            per_tool_config["user_id"] = memory_user_id
            tool_cfgs[MEMORY_SEARCH_TOOL_NAME] = per_tool_config
            metadata[TOOL_CONFIGS_KEY] = tool_cfgs
        except Exception as e:
            # Non-fatal; metadata injection is best-effort
            logger.warning("Failed to add user ID to memory tool config: %s", e)

    def _prepare_graph_input(self, input_data: str | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Convert user input to graph state format.

        Extracts mixed metadata schema supporting per-tool configuration.
        Delegation tools are isolated and do not receive parent per-tool metadata.
        Initializes tool output management for efficient tool result sharing.

        Args:
            input_data: The user's input (typically a query string).
            **kwargs: Additional keyword arguments including optional metadata.
                - thread_id: Thread identifier passed from _create_graph_config.

        Returns:
            Dictionary representing the initial graph state with messages, metadata, artifacts,
            and tool output management components.
        """
        if isinstance(input_data, str):
            query = input_data
        elif isinstance(input_data, dict) and "query" in input_data:
            query = input_data["query"]
        else:
            raise TypeError(f"Unsupported input type for LangGraphReactAgent: {type(input_data)}")

        existing_messages = kwargs.get("messages", []) or []
        messages: list[BaseMessage] = existing_messages + [HumanMessage(content=query)]

        # Extract metadata for tools and agent context
        metadata = self._extract_metadata_from_kwargs(**kwargs)

        # If caller specified memory_user_id, inject it as per-tool config for the Mem0 tool
        memory_user_id: str | None = kwargs.get("memory_user_id")
        if memory_user_id and self._memory_enabled():
            self._add_user_id_memory_tool_config(metadata, memory_user_id)

        # thread_id is passed explicitly from the caller after _create_graph_config
        thread_id = kwargs.get("thread_id")

        # Use the agent's tool output manager (shared or private)
        step_limit_config = kwargs.get("step_limit_config") or self.step_limit_config

        # Step limit context inheritance (Spec-2)
        try:
            inherited_depth = _DELEGATION_DEPTH_CVAR.get()
        except LookupError:
            inherited_depth = 0

        try:
            inherited_chain = list(_DELEGATION_CHAIN_CVAR.get())
        except LookupError:
            inherited_chain = []

        try:
            inherited_budget = _REMAINING_STEP_BUDGET_CVAR.get()
        except LookupError:
            inherited_budget = None

        # Set step_limit_config in ContextVar so delegation tools can access it
        if step_limit_config:
            _STEP_LIMIT_CONFIG_CVAR.set(step_limit_config)

        graph_input = {
            "messages": messages,
            "event_emitter": kwargs.get("event_emitter"),
            "artifacts": [],
            "metadata": metadata,
            "tool_output_manager": self.tool_output_manager,
            "thread_id": thread_id,
            # Step limit state initialization
            "current_step": 0,  # Start at step 0
            "delegation_depth": inherited_depth,
            "delegation_chain": inherited_chain,
            "step_limit_config": asdict(step_limit_config) if step_limit_config else None,
            "remaining_step_budget": inherited_budget,
        }

        return graph_input

    def _resolve_tool_metadata(self, tool_name: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
        """Resolve effective metadata for a specific tool given the mixed schema.

        Metadata Resolution Hierarchy (lowest to highest precedence):

        1. Agent-level flat defaults: Apply to all tools from self.tool_configs
           - Skips 'tool_configs' key and dict values (per-tool configs)

        2. Agent-level per-tool defaults: From self.tool_configs[tool_name] or
           self.tool_configs['tool_configs'][tool_name]

        3. Request-level global metadata: From metadata kwargs, excluding 'tool_configs' key

        4. Request-level per-tool metadata: From metadata['tool_configs'][tool_name]
           - Highest precedence, overrides all previous layers

        Tool names are sanitized for consistent lookup across all layers.

        Args:
            tool_name: Sanitized runtime tool name (e.g., 'delegate_to_report_generator')
            metadata: Raw metadata from kwargs (flat dict or mixed schema)

        Returns:
            Merged metadata for this tool with proper precedence hierarchy applied.
        """
        effective_metadata: dict[str, Any] = {}

        # Layer 1: Agent-level defaults (lowest precedence)
        self._apply_agent_defaults(effective_metadata, tool_name)

        # Layer 2: Request-level global metadata (middle precedence)
        self._apply_global_metadata(effective_metadata, metadata)

        # Layer 3: Request-level per-tool metadata (highest precedence)
        self._apply_per_tool_metadata(effective_metadata, tool_name, metadata)

        return effective_metadata

    def _apply_agent_defaults(self, effective_metadata: dict[str, Any], tool_name: str) -> None:
        """Apply agent-level default configurations to effective metadata.

        This method implements a 3-layer agent configuration hierarchy:

        1. Flat agent defaults: Apply to ALL tools from self.tool_configs
           - Processes top-level key-value pairs (excluding TOOL_CONFIGS_KEY)
           - Skips dictionary values as they are per-tool configurations
           - Example: {"api_timeout": 30, "retry_count": 3}

        2. Agent per-tool defaults (direct key mapping): From self.tool_configs[tool_name]
           - Direct tool name as key in agent configuration
           - Example: self.tool_configs["search_tool"] = {"max_results": 10}

        3. Agent per-tool defaults (nested structure): From self.tool_configs[TOOL_CONFIGS_KEY][tool_name]
           - Tool configurations nested under TOOL_CONFIGS_KEY
           - Tool names are sanitized for consistent lookup
           - Example: self.tool_configs["tool_configs"]["search_tool"] = {"max_results": 10}

        Configuration Precedence (later layers override earlier ones):
        Flat defaults < Direct per-tool < Nested per-tool

        Args:
            effective_metadata: The metadata dict to update with agent defaults
            tool_name: The sanitized tool name to apply configurations for
        """
        if not isinstance(self.tool_configs, dict):
            return

        # Flat agent defaults (apply to all tools)
        for k, v in self.tool_configs.items():
            if k != TOOL_CONFIGS_KEY and not isinstance(v, dict):
                effective_metadata[k] = v

        # Agent per-tool defaults (direct key mapping)
        agent_direct = self.tool_configs.get(tool_name)
        if isinstance(agent_direct, dict):
            effective_metadata.update(agent_direct)

        # Agent per-tool defaults (nested under 'tool_configs')
        agent_nested_map = self.tool_configs.get(TOOL_CONFIGS_KEY)
        if isinstance(agent_nested_map, dict):
            sanitized_map = self._sanitize_tool_names_map(agent_nested_map)
            agent_nested = sanitized_map.get(tool_name)
            if isinstance(agent_nested, dict):
                effective_metadata.update(agent_nested)

    def _apply_global_metadata(self, effective_metadata: dict[str, Any], metadata: dict[str, Any] | None) -> None:
        """Apply request-level global metadata to effective metadata.

        Args:
            effective_metadata: The metadata dict to update
            metadata: Raw metadata from request
        """
        if not (metadata and isinstance(metadata, dict)):
            return

        # Extract global metadata (excluding per-tool section)
        global_metadata = {k: v for k, v in metadata.items() if k != TOOL_CONFIGS_KEY}
        effective_metadata.update(global_metadata)

    def _apply_per_tool_metadata(
        self, effective_metadata: dict[str, Any], tool_name: str, metadata: dict[str, Any] | None
    ) -> None:
        """Apply request-level per-tool metadata to effective metadata.

        Args:
            effective_metadata: The metadata dict to update
            tool_name: The sanitized tool name
            metadata: Raw metadata from request
        """
        if metadata and isinstance(metadata, dict):
            tools_metadata = metadata.get(TOOL_CONFIGS_KEY, {})
            if isinstance(tools_metadata, dict):
                sanitized_tools_map = self._sanitize_tool_names_map(tools_metadata)
                tool_specific = sanitized_tools_map.get(tool_name, {})
                if isinstance(tool_specific, dict):
                    effective_metadata.update(tool_specific)

    def _sanitize_tool_names_map(self, tools_map: dict[str, Any]) -> dict[str, Any]:
        """Sanitize tool names in a mapping for consistent lookup.

        Args:
            tools_map: Dictionary with potentially unsanitized tool names as keys

        Returns:
            Dictionary with sanitized tool names as keys
        """
        sanitized_map = {}
        for user_key, tool_meta in tools_map.items():
            sanitized_key = self.name_preprocessor.sanitize_tool_name(user_key)
            sanitized_map[sanitized_key] = tool_meta
        return sanitized_map

    def _create_tool_config(
        self, base_config: dict[str, Any] | None, state: dict[str, Any], tool_name: str | None = None
    ) -> dict[str, Any]:
        """Create enriched tool configuration with metadata and context.

        Args:
            base_config: The base configuration passed to the tool node.
            state: The current agent state containing metadata and other context.
            tool_name: Optional tool name for per-tool metadata resolution.

        Returns:
            dict[str, Any]: Enriched configuration for tool execution.
        """
        tool_config = base_config.copy() if base_config else {}

        state_metadata = state.get("metadata")
        if tool_name:
            effective_metadata = self._resolve_tool_metadata(tool_name, state_metadata)
        else:
            effective_metadata = state_metadata if isinstance(state_metadata, dict) else {}

        if effective_metadata:
            if "metadata" not in tool_config:
                tool_config["metadata"] = effective_metadata
            else:
                tool_config["metadata"].update(effective_metadata)
            logger.debug(f"Agent '{self.name}': Passing metadata to tool '{tool_name}': {effective_metadata}")

        return tool_config

    def _extract_storable_data(self, tool_output: Any) -> Any:
        """Extract storable data from tool output for the tool output management system.

        This method determines what part of a tool's output should be stored for later
        reference by other tools. It handles different output formats and extracts the
        most relevant data for storage.

        The extraction logic varies by type:
        - Command objects: Extracts the 'result' field from the update dict, or the entire update dict
        - String objects: Returns the string as-is
        - Dict objects: Returns the 'result' key if present, otherwise the entire dict
        - Other types: Converts to string representation

        This method is used in the tool output management system to automatically store
        outputs from tools that have `store_final_output=True` set. The extracted data can
        then be referenced by other tools using the `$tool_output.<call_id>` syntax.

        Example:
            For a Command object with update = {"result": "success", "data": [1, 2, 3]},
            this method would return "success".

            For a dict = {"result": "completed", "status": "ok"},
            this method would return "completed".

            For a dict = {"status": "ok", "data": [1, 2, 3]} (no "result" key),
            this method would return the entire dict.

        Args:
            tool_output: The raw output from a tool execution. Can be any type including
                Command, str, dict, or other objects.

        Returns:
            The data that should be stored in the tool output management system.
            The return type depends on the input type:
            - Command -> dict or the value of update.get("result")
            - str -> str (unchanged)
            - dict -> dict (either the value of .get("result") or the original dict)
            - other -> str (string representation of the object)
        """
        if isinstance(tool_output, Command):
            update = getattr(tool_output, "update", {}) or {}
            return update.get("result", update)
        elif isinstance(tool_output, str):
            return tool_output
        elif isinstance(tool_output, dict):
            return tool_output.get("result", tool_output)
        else:
            return str(tool_output)

    def _build_tool_output_aware_instruction(
        self, base_instruction: str, state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> str:
        """Build LLM instruction that includes context about available tool outputs.

        This method enhances the base instruction with information about previously
        stored tool outputs, allowing the LLM to make informed decisions about
        which outputs to reference in subsequent tool calls.

        Args:
            base_instruction: The original system instruction for the agent.
            state: Current agent state containing the tool output manager.
            config: Optional configuration containing thread_id information.

        Returns:
            Enhanced instruction string that includes tool output context.
        """
        manager = state.get(TOOL_OUTPUT_MANAGER_KEY)

        if not manager or not self.tool_output_manager:
            return base_instruction

        thread_id = self._extract_thread_id_from_config(config)

        if not manager.has_outputs(thread_id):
            return base_instruction
        outputs_summary = manager.generate_summary(max_entries=10, thread_id=thread_id)

        # Build enhanced instruction
        prompt = dedent(f"""
        {base_instruction}

        <TOOL_OUTPUT_REFERENCES>

        # Goal
        - Use the most relevant stored tool output via "$tool_output.<call_id>" to avoid copying large data.

        # Usage
        - Syntax: "$tool_output.<call_id>" in any tool argument; returns the full stored output.
        - IDs: Use only those listed below; do not invent or modify.
        - Selection: Pick the most relevant (usually most recent).
        - Don’ts: Don’t paste raw output or expand references.
        - Errors: Invalid/missing IDs fail—ask for the correct call_id or run the prerequisite tool.

        # Example
        - tool_name.run(tool_argument="$tool_output.abc123")

        # User Output Schema
        - "reference": "$tool_output.<call_id>", "tool": "<tool_name>", "agent": "<agent_name>", "data_preview": "<truncated preview>"

        Available Outputs
        {outputs_summary}
        </TOOL_OUTPUT_REFERENCES>
        """)  # noqa: E501
        return prompt

    def _cleanup_thread_context(self, current_thread_id: str | None, token: Any) -> None:
        """Extend base cleanup to dispose cached PII handlers.

        Args:
            current_thread_id: ID of the thread whose context is being cleaned up.
            token: Cancellation or execution token passed from the caller.

        Returns:
            None. This method performs cleanup side effects only.
        """
        super()._cleanup_thread_context(current_thread_id, token)
        if current_thread_id:
            self._pii_handlers_by_thread.pop(current_thread_id, None)

    def _format_graph_output(self, final_state_result: dict[str, Any]) -> Any:
        """Convert final graph state to user-friendly output.

        Args:
            final_state_result: The final state from graph execution.

        Returns:
            Formatted output dictionary.
        """
        return self._extract_output_from_final_state(final_state_result)


class LangGraphAgent(LangGraphReactAgent):
    """Alias for LangGraphReactAgent."""


class LangChainAgent(LangGraphReactAgent):
    """Alias for LangGraphReactAgent."""
