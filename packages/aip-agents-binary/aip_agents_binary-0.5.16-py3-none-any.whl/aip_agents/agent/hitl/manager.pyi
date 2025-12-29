from _typeshed import Incomplete
from aip_agents.agent.hitl.config import ToolApprovalConfig as ToolApprovalConfig
from aip_agents.agent.hitl.prompt import BasePromptHandler as BasePromptHandler, DeferredPromptHandler as DeferredPromptHandler
from aip_agents.agent.hitl.registry import hitl_registry as hitl_registry
from aip_agents.schema.hitl import ApprovalDecision as ApprovalDecision, ApprovalDecisionType as ApprovalDecisionType, ApprovalLogEntry as ApprovalLogEntry, ApprovalRequest as ApprovalRequest
from collections.abc import Callable as Callable, Iterable
from typing import Any

MAX_ARGUMENTS_PREVIEW_LENGTH: int
DECISION_MESSAGE_MAP: Incomplete
TOOL_EXECUTION_BLOCKING_DECISIONS: Incomplete

class ApprovalManager:
    """Manages the HITL approval workflow for tools.

    This class coordinates the approval process from configuration through
    to final decision, handling timeouts and cleanup.
    """
    def __init__(self, prompt_handler: BasePromptHandler | None = None) -> None:
        """Initialize the approval manager.

        Args:
            prompt_handler: Optional prompt handler for user interaction.
                Defaults to DeferredPromptHandler which exposes pending requests
                for out-of-band resolution.
        """
    def create_approval_request(self, tool_name: str, arguments: dict[str, Any], config: ToolApprovalConfig, context: dict[str, str] | None = None) -> ApprovalRequest:
        """Create a new approval request for a tool call.

        Args:
            tool_name: Name of the tool being called.
            arguments: Tool arguments (will be JSON serialized).
            config: Approval configuration for this tool.
            context: Optional context metadata. Defaults to None.

        Returns:
            The created approval request.
        """
    def get_pending_request(self, request_id: str) -> ApprovalRequest | None:
        """Get a pending approval request by ID.

        Args:
            request_id: The unique identifier of the approval request.

        Returns:
            The pending approval request if found, None otherwise.
        """
    def approve_request(self, request: ApprovalRequest, operator_input: str = 'approved') -> ApprovalDecision:
        '''Record an approval decision for a request.

        This method creates an approval decision, calculates latency metrics,
        and removes the request from the active requests queue.

        Args:
            request: The approval request to approve.
            operator_input: Raw operator input that led to this decision. Defaults to "approved".

        Returns:
            The recorded approval decision.
        '''
    def reject_request(self, request: ApprovalRequest, operator_input: str = 'rejected') -> ApprovalDecision:
        '''Record a rejection decision for a request.

        This method creates a rejection decision, calculates latency metrics,
        and removes the request from the active requests queue.

        Args:
            request: The approval request to reject.
            operator_input: Raw operator input that led to this decision. Defaults to "rejected".

        Returns:
            The recorded rejection decision.
        '''
    def skip_request(self, request: ApprovalRequest, operator_input: str = 'skipped') -> ApprovalDecision:
        '''Record a skip decision for a request.

        This method creates a skip decision, calculates latency metrics,
        and removes the request from the active requests queue.

        Args:
            request: The approval request to skip.
            operator_input: Raw operator input that led to this decision. Defaults to "skipped".

        Returns:
            The recorded skip decision.
        '''
    def timeout_request(self, request: ApprovalRequest, operator_input: str = 'TIMEOUT') -> ApprovalDecision:
        '''Record a timeout decision for a request, always skipping the tool.

        Args:
            request (ApprovalRequest): The approval request that timed out.
            operator_input (str, optional): Input from the operator (defaults to "TIMEOUT").

        Returns:
            ApprovalDecision: The timeout decision.
        '''
    def check_timeout(self, request: ApprovalRequest) -> ApprovalDecision | None:
        """Check if a request has timed out and return timeout decision if so.

        Args:
            request: The approval request to check.

        Returns:
            Timeout decision if timed out, None otherwise.
        """
    async def prompt_for_decision(self, request: ApprovalRequest, timeout_seconds: int, context_keys: list[str] | None = None) -> ApprovalDecision:
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
    def list_pending_requests(self) -> Iterable[ApprovalRequest]:
        """Return a snapshot of currently pending requests.

        This method provides a thread-safe snapshot of all currently active
        approval requests that are waiting for operator decisions.

        Returns:
            An iterable of all pending approval requests.
        """
    def resolve_pending_request(self, request_id: str, decision: str, operator_input: str = '') -> ApprovalDecision:
        '''Resolve a pending request with an explicit decision.

        Args:
            request_id: The unique identifier of the pending approval request.
            decision: The decision string (e.g., "approved", "rejected", "skipped").
            operator_input: Optional raw operator input, defaults to the decision string. Defaults to "".

        Returns:
            The recorded approval decision.

        Raises:
            KeyError: If no pending request exists with the given request_id.
            ValueError: If the decision string is not supported.
        '''
    def create_log_entry(self, decision: ApprovalDecision, tool_name: str, agent_id: str | None = None, thread_id: str | None = None, additional_context: dict[str, Any] | None = None) -> ApprovalLogEntry:
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
    def cleanup_expired_requests(self) -> int:
        """Clean up expired requests and return count of cleaned requests.

        This method removes all approval requests that have exceeded their
        timeout period from the active requests queue. This is typically
        called periodically to prevent memory leaks from abandoned requests.

        Returns:
            The number of expired requests that were cleaned up.
        """
    def register_waiter(self, request_id: str, future: Any) -> None:
        """Register a waiter future for an approval request.

        Args:
            request_id: The id for which to wait.
            future: An asyncio.Future that will receive a tuple(decision, operator_input).
        """
    def unregister_waiter(self, request_id: str) -> None:
        """Unregister a waiter if present (used on timeout/cancellation).

        Args:
            request_id (str): The ID of the request to unregister the waiter for.
        """
    async def wait_for_pending_decision(self, request: ApprovalRequest, timeout_seconds: int) -> ApprovalDecision:
        """Wait for a pending request to be resolved and return the final decision.

        Args:
            request: The pending approval request to wait for.
            timeout_seconds: Maximum time to wait before treating as timeout.

        Returns:
            The finalized approval decision.
        """
    @staticmethod
    def get_decision_message(decision: ApprovalDecision) -> str:
        """Get the appropriate message for a HITL decision.

        Args:
            decision: The approval decision to get a message for.

        Returns:
            A human-readable message explaining the decision outcome.
        """
