"""Delegation tool manager for LangGraph agents.

This module provides the DelegationToolManager class that converts internal
agent instances into LangChain tools for delegation within LangGraph agents.
"""

import uuid
from contextvars import ContextVar
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langgraph.config import get_stream_writer
from langgraph.types import Command, StreamWriter

import aip_agents.agent.base_langgraph_agent as bla
from aip_agents.agent.base_agent import BaseAgent
from aip_agents.schema.step_limit import MaxDelegationDepthExceededError
from aip_agents.types import A2AEvent, A2AStreamEventType
from aip_agents.utils.artifact_helpers import extract_artifacts_from_agent_response
from aip_agents.utils.langgraph.tool_managers.base_tool_manager import BaseLangGraphToolManager
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata_helper import MetadataFieldKeys, get_next_step_number
from aip_agents.utils.pii.pii_helper import (
    anonymize_final_response_content,
    extract_pii_mapping_from_agent_response,
)
from aip_agents.utils.reference_helper import extract_references_from_agent_response
from aip_agents.utils.step_limit_manager import (
    _DELEGATION_CHAIN_CVAR,
    _DELEGATION_DEPTH_CVAR,
    _REMAINING_STEP_BUDGET_CVAR,
    _STEP_LIMIT_CONFIG_CVAR,
    StepLimitManager,
)
from aip_agents.utils.token_usage_helper import (
    STEP_USAGE_KEY,
    TOTAL_USAGE_KEY,
    USAGE_METADATA_KEY,
    extract_token_usage_from_agent_response,
)

# Context variable to carry parent step id from coordinator to sub-agent as a fallback
_DELEGATION_PARENT_STEP_ID_CVAR: ContextVar[str | None] = ContextVar("delegation_parent_step_id", default=None)
# Track the last sub-agent TOOL_CALL step_id so sub-agent TOOL_RESULT can link to it
_DELEGATION_SUB_START_STEP_CVAR: ContextVar[dict[str, str] | None] = ContextVar(
    "delegation_sub_start_step", default=None
)

logger = get_logger(__name__)

# Constants for response keys
OUTPUT_KEY = "output"
RESULT_KEY = "result"
ARTIFACTS_KEY = "artifacts"
METADATA_KEY = "metadata"

# Internal metadata keys to filter out
METADATA_INTERNAL_PREFIXES = ["__", "langgraph_", "langchain_"]
METADATA_INTERNAL_KEYS = {"step_id", "previous_step_ids", "agent_name"}
AGENT_RUN_A2A_STREAMING_METHOD = "arun_a2a_stream"


class DelegationToolManager(BaseLangGraphToolManager):
    """Manages internal agent delegation tools for LangGraph agents.

    This tool manager converts internal agent instances into LangChain tools
    that can be used for task delegation within a unified ToolNode. Each
    delegated agent becomes a tool that the coordinator can call.

    Simplified version following legacy BaseLangChainAgent patterns.
    """

    def __init__(self, parent_agent: BaseAgent | None = None):
        """Initialize the delegation tool manager.

        Args:
            parent_agent: The parent agent that creates delegation tools, used for parent step lookup.
        """
        super().__init__()
        self.registered_agents: list[BaseAgent] = []
        self.parent_agent = parent_agent

    def register_resources(self, agents: list[BaseAgent]) -> list[BaseTool]:
        """Register internal agents for delegation and convert them to tools.

        Args:
            agents: List of BaseAgent instances for internal task delegation.

        Returns:
            List of created delegation tools.
        """
        self.registered_agents = list(agents)
        self.created_tools = []

        for agent in agents:
            delegation_tool = self._create_delegation_tool_streaming(agent)
            self.created_tools.append(delegation_tool)

        logger.info(
            f"DelegationToolManager: Created {len(self.created_tools)} streaming delegation tools "
            f"for {len(agents)} agents"
        )
        return self.created_tools

    def get_resource_names(self) -> list[str]:
        """Get names of all registered delegation agents.

        Returns:
            list[str]: A list of names of all registered delegation agents.
        """
        return [agent.name for agent in self.registered_agents]

    def _create_delegation_tool_streaming(self, agent: BaseAgent) -> BaseTool:
        """Create a LangChain tool for agent delegation with real-time streaming support.

        This version uses async streaming to provide real-time tool call and artifact visibility.

        Args:
            agent: The agent to create a delegation tool for.

        Returns:
            BaseTool: An async LangChain tool for agent delegation with streaming.
        """

        @tool
        async def delegate_to_agent(query: str, config: RunnableConfig) -> str | dict[str, Any]:
            """Delegate task to internal agent with real-time streaming.

            Args:
                query: The task to delegate to the internal agent.
                config: The runtime configuration for the agent.

            Returns:
                The result from the delegated agent, including artifacts if any.
            """
            writer: StreamWriter = get_stream_writer()

            try:
                # Check delegation depth limit before executing
                try:
                    current_depth = _DELEGATION_DEPTH_CVAR.get() or 0
                    parent_config = _STEP_LIMIT_CONFIG_CVAR.get()

                    temp_state = {
                        "delegation_depth": current_depth,
                        "delegation_chain": list(_DELEGATION_CHAIN_CVAR.get() or []),
                    }
                    manager = StepLimitManager.from_state(temp_state, config=parent_config)
                    manager.check_delegation_depth(target_agent_name=agent.name)

                except MaxDelegationDepthExceededError as depth_error:
                    logger.warning(
                        f"DelegationToolManager: Delegation depth check failed for '{agent.name}': {depth_error}"
                    )
                    self._notify_error_via_writer(writer, agent.name, depth_error)
                    return self._handle_delegation_error(agent.name, depth_error)

                logger.debug(f"DelegationToolManager: Delegating to '{agent.name}'")
                configurable_kwargs = self._get_configurable_kwargs(agent, config)
                result = await self._execute_delegated_agent(agent, query, configurable_kwargs, config, writer)
                return self._handle_delegation_response_with_extras(agent.name, result)

            except Exception as e:
                self._notify_error_via_writer(writer, agent.name, e)
                return self._handle_delegation_error(agent.name, e)

        delegate_to_agent.name = f"delegate_to_{agent.name}"
        delegate_to_agent.description = (
            f"Delegate tasks to internal agent '{agent.name}'. "
            f"Use this when you need to: {agent.description or 'coordinate with this agent'}"
        )

        delegate_to_agent.metadata = self._build_delegation_tool_metadata(agent)

        return delegate_to_agent

    @staticmethod
    def _build_delegation_tool_metadata(agent: BaseAgent) -> dict[str, Any]:
        """Create metadata payload used to mark tools as delegation-capable.

        Args:
            agent (BaseAgent): The agent to create metadata for.

        Returns:
            dict[str, Any]: The metadata payload for the delegation tool.
        """
        return {
            "is_delegation_tool": True,
            "delegated_agent_name": agent.name,
            "tool_type": "delegation",
            "delegation_manager": DelegationToolManager.__name__,
        }

    async def _execute_delegated_agent(
        self,
        agent: BaseAgent,
        query: str,
        configurable_kwargs: dict[str, Any],
        config: RunnableConfig | None,
        writer: StreamWriter,
    ) -> Any:
        """Execute delegated agent call with streaming or synchronous fallback.

        Args:
            agent: The delegated agent to execute.
            query: The query string to pass to the agent.
            configurable_kwargs: Additional configuration arguments for the agent.
            config: Runnable configuration for the execution context.
            writer: Stream writer to emit events during execution.

        Returns:
            The result of the agent execution.
        """
        # T021: Propagate delegation depth and step budget to sub-agent
        # Import here to avoid circular dependencies if any
        from aip_agents.utils.step_limit_manager import (
            _DELEGATION_DEPTH_CVAR,
            _STEP_LIMIT_CONFIG_CVAR,
            StepLimitManager,
        )

        # Context tokens for reset
        depth_token = None
        chain_token = None
        budget_token = None

        try:
            # Get current delegation context from ContextVars
            current_depth = _DELEGATION_DEPTH_CVAR.get() or 0
            current_chain = _DELEGATION_CHAIN_CVAR.get() or []
            remaining_budget = _REMAINING_STEP_BUDGET_CVAR.get()
            parent_config = _STEP_LIMIT_CONFIG_CVAR.get()

            # Increment depth for sub-agent
            new_depth = current_depth + 1
            new_chain = list(current_chain) + [agent.name]

            # Calculate child budget using parent logic
            # Use transient manager to apply calculation rules
            manager = StepLimitManager(
                config=parent_config,
                initial_delegation_depth=current_depth,
                parent_step_budget=remaining_budget,
            )
            child_max_steps = None
            child_config = getattr(agent, "step_limit_config", None)
            if child_config is not None and hasattr(child_config, "max_steps"):
                child_max_steps = child_config.max_steps
            child_budget = manager.get_child_budget(child_max_steps=child_max_steps)

            # Set context for sub-agent
            depth_token = _DELEGATION_DEPTH_CVAR.set(new_depth)
            chain_token = _DELEGATION_CHAIN_CVAR.set(tuple(new_chain))
            budget_token = _REMAINING_STEP_BUDGET_CVAR.set(child_budget)

            logger.debug(
                f"DelegationToolManager: Delegating to '{agent.name}' at depth {new_depth}, "
                f"chain: {new_chain}, child_budget: {child_budget} (from parent: {remaining_budget})"
            )

            # Execute
            if not hasattr(agent, AGENT_RUN_A2A_STREAMING_METHOD):
                return agent.run(query, **configurable_kwargs)

            self._set_parent_step_context(config)
            final_chunk = await self._handle_delegation_streaming(agent, query, configurable_kwargs, writer)
            return self._format_final_chunk_sub_agent_output(final_chunk)

        except Exception as e:
            logger.warning(f"DelegationToolManager: Error in delegation execution: {e}")
            raise e
        finally:
            # Restore context and propagate child usage back to parent (Spec-1)
            # Parent context is restored by reset, then we set it to the final child budget
            if budget_token:
                final_child_budget = _REMAINING_STEP_BUDGET_CVAR.get()
                _REMAINING_STEP_BUDGET_CVAR.reset(budget_token)
                _REMAINING_STEP_BUDGET_CVAR.set(final_child_budget)

            if depth_token:
                _DELEGATION_DEPTH_CVAR.reset(depth_token)
            if chain_token:
                _DELEGATION_CHAIN_CVAR.reset(chain_token)

    def _set_parent_step_context(self, config: RunnableConfig | None) -> None:
        """Bridge parent step ID from tool configuration into context variables.

        Args:
            config: Runnable configuration containing parent step ID information.
        """
        try:
            parent_step_id = None
            cfg = config or {}
            cfg_conf = cfg.get("configurable") if isinstance(cfg, dict) else None
            if isinstance(cfg_conf, dict):
                parent_step_id = cfg_conf.get("parent_step_id")
            _DELEGATION_PARENT_STEP_ID_CVAR.set(parent_step_id)
        except Exception:
            _DELEGATION_PARENT_STEP_ID_CVAR.set(None)

    def _notify_error_via_writer(self, writer: StreamWriter, agent_name: str, exception: Exception) -> None:
        """Safely notify error via writer using A2AEvent structure.

        Args:
            writer: Stream writer for sending updates
            agent_name: Name of the agent that encountered the error
            exception: The exception that occurred
        """
        try:
            a2a_event: A2AEvent = {
                "event_type": A2AStreamEventType.ERROR,
                "content": f"Error in {agent_name}: {str(exception)}",
                "metadata": {},
                "is_final": False,
            }
            writer(a2a_event)
        except Exception:
            pass

    def _create_delegation_tool(self, agent: BaseAgent) -> BaseTool:
        """Create a LangChain tool for agent delegation (non-streaming version).

        Simplified version following legacy BaseLangChainAgent._create_delegation_func pattern.
        This is the original non-streaming version for backward compatibility.

        Args:
            agent: The agent to create a delegation tool for.

        Returns:
            BaseTool: A LangChain tool for agent delegation.
        """

        @tool
        def delegate_to_agent(query: str, config: RunnableConfig) -> str | dict[str, Any] | Command:
            """Delegate task to internal agent.

            Args:
                query: The task to delegate to the internal agent.
                config: The runtime configuration for the agent.

            Returns:
                The result from the delegated agent, including artifacts and metadata if any.
            """
            try:
                logger.debug(f"DelegationToolManager: Delegating to '{agent.name}'")

                # Use simple delegation kwargs (following legacy pattern)
                configurable_kwargs = self._get_configurable_kwargs(agent, config)
                result = agent.run(query, **configurable_kwargs)

                # Handle response with artifact, metadata, references and token usage support
                return self._handle_delegation_response_with_extras(agent.name, result)

            except Exception as e:
                return self._handle_delegation_error(agent.name, e)

        # Set tool metadata
        delegate_to_agent.name = f"delegate_to_{agent.name}"
        delegate_to_agent.description = (
            f"Delegate tasks to internal agent '{agent.name}'. "
            f"Use this when you need to: {agent.description or 'coordinate with this agent'}"
        )

        delegate_to_agent.metadata = self._build_delegation_tool_metadata(agent)

        return delegate_to_agent

    def _get_configurable_kwargs(self, agent: BaseAgent, config: RunnableConfig | None = None) -> dict[str, Any]:
        """Get configurable kwargs for agent delegation.

        Args:
            agent: The agent to get configurable kwargs for.
            config: The parent agent's config containing thread_id to inherit.

        Returns:
            dict[str, Any]: A dictionary with 'configurable' key if the agent
                            has 'thread_id_key', otherwise an empty dictionary.
        """
        if hasattr(agent, "thread_id_key"):
            # Try to use parent thread ID from config first
            parent_thread_id = None
            if config and config.get("configurable"):
                parent_thread_id = config["configurable"].get("thread_id")

            if parent_thread_id:
                # Use parent's thread ID to maintain conversation continuity
                return {"configurable": {agent.thread_id_key: parent_thread_id}}
            else:
                delegation_thread_id = f"delegation_to_{agent.name}_{uuid.uuid4().hex[:8]}"
                return {"configurable": {agent.thread_id_key: delegation_thread_id}}
        return {}

    def _handle_delegation_response(self, agent_name: str, result: Any) -> str:
        """Handle delegation response (following legacy pattern).

        Args:
            agent_name (str): The name of the agent that was delegated to.
            result (Any): The result from the delegated agent.

        Returns:
            str: The formatted response string.
        """
        try:
            if isinstance(result, dict):
                response_content = result.get(
                    OUTPUT_KEY, f"No '{OUTPUT_KEY}' key found in response from agent {agent_name}."
                )
                logger.info(f"DelegationToolManager: Agent '{agent_name}' responded: {response_content}")
                return str(response_content)
            else:
                return str(result)
        except Exception as e:
            logger.warning(f"DelegationToolManager: Error formatting delegation response from '{agent_name}': {e}")
            return str(result)

    async def _handle_delegation_streaming(
        self, agent: BaseAgent, query: str, configurable_kwargs: dict, writer: StreamWriter
    ) -> dict | None:
        """Handle streaming communication with a delegated agent.

        Args:
            agent: The agent to stream from
            query: The query to send to the agent
            configurable_kwargs: Configuration parameters for the agent
            writer: Stream writer for sending updates

        Returns:
            The final result chunk from the agent
        """
        final_result = None

        async for chunk in agent.arun_a2a_stream(query, **configurable_kwargs):
            if isinstance(chunk, dict):
                self._anonymize_final_chunk(chunk)
                self._forward_sub_agent_chunk(chunk, writer)

                if self._is_delegation_chunk_final(chunk):
                    final_result = chunk
        return final_result

    def _is_delegation_chunk_final(self, chunk: dict) -> bool:
        """Check if a delegation chunk represents the final result.

        Args:
            chunk: The chunk to check

        Returns:
            True if this is the final chunk
        """
        return chunk.get("is_final") or chunk.get("status") == "completed"

    def _anonymize_final_chunk(self, chunk: dict) -> None:
        """Mask sub-agent final responses using available PII mapping.

        Args:
            chunk: Streamed response chunk from the delegated agent.

        Returns:
            None: This method mutates the provided chunk in place when masking is applied.
        """
        if not self._is_delegation_chunk_final(chunk):
            return

        content = chunk.get("content")
        if not isinstance(content, str) or not content:
            return

        chunk["content"] = anonymize_final_response_content(content, chunk)

    def _handle_delegation_response_with_extras(self, agent_name: str, result: Any) -> str | dict[str, Any] | Command:
        """Handle delegation response with full support for artifacts, metadata, references, and token usage.

        Args:
            agent_name: The name of the agent that provided the response.
            result: The result from the delegated agent.

        Returns:
            Either a string (when no additional data), dict with 'result' and other keys,
            or Command with comprehensive updates.
        """
        try:
            text_response, artifacts = extract_artifacts_from_agent_response(result)
            metadata_update = self._extract_metadata_from_agent_response(result)
            token_usage = extract_token_usage_from_agent_response(result)
            references = extract_references_from_agent_response(result)
            pii_mapping = extract_pii_mapping_from_agent_response(result)

            if artifacts:
                logger.info(f"DelegationToolManager: Agent '{agent_name}' responded with {len(artifacts)} artifacts")
            if metadata_update:
                logger.info(
                    f"DelegationToolManager: Agent '{agent_name}' responded with metadata updates: {metadata_update}"
                )
            if token_usage:
                logger.info(f"DelegationToolManager: Agent '{agent_name}' responded with token usage: {token_usage}")
            if references:
                logger.info(f"DelegationToolManager: Agent '{agent_name}' responded with {len(references)} references")
            if pii_mapping:
                logger.info(
                    f"DelegationToolManager: Agent '{agent_name}' responded with PII mapping: {len(pii_mapping)} entries"
                )

            # Prepare response with any additional data
            has_extras = self._has_response_extras(artifacts, metadata_update, token_usage, references, pii_mapping)

            if has_extras:
                update_dict = self._build_response_update_dict(
                    agent_name, text_response, artifacts, metadata_update, token_usage, references, pii_mapping
                )
                return Command(update=update_dict)
            else:
                return f"[{agent_name}] {text_response}"

        except Exception as e:
            logger.warning(f"DelegationToolManager: Error formatting delegation response from '{agent_name}': {e}")
            return str(result)

    def _has_response_extras(
        self,
        artifacts: list,
        metadata_update: dict | None,
        token_usage: dict | None,
        references: list,
        pii_mapping: dict[str, str] | None = None,
    ) -> bool:
        """Check if the response has any extra data beyond the text response.

        Args:
            artifacts (list): List of artifacts from the response.
            metadata_update (dict | None): Optional metadata update.
            token_usage (dict | None): Optional token usage information.
            references (list): List of references from the response.
            pii_mapping (dict[str, str] | None): Optional PII mapping from the response.

        Returns:
            bool: True if any extra data is present, False otherwise.
        """
        return any([artifacts, metadata_update, token_usage, references, pii_mapping])

    def _build_response_update_dict(  # noqa: PLR0913
        self,
        agent_name: str,
        text_response: str,
        artifacts: list,
        metadata_update: dict | None,
        token_usage: dict | None,
        references: list,
        pii_mapping: dict[str, str] | None = None,
    ) -> dict[str, Any]:  # noqa: PLR0913
        """Build the update dictionary for responses with extra data.

        Args:
            agent_name: Name of the agent that generated the response.
            text_response: The main text response from the agent.
            artifacts: List of artifacts associated with the response.
            metadata_update: Optional metadata update dictionary.
            token_usage: Optional token usage information.
            references: List of references associated with the response.
            pii_mapping: Optional PII mapping from the response.

        Returns:
            Dictionary containing the formatted response with all extra data included.
        """
        update_dict = {RESULT_KEY: f"[{agent_name}] {text_response}"}

        # Add each type of extra data if available
        if artifacts:
            update_dict[ARTIFACTS_KEY] = artifacts
        if metadata_update:
            update_dict[METADATA_KEY] = metadata_update
        if token_usage:
            update_dict[USAGE_METADATA_KEY] = token_usage
        if references:
            update_dict[MetadataFieldKeys.REFERENCES] = references
        if pii_mapping:
            update_dict[MetadataFieldKeys.PII_MAPPING] = pii_mapping

        return update_dict

    def _extract_metadata_from_agent_response(self, result: Any) -> dict[str, Any] | None:
        """Extract metadata from agent response for delegation tools.

        Args:
            result: The result returned by the delegated agent.

        Returns:
            Metadata dict if found, None otherwise.
        """
        if not isinstance(result, dict):
            return None

        full_state = result.get("full_final_state", {})
        if not isinstance(full_state, dict):
            return None

        metadata = full_state.get("metadata")
        if not isinstance(metadata, dict):
            return None

        # Keep filtered metadata but also preserve linkage fields
        filtered = self._filter_metadata(metadata)
        prev_ids = metadata.get("previous_step_ids")
        if isinstance(prev_ids, list) and prev_ids:
            # Do not drop linkage information
            filtered["previous_step_ids"] = list(prev_ids)
        # Optionally keep step_id if present (useful for advanced tracing)
        if "step_id" in metadata and metadata["step_id"]:
            filtered.setdefault("step_id", metadata["step_id"])  # don't overwrite if user explicitly set

        return filtered

    def _filter_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Filter out internal LangGraph keys to avoid pollution.

        Args:
            metadata: Raw metadata dict

        Returns:
            Filtered metadata dict
        """
        filtered_metadata = {
            k: v
            for k, v in metadata.items()
            if not any(k.startswith(prefix) for prefix in METADATA_INTERNAL_PREFIXES)
            and k not in METADATA_INTERNAL_KEYS
        }
        return filtered_metadata if filtered_metadata else {}

    def _handle_delegation_error(self, agent_name: str, exception: Exception) -> str:
        """Handle delegation errors (following legacy pattern).

        Args:
            agent_name: The name of the agent that caused the error.
            exception: The exception that occurred.

        Returns:
            str: A string containing the error message.
        """
        error_msg = f"Error calling agent {agent_name}: {str(exception)}"
        logger.error(f"DelegationToolManager: Error delegating to '{agent_name}': {exception}", exc_info=True)
        return error_msg

    def _forward_sub_agent_chunk(self, chunk: dict, writer: StreamWriter) -> None:
        """Forward sub-agent streaming chunks in real-time.

        Args:
            chunk: Streaming chunk from the sub-agent
            writer: Stream writer to emit events
        """
        event_type = self._extract_event_type(chunk)

        if event_type == A2AStreamEventType.TOOL_CALL:
            self._forward_tool_call_event(chunk, writer)
        elif event_type == A2AStreamEventType.TOOL_RESULT:
            self._forward_tool_result_event(chunk, writer)

    def _extract_event_type(self, chunk: dict) -> A2AStreamEventType | None:
        """Extract event type from chunk, converting to A2AStreamEventType enum.

        Args:
            chunk: Streaming chunk from the sub-agent

        Returns:
            Event type as A2AStreamEventType enum, or None if not found/invalid
        """
        event_type = chunk.get("event_type")

        if isinstance(event_type, A2AStreamEventType):
            return event_type

        if isinstance(event_type, str):
            try:
                return A2AStreamEventType(event_type)
            except ValueError:
                return None

        return None

    def _extract_delegation_tool_name_prefix(self, tool_name: str) -> str:
        """Extract meaningful prefix from delegation tool name.

        Args:
            tool_name: The delegation tool name (e.g., "delegate_to_TableAgent")

        Returns:
            The extracted prefix (e.g., "table" from "delegate_to_TableAgent")
        """
        if tool_name.startswith("delegate_to_"):
            # Extract the agent name after "delegate_to_"
            agent_name = tool_name[12:]  # Remove "delegate_to_"
            # Remove "Agent" suffix if present
            if agent_name.endswith("Agent"):
                agent_name = agent_name[:-5]  # Remove "Agent"
            # Convert to lowercase and take first 4 characters
            return agent_name.lower()[:4]
        else:
            # Fallback to first 4 characters
            return tool_name[:4]

    def _generate_delegation_tool_call_step_id(self, tool_info: dict[str, Any], counter: int) -> str:
        """Generate step_id for delegation tool call events.

        Args:
            tool_info: Tool information
            counter: Step counter

        Returns:
            Generated step_id
        """
        if not tool_info or not tool_info.get("tool_calls"):
            return f"delegate_call_{counter:03d}"

        tool_calls = tool_info["tool_calls"]
        if len(tool_calls) == 1:
            # Single tool call
            tool_name = tool_calls[0].get("name", "unknown")
            prefix = self._extract_delegation_tool_name_prefix(tool_name)
            return f"{prefix}_call_{counter:03d}"
        else:
            # Multiple tool calls (parallel execution)
            tool_names = [self._extract_delegation_tool_name_prefix(tc.get("name", "unknown")) for tc in tool_calls]
            combined_name = "".join(tool_names)[:6]  # Limit length
            return f"{combined_name}_parent_{counter:03d}"

    def _generate_delegation_tool_result_step_id(self, tool_info: dict[str, Any] | None, counter: int) -> str:
        """Generate step_id for delegation tool result events.

        Args:
            tool_info: Tool information
            counter: Step counter

        Returns:
            Generated step_id
        """
        if not tool_info:
            return f"delegate_done_{counter:03d}"

        tool_name = tool_info.get("name", "unknown")
        prefix = self._extract_delegation_tool_name_prefix(tool_name)
        return f"{prefix}_done_{counter:03d}"

    def _generate_delegation_step_id(
        self, event_type: A2AStreamEventType, agent_name: str, tool_info: dict[str, Any] | None = None
    ) -> str:
        """Generate a meaningful step_id for delegation events.

        Args:
            event_type: The type of event (tool_call, tool_result, etc.)
            agent_name: The name of the delegated agent
            tool_info: Tool information containing tool names and IDs

        Returns:
            A meaningful step_id string
        """
        try:
            counter = get_next_step_number()

            # Use mapping to reduce branches
            step_id_generators = {
                A2AStreamEventType.TOOL_CALL: lambda: self._generate_delegation_tool_call_step_id(tool_info, counter),
                A2AStreamEventType.TOOL_RESULT: lambda: self._generate_delegation_tool_result_step_id(
                    tool_info, counter
                ),
            }

            generator = step_id_generators.get(event_type)
            if generator:
                return generator()

            # Handle both enum and string event types
            event_type_value = event_type.value if hasattr(event_type, "value") else str(event_type)
            fallback_prefix = self._build_fallback_prefix(agent_name)
            return f"{fallback_prefix}_{event_type_value}_{counter:03d}"

        except Exception:
            # Fallback to random generation if anything goes wrong
            return f"delegate_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _build_fallback_prefix(agent_name: str) -> str:
        """Create a fallback prefix that incorporates the agent name when available.

        Args:
            agent_name: The name of the agent to create a prefix for.

        Returns:
            A fallback prefix string incorporating the agent name.
        """
        if not agent_name:
            return "delegate"

        sanitized = "".join(ch for ch in agent_name.lower() if ch.isalnum())[:8]
        return f"delegate_{sanitized}" if sanitized else "delegate"

    def _forward_tool_call_event(self, chunk: dict, writer: StreamWriter) -> None:
        """Forward tool call events with coordinator-style format using A2AEvent structure.

        Args:
            chunk: Streaming chunk containing tool call info
            writer: Stream writer to emit events
        """
        tool_info = chunk.get("tool_info", {})
        message = self._create_tool_call_message(tool_info)
        metadata = self._prepare_tool_call_metadata(chunk, tool_info)

        a2a_event: A2AEvent = {
            "event_type": A2AStreamEventType.TOOL_CALL,
            "content": message,
            "metadata": metadata,
            "tool_info": tool_info,
            "is_final": False,
            "artifacts": chunk.get("artifacts"),
            MetadataFieldKeys.REFERENCES: chunk.get(MetadataFieldKeys.REFERENCES),
            STEP_USAGE_KEY: chunk.get(STEP_USAGE_KEY),
            TOTAL_USAGE_KEY: chunk.get(TOTAL_USAGE_KEY),
        }
        writer(a2a_event)

    def _prepare_tool_call_metadata(self, chunk: dict, tool_info: dict) -> dict:
        """Prepare metadata for tool call events with step ID generation and linkage.

        Args:
            chunk: Streaming chunk containing metadata
            tool_info: Tool information for step ID generation

        Returns:
            Prepared metadata dictionary
        """
        metadata = chunk.get("metadata") or {}
        self._ensure_step_id_in_metadata(metadata, tool_info)

        agent_name = metadata.get("agent_name")
        if agent_name:
            self._setup_agent_linkage(metadata, agent_name, tool_info)
        else:
            self._handle_missing_agent_name(metadata)

        return metadata

    def _ensure_step_id_in_metadata(self, metadata: dict, tool_info: dict) -> None:
        """Ensure step_id is present in metadata, generating one if missing.

        Args:
            metadata: Metadata dictionary to update
            tool_info: Tool information for step ID generation
        """
        if "step_id" not in metadata:
            agent_name_for_id = metadata.get("agent_name") or "anon_agent"
            metadata["step_id"] = self._generate_delegation_step_id(
                A2AStreamEventType.TOOL_CALL, agent_name_for_id, tool_info
            )

    def _setup_agent_linkage(self, metadata: dict, agent_name: str, tool_info: dict) -> None:
        """Setup linkage between parent and sub-agent for tool call events.

        Args:
            metadata: Metadata dictionary to update
            agent_name: Name of the agent
            tool_info: Tool information for parent lookup
        """
        parent_step_id = self._get_parent_step_id(tool_info)
        metadata["previous_step_ids"] = [parent_step_id] if parent_step_id else []

        # Record this sub-agent start step_id so its result can link back to it
        sub_start_map = _DELEGATION_SUB_START_STEP_CVAR.get() or {}
        sub_start_map[agent_name] = metadata["step_id"]
        _DELEGATION_SUB_START_STEP_CVAR.set(sub_start_map)

    def _get_parent_step_id(self, tool_info: dict) -> str | None:
        """Get parent step ID from context or parent agent lookup.

        Args:
            tool_info: Tool information for parent lookup

        Returns:
            Parent step ID if found, None otherwise
        """
        parent_step_id = _DELEGATION_PARENT_STEP_ID_CVAR.get()

        if not parent_step_id and self._can_lookup_parent_step():
            parent_step_id = self._lookup_parent_step_from_agent(tool_info)

        return parent_step_id

    def _can_lookup_parent_step(self) -> bool:
        """Check if parent step lookup is possible.

        Returns:
            True if parent agent has the required mapping
        """
        return self.parent_agent is not None and hasattr(self.parent_agent, "_tool_parent_map_by_thread")

    def _lookup_parent_step_from_agent(self, tool_info: dict) -> str | None:
        """Lookup parent step ID from parent agent's mapping.

        Args:
            tool_info: Tool information containing tool call ID

        Returns:
            Parent step ID if found, None otherwise
        """
        try:
            thread_id = bla._THREAD_ID_CVAR.get()
            if not thread_id:
                return None

            parent_map = self.parent_agent._tool_parent_map_by_thread.get(thread_id, {})
            tool_call_id = tool_info.get("id") if tool_info else None

            if tool_call_id:
                return parent_map.get(str(tool_call_id))

        except Exception as e:
            logger.debug(f"Failed to look up parent step ID from parent agent: {e}")

        return None

    def _handle_missing_agent_name(self, metadata: dict) -> None:
        """Handle case where agent_name is missing from metadata.

        Args:
            metadata: Metadata dictionary to update
        """
        logger.warning("Delegation tool call missing 'agent_name'; skipping linkage")
        metadata["previous_step_ids"] = []
        metadata["agent_name_missing"] = True

    def _forward_tool_result_event(self, chunk: dict, writer: StreamWriter) -> None:
        """Forward tool result events with coordinator-style format using A2AEvent structure.

        Args:
            chunk: Streaming chunk containing tool result info
            writer: Stream writer to emit events
        """
        tool_info = chunk.get("tool_info", {})
        tool_names: list[str] = []

        primary_name = tool_info.get("name")
        if isinstance(primary_name, str) and primary_name:
            tool_names.append(primary_name)
        elif isinstance(tool_info.get("tool_calls"), list):
            tool_names.extend(
                call.get("name")
                for call in tool_info["tool_calls"]
                if isinstance(call, dict) and isinstance(call.get("name"), str)
            )

        tool_names = [name for name in tool_names if name] or ["unknown_tool"]

        # Preserve sub-agent metadata
        metadata = chunk.get("metadata") or {}

        # Link result to sub-agent start step_id only if agent_name present
        agent_name = metadata.get("agent_name")
        if agent_name:
            sub_start_map = _DELEGATION_SUB_START_STEP_CVAR.get() or {}
            start_step_id = sub_start_map.get(agent_name)
            metadata["previous_step_ids"] = [start_step_id] if start_step_id else []
        else:
            logger.warning("Delegation tool result missing 'agent_name'; skipping linkage")
            metadata["previous_step_ids"] = []
            metadata["agent_name_missing"] = True

        content = self._build_completion_content(tool_names)

        a2a_event: A2AEvent = {
            "event_type": A2AStreamEventType.TOOL_RESULT,
            "content": content,
            "metadata": metadata,
            "tool_info": tool_info,
            "is_final": False,
            "artifacts": chunk.get("artifacts"),
            MetadataFieldKeys.REFERENCES: chunk.get(MetadataFieldKeys.REFERENCES),
            STEP_USAGE_KEY: chunk.get(STEP_USAGE_KEY),
            TOTAL_USAGE_KEY: chunk.get(TOTAL_USAGE_KEY),
        }
        writer(a2a_event)

    def _build_completion_content(self, tool_names: list[str]) -> str:
        """Create completion message consistent with coordinator formatting.

        Args:
            tool_names: List of tool names that were executed.

        Returns:
            Formatted completion message string.
        """
        deduped_names = list(dict.fromkeys(name for name in tool_names if name))
        if not deduped_names:
            deduped_names = ["unknown_tool"]

        if self.parent_agent and hasattr(self.parent_agent, "_get_tool_completion_content"):
            try:
                return self.parent_agent._get_tool_completion_content(deduped_names)
            except Exception:  # pragma: no cover - defensive fallback
                logger.debug("DelegationToolManager: parent agent completion formatting failed", exc_info=True)

        has_delegation = any(name.startswith("delegate_to") for name in deduped_names)
        prefix = "Completed sub-agents:" if has_delegation else "Completed tools:"
        return f"{prefix} {', '.join(deduped_names)}"

    def _create_tool_call_message(self, tool_info: dict) -> str:
        """Create a consistent message for tool call events.

        Args:
            tool_info: Tool information from the chunk

        Returns:
            Formatted message string
        """
        tool_calls = tool_info.get("tool_calls", [])
        tool_names = [tc.get("name", "unknown") for tc in tool_calls]
        return f"Processing with tools: {', '.join(tool_names)}"

    def _format_final_chunk_sub_agent_output(self, final_result: dict | str | Any) -> dict[str, Any]:
        """Format the final chunk from a sub-agent result to match the .arun() output.

        Args:
            final_result: The result from agent execution

        Returns:
            A dictionary with keys:
            {
                "output": <output string>,
                "full_final_state": {
                    "artifacts": <artifacts>,
                    "references": <references>,
                    "metadata": <metadata>,
                    "total_usage": <total_usage>,
                }
            }

        Note:
        - To preserve pattern of .arun():
        - the output will be stored in "output" key and extras will be stored in "full_final_state" key
        - Those extras being: "artifacts", "references", "metadata", and "total_usage"
        """
        result: dict[str, Any] = {
            "output": "",
            "full_final_state": {
                "artifacts": [],
                MetadataFieldKeys.REFERENCES: [],
                "metadata": {},
                TOTAL_USAGE_KEY: {},
            },
        }

        if not isinstance(final_result, dict):
            result["output"] = str(final_result)
        else:
            result["output"] = final_result.get("content", str(final_result))
            result["full_final_state"] = {
                "artifacts": final_result.get("artifacts", []),
                MetadataFieldKeys.REFERENCES: final_result.get(MetadataFieldKeys.REFERENCES, []),
                "metadata": final_result.get("metadata", {}),
                TOTAL_USAGE_KEY: final_result.get(TOTAL_USAGE_KEY, {}),
            }

            # Propagate sub-agent final step id to coordinator via metadata.previous_step_ids
            try:
                metadata = final_result.get("metadata") or {}
                final_step_id = metadata.get("step_id")
                if final_step_id:
                    result["metadata"] = {"previous_step_ids": [final_step_id]}
            except Exception:
                # If metadata access fails, ensure we have a metadata key
                result["metadata"] = {}

        # Single return point
        return result
