"""Langflow API client for HTTP communication with Langflow API.

This module provides the LangflowApiClient class that handles all HTTP communication
with Langflow APIs, including both streaming and non-streaming execution modes.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import json
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from aip_agents.clients.langflow.types import LangflowEventType
from aip_agents.schema.agent import HttpxClientOptions
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


DEFAULT_LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "https://langflow.obrol.id")
MAX_PAGE_SIZE = 1000


class LangflowApiClient:
    """HTTP client for Langflow API with streaming and non-streaming support.

    This client handles all communication with Langflow APIs, including:
    - Non-streaming execution
    - Server-Sent Events (SSE) streaming
    - Session management for conversation continuity
    - Error handling and retries
    - Credential management
    """

    def __init__(
        self,
        flow_id: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        httpx_client_options: "HttpxClientOptions" = None,
    ):
        """Initialize the Langflow API client.

        Args:
            flow_id: The unique identifier of the Langflow flow to execute.
            base_url: The base URL of the Langflow API server.
            api_key: The API key for Langflow authentication.
            httpx_client_options: HTTP client configuration options for httpx, including timeout.
        """
        self.flow_id = flow_id
        self.base_url = self._resolve_base_url(base_url)
        self.api_key = self._resolve_api_key(api_key)
        self.sessions: dict[str, str] = {}

        # Get client options from config or use defaults
        if not isinstance(httpx_client_options, HttpxClientOptions):
            client_options = HttpxClientOptions()
        else:
            client_options = httpx_client_options

        self.client_kwargs = {
            "timeout": httpx.Timeout(client_options.timeout),
            "trust_env": client_options.trust_env,
            "follow_redirects": client_options.follow_redirects,
        }

        logger.info(f"Initialized Langflow API client for flow {self.flow_id} at {self.base_url}")

    def _resolve_base_url(self, base_url: str | None) -> str:
        """Resolve the base URL from config or environment variables.

        Args:
            base_url: Base URL from config.

        Returns:
            Resolved base URL.
        """
        if base_url:
            return base_url.rstrip("/")

        return DEFAULT_LANGFLOW_BASE_URL.rstrip("/")

    def _resolve_api_key(self, api_key: str | None) -> str:
        """Resolve the API key from config or environment variables.

        Args:
            api_key: API key from config.

        Returns:
            Resolved API key.

        Raises:
            ValueError: If no API key is found.
        """
        if api_key:
            return api_key

        env_key = os.getenv("LANGFLOW_API_KEY")
        if env_key:
            return env_key

        raise ValueError("LANGFLOW_API_KEY not found. Please provide via config or environment variable.")

    def _build_url(self, flow_id: str | None = None, stream: bool = False) -> str:
        """Build the API URL for flow execution.

        Args:
            flow_id: Optional flow ID to use in the URL. If None, uses the instance flow_id.
            stream: Whether to build URL for streaming mode.

        Returns:
            Complete API URL.
        """
        base_flow_url = f"{self.base_url}/api/v1/run/{self._ensure_flow_id(flow_id)}"
        if stream:
            return f"{base_flow_url}?stream=true"
        return base_flow_url

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": self.api_key,
        }

    def _build_payload(self, input_value: str, session_id: str | None = None) -> dict[str, Any]:
        """Build the request payload for Langflow API.

        Args:
            input_value: The user input to send to the flow.
            session_id: Optional session ID for conversation continuity.

        Returns:
            Dictionary containing the request payload.
        """
        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "input_value": input_value,
        }

        if session_id:
            payload["session_id"] = session_id

        return payload

    def get_or_create_session(self, thread_id: str | None = None) -> str:
        """Get existing session ID or create a new one.

        Args:
            thread_id: Optional thread ID for session mapping.

        Returns:
            Session ID for the conversation.
        """
        if thread_id and thread_id in self.sessions:
            return self.sessions[thread_id]

        session_id = str(uuid.uuid4())
        if thread_id:
            self.sessions[thread_id] = session_id
            logger.debug(f"Created new session {session_id} for thread {thread_id}")
        else:
            logger.debug(f"Created new session {session_id}")

        return session_id

    def _ensure_flow_id(self, flow_id: str | None) -> str:
        """Ensure the flow ID is set.

        Args:
            flow_id: The flow ID to ensure.

        Returns:
            The flow ID.

        Raises:
            ValueError: If the flow ID is not set.
        """
        flow_id = flow_id or self.flow_id
        if not flow_id:
            raise ValueError("Flow ID is required")
        return flow_id

    async def call_flow(
        self, input_value: str, session_id: str | None = None, flow_id: str | None = None, **_: Any
    ) -> dict[str, Any]:
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
        url = self._build_url(flow_id=flow_id, stream=False)
        headers = self._build_headers()
        payload = self._build_payload(input_value, session_id)

        logger.debug(f"Calling flow {self._ensure_flow_id(flow_id)} with non-streaming mode")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                response_data = response.json()

                # Return content or fallback
                return response_data

            except httpx.HTTPError as e:
                logger.error(f"HTTP error during flow execution: {e}")
                raise
            except Exception as e:
                logger.error(f"Error parsing flow response: {e}")
                raise ValueError(f"Failed to parse flow response: {e}") from e

    async def stream_flow(
        self, input_value: str, session_id: str | None = None, flow_id: str | None = None, **_: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
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
        url = self._build_url(flow_id=flow_id, stream=True)
        headers = self._build_headers()
        payload = self._build_payload(input_value, session_id)

        logger.debug(f"Calling flow {self._ensure_flow_id(flow_id)} with streaming mode")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                event_data = json.loads(line)
                                yield event_data
                            except json.JSONDecodeError:
                                logger.warning(f"Skipping non-JSON line: {line}")
                                continue

            except httpx.HTTPError as e:
                logger.error(f"HTTP error during streaming: {e}")
                raise
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                raise

    def parse_stream_event(self, event_data: dict[str, Any]) -> dict[str, Any] | None:
        """Parse a single streaming event from Langflow.

        Args:
            event_data: Raw event data from Langflow streaming response.

        Returns:
            Parsed event dictionary or None if event should be skipped.
        """
        try:
            event_type = event_data.get("event")

            if event_type == LangflowEventType.ADD_MESSAGE:
                message_data = event_data.get("data", {})
                sender = message_data.get("sender", "Unknown")
                text = message_data.get("text", "")
                return {"type": LangflowEventType.ADD_MESSAGE, "sender": sender, "content": text, "raw": event_data}

            elif event_type == LangflowEventType.END:
                return {
                    "type": LangflowEventType.END,
                    "content": "Stream completed",
                    "final": True,
                    "raw": event_data,
                }

            else:
                return {
                    "type": LangflowEventType.UNKNOWN,
                    "event_type": event_type,
                    "content": str(event_data),
                    "raw": event_data,
                }

        except Exception as e:
            logger.warning(f"Error parsing stream event: {e}")
            return None

    def clear_session(self, thread_id: str) -> None:
        """Clear session for a specific thread.

        Args:
            thread_id: Thread ID to clear session for.
        """
        if thread_id in self.sessions:
            del self.sessions[thread_id]
            logger.debug(f"Cleared session for thread {thread_id}")

    def clear_all_sessions(self) -> None:
        """Clear all stored sessions."""
        self.sessions.clear()
        logger.debug("Cleared all sessions")

    async def get_flows(  # noqa: PLR0913
        self,
        project_id: str | None = None,
        remove_example_flows: bool = False,
        components_only: bool = False,
        header_flows: bool = False,
        get_all: bool = True,
        page: int = 1,
        size: int = 50,
    ) -> list[dict[str, Any]]:
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
        self._validate_pagination_params(page, size)

        url = f"{self.base_url}/api/v1/flows/"
        headers = self._build_headers()

        # Use exact parameter names from official docs
        params = {
            "remove_example_flows": str(remove_example_flows).lower(),
            "components_only": str(components_only).lower(),
            "get_all": str(get_all).lower(),
            "header_flows": str(header_flows).lower(),
            "page": page,
            "size": size,
        }

        if project_id:
            params["project_id"] = project_id

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                try:
                    response_data = response.json()
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.warning(f"Response body: {response.text[:500]}...")
                    raise ValueError(f"Failed to parse flows response: {e}") from e

                if isinstance(response_data, list):
                    return response_data
                elif isinstance(response_data, dict) and "flows" in response_data:
                    return response_data["flows"]
                else:
                    logger.warning(f"Unexpected response format: {type(response_data)}")
                    if isinstance(response_data, dict):
                        logger.warning(f"Response keys: {list(response_data.keys())}")
                    else:
                        logger.warning("Response keys: Not a dict")
                    return []

            except httpx.HTTPError as e:
                logger.error(f"HTTP error retrieving flows: {e}")
                logger.error(f"Response status: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during flows request: {e}")
                raise ValueError(f"Unexpected error during flows request: {e}") from e

    def _validate_pagination_params(self, page: int, size: int) -> None:
        """Validate pagination parameters for flow retrieval.

        Args:
            page: Page number for pagination.
            size: Number of flows per page.

        Raises:
            ValueError: If page or size parameters are invalid.
        """
        if page < 1:
            raise ValueError("page must be >= 1")
        if size < 1:
            raise ValueError("size must be >= 1")
        if size > MAX_PAGE_SIZE:
            logger.warning(f"Large page size requested: {size}")

    async def get_all_flows(
        self,
        project_id: str | None = None,
        remove_example_flows: bool = False,
        components_only: bool = False,
        header_flows: bool = False,
    ) -> list[dict[str, Any]]:
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
        return await self.get_flows(
            project_id=project_id,
            remove_example_flows=remove_example_flows,
            components_only=components_only,
            header_flows=header_flows,
            get_all=True,
        )

    async def health_check(self) -> bool:
        """Check if the Langflow API is accessible.

        Returns:
            True if the API is accessible, False otherwise.
        """
        try:
            async with httpx.AsyncClient(**self.client_kwargs) as client:
                response = await client.get(f"{self.base_url}/health", headers={"x-api-key": self.api_key})
                return response.status_code == httpx.codes.OK
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
