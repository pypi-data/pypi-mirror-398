"""Provides A2A communication functionality through a connector class.

This module contains the A2AConnector class which handles all A2A protocol
communication between agents, including message sending and streaming. This version
ensures immediate yielding of artifact events to reduce latency and adhere
to the A2A protocol design.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import concurrent.futures
import hashlib
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)
from a2a.utils import get_text_parts
from pydantic import BaseModel

from aip_agents.schema.a2a import A2AStreamEventType
from aip_agents.utils.event_handler_registry import (
    DEFAULT_EVENT_HANDLER_REGISTRY,
    EventHandlerRegistry,
)
from aip_agents.utils.final_response_builder import FinalResponseMetadataOptions, assemble_final_response
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata_helper import (
    Kind,
    MetadataFieldKeys,
    MetadataTimeTracker,
    Status,
    create_metadata,
    create_status_update_metadata,
    create_tool_processing_metadata,
)
from aip_agents.utils.sse_chunk_transformer import SSEChunkTransformer

logger = get_logger(__name__)


class ArtifactInfo(BaseModel):
    """Structured artifact information for A2A communication.

    This Pydantic model provides type safety and validation for artifact data
    exchanged between agents through the A2A protocol.
    """

    artifact_id: str | None = None
    name: str | None = None
    content_type: str | None = None
    mime_type: str | None = None
    file_name: str | None = None
    has_file_data: bool = False
    has_file_uri: bool = False
    file_data: str | None = None
    file_uri: str | None = None
    description: str | None = None
    parts: int | None = None


class StreamingConfig(BaseModel):
    """Configuration for A2A streaming operations."""

    http_kwargs: dict[str, Any] | None = None


class A2AConnector:
    """Handles A2A protocol communication between agents.

    This class provides methods for sending messages to other agents using the A2A protocol,
    supporting both synchronous and asynchronous communication patterns, as well as streaming
    responses with immediate artifact event handling.
    """

    # Epsilon value for floating point comparisons to avoid precision issues
    FLOAT_EPSILON = 1e-10
    event_registry: EventHandlerRegistry = DEFAULT_EVENT_HANDLER_REGISTRY

    @staticmethod
    def _create_message_payload(
        message: str | dict[str, Any],
        task_id: str | None = None,
        context_id: str | None = None,
    ) -> dict[str, Any]:
        """Creates a standardized message payload for A2A communication.

        Args:
            message: The message content to send. Can be a string or dictionary.
            task_id: Task ID to associate with the message. Defaults to None.
            context_id: Context ID to associate with the message. Defaults to None.

        Returns:
            A dictionary containing the formatted message payload.
        """
        payload = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": message if isinstance(message, str) else json.dumps(message),
                    }
                ],
                "messageId": str(uuid.uuid4()),
            }
        }

        if task_id:
            payload["message"]["taskId"] = task_id
        if context_id:
            payload["message"]["contextId"] = context_id

        return payload

    @staticmethod
    def _create_a2a_client(
        agent_card: AgentCard, http_kwargs: dict[str, Any] | None = None
    ) -> tuple[httpx.AsyncClient, A2AClient]:
        """Creates an A2A client with the given configuration.

        Args:
            agent_card: The AgentCard instance containing agent details.
            http_kwargs: Optional HTTP client configuration. Defaults to None.

        Returns:
            A tuple containing the HTTP client and A2A client.
        """
        http_client = httpx.AsyncClient(**(http_kwargs or {}))
        a2a_client = A2AClient(httpx_client=http_client, agent_card=agent_card)
        return http_client, a2a_client

    @staticmethod
    def _extract_task_info(res_data: Task | Message) -> dict[str, Any]:
        """Extracts task information from response data.

        Args:
            res_data: Response data from A2A communication.

        Returns:
            Dictionary containing task information.
        """
        if isinstance(res_data, Task):
            return {
                "task_id": res_data.id,
                "task_state": str(res_data.status.state),
                "context_id": res_data.contextId,
            }
        return {
            "context_id": res_data.contextId,
            "task_id": res_data.taskId,
        }

    @staticmethod
    def _extract_text_content(res_data: Task | Message) -> list[str]:
        """Extracts text content from response data.

        Args:
            res_data: Response data from A2A communication.

        Returns:
            List of extracted text strings.
        """
        texts = []
        if isinstance(res_data, Task):
            if res_data.artifacts:
                for artifact in res_data.artifacts:
                    texts.extend(get_text_parts(artifact.parts))
            if not texts and res_data.status and res_data.status.message and res_data.status.message.parts:
                texts.extend(get_text_parts(res_data.status.message.parts))
        elif res_data.parts:
            texts.extend(get_text_parts(res_data.parts))
        return texts

    @staticmethod
    def _handle_task_state_update(
        event: TaskStatusUpdateEvent,
    ) -> dict[str, Any] | None:
        """Handles task status update events from A2A protocol.

        This method now focuses on status tracking and tool processing updates only.
        Final responses are handled by _handle_artifact_update_event with lastChunk=True.

        Args:
            event: The TaskStatusUpdateEvent from A2A protocol.

        Returns:
            Response dictionary if there's content to return, None otherwise.
        """
        if not event.status:
            return None

        # Check if this is a tool processing status update
        tool_detection = A2AConnector._detect_tool_processing_in_status(event)
        if tool_detection["is_tool_processing"]:
            return A2AConnector._create_tool_processing_response(event, tool_detection)
        if tool_detection.get("skip_status_update"):
            return None

        # Handle non-tool status updates (generic status messages)
        extracted_texts = A2AConnector._extract_status_message_texts(event)

        # Filter out generic completion confirmations
        if A2AConnector._should_filter_completion_message(event, extracted_texts):
            return None

        # Emit placeholder when there is no textual content
        if not extracted_texts:
            custom_metadata = A2AConnector._extract_custom_metadata_from_status_message(event)
            metadata = create_status_update_metadata("", custom_metadata)
            metadata = A2AConnector._merge_event_metadata(metadata, event)
            task_state = event.status.state.value if event.status and event.status.state else "working"
            return A2AConnector._create_empty_payload_response(
                event=event,
                metadata=metadata,
                default_event_type=A2AStreamEventType.STATUS_UPDATE,
                task_state=task_state,
            )

        return A2AConnector._create_status_response(event, extracted_texts)

    @staticmethod
    def _create_tool_processing_response(
        event: TaskStatusUpdateEvent, tool_detection: dict[str, Any]
    ) -> dict[str, Any]:
        """Create response for tool processing status updates.

        Args:
            event (TaskStatusUpdateEvent): The task status update event.
            tool_detection (dict[str, Any]): Dictionary containing tool detection information.

        Returns:
            dict[str, Any]: Response dictionary with status and content.
        """
        # Use the original event metadata to ensure tool_info is preserved
        original_metadata = event.metadata or {}
        metadata = create_tool_processing_metadata(original_metadata)
        metadata = A2AConnector._merge_event_metadata(metadata, event)

        content = tool_detection["status_message"]
        event_type = tool_detection.get("event_type", A2AStreamEventType.STATUS_UPDATE)
        event_type = A2AConnector._resolve_metadata_event_type(metadata, event_type)

        # HITL: Override content with human-readable tool output when applicable
        content = A2AConnector._apply_hitl_content_override(content, event_type, metadata)

        normalized_content = content.strip() if isinstance(content, str) else content
        if not normalized_content:
            task_state = event.status.state.value if event.status and event.status.state else "working"
            return A2AConnector._create_empty_payload_response(
                event=event,
                metadata=metadata,
                default_event_type=event_type,
                task_state=task_state,
            )

        response = {
            "status": "success",
            "task_state": "working",
            "content": content,
            "task_id": event.taskId,
            "context_id": event.contextId,
            "final": False,
            "timestamp": event.status.timestamp,
            "metadata": metadata,
            "event_type": event_type,
        }

        return response

    @staticmethod
    def _apply_hitl_content_override(content: str, event_type: A2AStreamEventType, metadata: dict[str, Any]) -> str:
        """Apply HITL content override when HITL is active and tool results are available.

        Delegates to SSEChunkTransformer.apply_hitl_content_override for shared implementation.

        Args:
            content: The original content/status message.
            event_type: The type of event being processed.
            metadata: The metadata dictionary containing tool_info and hitl flag.

        Returns:
            The original content or human-readable tool output if HITL is active.
        """
        # Convert event_type enum to string for shared method
        event_type_str = event_type.value if isinstance(event_type, A2AStreamEventType) else str(event_type)
        result = SSEChunkTransformer.apply_hitl_content_override(content, event_type_str, metadata)
        return result if result is not None else content

    @staticmethod
    def _extract_status_message_texts(event: TaskStatusUpdateEvent) -> list[str]:
        """Extract text content from status message.

        Args:
            event (TaskStatusUpdateEvent): The task status update event.

        Returns:
            list[str]: List of text parts from the status message.
        """
        if event.status.message:
            return get_text_parts(event.status.message.parts)
        return []

    @staticmethod
    def _should_filter_completion_message(event: TaskStatusUpdateEvent, extracted_texts: list[str]) -> bool:
        """Check if this is a generic completion message that should be filtered.

        Args:
            event (TaskStatusUpdateEvent): The task status update event.
            extracted_texts (list[str]): List of extracted text parts.

        Returns:
            bool: True if the completion message should be filtered, False otherwise.
        """
        is_task_completed = event.status.state in [
            TaskState.completed,
            TaskState.failed,
            TaskState.canceled,
        ]

        if is_task_completed and event.final:
            content_text = "\n".join(extracted_texts) if extracted_texts else ""
            return not extracted_texts or content_text.strip() in [
                "Task completed successfully.",
                "Task completed successfully",
            ]
        return False

    @staticmethod
    def _create_status_response(event: TaskStatusUpdateEvent, extracted_texts: list[str]) -> dict[str, Any]:
        """Create response for non-tool status updates.

        Args:
            event (TaskStatusUpdateEvent): The task status update event.
            extracted_texts (list[str]): List of extracted text parts.

        Returns:
            dict[str, Any]: Response dictionary with status and content.
        """
        content = "\n".join(extracted_texts)
        custom_metadata = A2AConnector._extract_custom_metadata_from_status_message(event)
        metadata = create_status_update_metadata(content, custom_metadata)
        metadata = A2AConnector._merge_event_metadata(metadata, event)
        event_type = A2AConnector._resolve_metadata_event_type(metadata, A2AStreamEventType.STATUS_UPDATE)

        return {
            "status": "success",
            "task_state": event.status.state.value,
            "content": content,
            "task_id": event.taskId,
            "context_id": event.contextId,
            "final": False,
            "timestamp": event.status.timestamp,
            "metadata": metadata,
            "event_type": event_type,
        }

    @staticmethod
    def _merge_event_metadata(metadata: dict[str, Any] | None, event: TaskStatusUpdateEvent) -> dict[str, Any]:
        """Merge response metadata with event-level metadata and timestamps.

        Args:
            metadata (dict[str, Any] | None): The base metadata to merge.
            event (TaskStatusUpdateEvent): The event containing additional metadata.

        Returns:
            dict[str, Any]: The merged metadata dictionary.
        """
        merged: dict[str, Any] = {}
        if isinstance(metadata, dict):
            merged.update(metadata)

        if isinstance(event.metadata, dict):
            merged = {**event.metadata, **merged}

        timestamp = getattr(event.status, "timestamp", None) if event.status else None
        if timestamp is not None and "timestamp" not in merged:
            merged["timestamp"] = timestamp

        return merged

    @staticmethod
    def _create_empty_payload_response(
        event: TaskStatusUpdateEvent,
        metadata: dict[str, Any],
        default_event_type: A2AStreamEventType,
        task_state: str,
    ) -> dict[str, Any]:
        """Create a placeholder response for empty textual content.

        Args:
            event (TaskStatusUpdateEvent): The task status update event.
            metadata (dict[str, Any]): The metadata for the response.
            default_event_type (A2AStreamEventType): The default type of the streaming
                event when no override is present in metadata.
            task_state (str): The current state of the task.

        Returns:
            dict[str, Any]: Response dictionary with placeholder content.
        """
        response_metadata = metadata.copy() if isinstance(metadata, dict) else {}
        resolved_event_type = A2AConnector._resolve_metadata_event_type(response_metadata, default_event_type)
        return {
            "status": "success",
            "task_state": task_state,
            "content": None,
            "reason": "empty_payload",
            "task_id": event.taskId,
            "context_id": event.contextId,
            "final": bool(event.final),
            "timestamp": event.status.timestamp if event.status else None,
            "metadata": response_metadata,
            "event_type": resolved_event_type,
        }

    @staticmethod
    def _resolve_metadata_event_type(
        metadata: dict[str, Any] | None, default: A2AStreamEventType
    ) -> A2AStreamEventType | str:
        """Resolve custom event type stored in metadata.

        Args:
            metadata (dict[str, Any] | None): Metadata that may contain an
                ``event_type`` or ``type`` override.
            default (A2AStreamEventType): Default event type to use when no
                override is present or the override is invalid.

        Returns:
            A2AStreamEventType | str: Resolved event type value.
        """
        if not isinstance(metadata, dict):
            return default

        override = metadata.get("event_type") or metadata.get("type")
        if isinstance(override, A2AStreamEventType):
            return override
        if isinstance(override, str):
            try:
                return A2AStreamEventType(override)
            except ValueError:
                return override
        return default

    @staticmethod
    def _detect_tool_processing_in_status(event: TaskStatusUpdateEvent) -> dict[str, Any]:
        """Detect tool processing in TaskStatusUpdateEvent messages.

        This aligns with base_executor._is_tool_processing_content() logic
        but extracts additional information for A2A response formatting.

        Args:
            event: The TaskStatusUpdateEvent to analyze.

        Returns:
            Dictionary with tool processing detection results.
        """
        if not event.status or not event.status.message:
            return {"is_tool_processing": False}

        message = event.status.message
        metadata = event.metadata or {}
        tool_info = metadata.get("tool_info", {})

        if not tool_info:
            return {"is_tool_processing": False}

        # Extract message text once
        message_text = message.parts[0].root.text if message.parts else None

        # Handle tool calls (both invocation and results)
        if "tool_calls" in tool_info:
            kind = metadata.get(MetadataFieldKeys.KIND) if isinstance(metadata, dict) else None
            if tool_info.get("id") is None and getattr(kind, "value", kind) == Kind.FINAL_THINKING_STEP.value:
                logger.debug(
                    "A2AConnector: forwarding final thinking activity (tool=%s, state=%s)",
                    tool_info.get("name"),
                    metadata.get("status"),
                )
                return {"is_tool_processing": False}
            return A2AConnector._handle_tool_calls(tool_info, message_text, metadata)

        # Handle single tool result
        if "output" in tool_info:
            return A2AConnector._handle_single_tool_result(tool_info, message_text, metadata)

        return {"is_tool_processing": False}

    @staticmethod
    def _handle_tool_calls(
        tool_info: dict[str, Any], message_text: str | None, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle processing of tool calls with multiple tools.

        Args:
            tool_info (dict[str, Any]): Information about the tool calls.
            message_text (str | None): Optional message text to display.
            metadata (dict[str, Any]): The metadata for the response.

        Returns:
            dict[str, Any]: Response dictionary with tool call information.
        """
        tool_calls = tool_info["tool_calls"]
        has_output_in_tool_calls = any("output" in tool_call for tool_call in tool_calls)
        tool_names = [tc.get("name") for tc in tool_calls]

        if not has_output_in_tool_calls:
            # Handle tool invocation
            status_message = message_text or f"Processing with tools: {', '.join(tool_names)}"
            metadata[MetadataFieldKeys.STATUS] = Status.RUNNING
            event_type = A2AStreamEventType.TOOL_CALL
        else:
            # Handle multiple tool results
            status_message = message_text or A2AConnector._build_completion_message(tool_calls, tool_names)
            metadata[MetadataFieldKeys.STATUS] = Status.FINISHED
            event_type = A2AStreamEventType.TOOL_RESULT

        return A2AConnector._create_tool_processing_result(tool_names, status_message, metadata, event_type)

    @staticmethod
    def _handle_single_tool_result(
        tool_info: dict[str, Any], message_text: str | None, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle processing of single tool result.

        Args:
            tool_info (dict[str, Any]): Information about the single tool result.
            message_text (str | None): Optional message text to display.
            metadata (dict[str, Any]): The metadata for the response.

        Returns:
            dict[str, Any]: Response dictionary with tool result information.
        """
        tool_name = tool_info["name"]

        tool_calls = tool_info.get("tool_calls")
        if tool_info.get("id") is None and isinstance(tool_calls, list) and tool_calls:
            logger.info(
                "A2AConnector: skipping streaming tool duplicate result (tool=%s, state=%s)",
                tool_name,
                metadata.get("status"),
            )
            return {"is_tool_processing": False, "skip_status_update": True}

        if message_text:
            status_message = message_text
        elif isinstance(metadata.get("hitl"), dict):
            status_message = A2AConnector._format_tool_output(tool_info.get("output"), tool_name)
        else:
            output = tool_info.get("output")
            status_message = A2AConnector._format_tool_output(output, tool_name)

        if A2AConnector._is_generic_tool_completion(status_message, tool_info.get("output"), tool_name):
            return {"is_tool_processing": False, "skip_status_update": True}

        metadata[MetadataFieldKeys.STATUS] = Status.FINISHED
        return A2AConnector._create_tool_processing_result(
            [tool_name], status_message, metadata, A2AStreamEventType.TOOL_RESULT
        )

    @staticmethod
    def _build_completion_message(tool_calls: list[dict[str, Any]], tool_names: list[str]) -> str:
        """Build completion message for tool calls.

        Args:
            tool_calls (list[dict[str, Any]]): List of tool call dictionaries.
            tool_names (list[str]): List of tool names.

        Returns:
            str: The completion message.
        """
        outputs = SSEChunkTransformer.extract_tool_outputs(tool_calls)
        return "\n".join(outputs) if outputs else f"Completed {', '.join(tool_names)}"

    @staticmethod
    def _extract_tool_outputs(tool_calls: list[dict[str, Any]]) -> list[str]:
        """Extract human-readable output strings from tool calls.

        Delegates to SSEChunkTransformer.extract_tool_outputs for shared implementation.

        Args:
            tool_calls (list[dict[str, Any]]): List of tool call dictionaries.

        Returns:
            list[str]: List of human-readable output strings.
        """
        return SSEChunkTransformer.extract_tool_outputs(tool_calls)

    @staticmethod
    def _format_tool_output(output: Any, tool_name: str) -> str:
        """Format a single tool output for display.

        Delegates to SSEChunkTransformer.format_tool_output for shared implementation.

        Args:
            output (Any): The tool output to format.
            tool_name (str): The name of the tool.

        Returns:
            str: The formatted output string.
        """
        return SSEChunkTransformer.format_tool_output(output, tool_name)

    @staticmethod
    def _create_tool_processing_result(
        tool_names: list[str], status_message: str, metadata: dict[str, Any], event_type: A2AStreamEventType
    ) -> dict[str, Any]:
        """Create a standardized tool processing result dictionary.

        Args:
            tool_names: List of tool names to process.
            status_message: Status message to display.
            metadata: Metadata to include in the response.
            event_type: Type of A2A stream event for the response.

        Returns:
            Dictionary containing tool processing result information.
        """
        return {
            "is_tool_processing": True,
            "tool_names": tool_names,
            "status_message": status_message,
            "original_metadata": metadata,
            "event_type": event_type,
        }

    @staticmethod
    def _is_generic_tool_completion(
        status_message: str | None,
        tool_output: Any,
        tool_name: str | None,
    ) -> bool:
        """Return True when the message/output represents a generic completion placeholder.

        Args:
            status_message: The status message extracted from the event.
            tool_output: The tool output extracted from the metadata.
            tool_name: The tool name associated with the event.

        Returns:
            bool: True if the content matches known generic completion phrases.
        """
        normalized_candidates: list[str] = []
        for candidate in (status_message, tool_output):
            if isinstance(candidate, str):
                normalized_candidates.append(candidate.strip())
        if not normalized_candidates:
            return False

        default_messages = {
            "Task completed successfully.",
            "Task completed successfully",
        }
        if isinstance(tool_name, str) and tool_name:
            default_messages.add(f"Tool '{tool_name}' completed successfully")
            default_messages.add(f'Tool "{tool_name}" completed successfully')

        return any(message in default_messages for message in normalized_candidates)

    @staticmethod
    def _extract_custom_metadata_from_status_message(
        event: TaskStatusUpdateEvent,
    ) -> dict[str, Any] | None:
        """Extract custom metadata from a TaskStatusUpdateEvent.

        Args:
            event: Task status update event potentially containing event metadata.

        Returns:
            A dictionary of metadata if present and extractable; otherwise None.
        """
        try:
            metadata = event.metadata  # type: ignore[union-attr]
        except AttributeError:
            return None
        return metadata if isinstance(metadata, dict) else None

    @staticmethod
    def _handle_artifact_update_event(
        event: TaskArtifactUpdateEvent,
        artifact_tracker: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process an artifact update, add it to the collected list, and immediately yield it.

        This method now properly detects final responses based on lastChunk=True flag,
        aligning with the new base_executor.py implementation.

        Args:
            event: The TaskArtifactUpdateEvent from A2A protocol.
            artifact_tracker: Artifact tracking collections.

        Returns:
            Response dictionary to be yielded immediately, or None if duplicate.
        """
        artifact_dict = A2AConnector._handle_artifact_update(event)
        if not artifact_dict:
            return None

        is_final_response = event.lastChunk is True
        is_token_streaming = event.append is not None and not is_final_response

        # Handle artifact collection and deduplication
        # Skip deduplication for streaming chunks to avoid filtering out repeated content
        if not is_token_streaming:
            if not A2AConnector._process_artifact_collection(artifact_dict, artifact_tracker, is_final_response):
                return None

        # Determine response content and artifacts based on artifact type
        content, task_state, response_artifacts = A2AConnector._determine_artifact_response_content(
            artifact_dict, artifact_tracker, is_final_response
        )

        return A2AConnector._create_artifact_response(event, content, task_state, response_artifacts, is_final_response)

    @staticmethod
    def _process_artifact_collection(
        artifact_dict: dict[str, Any], artifact_tracker: dict[str, Any], is_final_response: bool
    ) -> bool:
        """Process artifact collection and deduplication. Returns False if should skip response.

        Args:
            artifact_dict (dict[str, Any]): The artifact dictionary to process.
            artifact_tracker (dict[str, Any]): The tracker for artifacts.
            is_final_response (bool): Whether this is the final response.

        Returns:
            bool: False if should skip response, True otherwise.
        """
        artifact_name = artifact_dict.get("artifact_name", "")

        if artifact_name != "final_response":
            artifact_hash = A2AConnector._create_artifact_hash(artifact_dict)
            if artifact_hash not in artifact_tracker["seen_artifact_hashes"]:
                artifact_tracker["seen_artifact_hashes"].add(artifact_hash)

                artifact_info = A2AConnector._create_artifact_info(artifact_dict, artifact_name)
                artifact_tracker["collected_artifacts"].append(artifact_info.model_dump())
            else:
                logger.debug(f"Skipping duplicate artifact: {artifact_name}")
                if not is_final_response:
                    return False
        return True

    @staticmethod
    def _create_artifact_info(artifact_dict: dict[str, Any], artifact_name: str) -> ArtifactInfo:
        """Create structured artifact info using Pydantic model.

        Args:
            artifact_dict (dict[str, Any]): The artifact dictionary to convert.
            artifact_name (str): The name of the artifact.

        Returns:
            ArtifactInfo: The structured artifact information.
        """
        return ArtifactInfo(
            artifact_id=artifact_dict.get("artifact_id"),
            name=artifact_name,
            content_type=artifact_dict.get("content_type"),
            mime_type=artifact_dict.get("mime_type"),
            file_name=artifact_dict.get("file_name"),
            has_file_data="file_data" in artifact_dict,
            has_file_uri="file_uri" in artifact_dict,
            file_data=artifact_dict.get("file_data"),
            file_uri=artifact_dict.get("file_uri"),
            description=artifact_dict.get("description"),
        )

    @staticmethod
    def _determine_artifact_response_content(
        artifact_dict: dict[str, Any], artifact_tracker: dict[str, Any], is_final_response: bool
    ) -> tuple[str, str, list[dict[str, Any]]]:
        """Determine response content, task state, and artifacts based on artifact type.

        Args:
            artifact_dict (dict[str, Any]): The artifact dictionary to process.
            artifact_tracker (dict[str, Any]): The tracker for artifacts.
            is_final_response (bool): Whether this is the final response.

        Returns:
            tuple[str, str, list[dict[str, Any]]]: Tuple of (content, task_state, response_artifacts).
        """
        artifact_name = artifact_dict.get("artifact_name", "")

        if is_final_response and artifact_name == "final_response":
            content = artifact_dict.get("content", f"Final response: {artifact_name}")
            task_state = "completed"
            response_artifacts = artifact_tracker["collected_artifacts"].copy()
        else:
            content = artifact_dict.get("content", f"Artifact received: {artifact_name}")
            task_state = "working"
            response_artifacts = []
            if artifact_name != "final_response":
                for artifact in artifact_tracker["collected_artifacts"]:
                    if artifact.get("name") == artifact_name:
                        response_artifacts = [artifact]
                        break

        return content, task_state, response_artifacts

    @staticmethod
    def _create_artifact_response(
        event: TaskArtifactUpdateEvent,
        content: str,
        task_state: str,
        response_artifacts: list[dict[str, Any]],
        is_final_response: bool,
    ) -> dict[str, Any]:
        """Create the final artifact response dictionary.

        Args:
            event (TaskArtifactUpdateEvent): The artifact update event.
            content (str): The content to include in the response.
            task_state (str): The current state of the task.
            response_artifacts (list[dict[str, Any]]): List of artifacts to include.
            is_final_response (bool): Whether this is the final response.

        Returns:
            dict[str, Any]: The complete artifact response dictionary.
        """
        # Extract metadata from final response artifacts if available
        metadata = A2AConnector._extract_artifact_metadata(event, content, is_final_response)

        if is_final_response:
            metadata_options = FinalResponseMetadataOptions(metadata_extra=metadata)
            return assemble_final_response(
                content=content,
                artifacts=response_artifacts or None,
                metadata_options=metadata_options,
                task_state=task_state,
                extra_fields={
                    "task_id": event.taskId,
                    "context_id": event.contextId,
                    "event_type": A2AStreamEventType.FINAL_RESPONSE,
                },
            )

        response = {
            "status": "success",
            "task_state": task_state,
            "content": content,
            "final": False,
            "task_id": event.taskId,
            "context_id": event.contextId,
            "metadata": metadata,
            "event_type": A2AStreamEventType.TOOL_RESULT,
        }

        if response_artifacts:
            response["artifacts"] = response_artifacts

        return response

    @staticmethod
    def _extract_artifact_metadata(
        event: TaskArtifactUpdateEvent, content: str, is_final_response: bool
    ) -> dict[str, Any]:
        """Extract comprehensive metadata from artifact events.

        For final responses, merges event metadata with standard metadata.
        For non-final responses, creates standard metadata.

        Args:
            event: The TaskArtifactUpdateEvent from A2A protocol.
            content: The response content.
            is_final_response: Whether this is a final response.

        Returns:
            A dictionary containing merged metadata.
        """
        # Normalize event metadata keys (may contain enum keys from server)
        event_md = event.metadata or {}
        normalized_md: dict[str, Any] = {}
        if isinstance(event_md, dict):
            for k, v in event_md.items():
                try:
                    if isinstance(k, MetadataFieldKeys):
                        normalized_md[k] = v
                    else:
                        normalized_md[str(k)] = v
                except Exception:
                    normalized_md[str(k)] = v

        merged_metadata = create_metadata(
            content=content,
            is_final=is_final_response,
            status=Status.FINISHED if is_final_response else Status.RUNNING,
            existing_metadata=normalized_md,
        )

        return merged_metadata

    @staticmethod
    def _process_task_object(
        res_data: Task,
        collected_artifacts: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Processes a Task object and returns a status update response.

        This method uses the ArtifactInfo Pydantic model to ensure consistent
        artifact structure when converting A2A artifacts to our internal format.

        Args:
            res_data: The Task object from A2A protocol.
            collected_artifacts: List of artifacts collected during streaming.

        Returns:
            Response dictionary if there's content to return, None otherwise.
        """
        texts = A2AConnector._extract_text_content(res_data)
        if not texts:
            return None

        # Convert and merge artifacts
        all_artifacts = A2AConnector._convert_and_merge_task_artifacts(res_data, collected_artifacts)

        # Determine task completion status
        content = "\n".join(texts)
        is_final = A2AConnector._is_task_final_state(res_data.status.state)

        return A2AConnector._create_task_response(res_data, content, all_artifacts, is_final)

    @staticmethod
    def _convert_and_merge_task_artifacts(
        res_data: Task, collected_artifacts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert A2A task artifacts to our format and merge with collected artifacts.

        Args:
            res_data: The Task object from A2A protocol.
            collected_artifacts: List of artifacts collected during streaming.

        Returns:
            List of all artifacts.
        """
        task_artifacts = []
        if res_data.artifacts:
            for artifact in res_data.artifacts:
                artifact_info = ArtifactInfo(
                    artifact_id=artifact.artifactId,
                    name=artifact.name,
                    description=artifact.description,
                    parts=len(artifact.parts) if artifact.parts else 0,
                )
                task_artifacts.append(artifact_info.model_dump())

        # Combine with collected artifacts (avoid duplicates)
        all_artifacts = collected_artifacts.copy()
        for task_artifact in task_artifacts:
            artifact_id = task_artifact.get("artifact_id")
            if not any(ca.get("artifact_id") == artifact_id for ca in all_artifacts):
                all_artifacts.append(task_artifact)

        return all_artifacts

    @staticmethod
    def _is_task_final_state(state: TaskState) -> bool:
        """Check if task state represents a final state.

        Args:
            state: The TaskState object from A2A protocol.

        Returns:
            True if the task state represents a final state, False otherwise.
        """
        return state in [TaskState.completed, TaskState.failed, TaskState.canceled]

    @staticmethod
    def _create_task_response(
        res_data: Task, content: str, all_artifacts: list[dict[str, Any]], is_final: bool
    ) -> dict[str, Any]:
        """Create the final task response dictionary.

        Args:
            res_data: The Task object from A2A protocol.
            content: The response content.
            all_artifacts: List of all artifacts.
            is_final: Whether this is a final response.
        """
        metadata = create_metadata(content=content, is_final=is_final)
        timestamp = datetime.now(UTC).isoformat()

        if is_final:
            metadata_options = FinalResponseMetadataOptions(metadata_extra=metadata)
            return assemble_final_response(
                content=content,
                artifacts=all_artifacts or None,
                metadata_options=metadata_options,
                task_state=res_data.status.state.value,
                extra_fields={
                    "task_id": res_data.id,
                    "context_id": res_data.contextId,
                    "event_type": A2AStreamEventType.FINAL_RESPONSE,
                    "timestamp": timestamp,
                },
            )

        response = {
            "status": "success",
            "task_state": res_data.status.state.value,
            "content": content,
            "task_id": res_data.id,
            "context_id": res_data.contextId,
            "final": False,
            "timestamp": timestamp,
            "metadata": metadata,
            "event_type": A2AStreamEventType.CONTENT_CHUNK,
        }

        if all_artifacts:
            response["artifacts"] = all_artifacts

        return response

    @staticmethod
    def _process_message_object(res_data: Message) -> dict[str, Any] | None:
        """Processes a Message object and returns a status update response.

        Args:
            res_data: The Message object from A2A protocol.

        Returns:
            Response dictionary if there's content to return, None otherwise.
        """
        if not res_data.parts:
            return None

        texts = get_text_parts(res_data.parts)
        if not texts:
            return None

        content = "\n".join(texts)
        return {
            "status": "success",
            "task_state": "working",
            "content": content,
            "task_id": res_data.taskId,
            "context_id": res_data.contextId,
            "final": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": create_metadata(content=content, is_final=False),
            "event_type": A2AStreamEventType.CONTENT_CHUNK,
        }

    @staticmethod
    def _handle_artifact_update(
        event: TaskArtifactUpdateEvent,
    ) -> dict[str, Any] | None:
        """Handles task artifact update events from A2A protocol.

        Args:
            event: The TaskArtifactUpdateEvent from A2A protocol.

        Returns:
            Response dictionary if there's content to return, None otherwise.
        """
        if not event.artifact or not event.artifact.parts:
            return None

        # Create base artifact response structure
        artifact_response = A2AConnector._create_base_artifact_response(event)

        # Try to extract text content first
        texts = get_text_parts(event.artifact.parts)
        if texts:
            return A2AConnector._create_text_artifact_response(artifact_response, texts)

        # Handle file artifacts
        return A2AConnector._create_file_artifact_response(event, artifact_response)

    @staticmethod
    def _create_base_artifact_response(event: TaskArtifactUpdateEvent) -> dict[str, Any]:
        """Create base artifact response structure.

        Args:
            event: The TaskArtifactUpdateEvent from A2A protocol.

        Returns:
            A dictionary containing the base artifact response structure.
        """
        return {
            "type": "artifact",
            "status": "success",
            "task_id": event.taskId,
            "context_id": event.contextId,
            "artifact_id": event.artifact.artifactId,
            "artifact_name": event.artifact.name,
            "append": event.append,
            "last_chunk": event.lastChunk,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def _create_text_artifact_response(artifact_response: dict[str, Any], texts: list[str]) -> dict[str, Any]:
        """Create response for text artifacts.

        Args:
            artifact_response: The artifact response dictionary.
            texts: List of text parts.
        """
        artifact_response.update(
            {
                "content_type": "text",
                "content": "\n".join(texts),
            }
        )
        return artifact_response

    @staticmethod
    def _create_file_artifact_response(
        event: TaskArtifactUpdateEvent, artifact_response: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Create response for file artifacts.

        Args:
            event: The TaskArtifactUpdateEvent from A2A protocol.
            artifact_response: The artifact response dictionary.
        """
        for part in event.artifact.parts:
            if hasattr(part, "root") and hasattr(part.root, "file"):
                file_info = part.root.file

                # Update with file metadata
                artifact_response.update(
                    {
                        "content_type": "file",
                        "mime_type": (
                            file_info.mimeType if hasattr(file_info, "mimeType") else "application/octet-stream"
                        ),
                        "file_name": (file_info.name if hasattr(file_info, "name") else event.artifact.name),
                    }
                )

                # Extract file content and create description
                A2AConnector._extract_file_content(file_info, artifact_response)
                return artifact_response

        return None

    @staticmethod
    def _extract_file_content(file_info: Any, artifact_response: dict[str, Any]) -> None:
        """Extract file content (bytes or URI) and create content description.

        Args:
            file_info: The file info object from A2A protocol.
            artifact_response: The artifact response dictionary.
        """
        file_name = artifact_response["file_name"]

        if hasattr(file_info, "bytes") and file_info.bytes:
            artifact_response["file_data"] = file_info.bytes
            artifact_response["content"] = f"File artifact: {file_name} ({len(file_info.bytes)} bytes base64 data)"
        elif hasattr(file_info, "uri") and file_info.uri:
            artifact_response["file_uri"] = file_info.uri
            artifact_response["content"] = f"File artifact: {file_name} (URI: {file_info.uri})"
        else:
            artifact_response["content"] = f"File artifact: {file_name} (no content available)"

    @staticmethod
    def send_to_agent(
        agent_card: AgentCard,
        message: str | dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synchronously sends a message to another agent using the A2A protocol.

        This method is a synchronous wrapper around asend_to_agent. It handles the creation
        of an event loop if one doesn't exist, and manages the asynchronous call internally.

        Args:
            agent_card: The AgentCard instance containing the target agent's details including
                URL, authentication requirements, and capabilities.
            message: The message to send to the agent. Can be either a string for simple text
                messages or a dictionary for structured data.
            **kwargs: Additional keyword arguments passed to asend_to_agent.

        Returns:
            A dictionary containing the response details:
                - status (str): 'success' or 'error'
                - content (str): Extracted text content from the response
                - task_id (str, optional): ID of the created/updated task
                - task_state (str, optional): Current state of the task
                - raw_response (str): Complete JSON response from the A2A client
                - error_type (str, optional): Type of error if status is 'error'
                - message (str, optional): Error message if status is 'error'

        Raises:
            RuntimeError: If asend_to_agent encounters an unhandled exception.
        """
        try:
            # Check if there's already a running event loop
            loop = asyncio.get_running_loop()
            logger.info(f"Running loop: {loop}")
        except RuntimeError:
            logger.info("No running loop, safe to use asyncio.run()")
            return asyncio.run(A2AConnector.asend_to_agent(agent_card, message, **kwargs))
        else:
            logger.info("There's a running loop, need to handle differently")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    A2AConnector.asend_to_agent(agent_card, message, **kwargs),
                )
                return future.result()

    @staticmethod
    async def asend_to_agent(
        agent_card: AgentCard,
        message: str | dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Asynchronously sends a message to another agent using the A2A protocol.

        This method uses the streaming approach internally but only returns the final response,
        avoiding direct httpx usage that can cause issues with Nuitka compilation.

        Args:
            agent_card: The AgentCard instance containing the target agent's details including
                URL, authentication requirements, and capabilities.
            message: The message to send to the agent. Can be either a string for simple text
                messages or a dictionary for structured data.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing the final response with the simplified structure:
                - status (str): "success" or "error"
                - task_state (str): Final A2A TaskState value
                - content (str): Final text content from the agent
                - task_id (str): ID of the associated task
                - context_id (str): Context ID of the task
                - final (bool): Always True for final responses
                - artifacts (list): List of all artifacts created during execution

        Raises:
            Exception: If there's an error during message sending or processing.
        """
        error_content = "No response received"
        final_response = A2AConnector._create_error_response("error", error_content)
        last_metadata_time = None

        try:
            # Process streaming response and only collect artifacts from final response
            async for chunk in A2AConnector.astream_to_agent(agent_card, message, **kwargs):
                # Process chunk and handle potential early error return
                processed_response = A2AConnector._merge_stream_chunk_into_final(chunk, final_response)
                if processed_response and processed_response.get("status") == "error":
                    return processed_response

                # Handle metadata
                final_response, last_metadata_time = A2AConnector._handle_chunk_metadata(
                    chunk, final_response, last_metadata_time
                )

            # Ensure final response metadata carries a meaningful cumulative time
            final_response = A2AConnector._ensure_final_metadata_time(final_response, last_metadata_time)

            return final_response

        except Exception as e:
            logger.error(f"Error in asend_to_agent: {e}", exc_info=True)
            error_content = f"Error during message sending: {str(e)}"
            return A2AConnector._create_error_response("error", error_content)

    @staticmethod
    def _merge_stream_chunk_into_final(chunk: dict[str, Any], final_response: dict[str, Any]) -> dict[str, Any]:
        """Merge a simplified streaming chunk into the cumulative final response.

        Used by asend_to_agent, where chunks are already normalized dicts coming
        from astream_to_agent (or a test double).

        Args:
            chunk (dict[str, Any]): The streaming chunk to merge.
            final_response (dict[str, Any]): The cumulative final response.

        Returns:
            dict[str, Any]: The updated final response.
        """
        # Handle error chunks
        if chunk.get("status") == "error":
            error_content = chunk.get("message", "Unknown error")
            return A2AConnector._create_error_response("error", error_content)

        # Update final response with latest information
        final_response.update(
            {
                "status": chunk.get("status", "success"),
                "task_state": chunk.get("task_state", "working"),
                "content": chunk.get("content", ""),
                "task_id": chunk.get("task_id", ""),
                "context_id": chunk.get("context_id", ""),
                "final": chunk.get("final", False),
            }
        )

        # Only collect artifacts from final response to avoid duplication
        if chunk.get("final", False):
            final_response["artifacts"] = chunk.get("artifacts", [])

        return final_response

    @staticmethod
    def _handle_chunk_metadata(
        chunk: dict[str, Any], final_response: dict[str, Any], last_metadata_time: float | None
    ) -> tuple[dict[str, Any], float | None]:
        """Handle metadata from a chunk and return updated response and time.

        Args:
            chunk (dict[str, Any]): The streaming chunk containing metadata.
            final_response (dict[str, Any]): The cumulative final response.
            last_metadata_time (float | None): The last metadata timestamp.

        Returns:
            tuple[dict[str, Any], float | None]: Tuple of (updated_response, new_metadata_time).
        """
        if chunk.get("metadata"):
            md = chunk.get("metadata")
            final_response["metadata"] = md

            # Extract time from metadata
            try:
                t = md.get(MetadataFieldKeys.TIME) if isinstance(md, dict) else None
                if isinstance(t, int | float) and t > 0:
                    last_metadata_time = t
            except Exception:
                pass

        return final_response, last_metadata_time

    @staticmethod
    def _ensure_final_metadata_time(final_response: dict[str, Any], last_metadata_time: float | None) -> dict[str, Any]:
        """Ensure final response metadata has meaningful cumulative time.

        Args:
            final_response (dict[str, Any]): The final response to update.
            last_metadata_time (float | None): The last metadata timestamp to use.

        Returns:
            dict[str, Any]: The updated final response with ensured time metadata.
        """
        try:
            md = final_response.get("metadata")
            if isinstance(md, dict):
                t = md.get(MetadataFieldKeys.TIME)
                if (
                    not isinstance(t, int | float) or abs(t) < A2AConnector.FLOAT_EPSILON
                ) and last_metadata_time is not None:
                    md[MetadataFieldKeys.TIME] = last_metadata_time
                    final_response["metadata"] = md
        except Exception:
            pass

        return final_response

    @staticmethod
    async def astream_to_agent(
        agent_card: AgentCard,
        message: str | dict[str, Any],
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronously sends a streaming message to another agent using the A2A protocol.

        This method supports streaming responses from the target agent, yielding chunks of
        the response as they become available. It handles the official A2A streaming event
        types as defined in the specification.

        Args:
            agent_card: The AgentCard instance containing the target agent's details including
                URL, authentication requirements, and capabilities.
            message: The message to send to the agent. Can be either a string for simple text
                messages or a dictionary for structured data.
            **kwargs: Additional keyword arguments.

        Yields:
            Dictionaries containing streaming response chunks with a simplified structure:

            For successful responses:
                - status (str): "success" or "error"
                - task_state (str): A2A TaskState value
                - content (str): Text content from the agent
                - task_id (str): ID of the associated task
                - context_id (str): Context ID of the task
                - final (bool): Whether this is the final update
                - artifacts (list, optional): List of artifacts created in this step

            Each artifact in the artifacts list contains:
                - artifact_id (str): ID of the artifact
                - name (str): Name of the artifact
                - content_type (str): "text" or "file"
                - mime_type (str): MIME type of the artifact
                - file_name (str, optional): Name of the file for file artifacts
                - has_file_data (bool): Whether file data is included
                - has_file_uri (bool): Whether file URI is included
                - file_data (str, optional): Base64 encoded file content
                - file_uri (str, optional): URI reference to the file

            For errors:
                - status (str): "error"
                - error_type (str): Type of error encountered
                - message (str): Error description

        Raises:
            httpx.HTTPError: If there's an HTTP-related error during the streaming request.
            Exception: For any other unexpected errors during message streaming or processing.
        """
        http_kwargs = kwargs.pop("http_kwargs", None)

        try:
            # Create message payload and request with required id field
            request = A2AConnector._create_streaming_request(message, kwargs)
            artifact_tracker = A2AConnector._create_artifact_tracker()
            metadata_time_tracker = MetadataTimeTracker()
            config = StreamingConfig(http_kwargs=http_kwargs)

            # Stream messages and process responses
            async for response in A2AConnector._stream_and_process_messages(
                agent_card,
                request,
                artifact_tracker,
                metadata_time_tracker,
                config,
            ):
                yield response

        except Exception as e:
            err = A2AConnector._create_error_response("client_side_exception", str(e))
            yield err

    @staticmethod
    def _create_streaming_request(message: str | dict[str, Any], kwargs: dict[str, Any]) -> SendStreamingMessageRequest:
        """Create a streaming message request from the input parameters.

        Args:
            message: The message to send.
            kwargs: Additional parameters including task_id, context_id, and metadata.

        Returns:
            A configured SendStreamingMessageRequest.
        """
        payload = A2AConnector._create_message_payload(
            message,
            kwargs.get("task_id"),
            kwargs.get("context_id"),
        )
        base_metadata = kwargs.get("metadata") or {}
        metadata = base_metadata.copy() if isinstance(base_metadata, dict) else {}

        pii_mapping = kwargs.get("pii_mapping")
        if isinstance(pii_mapping, dict) and pii_mapping:
            metadata["pii_mapping"] = pii_mapping

        return SendStreamingMessageRequest(id=str(uuid.uuid4()), params=MessageSendParams(**payload, metadata=metadata))

    @staticmethod
    def _create_artifact_tracker() -> dict[str, Any]:
        """Create an artifact tracking structure for deduplication.

        Returns:
            Dictionary containing artifact tracking collections.
        """
        return {
            "collected_artifacts": [],
            "seen_artifact_hashes": set(),
        }

    @staticmethod
    async def _stream_and_process_messages(
        agent_card: AgentCard,
        request: SendStreamingMessageRequest,
        artifact_tracker: dict[str, Any],
        metadata_time_tracker: MetadataTimeTracker,
        config: StreamingConfig,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream messages from A2A client and process each response chunk.

        Args:
            agent_card: The target agent's card.
            request: The streaming request to send.
            artifact_tracker: Artifact tracking collections.
            metadata_time_tracker: Tracker for accumulating execution time across agent steps.
            config: Configuration object containing streaming parameters.

        Yields:
            dict[str, Any]: Response dictionaries containing processed stream chunks with structure:
                - status (str): "success" or "error"
                - task_state (str): A2A TaskState value
                - content (str): Text content from the agent
                - task_id (str): ID of the associated task
                - context_id (str): Context ID of the task
                - final (bool): Whether this is the final update
                - artifacts (list, optional): List of artifacts created in this step

        Raises:
            httpx.HTTPError: If there's an HTTP-related error during the streaming request.
        """
        async with httpx.AsyncClient(**(config.http_kwargs or {})) as http_client:
            a2a_client = A2AClient(httpx_client=http_client, agent_card=agent_card)

            # Track metadata hash to avoid unnecessary normalization
            current_metadata_hash: str | None = None
            metadata_cache: dict[str, dict[str, Any]] = {}

            async for chunk in a2a_client.send_message_streaming(request):
                if not isinstance(chunk.root, SendStreamingMessageSuccessResponse):
                    continue

                response = A2AConnector._process_stream_chunk(chunk.root.result, artifact_tracker)
                if response:
                    async for processed_chunk, metadata_hash in A2AConnector._process_response_chunk(
                        response, metadata_time_tracker, config, current_metadata_hash, metadata_cache
                    ):
                        yield processed_chunk
                        # Update hash for next iteration if metadata was normalized
                        if metadata_hash is not None:
                            current_metadata_hash = metadata_hash

    @staticmethod
    async def _process_response_chunk(
        response: dict[str, Any],
        metadata_time_tracker: MetadataTimeTracker,
        config: StreamingConfig,
        previous_metadata_hash: str | None = None,
        metadata_cache: dict[str, dict[str, Any]] | None = None,
    ) -> AsyncGenerator[tuple[dict[str, Any], str | None], None]:
        """Process a single response chunk and yield the legacy format.

        Args:
            response: Response payload produced from the stream chunk.
            metadata_time_tracker: Tracker used to aggregate timing metadata.
            config: Streaming configuration flags.
            previous_metadata_hash: Hash of the previously normalized metadata payload.
            metadata_cache: Optional cache of normalized metadata keyed by hash for reuse.

        Yields:
            tuple[dict[str, Any], Optional[str]]: The processed chunk and the hash of the
            normalized metadata when it changes.
        """
        processed_response = metadata_time_tracker.update_response_metadata(response)
        processed_response, current_metadata_hash = A2AConnector._normalize_metadata_enums(
            processed_response, previous_metadata_hash, metadata_cache
        )

        # Remove artifacts field if empty (legacy behavior)
        if processed_response.get("artifacts") is None or processed_response.get("artifacts") == []:
            processed_response.pop("artifacts", None)

        routed_response = A2AConnector.event_registry.handle(processed_response.get("event_type"), processed_response)
        normalized_event_type = A2AConnector._normalize_event_type_value(routed_response.get("event_type"))
        if normalized_event_type is not None:
            routed_response["event_type"] = normalized_event_type

        yield routed_response, current_metadata_hash

    @staticmethod
    def _normalize_event_type_value(event_type: Any) -> str | None:
        """Normalize event type values to plain strings for downstream consumers.

        Delegates to SSEChunkTransformer.normalize_event_type_value for shared implementation.

        Args:
            event_type (Any): The event type to normalize.

        Returns:
            str | None: The normalized event type as a string, or None if invalid.
        """
        return SSEChunkTransformer.normalize_event_type_value(event_type)

    @staticmethod
    def _normalize_metadata_enums(
        response: dict[str, Any],
        previous_metadata_hash: str | None = None,
        metadata_cache: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        """Convert enum keys and values in metadata to strings for proper JSON serialization.

        Args:
            response: The response dictionary that may contain enum values in metadata.
            previous_metadata_hash: Hash of previously normalized metadata to avoid unnecessary work.
            metadata_cache: Optional cache mapping metadata hashes to normalized metadata dicts.

        Returns:
            Tuple of (normalized_response, new_metadata_hash) where new_metadata_hash
            is None if no normalization was needed.
        """
        if not isinstance(response, dict):
            return response, None

        normalized_response = response.copy()
        current_metadata = normalized_response.get("metadata")

        if not isinstance(current_metadata, dict):
            return normalized_response, None

        current_hash = A2AConnector._compute_metadata_hash(current_metadata)

        if previous_metadata_hash == current_hash:
            A2AConnector._handle_cached_metadata(normalized_response, current_hash, metadata_cache)
            return normalized_response, None

        return A2AConnector._handle_new_metadata(normalized_response, current_metadata, current_hash, metadata_cache)

    @staticmethod
    def _compute_metadata_hash(metadata: dict[str, Any]) -> str:
        """Compute hash of metadata for comparison and caching.

        Args:
            metadata (dict[str, Any]): The metadata to hash.

        Returns:
            str: The computed hash string.
        """
        metadata_items = []
        for k, v in metadata.items():
            key_str = k.value if hasattr(k, "value") else str(k)
            val_str = v.value if hasattr(v, "value") else str(v)
            metadata_items.append(f"{key_str}:{val_str}")
        metadata_str = "|".join(sorted(metadata_items))
        return hashlib.sha256(metadata_str.encode()).hexdigest()

    @staticmethod
    def _handle_cached_metadata(
        response: dict[str, Any],
        metadata_hash: str,
        metadata_cache: dict[str, dict[str, Any]] | None,
    ) -> None:
        """Handle case where metadata hasn't changed - use cached or compute new.

        Args:
            response: The response dictionary to update with normalized metadata.
            metadata_hash: Hash of the original metadata for cache lookup.
            metadata_cache: Optional cache dictionary to store/retrieve normalized metadata.
        """
        if metadata_cache and metadata_hash in metadata_cache:
            response["metadata"] = metadata_cache[metadata_hash]
        else:
            metadata = response["metadata"]
            normalized_metadata = A2AConnector._normalize_metadata_value(metadata)
            response["metadata"] = normalized_metadata
            if metadata_cache is not None:
                metadata_cache[metadata_hash] = normalized_metadata

    @staticmethod
    def _handle_new_metadata(
        response: dict[str, Any],
        metadata: dict[str, Any],
        metadata_hash: str,
        metadata_cache: dict[str, dict[str, Any]] | None,
    ) -> tuple[dict[str, Any], str]:
        """Handle case where metadata has changed - normalize and cache.

        Args:
            response: The response dictionary to update with normalized metadata.
            metadata: The new metadata to normalize and cache.
            metadata_hash: Hash of the metadata for cache storage.
            metadata_cache: Optional cache dictionary to store normalized metadata.

        Returns:
            Tuple of (updated_response, metadata_hash).
        """
        normalized_metadata = A2AConnector._normalize_metadata_value(metadata)
        response["metadata"] = normalized_metadata

        if metadata_cache is not None:
            metadata_cache[metadata_hash] = normalized_metadata

        return response, metadata_hash

    @staticmethod
    def _normalize_metadata_value(value: Any) -> Any:
        """Recursively convert enum instances to their serializable value.

        Delegates to SSEChunkTransformer.normalize_metadata_enums for shared implementation.

        Args:
            value: The value to normalize. Can be an enum, dict, list, tuple, set, or other type.

        Returns:
            The normalized value with enums converted to their values and nested structures processed.
        """
        return SSEChunkTransformer.normalize_metadata_enums(value)

    @staticmethod
    def _process_stream_chunk(res_data: Any, artifact_tracker: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single chunk from the stream based on its type.

        This method handles A2A protocol types (TaskArtifactUpdateEvent, TaskStatusUpdateEvent, Task)
        which are different from A2AEvent objects processed by SSEChunkTransformer. The separation
        is intentional as these are different input types at different protocol layers.

        Args:
            res_data: The response data from the stream (A2A protocol types).
            artifact_tracker: Artifact tracking collections.

        Returns:
            Processed response dictionary or None if no response should be yielded.
        """
        # Artifact updates are now handled first and yielded immediately
        if isinstance(res_data, TaskArtifactUpdateEvent):
            return A2AConnector._handle_artifact_update_event(res_data, artifact_tracker)

        elif isinstance(res_data, TaskStatusUpdateEvent):
            return A2AConnector._handle_task_state_update(res_data)

        elif isinstance(res_data, Task):
            return A2AConnector._process_task_object(res_data, artifact_tracker["collected_artifacts"])

        elif isinstance(res_data, Message):
            return A2AConnector._process_message_object(res_data)

        return None

    @staticmethod
    def _create_error_response(error_type: str, message: str) -> dict[str, Any]:
        """Create a standardized error response.

        Args:
            error_type: Type of error that occurred.
            message: Error message description.

        Returns:
            Standardized error response dictionary (legacy minimal format).
        """
        return {
            "status": "error",
            "task_state": "failed",
            "content": message,
            "event_type": A2AStreamEventType.ERROR.value,
        }

    @staticmethod
    def _create_artifact_hash(artifact_response: dict[str, Any]) -> str:
        """Create a hash for artifact deduplication.

        Delegates to SSEChunkTransformer.create_artifact_hash for shared implementation.

        Args:
            artifact_response: The artifact response dictionary.

        Returns:
            A hash string for deduplication.
        """
        return SSEChunkTransformer.create_artifact_hash(artifact_response)
