"""Base executor class for LangChain-based A2A executors.

This module provides a common base class for executors that work with LangChain-based
agents, such as LangChainAgent and LangGraphAgent. It implements shared functionality
for handling streaming responses and managing agent execution.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
from abc import ABC
from typing import Any

from a2a.server.agent_execution import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message

from aip_agents.a2a.server.base_executor import BaseA2AExecutor, StatusUpdateParams
from aip_agents.agent.interfaces import LangGraphAgentProtocol
from aip_agents.schema.step_limit import StepLimitConfig
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class LangGraphA2AExecutor(BaseA2AExecutor, ABC):
    """Base class for LangChain-based A2A executors.

    This class extends BaseA2AExecutor to provide common functionality for executors
    that work with LangChain-based agents (LangChainAgent and LangGraphAgent).
    It implements shared methods for handling streaming responses and managing
    agent execution, while leaving agent-specific initialization to subclasses.

    Attributes:
        agent (LangGraphAgentProtocol): The LangChain-based agent instance to be executed.
    """

    agent: LangGraphAgentProtocol

    def __init__(self, langgraph_agent_instance: LangGraphAgentProtocol) -> None:
        """Initializes the LangGraphA2AExecutor.

        Args:
            langgraph_agent_instance: Component implementing `LangGraphAgentProtocol`.

        Raises:
            TypeError: If the provided agent does not satisfy `LangGraphAgentProtocol`.
        """
        super().__init__()

        if not isinstance(langgraph_agent_instance, LangGraphAgentProtocol):
            _type_name = type(langgraph_agent_instance).__name__
            raise TypeError(
                f"LangGraphA2AExecutor expected an agent implementing LangGraphAgentProtocol, got {_type_name}"
            )
        self.agent = langgraph_agent_instance

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Processes an incoming agent request using a LangChain-based agent.

        This method first performs initial checks using _handle_initial_execute_checks.
        If successful, it prepares the _process_stream coroutine and passes it to
        _execute_agent_processing from the base class to manage its lifecycle.
        The _process_stream method is responsible for calling the agent's
        arun_a2a_stream and handling its output.

        Args:
            context (RequestContext): The A2A request context containing message details,
                task ID, and context ID.
            event_queue (EventQueue): The queue for sending A2A events (task status,
                artifacts) back to the server.
        """
        updater, query, metadata = await self._handle_initial_execute_checks(context, event_queue)
        if not updater or query is None:  # Checks failed, status already sent
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

    def _get_configurable_kwargs(self, task_id: str) -> dict[str, Any]:
        """Get configurable kwargs for agent delegation.

        Args:
            task_id: The A2A task ID.

        Returns:
            dict[str, Any]: A dictionary with 'configurable' key if the agent
                            has 'thread_id_key', otherwise an empty dictionary.
        """
        if hasattr(self.agent, "thread_id_key"):
            return {"configurable": {self.agent.thread_id_key: task_id}}
        return {}

    def _build_agent_kwargs(
        self,
        task_id: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build kwargs for agent stream execution from task and metadata.

        Args:
            task_id: The A2A task ID for configurable threading settings.
            metadata: Optional request metadata, including files and overrides.

        Returns:
            dict[str, Any]: Keyword arguments to pass to the agent's stream method.
        """
        kwargs = self._get_configurable_kwargs(task_id)

        files: list[str | dict[str, Any]] = self._extract_files_from_metadata(metadata)
        if metadata is not None:
            kwargs["metadata"] = metadata
            if isinstance(metadata, dict):
                raw_user_id = metadata.get("memory_user_id") or metadata.get("user_id")
                if raw_user_id:
                    kwargs["memory_user_id"] = str(raw_user_id)

                raw_pii_mapping = metadata.get("pii_mapping")
                if isinstance(raw_pii_mapping, dict) and raw_pii_mapping:
                    kwargs["pii_mapping"] = dict(raw_pii_mapping)

                # Extract invocation-level step limit overrides (Docs-1)
                raw_step_limit_config = metadata.get("step_limit_config")
                if isinstance(raw_step_limit_config, dict | StepLimitConfig):
                    kwargs["step_limit_config"] = raw_step_limit_config
        if files:
            kwargs["files"] = files

        return kwargs

    async def _process_stream(  # noqa: PLR0913
        self,
        query: str,
        updater: TaskUpdater,
        task_id: str,
        context_id: str,
        event_queue: EventQueue,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Processes the streaming response from a LangChain-based agent.

        This coroutine invokes the agent.arun_a2a_stream method with the given query and metadata.
        It then iterates over the asynchronous stream of dictionary chunks yielded by
        the agent. Each chunk is passed to _handle_stream_event from the base class
        to interpret common A2A statuses (working, completed, failed, etc.) and update
        the A2A task accordingly.

        If asyncio.CancelledError is raised (typically from the task managed by
        _execute_agent_processing), it is re-raised to be handled by the base class.
        Other exceptions during streaming are caught, logged, an A2A 'failed' status
        is sent, and the exception is re-raised.

        Args:
            query (str): The query string to be processed by the agent.
            updater (TaskUpdater): The TaskUpdater instance for sending status updates.
            task_id (str): The A2A task ID.
            context_id (str): The A2A context ID.
            event_queue (EventQueue): The A2A event queue for sending artifact events.
            metadata (dict[str, Any] | None): Optional metadata from the A2A request.

        Raises:
            asyncio.CancelledError: If the task is cancelled externally.
            Exception: If any other error occurs during the agent's stream processing.
        """
        stream = None
        try:
            kwargs = self._build_agent_kwargs(task_id=task_id, metadata=metadata)

            stream = self.agent.arun_a2a_stream(query=query, **kwargs)

            current_metadata: dict[str, Any] = metadata.copy() if metadata else {}

            async for chunk in stream:
                chunk_metadata = chunk.get("metadata")
                if chunk_metadata is not None:
                    try:
                        current_metadata.update(chunk_metadata)
                    except Exception as e:
                        logger.warning(f"Invalid metadata payload from chunk: {chunk_metadata}, error: {e}")

                should_terminate = await self._handle_stream_event(
                    chunk=chunk,
                    updater=updater,
                    task_id=task_id,
                    context_id=context_id,
                    event_queue=event_queue,
                    metadata=current_metadata if current_metadata else None,
                )
                if should_terminate:
                    return

        except asyncio.CancelledError:
            logger.info(f"LangChain stream processing for task {task_id} was cancelled.")
            raise
        except Exception as e:
            logger.error(
                f"Error during LangChain agent streaming for task {task_id}: {e}",
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

    @staticmethod
    def _extract_files_from_metadata(metadata: dict[str, Any] | None) -> list[str | dict[str, Any]]:
        """Extract file paths from metadata, removing them since they are passed via kwargs.

        Args:
            metadata: Metadata dict from the request, potentially containing files.

        Returns:
            List of non-empty file path strings or file metadata dictionaries.
        """
        if not isinstance(metadata, dict):
            return []

        try:
            raw_files = metadata.pop("files", None)
        except AttributeError:
            return []
        if raw_files is None:
            return []

        if not isinstance(raw_files, list):
            logger.warning("Invalid 'files' metadata received; expected list of strings or dicts.")
            return []

        normalized_files: list[str | dict[str, Any]] = []
        invalid_entry_logged = False
        for entry in raw_files:
            if isinstance(entry, str) and entry:
                normalized_files.append(entry)
                continue
            if isinstance(entry, dict):
                normalized_files.append(entry)
                continue
            if not invalid_entry_logged:
                logger.warning("Invalid file metadata entry received; expected string or dict.")
                invalid_entry_logged = True

        return normalized_files
