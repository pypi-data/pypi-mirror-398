"""HITL ApprovalManager for coordinating approval workflow.

This module provides the core approval management logic that coordinates
between configuration, requests, and CLI prompting.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import json
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from typing import Any

from aip_agents.agent.hitl.config import ToolApprovalConfig
from aip_agents.agent.hitl.prompt import BasePromptHandler, DeferredPromptHandler
from aip_agents.agent.hitl.registry import hitl_registry
from aip_agents.schema.hitl import ApprovalDecision, ApprovalDecisionType, ApprovalLogEntry, ApprovalRequest

# Constants
MAX_ARGUMENTS_PREVIEW_LENGTH = 2048

# Decision message templates for different HITL outcomes
DECISION_MESSAGE_MAP = {
    ApprovalDecisionType.SKIPPED: (
        "Tool execution was skipped by the human operator. Consider alternative approaches or gather additional "
        "context before retrying."
    ),
    ApprovalDecisionType.TIMEOUT_SKIP: (
        "Tool execution timed out waiting for human approval. Proceed without running the tool and surface a "
        "follow-up plan."
    ),
    ApprovalDecisionType.REJECTED: (
        "Tool execution was explicitly rejected by the human operator. Abort this action and provide a safe "
        "alternative or explanation."
    ),
    ApprovalDecisionType.PENDING: (
        "Awaiting human approval for request '{request_id}'. Invoke "
        "ApprovalManager.resolve_pending_request using this identifier to continue execution."
    ),
}

# Decisions that block tool execution (all except APPROVED)
TOOL_EXECUTION_BLOCKING_DECISIONS = {
    ApprovalDecisionType.REJECTED,
    ApprovalDecisionType.SKIPPED,
    ApprovalDecisionType.TIMEOUT_SKIP,
    ApprovalDecisionType.PENDING,
}


class ApprovalManager:
    """Manages the HITL approval workflow for tools.

    This class coordinates the approval process from configuration through
    to final decision, handling timeouts and cleanup.
    """

    def __init__(self, prompt_handler: BasePromptHandler | None = None):
        """Initialize the approval manager.

        Args:
            prompt_handler: Optional prompt handler for user interaction.
                Defaults to DeferredPromptHandler which exposes pending requests
                for out-of-band resolution.
        """
        self._active_requests: dict[str, ApprovalRequest] = {}
        self._waiters: dict[str, Any] = {}
        self._prompt_handler: BasePromptHandler = prompt_handler or DeferredPromptHandler()
        # Allow handlers that need manager access to attach it
        try:
            self._prompt_handler.attach_manager(self)  # type: ignore[attr-defined]
        except Exception:
            pass

    def create_approval_request(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        config: ToolApprovalConfig,
        context: dict[str, str] | None = None,
    ) -> ApprovalRequest:
        """Create a new approval request for a tool call.

        Args:
            tool_name: Name of the tool being called.
            arguments: Tool arguments (will be JSON serialized).
            config: Approval configuration for this tool.
            context: Optional context metadata. Defaults to None.

        Returns:
            The created approval request.
        """
        # Create truncated JSON preview (limit to 2KB)
        try:
            arguments_json = json.dumps(arguments, indent=2)
            if len(arguments_json) > MAX_ARGUMENTS_PREVIEW_LENGTH:
                arguments_json = arguments_json[: MAX_ARGUMENTS_PREVIEW_LENGTH - 3] + "..."
        except (TypeError, ValueError):
            # Handle non-serializable arguments with a safe fallback
            # Try to provide more specific information about what's not serializable
            non_serializable_info = self._get_non_serializable_info(arguments)
            arguments_json = f"<Non-serializable arguments: {non_serializable_info}>"

        request = ApprovalRequest.create(tool_name=tool_name, arguments_preview=arguments_json, context=context)

        # Set timeout and register the request
        self._set_timeout_based_on_config(request, config)

        return request

    def _get_non_serializable_info(self, arguments: Any) -> str:
        """Get information about non-serializable content in arguments.

        Args:
            arguments: The arguments that failed JSON serialization.

        Returns:
            String describing the non-serializable content.
        """
        # Handle dictionary arguments
        if isinstance(arguments, dict):
            return self._get_dict_serializable_info(arguments)

        # Handle list/tuple arguments
        if isinstance(arguments, list | tuple):
            return self._get_sequence_serializable_info(arguments)

        # For other types, just return the type name
        return type(arguments).__name__

    def _get_dict_serializable_info(self, arguments: dict[str, Any]) -> str:
        """Get serializable info for dictionary arguments.

        Args:
            arguments (dict[str, Any]): The dictionary arguments to analyze.

        Returns:
            str: Description of the arguments' serializability.
        """
        non_serializable_items = []

        for key, value in arguments.items():
            if not self._is_json_serializable(value):
                non_serializable_items.append(f"{key}={type(value).__name__}")

        if non_serializable_items:
            return f"dict with non-serializable keys: {', '.join(non_serializable_items)}"

        return "dict"

    def _get_sequence_serializable_info(self, arguments: list | tuple) -> str:
        """Get serializable info for list/tuple arguments.

        Args:
            arguments (list | tuple): The sequence arguments to analyze.

        Returns:
            str: Description of the arguments' serializability.
        """
        non_serializable_items = []

        for i, item in enumerate(arguments):
            if not self._is_json_serializable(item):
                non_serializable_items.append(f"[{i}]={type(item).__name__}")

        if non_serializable_items:
            return f"{type(arguments).__name__} with non-serializable items: {', '.join(non_serializable_items)}"

        return type(arguments).__name__

    def _is_json_serializable(self, value: Any) -> bool:
        """Check if a value is JSON serializable.

        Args:
            value (Any): The value to check for JSON serializability.

        Returns:
            bool: True if the value is JSON serializable, False otherwise.
        """
        try:
            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False

    # Set timeout based on config
    def _set_timeout_based_on_config(self, request: ApprovalRequest, config: ToolApprovalConfig) -> None:
        """Set timeout on the approval request based on configuration.

        Args:
            request: The approval request to set timeout on.
            config: The approval configuration.
        """
        if request.created_at:
            request.timeout_at = request.created_at + timedelta(seconds=config.timeout_seconds)

        self._active_requests[request.request_id] = request

        # Register ownership in global registry for hierarchical routing
        hitl_registry.register(request.request_id, self)

    def get_pending_request(self, request_id: str) -> ApprovalRequest | None:
        """Get a pending approval request by ID.

        Args:
            request_id: The unique identifier of the approval request.

        Returns:
            The pending approval request if found, None otherwise.
        """
        return self._active_requests.get(request_id)

    def approve_request(self, request: ApprovalRequest, operator_input: str = "approved") -> ApprovalDecision:
        """Record an approval decision for a request.

        This method creates an approval decision, calculates latency metrics,
        and removes the request from the active requests queue.

        Args:
            request: The approval request to approve.
            operator_input: Raw operator input that led to this decision. Defaults to "approved".

        Returns:
            The recorded approval decision.
        """
        return self._finalize_request(request, ApprovalDecisionType.APPROVED, operator_input)

    def reject_request(self, request: ApprovalRequest, operator_input: str = "rejected") -> ApprovalDecision:
        """Record a rejection decision for a request.

        This method creates a rejection decision, calculates latency metrics,
        and removes the request from the active requests queue.

        Args:
            request: The approval request to reject.
            operator_input: Raw operator input that led to this decision. Defaults to "rejected".

        Returns:
            The recorded rejection decision.
        """
        return self._finalize_request(request, ApprovalDecisionType.REJECTED, operator_input)

    def skip_request(self, request: ApprovalRequest, operator_input: str = "skipped") -> ApprovalDecision:
        """Record a skip decision for a request.

        This method creates a skip decision, calculates latency metrics,
        and removes the request from the active requests queue.

        Args:
            request: The approval request to skip.
            operator_input: Raw operator input that led to this decision. Defaults to "skipped".

        Returns:
            The recorded skip decision.
        """
        return self._finalize_request(request, ApprovalDecisionType.SKIPPED, operator_input)

    def timeout_request(self, request: ApprovalRequest, operator_input: str = "TIMEOUT") -> ApprovalDecision:
        """Record a timeout decision for a request, always skipping the tool.

        Args:
            request (ApprovalRequest): The approval request that timed out.
            operator_input (str, optional): Input from the operator (defaults to "TIMEOUT").

        Returns:
            ApprovalDecision: The timeout decision.
        """
        decision_type = ApprovalDecisionType.TIMEOUT_SKIP
        return self._finalize_request(request, decision_type, operator_input)

    def check_timeout(self, request: ApprovalRequest) -> ApprovalDecision | None:
        """Check if a request has timed out and return timeout decision if so.

        Args:
            request: The approval request to check.

        Returns:
            Timeout decision if timed out, None otherwise.
        """
        now = datetime.now()
        if request.timeout_at and now >= request.timeout_at:
            return self.timeout_request(request)

        return None

    def _finalize_request(
        self,
        request: ApprovalRequest,
        decision_type: ApprovalDecisionType,
        operator_input: str,
    ) -> ApprovalDecision:
        """Create a decision, record latency, and remove the request.

        This is a helper method used by all decision recording methods to
        create the ApprovalDecision object, calculate latency metrics, and
        clean up the request from the active queue.

        Args:
            request: The approval request being finalized.
            decision_type: The type of decision (approved, rejected, etc.).
            operator_input: The raw input that led to this decision.

        Returns:
            The completed approval decision with latency metrics.
        """
        decision = ApprovalDecision(
            request_id=request.request_id,
            decision=decision_type,
            operator_input=operator_input,
        )

        if request.created_at and decision.decided_at:
            latency = decision.decided_at - request.created_at
            decision.latency_ms = int(latency.total_seconds() * 1000)

        self._active_requests.pop(request.request_id, None)

        # Unregister from global registry when finalized
        hitl_registry.unregister(request.request_id)

        return decision

    async def prompt_for_decision(
        self,
        request: ApprovalRequest,
        timeout_seconds: int,
        context_keys: list[str] | None = None,
    ) -> ApprovalDecision:
        """Prompt for a decision using the configured handler.

        This method delegates to the configured prompt handler to obtain
        an approval decision from the operator. The handler may be interactive
        (CLI) or deferred (programmatic, resume-in-place).

        Args:
            request: The approval request to prompt for.
            timeout_seconds: How long to wait for input.
            context_keys: Optional keys to display from context. Defaults to None.

        Returns:
            The operator's decision on the request.
        """
        return await self._prompt_handler.prompt_for_decision(
            request=request,
            timeout_seconds=timeout_seconds,
            context_keys=context_keys,
        )

    def list_pending_requests(self) -> Iterable[ApprovalRequest]:
        """Return a snapshot of currently pending requests.

        This method provides a thread-safe snapshot of all currently active
        approval requests that are waiting for operator decisions.

        Returns:
            An iterable of all pending approval requests.
        """
        return list(self._active_requests.values())

    def _resolve_decision_handler(
        self, decision: str
    ) -> tuple[ApprovalDecisionType, Callable[[ApprovalRequest, str], ApprovalDecision]]:
        """Return the canonical decision enum and finalize callable.

        Args:
            decision (str): The decision string to resolve.

        Returns:
            tuple[ApprovalDecisionType, Callable[[ApprovalRequest, str], ApprovalDecision]]: The decision type and handler function.
        """
        normalized = decision.strip().lower()
        try:
            decision_type = ApprovalDecisionType(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported decision '{decision}' for pending request resolution") from exc

        decision_map: dict[ApprovalDecisionType, Callable[[ApprovalRequest, str], ApprovalDecision]] = {
            ApprovalDecisionType.APPROVED: self.approve_request,
            ApprovalDecisionType.REJECTED: self.reject_request,
            ApprovalDecisionType.SKIPPED: self.skip_request,
        }
        handler = decision_map.get(decision_type)
        if handler is None:
            raise ValueError(f"Unsupported decision '{decision}' for pending request resolution")
        return decision_type, handler

    def resolve_pending_request(self, request_id: str, decision: str, operator_input: str = "") -> ApprovalDecision:
        """Resolve a pending request with an explicit decision.

        Args:
            request_id: The unique identifier of the pending approval request.
            decision: The decision string (e.g., "approved", "rejected", "skipped").
            operator_input: Optional raw operator input, defaults to the decision string. Defaults to "".

        Returns:
            The recorded approval decision.

        Raises:
            KeyError: If no pending request exists with the given request_id.
            ValueError: If the decision string is not supported.
        """
        request = self.get_pending_request(request_id)
        if not request:
            raise KeyError(f"No pending approval request with id '{request_id}'")

        applied_input = operator_input or decision
        decision_type, finalize = self._resolve_decision_handler(decision)

        waiter = self._waiters.pop(request_id, None)
        if waiter is not None:
            waiter.set_result((decision_type.value, applied_input))
            return ApprovalDecision(
                request_id=request_id,
                decision=ApprovalDecisionType.PENDING,
                operator_input=applied_input,
            )

        return finalize(request, applied_input)

    def create_log_entry(
        self,
        decision: ApprovalDecision,
        tool_name: str,
        agent_id: str | None = None,
        thread_id: str | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> ApprovalLogEntry:
        """Create a log entry for a decision.

        Args:
            decision: The approval decision.
            tool_name: Name of the tool.
            agent_id: Optional agent identifier. Defaults to None.
            thread_id: Optional thread/session identifier. Defaults to None.
            additional_context: Optional additional logging context. Defaults to None.

        Returns:
            Structured log entry.
        """
        return ApprovalLogEntry(
            request_id=decision.request_id,
            tool_name=tool_name,
            decision=decision.decision,
            agent_id=agent_id,
            thread_id=thread_id,
            additional_context=additional_context,
        )

    def cleanup_expired_requests(self) -> int:
        """Clean up expired requests and return count of cleaned requests.

        This method removes all approval requests that have exceeded their
        timeout period from the active requests queue. This is typically
        called periodically to prevent memory leaks from abandoned requests.

        Returns:
            The number of expired requests that were cleaned up.
        """
        now = datetime.now()
        expired_ids = []

        for request_id, request in self._active_requests.items():
            if request.timeout_at and now >= request.timeout_at:
                expired_ids.append(request_id)

        for request_id in expired_ids:
            self._active_requests.pop(request_id, None)
            # Unregister expired requests from global registry
            hitl_registry.unregister(request_id)

        return len(expired_ids)

    # Deferred waiter helpers ----------------------------codex---------------------
    def register_waiter(self, request_id: str, future: Any) -> None:
        """Register a waiter future for an approval request.

        Args:
            request_id: The id for which to wait.
            future: An asyncio.Future that will receive a tuple(decision, operator_input).
        """
        self._waiters[request_id] = future

    def unregister_waiter(self, request_id: str) -> None:
        """Unregister a waiter if present (used on timeout/cancellation).

        Args:
            request_id (str): The ID of the request to unregister the waiter for.
        """
        self._waiters.pop(request_id, None)

    async def wait_for_pending_decision(self, request: ApprovalRequest, timeout_seconds: int) -> ApprovalDecision:
        """Wait for a pending request to be resolved and return the final decision.

        Args:
            request: The pending approval request to wait for.
            timeout_seconds: Maximum time to wait before treating as timeout.

        Returns:
            The finalized approval decision.
        """
        future = self._waiters.get(request.request_id)
        if future is None:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self.register_waiter(request.request_id, future)

        try:
            normalized_decision, operator_input = await asyncio.wait_for(future, timeout_seconds)
        except TimeoutError:
            self.unregister_waiter(request.request_id)
            return self.timeout_request(request)

        _decision_type, handler = self._resolve_decision_handler(normalized_decision)
        return handler(request, operator_input)

    @staticmethod
    def get_decision_message(decision: ApprovalDecision) -> str:
        """Get the appropriate message for a HITL decision.

        Args:
            decision: The approval decision to get a message for.

        Returns:
            A human-readable message explaining the decision outcome.
        """
        template = DECISION_MESSAGE_MAP.get(decision.decision)
        if template:
            return template.format(request_id=decision.request_id)
        else:
            return f"Tool execution {decision.decision} by human approval."
