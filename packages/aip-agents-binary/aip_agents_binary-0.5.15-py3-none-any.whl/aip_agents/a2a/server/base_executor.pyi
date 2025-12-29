from _typeshed import Incomplete
from a2a.server.agent_execution import AgentExecutor as A2ASDKExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from abc import ABC, abstractmethod
from aip_agents.types import A2AEvent as A2AEvent, A2AStreamEventType as A2AStreamEventType
from aip_agents.utils import serialize_references_for_metadata as serialize_references_for_metadata
from aip_agents.utils.artifact_helpers import ArtifactHandler as ArtifactHandler
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata_helper import MetadataFieldKeys as MetadataFieldKeys
from collections.abc import Callable as Callable
from dataclasses import dataclass
from typing import Any

logger: Incomplete

@dataclass
class StatusUpdateParams:
    """Parameters for status updates."""
    metadata: dict[str, Any] | None = ...
    final: bool = ...
    task_id: str | None = ...
    context_id: str | None = ...

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
    @abstractmethod
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
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
