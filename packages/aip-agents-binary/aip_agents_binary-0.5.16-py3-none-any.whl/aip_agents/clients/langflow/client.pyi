from _typeshed import Incomplete
from aip_agents.clients.langflow.types import LangflowEventType as LangflowEventType
from aip_agents.schema.agent import HttpxClientOptions as HttpxClientOptions
from aip_agents.utils.logger import get_logger as get_logger
from collections.abc import AsyncGenerator
from typing import Any

logger: Incomplete
DEFAULT_LANGFLOW_BASE_URL: Incomplete
MAX_PAGE_SIZE: int

class LangflowApiClient:
    """HTTP client for Langflow API with streaming and non-streaming support.

    This client handles all communication with Langflow APIs, including:
    - Non-streaming execution
    - Server-Sent Events (SSE) streaming
    - Session management for conversation continuity
    - Error handling and retries
    - Credential management
    """
    flow_id: Incomplete
    base_url: Incomplete
    api_key: Incomplete
    sessions: dict[str, str]
    client_kwargs: Incomplete
    def __init__(self, flow_id: str | None = None, base_url: str | None = None, api_key: str | None = None, httpx_client_options: HttpxClientOptions = None) -> None:
        """Initialize the Langflow API client.

        Args:
            flow_id: The unique identifier of the Langflow flow to execute.
            base_url: The base URL of the Langflow API server.
            api_key: The API key for Langflow authentication.
            httpx_client_options: HTTP client configuration options for httpx, including timeout.
        """
    def get_or_create_session(self, thread_id: str | None = None) -> str:
        """Get existing session ID or create a new one.

        Args:
            thread_id: Optional thread ID for session mapping.

        Returns:
            Session ID for the conversation.
        """
    async def call_flow(self, input_value: str, session_id: str | None = None, flow_id: str | None = None, **_: Any) -> dict[str, Any]:
        """Execute Langflow flow without streaming.

        Args:
            input_value: The user input to send to the flow.
            session_id: Optional session ID for conversation continuity.
            flow_id: Optional flow ID to execute. If None, uses the instance flow_id.
            **_: Additional keyword arguments.

        Returns:
            The response from the flow execution.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
            ValueError: If the response cannot be parsed.
        """
    async def stream_flow(self, input_value: str, session_id: str | None = None, flow_id: str | None = None, **_: Any) -> AsyncGenerator[dict[str, Any], None]:
        """Execute Langflow flow with streaming.

        Args:
            input_value: The user input to send to the flow.
            session_id: Optional session ID for conversation continuity.
            flow_id: Optional flow ID to execute. If None, uses the instance flow_id.
            **_: Additional keyword arguments.

        Yields:
            Parsed streaming events from the Langflow API.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
            ValueError: If streaming events cannot be parsed.
        """
    def parse_stream_event(self, event_data: dict[str, Any]) -> dict[str, Any] | None:
        """Parse a single streaming event from Langflow.

        Args:
            event_data: Raw event data from Langflow streaming response.

        Returns:
            Parsed event dictionary or None if event should be skipped.
        """
    def clear_session(self, thread_id: str) -> None:
        """Clear session for a specific thread.

        Args:
            thread_id: Thread ID to clear session for.
        """
    def clear_all_sessions(self) -> None:
        """Clear all stored sessions."""
    async def get_flows(self, project_id: str | None = None, remove_example_flows: bool = False, components_only: bool = False, header_flows: bool = False, get_all: bool = True, page: int = 1, size: int = 50) -> list[dict[str, Any]]:
        """Retrieve flows from Langflow API with full control over parameters.

        Based on the official API docs: https://docs.langflow.org/api-flows
        Uses the exact parameter format from the documentation.

        Args:
            project_id: Optional project ID to filter flows.
            remove_example_flows: Whether to exclude example flows. Defaults to False.
            components_only: Whether to return only components. Defaults to False.
            header_flows: Whether to return only flow headers. Defaults to False.
            get_all: Whether to return all flows (ignores pagination). Defaults to True.
            page: Page number for pagination (ignored if get_all=True). Defaults to 1.
            size: Number of flows per page (ignored if get_all=True). Defaults to 50.

        Returns:
            List of flows or flow headers from the Langflow API.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
            ValueError: If the response cannot be parsed or invalid parameters provided.
        """
    async def get_all_flows(self, project_id: str | None = None, remove_example_flows: bool = False, components_only: bool = False, header_flows: bool = False) -> list[dict[str, Any]]:
        """Convenience method to get ALL flows using the backend's get_all=true feature.

        This method is a simple wrapper around get_flows() with get_all=True,
        which uses the Langflow backend's ability to return all flows in one request.

        Args:
            project_id: Optional project ID to filter flows.
            remove_example_flows: Whether to exclude example flows. Defaults to False.
            components_only: Whether to return only components. Defaults to False.
            header_flows: Whether to return only flow headers. Defaults to False.

        Returns:
            List of all flows from the Langflow API.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
            ValueError: If the response cannot be parsed.
        """
    async def health_check(self) -> bool:
        """Check if the Langflow API is accessible.

        Returns:
            True if the API is accessible, False otherwise.
        """
