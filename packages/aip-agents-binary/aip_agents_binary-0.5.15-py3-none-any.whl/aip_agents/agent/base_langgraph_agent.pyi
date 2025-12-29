from _typeshed import Incomplete
from a2a.types import AgentCard as AgentCard
from abc import abstractmethod
from aip_agents.agent.base_agent import BaseAgent as BaseAgent
from aip_agents.agent.system_instruction_context import get_current_date_context as get_current_date_context
from aip_agents.constants import TEXT_PREVIEW_LENGTH as TEXT_PREVIEW_LENGTH
from aip_agents.mcp.client import LangchainMCPClient as LangchainMCPClient
from aip_agents.memory import BaseMemory as BaseMemory, MemoryFactory as MemoryFactory, MemoryMethod as MemoryMethod
from aip_agents.memory.constants import MemoryDefaults as MemoryDefaults
from aip_agents.schema.agent import StreamMode as StreamMode
from aip_agents.schema.hitl import HitlMetadata as HitlMetadata
from aip_agents.tools.tool_config_injector import CONFIG_SCHEMA_ATTR as CONFIG_SCHEMA_ATTR, TOOL_CONFIG_SCHEMA_ATTR as TOOL_CONFIG_SCHEMA_ATTR, inject_config_methods_into_tool as inject_config_methods_into_tool
from aip_agents.types import A2AEvent as A2AEvent, A2AStreamEventType as A2AStreamEventType
from aip_agents.utils import augment_query_with_file_paths as augment_query_with_file_paths, validate_references as validate_references
from aip_agents.utils.langgraph.tool_managers.a2a_tool_manager import A2AToolManager as A2AToolManager
from aip_agents.utils.langgraph.tool_managers.delegation_tool_manager import DelegationToolManager as DelegationToolManager
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata.activity_metadata_helper import create_tool_activity_info as create_tool_activity_info
from aip_agents.utils.metadata_helper import DefaultStepMessages as DefaultStepMessages, Kind as Kind, MetadataFieldKeys as MetadataFieldKeys, Status as Status, end_step_counter_scope as end_step_counter_scope, get_next_step_number as get_next_step_number, start_step_counter_scope as start_step_counter_scope
from aip_agents.utils.pii import deanonymize_final_response_content as deanonymize_final_response_content
from aip_agents.utils.sse_chunk_transformer import SSEChunkTransformer as SSEChunkTransformer
from aip_agents.utils.token_usage_helper import STEP_USAGE_KEY as STEP_USAGE_KEY, TOTAL_USAGE_KEY as TOTAL_USAGE_KEY, USAGE_METADATA_KEY as USAGE_METADATA_KEY
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from gllm_core.event import EventEmitter
from gllm_core.schema import Chunk as Chunk
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages as add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Checkpointer
from typing import Any

logger: Incomplete

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
    final_event_yielded: bool = ...
    pending_artifacts: list | None = ...
    seen_artifact_hashes: set | None = ...
    processed_message_count: int = ...
    final_state: dict[str, Any] | None = ...
    last_final_content: str | None = ...
    saved_memory: bool = ...
    is_token_streaming: bool = ...
    def __post_init__(self) -> None:
        """Initialize mutable defaults."""

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
    state_schema: Incomplete
    thread_id_key: Incomplete
    enable_a2a_token_streaming: Incomplete
    event_emitter: Incomplete
    checkpointer: Incomplete
    memory: BaseMemory | None
    a2a_tool_manager: Incomplete
    delegation_tool_manager: Incomplete
    regular_tools: list[BaseTool]
    mcp_tools: list[BaseTool]
    resolved_tools: list[BaseTool]
    def __init__(self, name: str, instruction: str, description: str | None = None, model: Any | None = None, tools: Sequence[BaseTool] | None = None, state_schema: type | None = None, thread_id_key: str = 'thread_id', event_emitter: EventEmitter | None = None, checkpointer: Checkpointer | None = None, enable_a2a_token_streaming: bool = False, **kwargs: Any) -> None:
        '''Initialize the BaseLangGraphAgent.

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
        '''
    def set_operation_mode(self, mode: str) -> None:
        '''Set the operation mode for dependency tracking.

        Args:
            mode: Operation mode - "parallel" (default) or "sequential"
        '''
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
    def register_a2a_agents(self, agent_cards: list[AgentCard]) -> None:
        """Register A2A communication capabilities using the A2A tool manager.

        Args:
            agent_cards (list[AgentCard]): List of AgentCard instances for external communication.
        """
    def register_delegation_agents(self, agents: list[BaseAgent]) -> None:
        """Register internal agent delegation capabilities using the delegation tool manager.

        Args:
            agents: List of BaseAgent instances for internal task delegation.
        """
    tools: Incomplete
    def update_regular_tools(self, new_tools: list[BaseTool], rebuild_graph: bool | None = None) -> None:
        """Update regular tools (not capabilities).

        Args:
            new_tools: New list of regular tools to use.
            rebuild_graph: Whether to rebuild graph. If None, uses auto_rebuild_graph setting.
        """
    def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Synchronously run the LangGraph agent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Returns:
            Dictionary containing the agent's response.
        """
    async def arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Asynchronously run the LangGraph agent with lazy MCP initialization.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments including configurable for LangGraph.

        Returns:
            Dictionary containing the agent's response and full final state.
        """
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
    async def cleanup(self) -> None:
        """Cleanup MCP resources including persistent sessions.

        This method performs best-effort cleanup of MCP client resources.
        Errors during cleanup are logged but do not raise exceptions to ensure
        the cleanup process completes gracefully.
        """
    async def arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        '''Asynchronously streams the agent\'s response in A2A format.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Dictionaries with "status" and "content" keys.
            Possible statuses: "working", "completed", "failed", "canceled".
        '''
    async def arun_sse_stream(self, query: str, task_id: str | None = None, context_id: str | None = None, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        '''Stream agent response as SSE-compatible chunks.

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
        '''
