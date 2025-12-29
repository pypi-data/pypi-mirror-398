"""Tool to execute web automation tasks using browser-use framework.

This tool provides browser automation capabilities using the browser-use framework
with Steel session management and streaming support.

Streaming Contract

The tool emits streaming events with the following structure:

Thinking Markers
- **thinking_start**: Indicates beginning of a thinking phase
```json
{
    "event_type": "status_update",
    "content": "Thinking start",
    "thinking_and_activity_info": {
        "data_type": "thinking_start",
        "data_value": "",
        "id": "default_thinking_id"
    }
}
```

- thinking: Contains actual thinking content
```json
{
    "event_type": "tool_result",
    "content": "Completed go_to_url, extract_structured_data",
    "thinking_and_activity_info": {
        "data_type": "thinking",
        "data_value": "**Starting fresh with the task...**",
        "id": "default_thinking_id"
    }
}
```

- thinking_end: Marks end of thinking phase
```json
{
    "event_type": "status_update",
    "content": "Thinking end",
    "thinking_and_activity_info": {
        "data_type": "thinking_end",
        "data_value": "",
        "id": "default_thinking_id"
    }
}
```

Iframe Activities

- Streaming URL: Live browser session URL
```json
{
    "event_type": "status_update",
    "content": "Receive streaming URL",
    "thinking_and_activity_info": {
        "data_type": "activity",
        "data_value": "{'type': 'iframe', 'message': 'https://steel.dev/...'}"
    }
}
```

- Recording URL: Session recording URL
```json
{
    "event_type": "status_update",
    "content": "Receive recording URL",
    "thinking_and_activity_info": {
        "data_type": "activity",
        "data_value": "{'type': 'iframe', 'message': 'http://minio/...'}"
    }
}
```

Event Flow

1. Initialize session → Yield streaming URL
2. For each agent step:
    - thinking_start
    - tool_result with thinking content (emitted between the markers)
    - thinking_end
3. Complete → Yield recording URL

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Saul Sayerz (saul.sayerz@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)

References:
    https://github.com/GDP-ADMIN/glair-rnd/tree/main/browser-use/steeldev
"""

import asyncio
import json
from collections.abc import Callable
from typing import Any, Literal

from browser_use import Agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from steel import Steel
from steel.types import Session

from aip_agents.tools.browser_use import session_errors
from aip_agents.tools.browser_use.action_parser import ActionParser
from aip_agents.tools.browser_use.llm_config import build_browser_use_llm, configure_browser_use_environment
from aip_agents.tools.browser_use.schemas import BrowserUseToolConfig, BrowserUseToolInput
from aip_agents.tools.browser_use.session import BrowserSession
from aip_agents.tools.browser_use.steel_session_recording import SteelSessionRecorder
from aip_agents.tools.browser_use.streaming import (
    create_error_response,
    create_step_response,
    generate_step_content,
    generate_thinking_message,
    yield_iframe_activity,
    yield_status_message,
    yield_thinking_marker,
)
from aip_agents.tools.browser_use.structured_data_parser import detect_structured_data_failure
from aip_agents.tools.browser_use.types import (
    BrowserUseFatalError,
    RetryDecision,
    StreamingResponse,
    StreamingState,
    ToolCallInfo,
)
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserUseTool(BaseTool):
    """Tool to execute web automation tasks using browser-use framework.

    This tool provides step-by-step execution of browser automation tasks with detailed
    logging of intermediate steps, including the agent's thinking process, goals, and
    results at each step.
    """

    name: str = "browser_use_tool"
    description: str = (
        "Execute web automation tasks using browser-use framework. "
        "Connects browser-use agent, and runs the specified task step by step. "
        "Provides detailed logging of intermediate steps including agent thinking and goals. "
        "Returns the task execution results with step-by-step information."
    )
    args_schema: type[BaseModel] = BrowserUseToolInput
    tool_config_schema: type[BaseModel] = BrowserUseToolConfig

    MAX_SESSION_RELEASE_RETRIES: int = 3
    SESSION_RELEASE_SLEEP_TIME_IN_S: int = 10

    def _run(self, task: str, config: RunnableConfig | None = None) -> str:
        """Run the tool synchronously.

        Args:
            task (str): The task prompt for the AI agent to execute in the browser.
            config (RunnableConfig): RunnableConfig containing tool configuration.

        Returns:
            str: The result of the task execution or an error message if the task fails.
        """
        return asyncio.run(self._arun(task, config))

    async def _arun(self, task: str, config: RunnableConfig | None = None) -> str:
        """Execute a web automation task using browser-use asynchronously.

        This method creates a Steel browser session, initializes a browser-use agent with
        the specified task, and executes the automation. It handles session cleanup and
        error handling.

        Args:
            task (str): The task prompt for the AI agent to execute in the browser.
            config (RunnableConfig): RunnableConfig containing tool configuration.

        Returns:
            str: A success message with the task result, or an error message if the task
                execution fails. The result includes the final output from the browser-use
                agent's execution.

        Raises:
            Exception: Any exception that occurs during task execution will be caught
                and returned as an error message string.
        """
        tool_config = self._get_tool_config(config)

        if not tool_config.browser_use_llm_openai_api_key:
            return self._log_and_return("warning", "Browser-use LLM OpenAI API key is required.")
        if not tool_config.browser_use_page_extraction_llm_openai_api_key:
            return self._log_and_return("warning", "Browser-use Page Extraction OpenAI API key is required.")
        if not tool_config.steel_api_key:
            return self._log_and_return("warning", "Steel API key is required.")

        client = self._init_steel_client(tool_config)

        session = None
        try:
            session = self._create_steel_session(client, tool_config)
            cdp_url = self._construct_cdp_url(session.id, tool_config)
            agent = self._create_browser_use_agent(task, cdp_url, tool_config)
            result = await agent.run()
            return self._log_and_return("info", f"Task completed successfully!\nResult: {result.final_result()}")

        except Exception as e:
            return self._log_and_return("warning", f"Error during task execution: {str(e)}")
        finally:
            await self._release_session(session, client)

    def _get_tool_config(self, config: RunnableConfig | None) -> BrowserUseToolConfig:
        """Get the tool configuration.

        Args:
            config (RunnableConfig): RunnableConfig containing tool configuration.

        Returns:
            BrowserUseToolConfig: The tool configuration.
        """
        tool_config: BrowserUseToolConfig | None = None
        if hasattr(self, "get_tool_config") and callable(self.get_tool_config):
            tool_config = self.get_tool_config(config)
        if not tool_config:
            tool_config = BrowserUseToolConfig()
        return tool_config

    def _log_and_return(self, level: Literal["info", "warning"], message: str) -> str:
        """Log a message and return it.

        Args:
            level (Literal["info", "warning"]): The log level.
            message (str): The message to log and return.

        Returns:
            str: The logged message.
        """
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        return message

    def _init_steel_client(self, tool_config: BrowserUseToolConfig) -> Steel:
        """Initialize the Steel client.

        Args:
            tool_config: Tool configuration containing Steel settings.

        Returns:
            Steel: The Steel client.
        """
        return Steel(steel_api_key=tool_config.steel_api_key, base_url=tool_config.steel_base_url)

    def _create_steel_session(self, client: Steel, tool_config: BrowserUseToolConfig) -> Session:
        """Create the Steel session.

        Args:
            client: The Steel client.
            tool_config: Tool configuration containing Steel session settings.

        Returns:
            Session: The Steel session.
        """
        return client.sessions.create(use_proxy=False, api_timeout=tool_config.steel_timeout_in_ms)

    def _construct_cdp_url(self, session_id: str, tool_config: BrowserUseToolConfig) -> str:
        """Construct the CDP URL for browser connection.

        Args:
            session_id: The Steel session ID.
            tool_config: Tool configuration containing Steel WebSocket URL.

        Returns:
            str: The CDP URL.
        """
        return f"{tool_config.steel_ws_url}?apiKey={tool_config.steel_api_key}&sessionId={session_id}"

    def _create_browser_use_agent(self, task: str, cdp_url: str, tool_config: BrowserUseToolConfig) -> Agent:
        """Create OpenAI LLM and browser-use agent bound to the provided task and CDP URL.

        Args:
            task: The task prompt for the AI agent
            cdp_url: The CDP URL for the browser session
            tool_config: Tool configuration containing OpenAI model settings

        Returns:
            Agent: The browser-use agent
        """
        llm = build_browser_use_llm(
            model=tool_config.browser_use_llm_openai_model,
            reasoning_effort=tool_config.browser_use_llm_openai_reasoning_effort,
            temperature=tool_config.browser_use_llm_openai_temperature,
            api_key=tool_config.browser_use_llm_openai_api_key,
            base_url=tool_config.browser_use_llm_openai_base_url,
        )

        page_extraction_llm = build_browser_use_llm(
            model=tool_config.browser_use_page_extraction_llm_openai_model,
            reasoning_effort=tool_config.browser_use_page_extraction_llm_openai_reasoning_effort,
            temperature=tool_config.browser_use_page_extraction_llm_openai_temperature,
            api_key=tool_config.browser_use_page_extraction_llm_openai_api_key,
            base_url=tool_config.browser_use_page_extraction_llm_openai_base_url,
        )

        browser_session = BrowserSession(cdp_url=cdp_url)
        # Mark the proxy-created session as owned so browser-use does not clone it with warnings.
        setattr(browser_session, "_owns_browser_resources", True)

        configure_browser_use_environment(
            enable_cloud_sync=tool_config.browser_use_enable_cloud_sync,
            logging_level=tool_config.browser_use_logging_level,
        )

        return Agent(
            task=task,
            llm=llm,
            page_extraction_llm=page_extraction_llm,
            browser_session=browser_session,
            extend_system_message=tool_config.browser_use_extend_system_message,
            vision_detail_level=tool_config.browser_use_vision_detail_level,
            llm_timeout=tool_config.browser_use_llm_timeout_in_s,
            step_timeout=tool_config.browser_use_step_timeout_in_s,
        )

    def _create_agent_session(
        self,
        client: Steel,
        recorder: SteelSessionRecorder,
        tool_config: BrowserUseToolConfig,
        task: str,
    ) -> tuple[Session, StreamingState, Agent]:
        """Provision a Steel session, streaming state, and browser-use agent.

        Args:
            client: Initialized Steel SDK client.
            recorder: Recorder responsible for generating session recordings.
            tool_config: Tool configuration containing browser-use settings.
            task: The textual task prompt the agent must execute.

        Returns:
            tuple[Session, StreamingState, Agent]: Provisioned Steel session,
            streaming state metadata, and browser-use agent instance.
        """
        session = self._create_steel_session(client, tool_config)
        streaming_state = self._create_streaming_state(session, recorder)
        cdp_url = self._construct_cdp_url(session.id, tool_config)
        agent = self._create_browser_use_agent(task, cdp_url, tool_config)
        return session, streaming_state, agent

    async def _retry_stream_events(self, task: str, tool_config: BrowserUseToolConfig):
        """Yield streaming events while automatically retrying Steel sessions.

        Args:
            task: Textual task prompt.
            tool_config: Tool configuration containing Steel/OpenAI settings.

        Yields:
            dict: Streaming events produced by the browser-use agent.
        """
        client = self._init_steel_client(tool_config)
        recorder = SteelSessionRecorder(tool_config.steel_base_url, tool_config.steel_api_key)

        retry_state = self._init_retry_state(tool_config)

        while True:
            state_holder: dict[str, StreamingState | None] = {"state": None}
            store_state = self._make_state_store(state_holder)

            try:
                async for event in self._session_event_stream(
                    client,
                    recorder,
                    tool_config,
                    task,
                    store_state,
                ):
                    yield event
                return

            except Exception as exc:  # pragma: no cover - defensive orchestration
                async for event in self._emit_retry_exception(
                    exc,
                    state_holder,
                    recorder,
                    tool_config,
                    retry_state,
                ):
                    yield event

    def _init_retry_state(self, tool_config: BrowserUseToolConfig) -> dict[str, int]:
        """Initialize retry state tracking.

        Args:
            tool_config: Tool configuration containing retry settings.

        Returns:
            Dictionary with retry state counters.
        """
        return {
            "retries_remaining": max(0, tool_config.browser_use_max_session_retries),
            "attempted_retries": 0,
        }

    async def _handle_fatal_error_during_retry(
        self,
        fatal_error: BrowserUseFatalError,
        state_holder: dict[str, StreamingState | None],
        tool_config: BrowserUseToolConfig,
        retry_state: dict[str, int],
    ):
        """Handle fatal errors during retry attempts.

        Args:
            fatal_error: The fatal error that occurred.
            state_holder: Container for current streaming state.
            tool_config: Tool configuration for retry logic.
            retry_state: Current retry counters and state.
        """
        streaming_state = state_holder["state"]
        decision, pending_event = await self._handle_retryable_fatal_error(
            fatal_error,
            streaming_state,
            retry_state["retries_remaining"],
            retry_state["attempted_retries"],
            tool_config,
        )
        if pending_event:
            yield pending_event
        retry_state["retries_remaining"], retry_state["attempted_retries"] = self._apply_retry_decision(
            fatal_error, decision
        )

    async def _handle_cancellation_during_retry(
        self,
        state_holder: dict[str, StreamingState | None],
        recorder: SteelSessionRecorder,
    ):
        """Handle cancellation during retry attempts.

        Args:
            state_holder: Container for current streaming state.
            recorder: Session recorder for cleanup operations.
        """
        streaming_state = state_holder["state"]
        if streaming_state:
            self._finalize_streaming_on_cancel(streaming_state, recorder)
            if streaming_state.recording_url:
                yield yield_iframe_activity(streaming_state.recording_url, "Receive recording URL")

    async def _handle_unexpected_error_during_retry(
        self,
        exc: Exception,
        state_holder: dict[str, StreamingState | None],
    ):
        """Handle unexpected errors during retry attempts.

        Args:
            exc: The unexpected exception that occurred.
            state_holder: Container for current streaming state.
        """
        streaming_state = state_holder["state"]
        error_url = streaming_state.recording_url if streaming_state else ""
        yield create_error_response(f"Error during task execution: {str(exc)}", error_url)

    @staticmethod
    def _make_state_store(state_holder: dict[str, StreamingState | None]) -> Callable[[StreamingState], None]:
        """Return a callback that records the latest streaming state.

        Args:
            state_holder: Mutable container storing the latest streaming state.
        """

        def store(streaming_state: StreamingState) -> None:
            """Persist the latest streaming state in the shared holder.

            Args:
                streaming_state: Streaming state emitted by browser-use callbacks.
            """
            state_holder["state"] = streaming_state

        return store

    def _apply_retry_decision(
        self, fatal_error: BrowserUseFatalError, decision: RetryDecision | None
    ) -> tuple[int, int]:
        """Update retry counters or re-raise when no retries remain.

        Args:
            fatal_error: The fatal error that triggered the retry decision.
            decision: The retry decision containing retry counters, or None if no retries available.

        Returns:
            tuple[int, int]: A tuple containing (retries_remaining, attempted_retries).
        """
        if not decision:
            raise fatal_error
        return decision.retries_remaining, decision.attempted_retries

    async def _emit_retry_exception(
        self,
        exc: Exception,
        state_holder: dict[str, StreamingState | None],
        recorder: SteelSessionRecorder,
        tool_config: BrowserUseToolConfig,
        retry_state: dict[str, int],
    ):
        """Normalize retry exception handling and yield resulting events.

        Args:
            exc: Exception raised during the streaming attempt.
            state_holder: Container for current streaming state.
            recorder: Session recorder for cleanup operations.
            tool_config: Tool configuration containing retry settings.
            retry_state: Mutable retry counters.
        """
        if isinstance(exc, asyncio.CancelledError):
            async for event in self._handle_cancellation_during_retry(state_holder, recorder):
                yield event
            raise exc

        if isinstance(exc, BrowserUseFatalError):
            async for event in self._handle_fatal_error_during_retry(exc, state_holder, tool_config, retry_state):
                yield event
            return

        async for event in self._handle_unexpected_error_during_retry(exc, state_holder):
            yield event
        raise BrowserUseFatalError(str(exc)) from exc

    async def _session_event_stream(
        self,
        client: Steel,
        recorder: SteelSessionRecorder,
        tool_config: BrowserUseToolConfig,
        task: str,
        on_state_ready: Callable[[StreamingState], None],
    ):
        """Yield streaming events for a single Steel session attempt.

        Args:
            client: Steel SDK client instance.
            recorder: Steel session recorder.
            tool_config: Tool configuration for the agent.
            task: Task prompt assigned to the agent.
            on_state_ready: Callback invoked when streaming state is initialized.

        Yields:
            dict: Streaming events describing agent progress.
        """
        session: Session | None = None
        streaming_state: StreamingState | None = None
        try:
            session, streaming_state, agent = self._create_agent_session(client, recorder, tool_config, task)
            on_state_ready(streaming_state)
            iframe_event = yield_iframe_activity(streaming_state.debug_url, "Receive streaming URL")
            self._log_stream_event("iframe_start", iframe_event)
            yield iframe_event
            async for event in self._stream_agent_with_markers(agent, streaming_state, recorder):
                self._log_stream_event("agent_event", event)
                yield event
            recording_event = self._recording_event(streaming_state)
            if recording_event:
                self._log_stream_event("recording_event", recording_event)
                yield recording_event
        finally:
            await self._release_session(session, client)

    async def _release_session(self, session: Session | None, client: Steel) -> None:
        """Release a Steel browser session.

        This method attempts to release the provided Steel session.
        It retries the release operation up to MAX_SESSION_RELEASE_RETRIES times, waiting
        SESSION_RELEASE_SLEEP_TIME_IN_S seconds between attempts. If the session is None, the method
        returns immediately.

        Args:
            session (Session | None): The Steel session to release. If None, no action is taken.
            client (Steel): The Steel client used to release the session.
        """
        if not session:
            return

        for attempt in range(self.MAX_SESSION_RELEASE_RETRIES):
            try:
                await asyncio.sleep(self.SESSION_RELEASE_SLEEP_TIME_IN_S)
                client.sessions.release(session.id)
                logger.info(f"Session {session.id} released")
                break
            except Exception as e:
                if attempt == self.MAX_SESSION_RELEASE_RETRIES - 1:
                    logger.warning(f"Failed to release session after {self.MAX_SESSION_RELEASE_RETRIES} attempts: {e}")

    async def arun_streaming(self, task: str = None, config: RunnableConfig | None = None, **kwargs):
        """Execute a web automation task using browser-use asynchronously with streaming output.

        This method creates a Steel browser session, initializes a browser-use agent with
        the specified task, and executes the automation step by step, yielding results
        in streaming fashion. Starts background recording after completion.

        Args:
            task (str, optional): The task prompt for the AI agent to execute in the browser.
                                 If not provided, will attempt to extract from kwargs.
            config (RunnableConfig): RunnableConfig containing tool configuration.
            **kwargs: Additional parameters that may contain the task or other tool-specific arguments.

        Yields:
            dict: Step-by-step results in standardized StreamingResponse format.

        Raises:
            Exception: Any exception that occurs during task execution will be caught
                and yielded as an error message.
        """
        if task is None:
            task = kwargs.get("task")

        tool_config = self._get_tool_config(config)

        missing_key_error = self._missing_api_key_error(tool_config)
        if missing_key_error:
            yield create_error_response(missing_key_error)
            return

        async for event in self._retry_stream_events(task, tool_config):
            yield event

    @staticmethod
    def _missing_api_key_error(tool_config: BrowserUseToolConfig) -> str | None:
        """Return a descriptive error when required API keys are missing.

        Args:
            tool_config: The tool configuration containing API key settings.

        Returns:
            str | None: Error message if API keys are missing, otherwise None.
        """
        if not tool_config.browser_use_llm_openai_api_key:
            return "Browser-use LLM OpenAI API key is required."
        if not tool_config.browser_use_page_extraction_llm_openai_api_key:
            return "Browser-use Page Extraction OpenAI API key is required."
        if not tool_config.steel_api_key:
            return "Steel API key is required."
        return None

    def _create_streaming_state(self, session: Session, recorder: SteelSessionRecorder) -> StreamingState:
        """Build initial streaming state for a Steel session.

        Args:
            session: The Steel browser session to create streaming state for.
            recorder: The Steel session recorder for video capture.

        Returns:
            StreamingState: The initialized streaming state with debug URL, recording URL, and session ID.
        """
        video_filename = recorder.generate_video_filename(session.id)
        recording_url = recorder.minio_storage.get_file_url(video_filename) if recorder.minio_storage else ""
        return StreamingState(debug_url=session.debug_url, recording_url=recording_url, session_id=session.id)

    def _should_retry_session(self, error_message: str, retries_remaining: int) -> bool:
        """Return True when the failure qualifies for an automatic Steel session retry.

        Args:
            error_message: The error message from the failed session.
            retries_remaining: The number of retry attempts still available.

        Returns:
            bool: True if the error is recoverable and retries are available, False otherwise.
        """
        if retries_remaining <= 0:
            return False
        return session_errors.is_recoverable_message(error_message)

    def _build_retry_decision(
        self,
        error_message: str,
        retries_remaining: int,
        attempted_retries: int,
        tool_config: BrowserUseToolConfig,
    ) -> RetryDecision | None:
        """Create a retry decision payload when a Steel session disconnects.

        Args:
            error_message: Message describing the fatal error.
            retries_remaining: Number of retries still allowed.
            attempted_retries: Number of retries already attempted.
            tool_config: Tool configuration containing retry settings.

        Returns:
            RetryDecision | None: A retry decision when the error is recoverable,
            otherwise None.
        """
        if not self._should_retry_session(error_message, retries_remaining):
            return None

        new_retries = retries_remaining - 1
        new_attempts = attempted_retries + 1
        retry_total = tool_config.browser_use_max_session_retries or 1
        retry_message = f"Steel session disconnected. Attempting automatic recovery ({new_attempts}/{retry_total})."
        delay = max(0.0, tool_config.browser_use_session_retry_delay_in_s)
        return RetryDecision(
            retries_remaining=new_retries,
            attempted_retries=new_attempts,
            message=retry_message,
            delay=delay,
        )

    def _recording_event(self, streaming_state: StreamingState | None) -> dict | None:
        """Return an iframe activity event for successful runs.

        Args:
            streaming_state: Current streaming metadata, if available.

        Returns:
            dict | None: Iframe activity event when a recording is available.
        """
        if not streaming_state or streaming_state.terminal_error or not streaming_state.recording_url:
            return None
        return yield_iframe_activity(streaming_state.recording_url, "Receive recording URL")

    async def _handle_retryable_fatal_error(
        self,
        fatal_error: BrowserUseFatalError,
        streaming_state: StreamingState | None,
        retries_remaining: int,
        attempted_retries: int,
        tool_config: BrowserUseToolConfig,
    ) -> tuple[RetryDecision | None, dict | None]:
        """Handle a fatal error by either yielding an error response or scheduling a retry.

        Args:
            fatal_error: The raised fatal exception.
            streaming_state: Current streaming metadata, if any.
            retries_remaining: Number of retries still allowed.
            attempted_retries: Number of retries already attempted.
            tool_config: Tool configuration containing retry settings.

        Returns:
            tuple[RetryDecision | None, dict | None]: Retry decision (None when unrecoverable)
            and a streaming event to emit (error or status).
        """
        decision = self._build_retry_decision(
            str(fatal_error),
            retries_remaining,
            attempted_retries,
            tool_config,
        )
        if not decision:
            error_url = streaming_state.recording_url if streaming_state else ""
            return None, create_error_response(str(fatal_error), error_url)

        status_event = yield_status_message(decision.message)
        self._log_stream_event("retry_status", status_event)
        if decision.delay:
            await asyncio.sleep(decision.delay)
        return decision, status_event

    async def _stream_agent_with_markers(
        self, agent: Agent, streaming_state: StreamingState, recorder: SteelSessionRecorder
    ):
        """Yield agent progress events surrounded by thinking markers.

        Args:
            self: The BrowserUseTool instance.
            agent: The browser-use agent to execute steps with.
            streaming_state: State management for the streaming operation.
            recorder: The Steel session recorder for video capture.

        Yields:
            dict: Streaming events including thinking start/end markers and step results.
        """
        async for stream_item in self._execute_agent_steps_streaming(agent, streaming_state, recorder):
            payload = stream_item["payload"]
            wrap_markers = stream_item.get("wrap_markers", False)
            label = stream_item.get("label", "step_result")

            if wrap_markers:
                start_marker = yield_thinking_marker("start")
                self._log_stream_event(f"{label}_thinking_start", start_marker)
                yield start_marker

                self._log_stream_event(label, payload)
                yield payload

                end_marker = yield_thinking_marker("end")
                self._log_stream_event(f"{label}_thinking_end", end_marker)
                yield end_marker
            else:
                self._log_stream_event(label, payload)
                yield payload

    async def _execute_agent_steps_streaming(
        self, agent: Agent, streaming_state: StreamingState, recorder: SteelSessionRecorder
    ):
        """Execute agent steps one by one and yield intermediate progress in streaming fashion.

        This method uses the take_step approach to execute the agent's task step by step,
        yielding each step's information in a standardized format. Starts background recording after completion.

        Args:
            agent (Agent): The browser-use agent to execute.
            streaming_state (StreamingState): State management for the streaming operation.
            recorder (SteelSessionRecorder): The Steel session recorder.

        Yields:
            dict: Step information in standardized StreamingResponse format.
        """
        while not streaming_state.is_complete:
            events = await self._next_step_events(agent, streaming_state, recorder)
            for event in events:
                yield event
            if streaming_state.is_complete:
                break

    async def _perform_agent_step(
        self, agent: Agent, streaming_state: StreamingState, recorder: SteelSessionRecorder
    ) -> StreamingResponse:
        """Execute a single agent step and return its streaming payload.

        Args:
            agent: The browser-use agent currently executing the plan.
            streaming_state: Mutable state tracking streaming progress and errors.
            recorder: Steel recorder used to schedule background video exports.

        Returns:
            StreamingResponse: Serialized streaming payload for the current step.
        """
        is_done, _ = await agent.take_step()
        streaming_state.step_count += 1

        tool_calls = ActionParser.extract_actions(agent.state.last_model_output, agent.state.last_result)
        logger.info("Browser-use raw tool calls: %s", [call.__dict__ for call in tool_calls])

        error_message = self._resolve_step_error(agent, streaming_state, recorder, tool_calls)
        if error_message:
            raise BrowserUseFatalError(error_message)

        if is_done:
            self._update_completion_state(streaming_state, recorder)

        tool_calls_dict = [{"name": tc.name, "args": tc.args, "output": tc.output} for tc in tool_calls]
        content = generate_step_content(tool_calls, is_done)
        thinking_message = await generate_thinking_message(content, tool_calls_dict, is_final=is_done)

        step_response = create_step_response(agent, tool_calls, is_done, content, thinking_message)
        logger.info("Browser-use step event: %s", step_response.to_dict())

        self._log_stream_event("step_streaming_response", step_response)

        return step_response

    def _prepare_step_events(
        self,
        response: StreamingResponse,
        streaming_state: StreamingState,
    ) -> list[dict[str, Any]]:
        """Construct serialized events for a streaming step.

        Args:
            response: Primary streaming response generated for the current step.
            streaming_state: Streaming state describing overall progress/completion.

        Returns:
            List of serialized event dictionaries ready to be emitted.
        """
        wrap_markers = not streaming_state.is_complete
        return [
            {
                "payload": response.to_dict(),
                "wrap_markers": wrap_markers,
                "label": "step_result",
            }
        ]

    async def _next_step_events(
        self,
        agent: Agent,
        streaming_state: StreamingState,
        recorder: SteelSessionRecorder,
    ) -> list[dict[str, Any]]:
        """Execute a step and return serialized events, handling errors consistently.

        Args:
            agent: Browser-use agent executing the step.
            streaming_state: Mutable streaming state metadata.
            recorder: Recorder used for background capture scheduling.

        Returns:
            List of serialized event dictionaries produced by the step.
        """
        try:
            response = await self._perform_agent_step(agent, streaming_state, recorder)
            return self._prepare_step_events(response, streaming_state)
        except asyncio.CancelledError as cancel:
            self._finalize_streaming_on_cancel(streaming_state, recorder)
            raise cancel
        except BrowserUseFatalError:
            raise
        except Exception as error:  # pragma: no cover - defensive path
            error_message = f"Error in step execution: {error}"
            raise BrowserUseFatalError(error_message) from error

    def _resolve_step_error(
        self,
        agent: Agent,
        streaming_state: StreamingState,
        recorder: SteelSessionRecorder,
        tool_calls: list[ToolCallInfo],
    ) -> str | None:
        """Handle terminal or extraction errors detected during a step.

        Args:
            agent: Browser-use agent with latest results.
            streaming_state: Current streaming state object.
            recorder: Recorder used to schedule background exports.
            tool_calls: Tool calls extracted from the agent step.

        Returns:
            Error message when the step must terminate, otherwise ``None``.
        """
        terminal_error = self._detect_terminal_session_error(agent, tool_calls)
        if terminal_error:
            message = f"Browser session disconnected unexpectedly. Steel reported: {terminal_error}"
            self._finalize_stream_with_error(streaming_state, recorder, message)
            return message

        extraction_error = detect_structured_data_failure(tool_calls, self._summarize_terminal_error)
        if extraction_error:
            self._finalize_stream_with_error(streaming_state, recorder, extraction_error)
            return extraction_error

        return None

    def _finalize_stream_with_error(
        self,
        streaming_state: StreamingState,
        recorder: SteelSessionRecorder,
        message: str,
    ) -> None:
        """Mark the stream as complete due to an unrecoverable error.

        Args:
            streaming_state: Current streaming state to update.
            recorder: Recorder used to schedule background exports.
            message: Human-readable error message to persist.
        """
        streaming_state.terminal_error = message
        streaming_state.is_complete = True
        if streaming_state.session_id:
            self._start_background_recording(recorder, streaming_state.session_id)
            streaming_state.recording_started = True

    def _update_completion_state(
        self,
        streaming_state: StreamingState,
        recorder: SteelSessionRecorder,
    ) -> None:
        """Mark the streaming state as complete and schedule recording when needed.

        Args:
            streaming_state: Current streaming state to mutate.
            recorder: Recorder used to kick off background exports.
        """
        streaming_state.is_complete = True
        if streaming_state.session_id:
            self._start_background_recording(recorder, streaming_state.session_id)
            streaming_state.recording_started = True

    def _detect_terminal_session_error(self, agent: Agent, tool_calls: list[ToolCallInfo]) -> str | None:
        """Inspect tool outputs and agent results for terminal Steel session failures.

        Args:
            agent: The browser-use agent providing result context.
            tool_calls: Tool call descriptors extracted for the current step.

        Returns:
            str | None: A concise terminal error summary when detected, otherwise None.
        """
        candidates = self._collect_session_messages(agent, tool_calls)

        fatal_match = session_errors.find_fatal_message(candidates)
        if fatal_match:
            fatal_message, _ = fatal_match
            return self._summarize_terminal_error(fatal_message)

        self._log_session_warnings(candidates)

        return None

    def _collect_session_messages(self, agent: Agent, tool_calls: list[ToolCallInfo]) -> list[str]:
        """Gather outputs and errors emitted during a step for analysis.

        Args:
            agent: Browser-use agent providing result context.
            tool_calls: Tool calls extracted from the step execution.

        Returns:
            List of raw output/error messages produced during the step.
        """
        tool_outputs = [call.output for call in tool_calls if call.output]
        result_errors = []
        if agent.state.last_result:
            result_errors = [result.error for result in agent.state.last_result if result and result.error]
        return [message for message in (*tool_outputs, *result_errors) if message]

    def _log_session_warnings(self, candidates: list[str]) -> None:
        """Emit debug logs for non-fatal Steel session warnings.

        Args:
            candidates: Messages captured during the step to inspect for warnings.
        """
        logged_warnings: set[str] = set()
        for candidate in candidates:
            warning_name = session_errors.categorize_warning_message(candidate)
            if warning_name and warning_name not in logged_warnings:
                logger.debug("Detected session warning=%s; continuing stream.", warning_name)
                logged_warnings.add(warning_name)

    def _detect_terminal_error_from_exception(self, error_message: str) -> str | None:
        """Detect terminal Steel session failures from raised exceptions.

        Args:
            error_message: The exception message captured during step execution.

        Returns:
            str | None: Terminal error summary when matched, otherwise None.
        """
        fatal_match = session_errors.find_fatal_message([error_message])
        if fatal_match:
            fatal_message, _ = fatal_match
            return self._summarize_terminal_error(fatal_message)
        warning_name = session_errors.categorize_warning_message(error_message)
        if warning_name:
            logger.debug(
                "Detected session warning=%s from exception; continuing stream.",
                warning_name,
            )
        return None

    @staticmethod
    def _summarize_terminal_error(error_message: str, max_length: int = 200) -> str:
        """Produce a concise summary for terminal error messages.

        Args:
            error_message: The original terminal error message.
            max_length: Maximum length for the summary text.

        Returns:
            str: Sanitized and truncated error summary.
        """
        sanitized = " ".join(error_message.split())
        if len(sanitized) <= max_length:
            return sanitized
        return sanitized[: max_length - 1] + "…"

    def _log_stream_event(self, label: str, event: dict[str, Any] | StreamingResponse) -> None:
        """Log streaming events to trace emission order during debugging.

        Args:
            label: Descriptive label for the event source.
            event: Streaming payload (dict or StreamingResponse).
        """
        try:
            payload = event.to_dict() if isinstance(event, StreamingResponse) else event
            if isinstance(payload, dict):
                message = json.dumps(payload, default=str)
            else:
                message = repr(payload)
            logger.info("Streaming event (%s): %s", label, message)
        except Exception as error:  # pragma: no cover - defensive logging
            logger.info("Streaming event (%s): logging failed: %s", label, error)

    def _start_background_recording(self, recorder: SteelSessionRecorder, session_id: str) -> None:
        """Start background process to record and convert Steel session to video.

        This method starts a background task to fetch rrweb events and convert them to video
        after the browser-use agent has completed its task. The recording happens asynchronously
        to avoid blocking the main execution flow.

        Args:
            recorder: The Steel session recorder instance.
            session_id: The Steel session ID to record.

        Note:
            The recording task is created using asyncio.create_task() to run in the
            background. This allows the main execution to continue while video
            generation happens asynchronously.
        """
        recording_task = asyncio.create_task(recorder.record_session_to_video(session_id=session_id))
        background_tasks: set[asyncio.Task[Any]] = getattr(self, "_background_tasks", set())
        background_tasks.add(recording_task)
        recording_task.add_done_callback(background_tasks.discard)
        self._background_tasks = background_tasks

    def _finalize_streaming_on_cancel(
        self, streaming_state: StreamingState | None, recorder: SteelSessionRecorder
    ) -> None:
        """Mark streaming as complete and trigger recording when execution is cancelled.

        Args:
            streaming_state: Current state container for streaming progress.
            recorder: Recorder instance responsible for exporting session recordings.
        """
        if not streaming_state or streaming_state.is_complete:
            return

        streaming_state.is_complete = True
        if not streaming_state.terminal_error:
            streaming_state.terminal_error = "Execution cancelled by upstream request."

        if streaming_state.session_id and not streaming_state.recording_started:
            self._start_background_recording(recorder, streaming_state.session_id)
            streaming_state.recording_started = True
