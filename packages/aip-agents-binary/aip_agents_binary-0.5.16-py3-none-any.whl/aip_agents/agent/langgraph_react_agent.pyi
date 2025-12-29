from _typeshed import Incomplete
from aip_agents.agent.base_langgraph_agent import BaseLangGraphAgent as BaseLangGraphAgent
from aip_agents.agent.hitl.langgraph_hitl_mixin import LangGraphHitLMixin as LangGraphHitLMixin
from aip_agents.agent.hitl.manager import TOOL_EXECUTION_BLOCKING_DECISIONS as TOOL_EXECUTION_BLOCKING_DECISIONS
from aip_agents.middleware.base import AgentMiddleware as AgentMiddleware, ModelRequest as ModelRequest
from aip_agents.middleware.manager import MiddlewareManager as MiddlewareManager
from aip_agents.middleware.todolist import TodoList as TodoList, TodoListMiddleware as TodoListMiddleware
from aip_agents.schema.a2a import A2AStreamEventType as A2AStreamEventType
from aip_agents.schema.hitl import ApprovalDecision as ApprovalDecision, HitlMetadata as HitlMetadata
from aip_agents.schema.langgraph import ToolCallResult as ToolCallResult, ToolStorageParams as ToolStorageParams
from aip_agents.schema.step_limit import MaxStepsExceededError as MaxStepsExceededError, StepLimitConfig as StepLimitConfig
from aip_agents.tools.memory_search_tool import MEMORY_SEARCH_TOOL_NAME as MEMORY_SEARCH_TOOL_NAME
from aip_agents.tools.tool_config_injector import TOOL_CONFIGS_KEY as TOOL_CONFIGS_KEY
from aip_agents.utils import add_references_chunks as add_references_chunks
from aip_agents.utils.langgraph import convert_langchain_messages_to_gllm_messages as convert_langchain_messages_to_gllm_messages, convert_lm_output_to_langchain_message as convert_lm_output_to_langchain_message
from aip_agents.utils.langgraph.tool_output_management import StoreOutputParams as StoreOutputParams, ToolOutputManager as ToolOutputManager, ToolReferenceError as ToolReferenceError, ToolReferenceResolver as ToolReferenceResolver
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata.activity_metadata_helper import create_tool_activity_info as create_tool_activity_info
from aip_agents.utils.metadata_helper import Kind as Kind, MetadataFieldKeys as MetadataFieldKeys, Status as Status
from aip_agents.utils.pii import ToolPIIHandler as ToolPIIHandler, add_pii_mappings as add_pii_mappings, normalize_enable_pii as normalize_enable_pii
from aip_agents.utils.reference_helper import extract_references_from_tool as extract_references_from_tool
from aip_agents.utils.step_limit_manager import StepLimitManager as StepLimitManager
from aip_agents.utils.token_usage_helper import TOTAL_USAGE_KEY as TOTAL_USAGE_KEY, USAGE_METADATA_KEY as USAGE_METADATA_KEY, add_usage_metadata as add_usage_metadata, extract_and_update_token_usage_from_ai_message as extract_and_update_token_usage_from_ai_message, extract_token_usage_from_tool_output as extract_token_usage_from_tool_output
from collections.abc import Awaitable as Awaitable, Sequence
from dataclasses import dataclass
from gllm_core.event import EventEmitter
from gllm_core.schema import Chunk as Chunk
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage as BaseMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages as add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.managed import IsLastStep, RemainingSteps
from typing import Annotated, Any
from typing_extensions import TypedDict

logger: Incomplete
DEFAULT_INSTRUCTION: str
TOOL_RUN_STREAMING_METHOD: str
TOOL_OUTPUT_MANAGER_KEY: str
CALL_ID_KEY: str

@dataclass
class ToolCallContext:
    """Context information for executing a single tool call."""
    config: dict[str, Any] | None
    state: dict[str, Any]
    pending_artifacts: list[dict[str, Any]]
    hitl_decision: ApprovalDecision | None = ...

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
    todos: TodoList | None
    current_step: int
    delegation_depth: int
    delegation_chain: list[str]
    step_limit_config: StepLimitConfig | None

class LangGraphReactAgent(LangGraphHitLMixin, BaseLangGraphAgent):
    """A ReAct agent template built on LangGraph.

    This agent can use either:
    - An LMInvoker (if self.lm_invoker is set by BaseAgent)
    - A LangChain BaseChatModel (if self.model is set by BaseAgent)

    The graph structure follows the standard ReAct pattern:
    agent -> tools -> agent (loop) -> END
    """
    tool_output_manager: Incomplete
    step_limit_config: Incomplete
    def __init__(self, name: str, instruction: str = ..., model: BaseChatModel | str | Any | None = None, tools: Sequence[BaseTool] | None = None, agents: Sequence[Any] | None = None, description: str | None = None, thread_id_key: str = 'thread_id', event_emitter: EventEmitter | None = None, tool_output_manager: ToolOutputManager | None = None, planning: bool = False, middlewares: Sequence[AgentMiddleware] | None = None, step_limit_config: StepLimitConfig | None = None, **kwargs: Any) -> None:
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
    def define_graph(self, graph_builder: StateGraph) -> CompiledStateGraph:
        """Define the ReAct agent graph structure.

        Args:
            graph_builder: The StateGraph builder to define the graph structure.

        Returns:
            Compiled LangGraph ready for execution.
        """

class LangGraphAgent(LangGraphReactAgent):
    """Alias for LangGraphReactAgent."""
class LangChainAgent(LangGraphReactAgent):
    """Alias for LangGraphReactAgent."""
