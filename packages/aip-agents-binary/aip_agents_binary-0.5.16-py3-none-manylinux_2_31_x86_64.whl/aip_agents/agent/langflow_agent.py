"""Langflow agent implementation for integrating with Langflow API.

This module provides the LangflowAgent class that integrates with Langflow flows
through the SDK's agent framework, supporting both streaming and non-streaming
execution modes with full A2A compatibility.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from a2a.types import AgentCard

from aip_agents.agent.base_agent import BaseAgent
from aip_agents.clients.langflow import LangflowApiClient
from aip_agents.clients.langflow.types import LangflowEventType
from aip_agents.schema.agent import LangflowAgentConfig
from aip_agents.types import A2AEvent, A2AStreamEventType
from aip_agents.utils.logger import get_logger
from aip_agents.utils.sse_chunk_transformer import SSEChunkTransformer

logger = get_logger(__name__)


class LangflowAgent(BaseAgent):
    """Langflow agent implementation for executing Langflow flows.

    This agent integrates with Langflow APIs to execute flows while providing
    full compatibility with the SDK's agent framework, including:
    - Synchronous and asynchronous execution
    - Regular and A2A streaming support
    - Session management for conversation continuity
    - Error handling and retry logic
    - Credential management through BaseAgent

    The agent builds on BaseAgent to gain shared A2A utilities while focusing on
    Langflow-specific execution logic.
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        flow_id: str,
        description: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        config: LangflowAgentConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Initialize the LangflowAgent.

        Args:
            name: The name of the agent.
            flow_id: The unique identifier of the Langflow flow to execute.
            description: Human-readable description.
            base_url: The base URL of the Langflow API server.
            api_key: The API key for Langflow authentication.
            config: Langflow-specific configuration or dict.
            **kwargs: Additional keyword arguments passed to BaseAgent.
        """
        config = self._create_or_update_config(flow_id, base_url, api_key, config)

        super().__init__(
            name=name,
            instruction="",
            description=description,
            model=None,
            tools=None,
            config=config,
            **kwargs,
        )

        self.langflow_config = config
        self.flow_id = flow_id
        self.api_client = LangflowApiClient(
            flow_id=config.flow_id,
            base_url=config.base_url,
            api_key=config.api_key,
        )

        logger.info(f"Initialized LangflowAgent '{name}' for flow {self.flow_id}")

    def _create_or_update_config(
        self,
        flow_id: str,
        base_url: str | None,
        api_key: str | None,
        config: LangflowAgentConfig | dict[str, Any] | None,
    ) -> LangflowAgentConfig:
        """Create or update LangflowAgentConfig based on provided parameters.

        Args:
            flow_id: The unique identifier of the Langflow flow to execute.
            base_url: The base URL of the Langflow API server.
            api_key: The API key for Langflow authentication.
            config: Existing configuration to update or None to create new.

        Returns:
            LangflowAgentConfig instance with updated values.
        """
        if config is None:
            return LangflowAgentConfig(
                flow_id=flow_id,
                base_url=base_url,
                api_key=api_key,
            )
        elif isinstance(config, dict):
            config_dict = config.copy()
            config_dict.update(
                {
                    "flow_id": flow_id,
                    "base_url": base_url or config_dict.get("base_url"),
                    "api_key": api_key or config_dict.get("api_key"),
                }
            )
            return LangflowAgentConfig(**config_dict)
        elif isinstance(config, LangflowAgentConfig):
            if flow_id:
                config.flow_id = flow_id
            if base_url:
                config.base_url = base_url
            if api_key:
                config.api_key = api_key
            return config

        return LangflowAgentConfig(flow_id=flow_id, base_url=base_url, api_key=api_key)

    def _get_or_create_session(self, **kwargs: Any) -> str:
        """Get or create a session ID for the current conversation context.

        Args:
            **kwargs: Keyword arguments that may contain configurable with thread_id.

        Returns:
            Session ID for the conversation.
        """
        configurable = kwargs.get("configurable", {})
        thread_id = configurable.get("thread_id")

        if thread_id:
            logger.debug(f"Using thread_id as session_id: {thread_id}")
            return thread_id
        else:
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated new session_id: {session_id}")
            return session_id

    def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Synchronously run the Langflow agent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Returns:
            Dictionary containing the agent's response.
        """
        try:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    logger.warning(
                        f"Agent '{self.name}': Cannot use sync 'run' from within async context. Use 'arun' instead."
                    )
                    raise RuntimeError(f"Agent '{self.name}': sync 'run' cannot be called from within an async context")
            except RuntimeError:
                pass

            return asyncio.run(self.arun(query, **kwargs))
        except RuntimeError as e:
            raise RuntimeError(f"Agent '{self.name}': Error in sync 'run'. Original: {e}") from e

    async def arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Asynchronously run the Langflow agent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Returns:
            Dictionary containing the agent's response and metadata.
        """
        try:
            session_id = self._get_or_create_session(**kwargs)

            logger.debug(f"Agent '{self.name}': Executing flow {self.flow_id} with session {session_id}")

            result = await self.api_client.call_flow(input_value=query, session_id=session_id, **kwargs)

            return result["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        except Exception as e:
            logger.error(f"Agent '{self.name}': Error during execution: {e}")
            raise RuntimeError(f"Agent '{self.name}': Execution failed: {e}") from e

    async def arun_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[str | dict[str, Any], None]:
        """Asynchronously stream the Langflow agent's response.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            Chunks of output (strings or dicts) from the streaming response.
        """
        try:
            session_id = self._get_or_create_session(**kwargs)

            logger.debug(f"Agent '{self.name}': Streaming flow {self.flow_id} with session {session_id}")

            async for event_data in self.api_client.stream_flow(input_value=query, session_id=session_id, **kwargs):
                parsed_event = self.api_client.parse_stream_event(event_data)
                if parsed_event:
                    content = parsed_event.get("content", "")
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"Agent '{self.name}': Error during streaming: {e}")
            yield {"error": f"Streaming failed: {e}"}

    async def arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronously stream the agent's response in A2A format.

        This method converts Langflow streaming events into A2A-compatible events
        following the patterns established by BaseLangGraphAgent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            A2A-compatible event dictionaries with semantic event types.
        """
        try:
            session_id = self._get_or_create_session(**kwargs)
            logger.debug(f"Agent '{self.name}': A2A streaming flow {self.flow_id} with session {session_id}")

            # Yield initial status update
            yield self._create_initial_status_event(session_id)

            final_content = ""

            async for event_data in self.api_client.stream_flow(input_value=query, session_id=session_id, **kwargs):
                parsed_event = self.api_client.parse_stream_event(event_data)
                if not parsed_event:
                    continue

                event_type = parsed_event.get("type")
                content = parsed_event.get("content", "")

                if event_type == LangflowEventType.ADD_MESSAGE:
                    if content:
                        final_content = content

                elif event_type == LangflowEventType.END:
                    yield self._create_final_response_event(final_content, session_id)
                    return

                elif content:
                    yield self._create_a2a_event(
                        event_type=A2AStreamEventType.STATUS_UPDATE,
                        content=content,
                        is_final=False,
                        session_id=session_id,
                    )

            yield self._create_final_response_event(final_content, session_id)

        except Exception as e:
            logger.error(f"Agent '{self.name}': Error during A2A streaming: {e}")
            error_session_id = self._get_error_session_id(**kwargs)
            yield self._create_error_event(str(e), error_session_id)

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

    def _create_initial_status_event(self, session_id: str) -> A2AEvent:
        """Create the initial status update event for A2A streaming.

        Args:
            session_id: The session ID for the conversation.

        Returns:
            A2A event dictionary for initial status update.
        """
        return self._create_a2a_event(
            event_type=A2AStreamEventType.STATUS_UPDATE,
            content="Performing agent tasks",
            is_final=False,
            metadata={
                "agent_name": self.name,
                "step_id": "status_update_001",
                "previous_step_ids": [],
                "session_id": session_id,
            },
        )

    def _create_final_response_event(self, content: str, session_id: str) -> A2AEvent:
        """Create a final response event for A2A streaming.

        Args:
            content: The final response content.
            session_id: The session ID for the conversation.

        Returns:
            A2A event dictionary for final response.
        """
        return self._create_a2a_event(
            event_type=A2AStreamEventType.FINAL_RESPONSE,
            content=content,
            is_final=True,
            session_id=session_id,
        )

    def _get_error_session_id(self, **kwargs: Any) -> str | None:
        """Get session ID for error handling, with fallback to None if fails.

        Args:
            **kwargs: Keyword arguments that may contain configurable with thread_id.

        Returns:
            Session ID for error reporting, or None if unable to obtain.
        """
        try:
            return self._get_or_create_session(**kwargs)
        except Exception as e:
            logger.error(f"Agent '{self.name}': Error getting session_id: {e}")
            return None

    def _create_error_event(self, error_message: str, session_id: str | None) -> A2AEvent:
        """Create an error event for A2A streaming.

        Args:
            error_message: The error message to include.
            session_id: The session ID for the conversation, if available.

        Returns:
            A2A event dictionary for error reporting.
        """
        return self._create_a2a_event(
            event_type=A2AStreamEventType.ERROR,
            content=f"A2A streaming failed: {error_message}",
            is_final=True,
            session_id=session_id,
        )

    def _create_a2a_event(
        self,
        event_type: A2AStreamEventType,
        content: str,
        is_final: bool = False,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> A2AEvent:
        """Create an A2A-compatible event following BaseLangGraphAgent patterns.

        Args:
            event_type: The semantic type of the event.
            content: The main text content of the event.
            is_final: Whether this is a final event.
            metadata: Additional metadata for the event.
            session_id: Optional session ID to include in metadata.

        Returns:
            A2A event dictionary.
        """
        if metadata is None:
            metadata = {"agent_name": self.name, "step_id": f"langflow_{uuid.uuid4().hex[:8]}", "previous_step_ids": []}

        if session_id:
            metadata["session_id"] = session_id

        return {
            "event_type": event_type,
            "content": content,
            "metadata": metadata,
            "tool_info": None,
            "is_final": is_final,
            "artifacts": None,
            "references": None,
            "step_usage": None,
            "total_usage": None,
        }

    def register_a2a_agents(self, agents: list[AgentCard]) -> None:
        """Register A2A agents (not supported for Langflow agents).

        Args:
            agents: List of AgentCard instances.

        Raises:
            NotImplementedError: Langflow agents don't support A2A agent registration.
        """
        logger.warning(f"Agent '{self.name}': A2A agent registration not supported for Langflow agents")
        raise NotImplementedError("Langflow agents don't support A2A agent registration")

    def add_mcp_server(self, mcp_config: dict[str, dict[str, Any]]) -> None:
        """Add MCP server configuration (not supported for Langflow agents).

        Args:
            mcp_config: MCP server configuration.

        Raises:
            NotImplementedError: Langflow agents don't support MCP servers.
        """
        logger.warning(f"Agent '{self.name}': MCP server configuration not supported for Langflow agents")
        raise NotImplementedError("Langflow agents don't support MCP servers")

    async def health_check(self) -> bool:
        """Check if the Langflow API is accessible.

        Returns:
            True if the API is accessible, False otherwise.
        """
        try:
            return await self.api_client.health_check()
        except Exception as e:
            logger.warning(f"Agent '{self.name}': Health check failed: {e}")
            return False
