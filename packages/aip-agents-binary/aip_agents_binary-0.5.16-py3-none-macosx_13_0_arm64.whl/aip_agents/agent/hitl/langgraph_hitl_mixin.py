"""Mixin that encapsulates HITL helper logic for LangGraph agents."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from langchain_core.messages import ToolMessage
from langgraph.config import get_stream_writer
from langgraph.types import StreamWriter

from aip_agents.agent.hitl.config import ToolApprovalConfig
from aip_agents.agent.hitl.manager import ApprovalManager
from aip_agents.schema.hitl import ApprovalDecision, ApprovalDecisionType, ApprovalRequest, HitlMetadata
from aip_agents.schema.langgraph import ToolCallResult
from aip_agents.tools.tool_config_injector import TOOL_CONFIGS_KEY
from aip_agents.utils.datetime import ensure_utc_datetime
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

MAX_CONTEXT_MESSAGE_LENGTH = 200


class LangGraphHitLMixin:
    """Provide Human-in-the-Loop helpers for LangGraph agents."""

    _hitl_manager: ApprovalManager | None
    tool_configs: dict[str, Any] | None
    name: str

    @property
    def hitl_manager(self) -> ApprovalManager | None:
        """Return the active ``ApprovalManager``, creating one if needed."""
        manager = getattr(self, "_hitl_manager", None)
        if manager is not None:
            return manager
        return self._initialize_hitl_manager_if_needed()

    @hitl_manager.setter
    def hitl_manager(self, manager: ApprovalManager | None) -> None:
        """Set the HITL approval manager instance.

        Args:
            manager: ApprovalManager instance or None.
        """
        self._hitl_manager = manager

    async def _check_hitl_approval(
        self,
        tool_call: dict[str, Any],
        tool_name: str,
        state: dict[str, Any],
    ) -> ApprovalDecision | None:
        """Resolve approval gating for a tool call if HITL is configured.

        Args:
            tool_call: The tool call information containing id, name, and args.
            tool_name: Name of the tool being executed.
            state: Current agent state containing conversation context.

        Returns:
            ApprovalDecision if HITL is configured and decision is made, None otherwise.
        """
        hitl_config = self._get_hitl_config(tool_name)
        manager = self.hitl_manager
        if manager is None and hitl_config is not None:
            manager = self._initialize_hitl_manager_for_tool(tool_name)

        if manager is None or hitl_config is None:
            return None

        request = manager.create_approval_request(
            tool_name=tool_name,
            arguments=tool_call.get("args", {}),
            config=hitl_config,
            context=self._extract_hitl_context(state),
        )

        try:
            decision = await manager.prompt_for_decision(
                request=request,
                timeout_seconds=hitl_config.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "HITL approval check failed, proceeding with tool execution",
                extra={"tool_name": tool_name, "error": str(exc), "error_type": type(exc).__name__},
            )
            return None

        if decision.decision == ApprovalDecisionType.PENDING:
            return await self._handle_pending_hitl_decision(
                tool_call=tool_call,
                pending_decision=decision,
                request=request,
                hitl_config=hitl_config,
                state=state,
            )

        finalized_decision = self._finalize_hitl_decision(request, decision)
        self._log_hitl_decision(tool_name, finalized_decision, state)
        return finalized_decision

    def _finalize_hitl_decision(
        self,
        request: ApprovalRequest,
        decision: ApprovalDecision,
    ) -> ApprovalDecision:
        """Convert prompt handler output into a manager-recorded decision.

        Args:
            request: The approval request that was made.
            decision: The decision returned by the prompt handler.

        Returns:
            Finalized ApprovalDecision recorded with the manager.
        """
        manager = self.hitl_manager
        if manager is None:
            return decision

        operator_input = decision.operator_input or ""

        if decision.decision == ApprovalDecisionType.PENDING:
            return decision

        if decision.decision == ApprovalDecisionType.TIMEOUT_SKIP:
            return manager.timeout_request(
                request,
                operator_input=operator_input or "TIMEOUT",
            )

        decision_handlers = {
            ApprovalDecisionType.APPROVED: manager.approve_request,
            ApprovalDecisionType.REJECTED: manager.reject_request,
            ApprovalDecisionType.SKIPPED: manager.skip_request,
        }

        handler = decision_handlers.get(decision.decision)
        if handler:
            return handler(request, operator_input)

        return manager.skip_request(request, operator_input)

    async def _handle_pending_hitl_decision(
        self,
        tool_call: dict[str, Any],
        pending_decision: ApprovalDecision,
        request: ApprovalRequest | None,
        hitl_config: ToolApprovalConfig | None,
        state: dict[str, Any],
    ) -> ApprovalDecision:
        """Emit a pending sentinel and wait for resolution from the manager.

        Args:
            tool_call: The tool call information that requires approval.
            pending_decision: The initial pending decision from the prompt handler.
            request: The approval request that was created.
            hitl_config: Configuration for the HITL approval process.
            state: Current agent state containing conversation context.

        Returns:
            Final approval decision after waiting for external resolution.
        """
        manager = self.hitl_manager
        if manager is None or request is None or hitl_config is None:
            return pending_decision

        self._emit_hitl_pending_event(
            tool_call=tool_call,
            decision=pending_decision,
            request=request,
            hitl_config=hitl_config,
        )

        final_decision = await manager.wait_for_pending_decision(
            request=request,
            timeout_seconds=hitl_config.timeout_seconds,
        )

        self._log_hitl_decision(tool_call["name"], final_decision, state)
        return final_decision

    def _log_hitl_decision(self, tool_name: str, decision: ApprovalDecision, state: dict[str, Any]) -> None:
        """Emit a structured log entry for a resolved HITL decision.

        Args:
            tool_name: Name of the tool that required approval.
            decision: The final approval decision that was made.
            state: Current agent state containing thread_id and other context.
        """
        manager = self.hitl_manager
        if manager is None:
            return

        log_entry = manager.create_log_entry(
            decision=decision,
            tool_name=tool_name,
            agent_id=getattr(self, "name", None),
            thread_id=state.get("thread_id"),
        )
        logger.info("HITL decision recorded", extra=log_entry.__dict__)

    def _emit_hitl_pending_event(
        self,
        tool_call: dict[str, Any],
        decision: ApprovalDecision,
        request: ApprovalRequest | None = None,
        hitl_config: ToolApprovalConfig | None = None,
    ) -> None:
        """Send a streaming sentinel describing a pending HITL request.

        Args:
            tool_call: The tool call information that requires approval.
            decision: The pending approval decision.
            request: The approval request that was created.
            hitl_config: Configuration for the HITL approval process.
        """
        # Pending uses the same sentinel builder as other blocking decisions so streaming stays consistent.
        sentinel_result = self._create_hitl_blocking_result(
            tool_call=tool_call,
            decision=decision,
            pending_request=request,
            hitl_config=hitl_config,
        )
        if not sentinel_result.messages:
            return

        try:
            writer: StreamWriter | None = get_stream_writer()
        except Exception:  # noqa: BLE001
            writer = None

        if writer is None:
            return

        event = self._create_tool_result_event(sentinel_result.messages[0])
        try:
            writer(event)
        except Exception:  # noqa: BLE001
            logger.warning(f"Failed to emit HITL pending event: {tool_call['name']}")

    def _get_hitl_config(self, tool_name: str) -> ToolApprovalConfig | None:
        """Extract the HITL configuration for a tool from agent-level settings.

        Args:
            tool_name: Name of the tool to get HITL configuration for.

        Returns:
            ToolApprovalConfig if HITL is configured for the tool, None otherwise.
        """
        tool_configs = self.tool_configs
        if not isinstance(tool_configs, dict):
            return None

        direct_config = self._get_direct_tool_hitl_config(tool_name)
        if direct_config:
            return direct_config

        nested_config = self._get_nested_tool_hitl_config(tool_name)
        if nested_config:
            return nested_config

        return None

    def _get_direct_tool_hitl_config(self, tool_name: str) -> ToolApprovalConfig | None:
        """Resolve HITL configuration using a direct tool name lookup.

        Args:
            tool_name: Name of the tool to get HITL configuration for.

        Returns:
            ToolApprovalConfig if found using direct lookup, None otherwise.
        """
        tool_configs = self.tool_configs or {}
        tool_config = tool_configs.get(tool_name)
        return self._parse_hitl_config_value(tool_config, tool_name)

    def _get_nested_tool_hitl_config(self, tool_name: str) -> ToolApprovalConfig | None:
        """Resolve HITL configuration from a nested ``tool_configs`` map.

        Args:
            tool_name: Name of the tool to get HITL configuration for.

        Returns:
            ToolApprovalConfig if found in nested configuration, None otherwise.
        """
        tool_configs = self.tool_configs or {}
        nested_configs = tool_configs.get(TOOL_CONFIGS_KEY)
        if not isinstance(nested_configs, dict):
            return None

        tool_config = nested_configs.get(tool_name)
        return self._parse_hitl_config_value(tool_config, tool_name)

    def _parse_hitl_config_value(self, value: Any, tool_name: str) -> ToolApprovalConfig | None:
        """Convert a configuration value into ``ToolApprovalConfig`` if possible.

        Args:
            value: The configuration value to parse (can be ToolApprovalConfig, dict, or other).
            tool_name: Name of the tool this configuration is for.

        Returns:
            ToolApprovalConfig if parsing succeeds, None otherwise.
        """
        if isinstance(value, ToolApprovalConfig):
            return value

        if isinstance(value, dict):
            return self._parse_hitl_config_dict(value, tool_name)

        return None

    def _parse_hitl_config_dict(self, value: dict[str, Any], tool_name: str) -> ToolApprovalConfig | None:
        """Construct ``ToolApprovalConfig`` from a dictionary of values.

        Args:
            value: Dictionary containing HITL configuration parameters.
            tool_name: Name of the tool this configuration is for.

        Returns:
            ToolApprovalConfig if construction succeeds, None otherwise.
        """
        if "hitl" in value:
            return self._parse_hitl_config_value(value["hitl"], tool_name)

        allowed_keys = {"timeout_seconds", "requires_approval"}
        if not set(value.keys()).issubset(allowed_keys):
            return None

        config_kwargs = dict(value)
        config_kwargs.pop("requires_approval", None)
        try:
            return ToolApprovalConfig(**config_kwargs)
        except (TypeError, ValueError):
            return None

    def ensure_hitl_manager(self) -> ApprovalManager | None:
        """Ensure an ``ApprovalManager`` exists when HITL configs are present."""
        return self._initialize_hitl_manager_if_needed()

    def use_hitl_manager(self, manager: ApprovalManager) -> None:
        """Replace the current ``ApprovalManager`` with the supplied instance.

        Args:
            manager: The ApprovalManager instance to use for HITL approvals.
        """
        self.hitl_manager = manager

    def register_hitl_notifier(self, notifier: Callable[[ApprovalRequest], None]) -> None:
        """Register a notifier callback to receive HITL approval requests.

        Args:
            notifier: Callback function that will be called with approval requests.
        """
        manager = self.ensure_hitl_manager()
        if manager is None:
            manager = self._create_default_hitl_manager()
            self.hitl_manager = manager

        handler = getattr(manager, "_prompt_handler", None)
        if handler is None:
            return

        if hasattr(handler, "attach_manager"):
            try:
                handler.attach_manager(manager)  # type: ignore[call-arg]
            except Exception:
                pass

        try:
            handler._notify = notifier
        except Exception:
            logger.warning("Failed to attach HITL notifier callback", extra={"agent": getattr(self, "name", None)})

    def _initialize_hitl_manager_for_tool(self, tool_name: str) -> ApprovalManager | None:
        """Create a default ``ApprovalManager`` for a specific tool if required.

        Args:
            tool_name: Name of the tool that requires HITL approval.

        Returns:
            ApprovalManager instance if HITL is needed, None otherwise.
        """
        return self._initialize_hitl_manager_if_needed(tool_name)

    def _initialize_hitl_manager_if_needed(self, tool_name: str | None = None) -> ApprovalManager | None:
        """Create a default ``ApprovalManager`` when HITL configs require it.

        Args:
            tool_name: Optional name of the tool that triggered the initialization.

        Returns:
            ApprovalManager instance if HITL is needed, None otherwise.
        """
        manager = getattr(self, "_hitl_manager", None)
        if manager is not None:
            return manager

        candidate_names = {tool_name} if tool_name else self._collect_hitl_tool_names()
        if candidate_names and any(self._get_hitl_config(name) for name in candidate_names):
            self._hitl_manager = self._create_default_hitl_manager()
            logger.debug("Agent '%s': HITL manager auto-initialized", self.name)

        return getattr(self, "_hitl_manager", None)

    def _collect_hitl_tool_names(self) -> set[str]:
        """Gather candidate tool names that may have HITL configuration."""
        names: set[str] = set()

        try:
            names.update(tool.name for tool in getattr(self, "resolved_tools", []) if getattr(tool, "name", None))
        except Exception:
            pass

        tool_configs = getattr(self, "tool_configs", {})
        if isinstance(tool_configs, dict):
            for key, value in tool_configs.items():
                if key != TOOL_CONFIGS_KEY and isinstance(value, dict):
                    names.add(str(key))

            nested = tool_configs.get(TOOL_CONFIGS_KEY)
            if isinstance(nested, dict):
                names.update(str(k) for k in nested.keys())

        return names

    def _create_default_hitl_manager(self) -> ApprovalManager:
        """Create the default ``ApprovalManager`` used for auto HITL handling."""
        return ApprovalManager()

    def _extract_hitl_context(self, state: dict[str, Any]) -> dict[str, str] | None:
        """Collect human-readable context for approval prompts.

        Args:
            state: Current agent state containing messages and thread information.

        Returns:
            Dictionary containing context information like last user message and thread_id,
            or None if no context is available.
        """
        context: dict[str, str] = {}

        messages = state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "human":
                content = getattr(msg, "content", "")
                if content:
                    truncated_content = content[:MAX_CONTEXT_MESSAGE_LENGTH]
                    context["last_user_message"] = truncated_content
                break

        thread_id = state.get("thread_id")
        if thread_id:
            context["thread_id"] = str(thread_id)

        return context or None

    def _create_hitl_blocking_result(
        self,
        tool_call: dict[str, Any],
        decision: ApprovalDecision,
        pending_request: ApprovalRequest | None = None,
        hitl_config: ToolApprovalConfig | None = None,
    ) -> ToolCallResult:
        """Build a sentinel ``ToolCallResult`` for any tool-execution-blocking HITL decision.

        Covers ``REJECTED``, ``SKIPPED``, ``TIMEOUT_SKIP`` and ``PENDING`` decisions, providing a
        consistent message payload for streaming and logging when execution does not proceed.

        Args:
            tool_call: The tool call information that was blocked.
            decision: The approval decision that blocked execution.
            pending_request: The approval request if decision is pending.
            hitl_config: Configuration for the HITL approval process.

        Returns:
            ToolCallResult with sentinel messages and metadata for the blocking decision.
        """
        manager = self.hitl_manager
        if manager is None:
            return ToolCallResult(messages=[], artifacts=[], metadata_delta={}, references=[], step_usage=None)

        tool_call_id = tool_call["id"]
        message_content = manager.get_decision_message(decision)

        timeout_seconds = None
        if hitl_config and getattr(hitl_config, "timeout_seconds", None) is not None:
            timeout_seconds = hitl_config.timeout_seconds

        timeout_at = getattr(pending_request, "timeout_at", None)
        timeout_at_utc = ensure_utc_datetime(timeout_at) if isinstance(timeout_at, datetime) else None

        hitl_meta = HitlMetadata.from_decision(
            decision,
            timeout_seconds=timeout_seconds,
            timeout_at=timeout_at_utc,
        ).as_payload()

        sentinel_message = ToolMessage(
            content=message_content,
            tool_call_id=tool_call_id,
            name=tool_call["name"],
            response_metadata={"hitl": hitl_meta},
        )

        return ToolCallResult(
            messages=[sentinel_message],
            artifacts=[],
            metadata_delta={},
            references=[],
            step_usage=None,
        )
