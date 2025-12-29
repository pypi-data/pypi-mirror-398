"""A2A executor for Langflow agents.

This module provides the LangflowA2AExecutor class that extends BaseA2AExecutor
to handle A2A requests for Langflow agents, similar to how LangGraphA2AExecutor
works for LangGraph agents.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import typing
from abc import ABC

from a2a.server.agent_execution import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message

from aip_agents.a2a.server.base_executor import BaseA2AExecutor, StatusUpdateParams
from aip_agents.agent.interfaces import LangflowAgentProtocol
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class LangflowA2AExecutor(BaseA2AExecutor, ABC):
    """A2A executor for Langflow agents.

    This class extends BaseA2AExecutor to provide A2A execution capabilities
    for Langflow agents. It follows the same patterns as LangGraphA2AExecutor
    but handles Langflow-specific streaming and execution logic.

    Attributes:
        agent: The LangflowAgent-compatible instance to be executed.
    """

    agent: LangflowAgentProtocol

    def __init__(self, langflow_agent_instance: LangflowAgentProtocol) -> None:
        """Initialize the LangflowA2AExecutor.

        Args:
            langflow_agent_instance: Component implementing `LangflowAgentProtocol`.

        Raises:
            TypeError: If the agent does not satisfy `LangflowAgentProtocol`.
        """
        super().__init__()

        if not isinstance(langflow_agent_instance, LangflowAgentProtocol):
            type_name = type(langflow_agent_instance).__name__
            raise TypeError(
                f"LangflowA2AExecutor expected an agent implementing LangflowAgentProtocol, got {type_name}"
            )

        self.agent = langflow_agent_instance
        logger.info(f"Initialized LangflowA2AExecutor for agent '{self.agent.name}'")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Process an incoming agent request using a Langflow agent.

        This method handles the execution lifecycle for Langflow agents:
        1. Performs initial validation and setup
        2. Creates agent processing coroutine
        3. Manages the execution lifecycle through BaseA2AExecutor

        Args:
            context: The A2A request context containing message details,
                task ID, and context ID.
            event_queue: The queue for sending A2A events back to the server.
        """
        updater, query, metadata = await self._handle_initial_execute_checks(context, event_queue)
        if not updater or query is None:
            return

        agent_processing_coro = self._process_stream(
            query=query,
            updater=updater,
            task_id=context.task_id,
            context_id=context.context_id,
            event_queue=event_queue,
            metadata=metadata,
        )

        await self._execute_agent_processing(
            agent_processing_coro=agent_processing_coro,
            updater=updater,
            task_id=context.task_id,
            context_id=context.context_id,
        )

    def _get_configurable_kwargs(self, task_id: str) -> dict[str, typing.Any]:
        """Get configurable kwargs for agent execution.

        For Langflow agents, we use thread_id for session management.

        Args:
            task_id: The A2A task ID to use as thread_id.

        Returns:
            Dictionary with configurable parameters for the agent.
        """
        return {"configurable": {"thread_id": task_id}}

    async def _process_stream(  # noqa: PLR0913
        self,
        query: str,
        updater: TaskUpdater,
        task_id: str,
        context_id: str,
        event_queue: EventQueue,
        metadata: dict[str, typing.Any] | None = None,
    ) -> None:
        """Process the streaming response from a Langflow agent.

        This method invokes the agent's arun_a2a_stream method and processes
        the A2A events it yields. It handles event routing through the base
        class's _handle_stream_event method.

        Args:
            query: The query string to be processed by the agent.
            updater: The TaskUpdater instance for sending status updates.
            task_id: The A2A task ID.
            context_id: The A2A context ID.
            event_queue: The A2A event queue for sending artifact events.
            metadata: Optional metadata from the A2A request.

        Raises:
            asyncio.CancelledError: If the task is cancelled externally.
            Exception: If any other error occurs during streaming.
        """
        try:
            kwargs = self._get_configurable_kwargs(task_id)
            if metadata:
                kwargs["metadata"] = metadata

            logger.debug(f"Starting Langflow agent stream for task {task_id}")

            current_metadata: dict[str, typing.Any] = metadata.copy() if metadata else {}

            async for chunk in self.agent.arun_a2a_stream(query=query, **kwargs):
                chunk_metadata = chunk.get("metadata")
                if chunk_metadata and isinstance(chunk_metadata, dict):
                    try:
                        current_metadata.update(chunk_metadata)
                    except Exception as e:
                        logger.warning(f"Invalid metadata in chunk: {chunk_metadata}, error: {e}")

                should_terminate = await self._handle_stream_event(
                    chunk=chunk,
                    updater=updater,
                    task_id=task_id,
                    context_id=context_id,
                    event_queue=event_queue,
                    metadata=current_metadata if current_metadata else None,
                )

                if should_terminate:
                    logger.debug(f"Stream terminated for task {task_id}")
                    return

        except Exception as e:
            logger.error(f"Error during Langflow agent streaming for task {task_id}: {e}", exc_info=True)

            await self._update_status(
                updater,
                TaskState.failed,
                message=new_agent_text_message(
                    f"Error during Langflow execution: {str(e)}",
                    context_id=context_id,
                    task_id=task_id,
                ),
                params=StatusUpdateParams(final=True, task_id=task_id, context_id=context_id),
            )
            raise
