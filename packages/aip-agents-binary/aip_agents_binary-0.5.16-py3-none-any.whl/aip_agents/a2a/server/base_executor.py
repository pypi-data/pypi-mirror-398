"""Defines the base abstract class for A2A server-side executors.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from a2a.server.agent_execution import AgentExecutor as A2ASDKExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithBytes,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils import get_text_parts, new_agent_text_message, new_text_artifact
from a2a.utils.artifact import new_artifact

from aip_agents.types import A2AEvent, A2AStreamEventType
from aip_agents.utils import serialize_references_for_metadata
from aip_agents.utils.artifact_helpers import ArtifactHandler
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata_helper import MetadataFieldKeys

logger = get_logger(__name__)


@dataclass
class StatusUpdateParams:
    """Parameters for status updates."""

    metadata: dict[str, Any] | None = None
    final: bool = False
    task_id: str | None = None
    context_id: str | None = None


class BaseA2AExecutor(A2ASDKExecutor, ABC):
    """Abstract base class for GLLM Agent framework's A2A server-side executors.

    This class extends the A2A SDK's `AgentExecutor`. It serves as a common
    foundation for specific executors tailored to different agent types within the
    `aip-agents` framework, such as `LangGraphA2AExecutor` or
    `GoogleADKA2AExecutor`.

    Subclasses are required to implement the `execute` method to handle A2A
    requests. The `cancel` method has a common implementation.

    Attributes:
        _active_tasks (dict[str, asyncio.Task]): A dictionary mapping task IDs to
            their corresponding asyncio.Task instances for active agent executions.
    """

    def __init__(self) -> None:
        """Initializes the BaseA2AExecutor."""
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._processed_artifacts: dict[str, set[str]] = {}  # task_id -> set of artifact hashes
        self._streaming_artifacts: dict[str, bool] = {}  # task_id -> has_streaming_content
        self._streaming_artifact_ids: dict[str, str] = {}  # task_id -> artifact_id for consistent streaming
        # Track cumulative time per task (monotonic seconds) for metadata.time
        self._task_start_times: dict[str, float] = {}

    def _remove_active_task(self, task_id: str) -> None:
        """Removes an active task from the internal tracking dictionary.

        Args:
            task_id (str): The ID of the task to remove.
        """
        if task_id in self._active_tasks:
            self._active_tasks.pop(task_id)
        # Clean up processed artifacts for this task
        if task_id in self._processed_artifacts:
            self._processed_artifacts.pop(task_id)
        # Clean up streaming artifacts tracking
        if task_id in self._streaming_artifacts:
            self._streaming_artifacts.pop(task_id)
        # Clean up streaming artifact IDs
        if task_id in self._streaming_artifact_ids:
            self._streaming_artifact_ids.pop(task_id)
        # Clean up task start time tracking
        if task_id in self._task_start_times:
            self._task_start_times.pop(task_id)

    def _apply_cumulative_time(self, task_id: str, metadata: dict[str, Any] | None) -> None:
        """Ensure metadata.time is cumulative since first status event for the task.

        Args:
            task_id: The A2A task ID.
            metadata: The metadata dict to mutate.
        """
        if metadata is None:
            return
        now = time.monotonic()
        start = self._task_start_times.get(task_id)
        if start is None:
            self._task_start_times[task_id] = now
            elapsed = 0.0
        else:
            elapsed = max(0.0, now - start)
        # Always use string keys in metadata to ensure JSON-serializable output
        metadata[MetadataFieldKeys.TIME] = elapsed

    async def _handle_initial_execute_checks(
        self, context: RequestContext, event_queue: EventQueue
    ) -> tuple[TaskUpdater | None, str | None, dict[str, Any] | None]:
        """Performs initial validation and setup for an incoming agent request.

        This method checks for the presence of message content, extracts the query and metadata,
        and initializes the task status with the A2A server.

        Args:
            context (RequestContext): The A2A request context, containing message
                details and task information.
            event_queue (EventQueue): The queue for sending task status updates back
                to the A2A server.

        Returns:
            tuple[TaskUpdater | None, str | None, dict[str, typing.Any] | None]: A tuple containing a `TaskUpdater`
            instance, the extracted query string, and extracted metadata dictionary if initial checks pass. If checks
            fail (e.g., no message content), it returns (None, None, None) and will have
            already sent a failure status through the updater.
        """
        if not context.message or not context.message.parts:
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.failed(message=new_agent_text_message("No message content provided."))
            return None, None, None

        query_parts = get_text_parts(context.message.parts)
        query = "\n".join(query_parts)

        if not query:
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.failed(message=new_agent_text_message("Extracted query is empty."))
            return None, None, None

        # Extract metadata from both message and request params
        metadata = self._extract_metadata(context)

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()
        return updater, query, metadata

    def _extract_metadata(self, context: RequestContext) -> dict[str, Any]:
        """Extracts metadata from the request context.

        This method combines metadata from both the message and the request parameters
        to provide a comprehensive metadata dictionary for the agent.

        Args:
            context (RequestContext): The A2A request context containing message and params.

        Returns:
            dict[str, Any]: A dictionary containing all available metadata.
        """
        metadata = {}

        if context._params and context._params.metadata:
            metadata.update(context._params.metadata)

        logger.debug(f"Final extracted metadata: {metadata}")
        return metadata

    async def _update_status(
        self,
        updater: TaskUpdater,
        state: TaskState,
        message: Message,
        params: StatusUpdateParams | None = None,
    ) -> None:
        """Update task status with metadata placed in TaskStatusUpdateEvent according to A2A spec.

        This method creates a TaskStatusUpdateEvent with metadata in the correct location
        (the event's metadata field) rather than in the message metadata field.

        Args:
            updater (TaskUpdater): The TaskUpdater instance for sending status updates.
            state (TaskState): The new task state.
            message (Message): The message associated with the status update.
            params (StatusUpdateParams | None): Parameters for the status update.
        """
        current_timestamp = datetime.now(UTC).isoformat()

        # Use defaults if params not provided
        if params is None:
            params = StatusUpdateParams()

        # Use provided task_id and context_id, or extract from message/updater
        task_id = params.task_id
        if task_id is None:
            task_id = message.taskId
        context_id = params.context_id
        if context_id is None:
            context_id = message.contextId

        # Ensure we have valid IDs
        if task_id is None or context_id is None:
            raise ValueError("task_id and context_id must be provided or available in the message")

        # Ensure metadata exists and apply cumulative time for this task
        metadata = params.metadata or {}
        try:
            self._apply_cumulative_time(task_id, metadata)
        except Exception as e:
            logger.warning(f"Failed to apply cumulative time for task {task_id}: {e}")

        event = TaskStatusUpdateEvent(
            taskId=task_id,
            contextId=context_id,
            final=params.final,
            status=TaskStatus(
                state=state,
                message=message,
                timestamp=current_timestamp,
            ),
            metadata=metadata,
        )

        # Use status-specific enqueue to ensure servers treat it as a status event
        try:
            await updater.event_queue.enqueue_status(event)
        except AttributeError:
            # Fallback for older SDKs without enqueue_status
            await updater.event_queue.enqueue_event(event)

    async def _execute_agent_processing(
        self,
        agent_processing_coro: Awaitable[None],
        updater: TaskUpdater,
        task_id: str,
        context_id: str | None = None,
    ) -> None:
        """Manages the execution lifecycle of an agent processing coroutine.

        This method creates an asyncio task for the provided agent processing
        coroutine, stores it for potential cancellation, and awaits its completion.
        It handles `asyncio.CancelledError` to update task status to cancelled
        and logs other exceptions, marking the task as failed.

        Args:
            agent_processing_coro (typing.Awaitable[None]): The coroutine that
                performs the agent-specific processing (e.g., streaming results).
            updater (TaskUpdater): The TaskUpdater instance for sending status updates.
            task_id (str): The unique ID of the A2A task.
            context_id (str | None): The context ID. Defaults to None.
        """
        task = asyncio.create_task(agent_processing_coro)
        self._active_tasks[task_id] = task

        try:
            await task
        except asyncio.CancelledError:
            # This specific CancelledError is raised if the task created from
            # agent_processing_coro is cancelled externally (e.g., by the cancel method).
            logger.info(f"Agent processing task {task_id} was cancelled by client request.")
            await self._update_status(
                updater,
                TaskState.canceled,
                new_agent_text_message("Task was cancelled by client."),
                params=StatusUpdateParams(task_id=task_id, context_id=context_id),
            )
            raise
        except Exception as e:
            self._remove_active_task(task_id)
            logger.error(f"Error during agent execution for task {task_id}: {e}", exc_info=True)
            await self._update_status(
                updater,
                TaskState.failed,
                new_agent_text_message(f"Error during execution: {str(e)}"),
                params=StatusUpdateParams(final=True, task_id=task_id, context_id=context_id),
            )
        finally:
            self._remove_active_task(task_id)

    async def _handle_artifact_event(
        self,
        payload: dict[str, Any],
        updater: TaskUpdater,
        task_id: str | None = None,
    ) -> bool:
        """Handles an artifact event from the agent stream.

        Args:
            payload (dict[str, typing.Any]): The artifact payload containing data, name, etc.
            updater (TaskUpdater): The TaskUpdater instance for sending artifact updates.
            task_id (str | None): The task ID for deduplication tracking.

        Returns:
            bool: False to continue stream, True if there was an error that should stop processing.
        """
        try:
            # Validate and extract artifact data
            artifact_data_b64 = payload.get("data")
            if not artifact_data_b64:
                logger.warning("Artifact payload missing 'data' field")
                return False

            # Check for duplicates
            if task_id and self._is_duplicate_artifact(payload, task_id):
                return False

            # Create A2A-compliant artifact
            artifact_to_send = self._create_a2a_artifact(payload)
            if not artifact_to_send:
                return False

            # Merge payload metadata (if any) and apply cumulative time
            event_metadata: dict[str, Any] | None = None
            try:
                raw_md = payload.get("metadata") if isinstance(payload, dict) else None
                event_metadata = raw_md.copy() if isinstance(raw_md, dict) else {}
            except Exception as e:
                logger.warning(f"Failed to copy artifact metadata for task {task_id}: {e}")
                event_metadata = {}
            if task_id:
                try:
                    self._apply_cumulative_time(task_id, event_metadata)
                except Exception as e:
                    logger.warning(f"Failed to apply cumulative time to artifact metadata for task {task_id}: {e}")

            # Send artifact to client with metadata
            return await self._send_artifact_to_client(artifact_to_send, updater, metadata=event_metadata)

        except Exception as e:
            logger.error(f"Failed to process artifact payload: {e}", exc_info=True)
            return False

    def _is_duplicate_artifact(self, payload: dict[str, Any], task_id: str) -> bool:
        """Check if artifact is a duplicate and handle deduplication tracking.

        Args:
            payload: The artifact payload.
            task_id: The task ID for tracking.

        Returns:
            True if artifact is a duplicate, False otherwise.
        """
        artifact_hash = ArtifactHandler.generate_artifact_hash(
            payload.get("data", ""),
            payload.get("name", ""),
            payload.get("mime_type", ""),
        )

        if task_id not in self._processed_artifacts:
            self._processed_artifacts[task_id] = set()

        if artifact_hash in self._processed_artifacts[task_id]:
            logger.warning(
                f"Skipping duplicate artifact: {payload.get('name', 'unnamed')} (hash: {artifact_hash[:8]}...)"
            )
            return True

        self._processed_artifacts[task_id].add(artifact_hash)
        logger.info(f"Processing new artifact: {payload.get('name', 'unnamed')} (hash: {artifact_hash[:8]}...)")
        return False

    def _create_a2a_artifact(self, payload: dict[str, Any]) -> Any | None:
        """Create A2A-compliant artifact from payload with flexible part type support.

        Args:
            payload: The artifact payload.

        Returns:
            A2A artifact object or None if creation failed.
        """
        try:
            # Determine the appropriate part type based on payload content
            part = self._create_artifact_part(payload)
            if not part:
                return None

            artifact_to_send = new_artifact(
                parts=[Part(root=part)],
                name=payload.get("name", "Generated Artifact"),
                description=payload.get("description", ""),
            )
            return artifact_to_send

        except Exception as artifact_error:
            logger.error(f"Failed to create artifact: {artifact_error}")
            return None

    def _create_artifact_part(self, payload: dict[str, Any]) -> Any | None:
        """Create the appropriate part type based on payload content.

        Args:
            payload: The artifact payload.

        Returns:
            A Part object (TextPart, FilePart, etc.) or None if creation failed.
        """
        try:
            # Check if this is text content (common for streaming responses)
            if "text" in payload or ("mime_type" in payload and payload["mime_type"].startswith("text/")):
                return TextPart(
                    kind="text",
                    text=payload.get("text", payload.get("data", "")),
                    metadata=payload.get("metadata"),
                )

            # Check if this has binary data (files, images, etc.)
            elif "data" in payload:
                return FilePart(
                    kind="file",
                    file=FileWithBytes(
                        bytes=payload.get("data"),
                        name=payload.get("name", "artifact"),
                        mimeType=payload.get("mime_type", "application/octet-stream"),
                    ),
                    metadata=payload.get("metadata"),
                )

            # Fallback to text part for any other content
            else:
                content = str(payload.get("content", payload.get("data", "")))
                return TextPart(
                    kind="text",
                    text=content,
                    metadata=payload.get("metadata"),
                )

        except Exception as part_error:
            logger.error(f"Failed to create artifact part: {part_error}")
            return None

    async def _send_artifact_to_client(
        self,
        artifact: Any,
        updater: TaskUpdater,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send artifact to client as a TaskArtifactUpdateEvent with event metadata.

        Args:
            artifact: The A2A artifact to send.
            updater: The TaskUpdater instance used to enqueue artifact events.
            metadata: Optional event-level metadata to include with the update
                (e.g., cumulative time, tracing fields). This is attached to the
                TaskArtifactUpdateEvent so clients receive it on the event envelope.

        Returns:
            False to continue stream on success, True if there was an error.
        """
        try:
            event = TaskArtifactUpdateEvent(
                taskId=updater.task_id,
                contextId=updater.context_id,
                artifact=artifact,
                append=None,
                lastChunk=None,
                metadata=metadata,
            )
            await updater.event_queue.enqueue_event(event)
            logger.info(f"Successfully sent artifact '{artifact.name}' to client")
            return False  # Continue stream

        except Exception as send_error:
            logger.error(f"Failed to send artifact to client: {send_error}")
            return True  # Error occurred, stop processing

    async def _send_content_as_artifact(  # noqa: PLR0913
        self,
        content: str,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        append: bool = True,
        last_chunk: bool = False,
        artifact_name: str = "streaming_response",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send content as a streaming artifact update event.

        This method creates and sends a TaskArtifactUpdateEvent for content delivery,
        which is the correct way to stream content according to A2A protocol.

        Args:
            content (str): The content to send as an artifact.
            event_queue (EventQueue): The event queue for sending the artifact event.
            task_id (str): The task ID.
            context_id (str): The context ID.
            append (bool): Whether this content should be appended to previous chunks.
                Defaults to True for streaming content.
            last_chunk (bool): Whether this is the final chunk. Defaults to False.
            artifact_name (str): Name for the artifact. Defaults to "streaming_response".
            metadata (dict[str, Any] | None): Optional metadata to include with the artifact.
        """
        try:
            # Get or create consistent artifact ID for this streaming task
            if task_id not in self._streaming_artifact_ids:
                # Create new artifact and store its ID
                artifact_payload = new_text_artifact(
                    name=artifact_name,
                    description="Streaming response from the agent.",
                    text=content,
                )
                self._streaming_artifact_ids[task_id] = artifact_payload.artifactId
            else:
                # Reuse existing artifact ID for consistency
                artifact_payload = new_text_artifact(
                    name=artifact_name,
                    description="Streaming response from the agent.",
                    text=content,
                )
                # Override the auto-generated ID with our consistent one
                artifact_payload.artifactId = self._streaming_artifact_ids[task_id]

            artifact_event = TaskArtifactUpdateEvent(
                append=append,
                contextId=context_id,
                taskId=task_id,
                lastChunk=last_chunk,
                artifact=artifact_payload,
                metadata=metadata,
            )

            await event_queue.enqueue_event(artifact_event)
            logger.debug(f"Sent content as artifact: {artifact_name} (append={append}, lastChunk={last_chunk})")

        except Exception as e:
            logger.error(f"Failed to send content as artifact: {e}", exc_info=True)

    async def _handle_stream_event(  # noqa: PLR0913, PLR0911 TODO: Refactor this
        self,
        chunk: A2AEvent,
        updater: TaskUpdater,
        task_id: str,
        context_id: str,
        event_queue: EventQueue,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Handle semantically typed A2A events with type-based dispatching.

        This method processes A2AEvent objects using their semantic event types,
        eliminating the need for string parsing and JSON decoding. Each event type
        is handled by a dedicated method for better maintainability.

        Args:
            chunk: The A2AEvent to process with semantic type information.
            updater: TaskUpdater instance for sending A2A status updates.
            task_id: Unique identifier for the A2A task.
            context_id: Context identifier for the A2A session.
            event_queue: Event queue for sending artifact update events.
            metadata: Optional metadata to merge with chunk metadata.

        Returns:
            bool: True if stream processing should terminate, False to continue.
        """
        event_type = chunk.get("event_type")

        # Convert string event type to Enum if possible to match handler_map keys
        if isinstance(event_type, str):
            try:
                event_type = A2AStreamEventType(event_type)
            except ValueError:
                # Keep as string if not a valid enum member (will likely fall through to unknown)
                event_type = chunk.get("event_type")

        # Prepare metadata and handle artifacts
        final_metadata = self._prepare_event_metadata(chunk, metadata)
        self._apply_cumulative_time(task_id, final_metadata)
        await self._process_event_artifacts(chunk, updater, task_id)

        # Dispatch to appropriate handler based on event type
        handler_map: dict[Any, Callable[[], Awaitable[bool]]] = {
            A2AStreamEventType.TOOL_CALL: lambda: self._handle_tool_call_event(
                chunk, updater, task_id, context_id, metadata
            ),
            A2AStreamEventType.TOOL_RESULT: lambda: self._handle_tool_result_event(
                chunk, updater, task_id, context_id, metadata
            ),
            A2AStreamEventType.CONTENT_CHUNK: lambda: self._handle_content_chunk_event(
                chunk, event_queue, task_id, context_id, final_metadata
            ),
            A2AStreamEventType.FINAL_RESPONSE: lambda: self._handle_final_response_event(
                chunk, updater, event_queue, task_id, context_id, final_metadata
            ),
            A2AStreamEventType.STATUS_UPDATE: lambda: self._handle_status_update_event(
                chunk, updater, task_id, context_id
            ),
            A2AStreamEventType.STEP_LIMIT_EXCEEDED: lambda: self._handle_step_limit_exceeded_event(
                chunk, updater, task_id, context_id
            ),
            A2AStreamEventType.ERROR: lambda: self._handle_error_event(chunk, updater, task_id, context_id),
        }

        handler = handler_map.get(event_type)
        if handler:
            return await handler()

        logger.warning(f"Unknown event type: {event_type}")
        return False

    def _prepare_event_metadata(self, chunk: A2AEvent, metadata: dict[str, Any] | None) -> dict[str, Any]:
        """Prepare final metadata by merging chunk and provided metadata.

        Args:
            chunk: A2AEvent containing chunk metadata.
            metadata: Optional additional metadata to merge.

        Returns:
            dict[str, Any]: Merged metadata dictionary.
        """
        final_metadata = {}
        if metadata:
            final_metadata.update(metadata)

        chunk_metadata = chunk.get("metadata", {})
        if chunk_metadata:
            final_metadata.update(chunk_metadata)

        if chunk.get(MetadataFieldKeys.REFERENCES):
            final_metadata[MetadataFieldKeys.REFERENCES] = serialize_references_for_metadata(
                chunk[MetadataFieldKeys.REFERENCES]
            )

        event_type_value = chunk.get("event_type")
        if isinstance(event_type_value, A2AStreamEventType):
            final_metadata["event_type"] = event_type_value.value
        elif isinstance(event_type_value, str):
            final_metadata["event_type"] = event_type_value

        # Merge selected top-level fields from chunk into metadata using string keys
        metadata_fields = [
            MetadataFieldKeys.TOOL_INFO,
            MetadataFieldKeys.STEP_USAGE,
            MetadataFieldKeys.TOTAL_USAGE,
            MetadataFieldKeys.THINKING_AND_ACTIVITY_INFO,
        ]

        for key in metadata_fields:
            value = chunk.get(key)
            if value is not None and value:  # Only overwrite if value is truthy
                final_metadata[key] = value

        return final_metadata

    async def _process_event_artifacts(self, chunk: A2AEvent, updater: TaskUpdater, task_id: str) -> None:
        """Process any artifacts attached to the event.

        Args:
            chunk: A2AEvent that may contain artifacts.
            updater: TaskUpdater for handling artifact events.
            task_id: Task identifier for artifact processing.
        """
        if "artifacts" in chunk and chunk["artifacts"]:
            for artifact_data in chunk["artifacts"]:
                await self._handle_artifact_event(artifact_data, updater, task_id)

    async def _handle_tool_call_event(
        self,
        chunk: A2AEvent,
        updater: TaskUpdater,
        task_id: str,
        context_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Handle TOOL_CALL event by sending appropriate status update.

        Args:
            chunk: A2AEvent with TOOL_CALL type and tool information.
            updater: TaskUpdater for sending status updates.
            task_id: Task identifier.
            context_id: Context identifier.
            metadata: Optional metadata to include with the status update.

        Returns:
            bool: False to continue stream processing.
        """
        status_message = chunk["content"]
        final_metadata = self._prepare_event_metadata(chunk, metadata)
        message = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=status_message))],
            messageId=str(uuid.uuid4()),
            taskId=task_id,
            contextId=context_id,
        )

        await self._update_status(
            updater,
            TaskState.working,
            message,
            StatusUpdateParams(metadata=final_metadata, task_id=task_id, context_id=context_id),
        )
        return False

    async def _handle_tool_result_event(
        self,
        chunk: A2AEvent,
        updater: TaskUpdater,
        task_id: str,
        context_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Handle TOOL_RESULT event by sending completion status update.

        Args:
            chunk: A2AEvent with TOOL_RESULT type and execution details.
            updater: TaskUpdater for sending status updates.
            task_id: Task identifier.
            context_id: Context identifier.
            metadata: Optional metadata to include with the status update.

        Returns:
            bool: False to continue stream processing.
        """
        status_message = self._extract_tool_result_status_message(chunk)
        final_metadata = self._prepare_event_metadata(chunk, metadata)
        message = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=status_message))],
            messageId=str(uuid.uuid4()),
            taskId=task_id,
            contextId=context_id,
        )

        await self._update_status(
            updater,
            TaskState.working,
            message,
            StatusUpdateParams(metadata=final_metadata, task_id=task_id, context_id=context_id),
        )
        return False

    async def _handle_content_chunk_event(
        self, chunk: A2AEvent, event_queue: EventQueue, task_id: str, context_id: str, final_metadata: dict[str, Any]
    ) -> bool:
        """Handle CONTENT_CHUNK event by streaming content as artifact.

        Args:
            chunk: A2AEvent with CONTENT_CHUNK type and user content.
            event_queue: Event queue for artifact updates.
            task_id: Task identifier.
            context_id: Context identifier.
            final_metadata: Merged metadata for the artifact.

        Returns:
            bool: False to continue stream processing.
        """
        is_first_chunk = task_id not in self._streaming_artifacts
        self._apply_cumulative_time(task_id, final_metadata)
        await self._send_content_as_artifact(
            content=chunk["content"],
            event_queue=event_queue,
            task_id=task_id,
            context_id=context_id,
            append=not is_first_chunk,
            last_chunk=False,
            metadata=final_metadata,
        )
        self._streaming_artifacts[task_id] = True
        return False

    async def _handle_final_response_event(  # noqa: PLR0913
        self,
        chunk: A2AEvent,
        updater: TaskUpdater,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        final_metadata: dict[str, Any],
    ) -> bool:
        """Handle FINAL_RESPONSE event by sending final artifact and completing task.

        Args:
            chunk: A2AEvent with FINAL_RESPONSE type and final content.
            updater: TaskUpdater for task completion.
            event_queue: Event queue for artifact updates.
            task_id: Task identifier.
            context_id: Context identifier.
            final_metadata: Merged metadata for the artifact.

        Returns:
            bool: True to terminate stream processing.
        """
        content = chunk["content"]
        has_streaming_content = task_id in self._streaming_artifacts

        if content is not None:
            self._apply_cumulative_time(task_id, final_metadata)
            artifact_name = "final_response" if not has_streaming_content else "streaming_response"
            await self._send_content_as_artifact(
                content=content,
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                append=has_streaming_content,
                last_chunk=True,
                artifact_name=artifact_name,
                metadata=final_metadata,
            )

        # Complete the task via status enqueue to preserve metadata
        completion_message = "Task completed successfully."
        completion_metadata = final_metadata.copy()
        completion_metadata.pop(MetadataFieldKeys.TOOL_INFO, None)
        completion_metadata.pop(MetadataFieldKeys.THINKING_AND_ACTIVITY_INFO, None)
        await self._update_status(
            updater,
            TaskState.completed,
            new_agent_text_message(completion_message, context_id=context_id, task_id=task_id),
            params=StatusUpdateParams(metadata=completion_metadata, final=True, task_id=task_id, context_id=context_id),
        )
        return True

    async def _handle_status_update_event(
        self, chunk: A2AEvent, updater: TaskUpdater, task_id: str, context_id: str
    ) -> bool:
        """Handle STATUS_UPDATE event by sending generic status message.

        Args:
            chunk: A2AEvent with STATUS_UPDATE type.
            updater: TaskUpdater for sending status updates.
            task_id: Task identifier.
            context_id: Context identifier.

        Returns:
            bool: False to continue stream processing.
        """
        # Include metadata for status updates as well, so clients can trace step_ids
        final_metadata = self._prepare_event_metadata(chunk, None)
        message = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=chunk["content"]))],
            messageId=str(uuid.uuid4()),
            taskId=task_id,
            contextId=context_id,
        )
        await self._update_status(
            updater,
            TaskState.working,
            message,
            StatusUpdateParams(metadata=final_metadata, task_id=task_id, context_id=context_id),
        )
        return False

    async def _handle_error_event(self, chunk: A2AEvent, updater: TaskUpdater, task_id: str, context_id: str) -> bool:
        """Handle ERROR event by failing the task.

        Args:
            chunk: A2AEvent with ERROR type and error details.
            updater: TaskUpdater for task failure.
            task_id: Task identifier.
            context_id: Context identifier.

        Returns:
            bool: True to terminate stream processing.
        """
        await self._update_status(
            updater,
            TaskState.failed,
            new_agent_text_message(chunk["content"], context_id=context_id, task_id=task_id),
            params=StatusUpdateParams(final=True),
        )
        return True

    async def _handle_step_limit_exceeded_event(
        self, chunk: A2AEvent, updater: TaskUpdater, task_id: str, context_id: str
    ) -> bool:
        """Handle step limit exceeded events by failing the task with metadata.

        Args:
            chunk: A2AEvent payload describing the step limit exceed event,
                including content and optional metadata.
            updater: TaskUpdater used to emit status updates to the A2A server.
            task_id: Identifier of the task whose step limit was exceeded.
            context_id: Context identifier associated with the task.

        Returns:
            bool: True to terminate further stream processing for the task.
        """
        final_metadata = self._prepare_event_metadata(chunk, None)
        message_text = chunk.get("content") or "Agent exceeded the configured step limit."

        await self._update_status(
            updater,
            TaskState.failed,
            new_agent_text_message(message_text, context_id=context_id, task_id=task_id),
            params=StatusUpdateParams(final=True, metadata=final_metadata, task_id=task_id, context_id=context_id),
        )
        return True

    def _extract_tool_result_status_message(self, chunk: A2AEvent) -> str:
        """Extract status message for tool completion from A2AEvent.

        Args:
            chunk: A2AEvent with TOOL_RESULT type and execution details.

        Returns:
            str: Human-readable status message for tool completion.
        """
        content = chunk.get("content")
        if isinstance(content, str) and content.strip():
            return content

        tool_info = chunk.get(MetadataFieldKeys.TOOL_INFO)
        if tool_info and tool_info.get("name"):
            return f"Completed {tool_info['name']}"
        # Fall back to the generic completion message used when tasks end silently.
        return "Task completed successfully."

    @abstractmethod
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Processes an incoming agent request and manages its execution.

        Implementations should interact with the underlying agent (e.g., a LangGraph
        or Google ADK agent) based on the provided `context`. All communications
        regarding task status, artifacts, and completion must be sent through
        the `event_queue`.

        This method typically involves:
        1. Calling `_handle_initial_execute_checks` for validation and setup.
        2. Defining an agent-specific coroutine for processing (e.g., `_process_stream`).
        3. Calling `_execute_agent_processing` to manage the lifecycle of this coroutine.

        Args:
            context (RequestContext): The request context containing information about the incoming
                     message, task, and other relevant data.
            event_queue (EventQueue): The queue used to send events (e.g., task status updates,
                         artifacts) back to the A2A server infrastructure.
        """
        raise NotImplementedError("Concrete A2A executors must implement the 'execute' method.")

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handles a request to cancel an ongoing agent task.

        This method attempts to cancel an active asyncio.Task associated with the
        given `context.task_id`. It waits for a short period for the task to handle
        the cancellation gracefully. The `event_queue` is used to report the
        outcome of the cancellation attempt (e.g., success, error during cleanup).

        Args:
            context (RequestContext): The request context for the task to be cancelled,
                primarily used to get the `task_id` and `context_id`.
            event_queue (EventQueue): The queue for sending cancellation status events.
        """
        task_id = context.task_id
        task = self._active_tasks.get(task_id)
        updater = TaskUpdater(event_queue, task_id, context.context_id)

        cancelled_by_client = False
        handled = False
        cancelled_error: asyncio.CancelledError | None = None
        if task and not task.done():
            logger.info(f"Attempting to cancel task {task_id} due to client request.")
            task.cancel()
            cancelled_by_client = True
            cancelled_error, handled = await self._request_task_cancellation(task, task_id, context, updater)
            if handled:
                return

        self._remove_active_task(task_id)
        await self._emit_cancellation_status(context, updater, task, cancelled_by_client)

        if cancelled_error is not None:
            raise cancelled_error

    async def _request_task_cancellation(
        self,
        task: asyncio.Task,
        task_id: str,
        context: RequestContext,
        updater: TaskUpdater,
    ) -> tuple[asyncio.CancelledError | None, bool]:
        """Wait for a cancelled task to finish any cleanup.

        Args:
            task: The asyncio.Task that was cancelled.
            task_id: The ID of the task being cancelled.
            context: The RequestContext for the cancellation request.
            updater: The TaskUpdater for sending status updates.

        Returns:
            A tuple containing:
            - The asyncio.CancelledError if the task surfaced one while waiting.
            - A boolean indicating whether the caller should stop further processing
              because the helper already handled status updates and cleanup.
        """
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
            logger.info(f"Task {task_id} completed its execution or cleanup after cancellation request.")
            return None, False
        except asyncio.CancelledError as exc:
            logger.info(f"Task {task_id} was externally cancelled and finished its cancellation logic or timed out.")
            return exc, False
        except TimeoutError:
            logger.warning(
                f"Timeout waiting for task {task_id} to complete after cancellation request. "
                "It might still be running cleanup in the background or may not have handled cancellation properly."
            )
            return None, False
        except Exception as error:  # noqa: BLE001
            logger.error(
                f"Error encountered while waiting for cancelled task {task_id} to finish: {error}",
                exc_info=True,
            )
            await self._update_status(
                updater,
                TaskState.canceled,
                message=new_agent_text_message(
                    f"Task cancelled, but an error occurred during its cleanup: {str(error)}"
                ),
                params=StatusUpdateParams(task_id=task_id, context_id=context.context_id),
            )
            self._remove_active_task(task_id)
            return None, True

    async def _emit_cancellation_status(
        self,
        context: RequestContext,
        updater: TaskUpdater,
        task: asyncio.Task | None,
        cancelled_by_client: bool,
    ) -> None:
        """Emit the final cancellation status based on task state.

        Args:
            context: The RequestContext for the cancellation request.
            updater: The TaskUpdater for sending status updates.
            task: The asyncio.Task that was cancelled, or None.
            cancelled_by_client: Whether the cancellation was requested by the client.
        """
        if cancelled_by_client:
            await self._update_status(
                updater,
                TaskState.canceled,
                message=new_agent_text_message("Task cancelled successfully by client request."),
                params=StatusUpdateParams(task_id=context.task_id, context_id=context.context_id),
            )
            return

        if task and task.cancelled():
            await self._update_status(
                updater,
                TaskState.canceled,
                message=new_agent_text_message("Task was found to be already cancelled."),
                params=StatusUpdateParams(task_id=context.task_id, context_id=context.context_id),
            )
            return

        if task and task.done() and not task.cancelled():
            logger.info(f"Task {context.task_id} was already done (completed/failed) when cancel was processed.")
            current_task = context.current_task
            if current_task and current_task.status not in (
                TaskState.completed,
                TaskState.failed,
                TaskState.canceled,
            ):
                await self._update_status(
                    updater,
                    TaskState.canceled,
                    message=new_agent_text_message("Task was already done but marked as cancelled per request."),
                    params=StatusUpdateParams(task_id=context.task_id, context_id=context.context_id),
                )
            return

        await self._update_status(
            updater,
            TaskState.canceled,
            message=new_agent_text_message(
                "Task cancellation processed; task was not actively running or already handled."
            ),
            params=StatusUpdateParams(task_id=context.task_id, context_id=context.context_id),
        )
