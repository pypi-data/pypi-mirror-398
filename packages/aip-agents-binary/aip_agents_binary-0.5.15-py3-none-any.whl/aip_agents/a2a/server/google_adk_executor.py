"""A2A server-side executor for Google ADK agent instances.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
from typing import Any

from a2a.server.agent_execution import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message

from aip_agents.a2a.server.base_executor import BaseA2AExecutor, StatusUpdateParams
from aip_agents.agent.google_adk_constants import DEFAULT_AUTH_URL
from aip_agents.agent.interfaces import GoogleADKAgentProtocol
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleADKExecutor(BaseA2AExecutor):
    """A2A Executor for serving a `GoogleADKAgent`.

    This executor bridges the A2A server protocol with a `aip_agents.agent.GoogleADKAgent`.
    It handles incoming requests by invoking the agent's `arun_a2a_stream` method,
    which is specifically designed to yield ADK events in an A2A-compatible dictionary
    format. This executor's `_process_stream` method is tailored to handle this stream,
    including ADK-specific statuses like "auth_required", before delegating common
    status handling to `BaseA2AExecutor._handle_stream_event`.

    It leverages common functionality from `BaseA2AExecutor` for task management,
    initial request checks, and cancellation.

    Attributes:
        agent (GoogleADKAgentProtocol): The instance of `GoogleADKAgent`-compatible class to execute.
    """

    agent: GoogleADKAgentProtocol

    def __init__(self, agent: GoogleADKAgentProtocol) -> None:
        """Initializes the GoogleADKExecutor.

        Args:
            agent: Component implementing `GoogleADKAgentProtocol`.

        Raises:
            TypeError: If the provided agent does not satisfy `GoogleADKAgentProtocol`.
        """
        super().__init__()

        if not isinstance(agent, GoogleADKAgentProtocol):
            raise TypeError(
                f"GoogleADKExecutor expected an agent implementing GoogleADKAgentProtocol, got {type(agent).__name__}"
            )
        self.agent = agent
        self._default_auth_url = DEFAULT_AUTH_URL

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Processes an incoming agent request using the `GoogleADKAgent`.

        This method first performs initial checks using `_handle_initial_execute_checks`
        from the base class. If successful, it prepares the `_process_stream` coroutine
        and passes it to `_execute_agent_processing` (also from the base class) to
        manage its execution lifecycle. The `_process_stream` method is responsible for
        calling the agent's `arun_a2a_stream` and handling its ADK-specific output.

        Args:
            context (RequestContext): The A2A request context containing message details,
                task ID, and context ID.
            event_queue (EventQueue): The queue for sending A2A events (task status,
                artifacts) back to the server.
        """
        updater, query, metadata = await self._handle_initial_execute_checks(context, event_queue)
        if not updater or query is None:  # Checks failed, status already sent by base method
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

    async def _process_stream(  # noqa: PLR0913
        self,
        query: str,
        updater: TaskUpdater,
        task_id: str,
        context_id: str,
        event_queue: EventQueue,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Processes the streaming response from the `GoogleADKAgent`.

        This coroutine invokes `self.agent.arun_a2a_stream`, which is designed to yield
        dictionary chunks adapting native Google ADK `Event` objects into an A2A-compatible
        format. This method specifically handles the "auth_required" status that can be
        yielded by the agent's stream. For all other statuses, it delegates to the
        `self._handle_stream_event` method from `BaseA2AExecutor` for common processing.

        The `GoogleADKAgent.arun_a2a_stream` and its helper methods are responsible for
        the ADK-specific event transformation. This executor's role here is to consume
        that adapted stream.

        If `asyncio.CancelledError` is raised (e.g., by the task managed by
        `_execute_agent_processing`), it is re-raised to be handled by the base class.
        Other exceptions during streaming are caught, logged, an A2A 'failed' status
        is sent, and the exception is re-raised.

        Args:
            query (str): The query string to be processed by the agent.
            updater (TaskUpdater): The `TaskUpdater` instance for sending status updates.
            task_id (str): The A2A task ID.
            context_id (str): The A2A context ID.
            event_queue (EventQueue): The A2A event queue, used by the base handler
                for sending artifact events.
            metadata (dict[str, Any] | None): Optional metadata from the A2A request.

        Raises:
            asyncio.CancelledError: If the task is cancelled externally.
            Exception: If any other error occurs during the agent's stream processing.
        """
        try:
            async for chunk in self.agent.arun_a2a_stream(
                query=query,
                configurable={"thread_id": task_id, "context_id": context_id},
            ):
                # Handle ADK-specific statuses first
                if chunk.get("status") == "auth_required":
                    auth_content = chunk.get("content", {})
                    auth_url = (
                        auth_content.get("auth_url", self._default_auth_url)
                        if isinstance(auth_content, dict)
                        else self._default_auth_url
                    )
                    auth_message = (
                        auth_content.get("message", "Authorization is required.")
                        if isinstance(auth_content, dict)
                        else "Authorization is required."
                    )
                    full_message = f"{auth_message} Visit {auth_url}"

                    await self._update_status(
                        updater,
                        TaskState.auth_required,
                        message=new_agent_text_message(full_message, context_id=context_id, task_id=task_id),
                        params=StatusUpdateParams(final=True, task_id=task_id, context_id=context_id),
                    )
                    return  # Terminate stream processing as auth is required

                # For other statuses, use the common handler from BaseA2AExecutor
                should_terminate = await self._handle_stream_event(
                    chunk=chunk,
                    updater=updater,
                    task_id=task_id,
                    context_id=context_id,
                    event_queue=event_queue,
                    metadata=metadata,
                )
                if should_terminate:
                    return

        except asyncio.CancelledError:
            logger.info(f"ADK Stream processing for task {task_id} was cancelled.")
            # Re-raise for _execute_agent_processing to handle and set A2A status
            raise
        except Exception as e:
            logger.error(
                f"Error during ADK agent streaming for task {task_id}: {e}",
                exc_info=True,
            )
            await self._update_status(
                updater,
                TaskState.failed,
                message=new_agent_text_message(
                    f"Error during streaming: {str(e)}",
                    context_id=context_id,
                    task_id=task_id,
                ),
                params=StatusUpdateParams(final=True, task_id=task_id, context_id=context_id),
            )
            raise
