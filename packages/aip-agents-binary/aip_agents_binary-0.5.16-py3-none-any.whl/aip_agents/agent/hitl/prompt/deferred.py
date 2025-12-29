"""Deferred prompt handler that waits for external approval resolution."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from aip_agents.agent.hitl.prompt.base import BasePromptHandler
from aip_agents.schema.hitl import ApprovalDecision, ApprovalDecisionType, ApprovalRequest

if TYPE_CHECKING:  # pragma: no cover - typing-only import
    from aip_agents.agent.hitl.manager import ApprovalManager


class DeferredPromptHandler(BasePromptHandler):
    """Prompt handler that defers tool execution until an external decision is received."""

    def __init__(self, notify: Callable[[ApprovalRequest], None] | None = None) -> None:
        """Initialize the deferred prompt handler.

        Args:
            notify: Optional callback function to notify when an approval request is made.
        """
        self._notify = notify
        self._manager: ApprovalManager | None = None

    def attach_manager(self, manager: ApprovalManager) -> None:
        """Attach the ApprovalManager orchestrating approvals.

        Args:
            manager: The ApprovalManager instance to attach for handling approval decisions.
        """
        self._manager = manager

    async def prompt_for_decision(
        self,
        request: ApprovalRequest,
        timeout_seconds: int,
        context_keys: list[str] | None = None,
    ) -> ApprovalDecision:
        """Register a waiter and return a pending decision sentinel.

        Args:
            request: The approval request containing the tool call details and context.
            timeout_seconds: Number of seconds to wait for approval before timing out.
            context_keys: Optional list of context keys to include in the approval request.

        Returns:
            ApprovalDecision with PENDING status and registered waiter for external resolution.
        """
        if self._notify:
            try:
                self._notify(request)
            except Exception:
                pass

        if self._manager is None:
            return ApprovalDecision(
                request_id=request.request_id,
                decision=ApprovalDecisionType.PENDING,
                operator_input="PENDING",
            )

        loop = asyncio.get_running_loop()
        waiter = loop.create_future()
        self._manager.register_waiter(request.request_id, waiter)

        return ApprovalDecision(
            request_id=request.request_id,
            decision=ApprovalDecisionType.PENDING,
            operator_input="PENDING",
        )
