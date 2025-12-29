"""Step limit manager for enforcing execution and delegation limits.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from typing import Any

from aip_agents.schema.step_limit import (
    MaxDelegationDepthExceededError,
    MaxStepsExceededError,
    StepLimitConfig,
    StepLimitErrorResponse,
    StepLimitErrorType,
)

# Context variables for cross-agent propagation
_DELEGATION_DEPTH_CVAR: ContextVar[int] = ContextVar("delegation_depth", default=0)
_REMAINING_STEP_BUDGET_CVAR: ContextVar[int | None] = ContextVar("remaining_step_budget", default=None)
_DELEGATION_CHAIN_CVAR: ContextVar[tuple[str, ...]] = ContextVar("delegation_chain", default=())
_STEP_LIMIT_CONFIG_CVAR: ContextVar[StepLimitConfig | None] = ContextVar("step_limit_config", default=None)


@dataclass
class StepExecutionContext:
    """Runtime context for tracking step execution and delegation depth.

    Attributes:
        current_step: Current step number (0-indexed).
        delegation_depth: Current depth in delegation chain (0 for root agent).
        remaining_step_budget: Steps remaining before limit is hit.
        delegation_chain: List of agent names in the delegation chain.
    """

    current_step: int = 0
    delegation_depth: int = 0
    remaining_step_budget: int | None = None
    delegation_chain: list[str] = field(default_factory=list)


class StepLimitManager:
    """Manages step and delegation limit enforcement during agent execution.

    This manager integrates with LangGraph's existing step mechanisms and adds
    delegation depth tracking and budget propagation.

    Attributes:
        config: Step limit configuration.
        context: Current execution context.
    """

    def __init__(
        self,
        config: StepLimitConfig | None = None,
        initial_delegation_depth: int = 0,
        parent_step_budget: int | None = None,
    ) -> None:
        """Initialize step limit manager.

        Args:
            config: Optional step limit configuration. Uses defaults if None.
            initial_delegation_depth: Starting delegation depth (from parent).
            parent_step_budget: Remaining step budget inherited from parent agent.
        """
        self.config = config or StepLimitConfig()
        self.context = StepExecutionContext(
            delegation_depth=initial_delegation_depth,
            remaining_step_budget=parent_step_budget if parent_step_budget is not None else self.config.max_steps,
        )

    def check_step_limit(self, agent_name: str = "agent", count: int = 1) -> None:
        """Check if taking 'count' steps would exceed limit.

        Args:
            agent_name: Name of the agent to identify in error message.
            count: Number of steps to check (useful for parallel tool batches).

        Raises:
            MaxStepsExceededError: If max_steps limit is exceeded.
        """
        limit_exceeded = False
        limit_val = self.config.max_steps
        current_val = self.context.current_step

        if self.context.current_step + count > self.config.max_steps:
            limit_exceeded = True
        elif self.context.remaining_step_budget is not None and self.context.remaining_step_budget < count:
            limit_exceeded = True
            # If we hit budget, the limit was effectively what we've done so far + what's left
            limit_val = self.context.current_step + self.context.remaining_step_budget

        if limit_exceeded:
            error_response = StepLimitErrorResponse(
                error_type=StepLimitErrorType.STEP_LIMIT_EXCEEDED,
                agent_name=agent_name,
                current_value=current_val,
                configured_limit=limit_val,
                message=f"Agent exceeded maximum step limit ({current_val + count}/{limit_val} steps)",
            )
            raise MaxStepsExceededError(error_response)

    def check_delegation_depth(self, target_agent_name: str) -> None:
        """Check if delegation to target agent would exceed depth limit.

        Args:
            target_agent_name: Name of the agent to delegate to.

        Raises:
            MaxDelegationDepthExceededError: If delegation depth limit exceeded.
        """
        # Check for circular delegation
        if target_agent_name in self.context.delegation_chain:
            error_response = StepLimitErrorResponse(
                error_type=StepLimitErrorType.DELEGATION_DEPTH_EXCEEDED,
                agent_name=target_agent_name,
                current_value=self.context.delegation_depth,
                configured_limit=self.config.max_delegation_depth,
                message=f"Circular delegation detected: '{target_agent_name}' already in chain {self.context.delegation_chain}",
                delegation_chain=self.context.delegation_chain,
            )
            raise MaxDelegationDepthExceededError(error_response)

        # Check depth limit
        if self.context.delegation_depth >= self.config.max_delegation_depth:
            error_response = StepLimitErrorResponse(
                error_type=StepLimitErrorType.DELEGATION_DEPTH_EXCEEDED,
                agent_name=target_agent_name,
                current_value=self.context.delegation_depth,
                configured_limit=self.config.max_delegation_depth,
                message=f"Cannot delegate to '{target_agent_name}': Maximum delegation depth ({self.context.delegation_depth}/{self.config.max_delegation_depth}) exceeded",
                delegation_chain=self.context.delegation_chain,
            )
            raise MaxDelegationDepthExceededError(error_response)

    def increment_step(self, count: int = 1) -> None:
        """Increment step counter and update remaining budget.

        Args:
            count: Number of steps to consume (defaults to 1).
        """
        if count <= 0:
            return
        self.context.current_step += count
        if self.context.remaining_step_budget is not None:
            self.context.remaining_step_budget = max(0, self.context.remaining_step_budget - count)

    def get_child_budget(self, child_max_steps: int | None = None) -> int:
        """Calculate step budget to allocate to child agent.

        Algorithm:
        1. If remaining_step_budget is None (root with no limit), use config.max_steps - 1
        2. If remaining_step_budget <= 1, return 0 (no budget left for child)
        3. Calculate child_budget = remaining_step_budget - 1 (reserve 1 for parent)
        4. If child has own max_steps config, return min(child_budget, child.max_steps)
        5. Otherwise return child_budget

        Args:
            child_max_steps: Optional child agent's own max_steps limit.

        Returns:
            Step budget for child agent, accounting for parent's continuation.
            Returns 0 if no budget available for child.

        Edge Cases:
            - remaining=1: Returns 0 (parent needs the last step)
            - remaining=None: Uses config.max_steps - 1
            - child has own limit: Returns min(calculated_budget, child_limit)
        """
        if self.context.remaining_step_budget is None:
            child_budget = self.config.max_steps - 1
        elif self.context.remaining_step_budget <= 1:
            return 0
        else:
            child_budget = self.context.remaining_step_budget - 1

        if child_max_steps is not None:
            return min(child_budget, child_max_steps)
        return child_budget

    def add_to_delegation_chain(self, agent_name: str) -> None:
        """Add agent to delegation chain for tracking.

        Args:
            agent_name: Name of the agent being delegated to.
        """
        self.context.delegation_chain.append(agent_name)

    @classmethod
    def from_state(
        cls,
        state: dict[str, Any],
        config: StepLimitConfig | None = None,
    ) -> "StepLimitManager":
        """Create manager from LangGraph state.

        Args:
            state: LangGraph agent state containing remaining_steps, etc.
            config: Optional step limit configuration.

        Returns:
            Initialized step limit manager.
        """
        raw_config = state.get("step_limit_config")
        if isinstance(raw_config, dict):
            step_limit_config = StepLimitConfig(**raw_config)
        else:
            step_limit_config = raw_config or config or StepLimitConfig()

        delegation_depth = state.get("delegation_depth")
        delegation_chain = state.get("delegation_chain")
        current_step = state.get("current_step", 0)

        # Restore remaining budget
        remaining_step_budget = state.get("remaining_step_budget")

        # Try to read from ContextVars if not in state (fallback for first step)
        if remaining_step_budget is None:
            try:
                remaining_step_budget = _REMAINING_STEP_BUDGET_CVAR.get()
            except LookupError:  # pragma: no cover - unreachable with default value, defensive code
                pass

        if delegation_depth is None:
            try:
                delegation_depth = _DELEGATION_DEPTH_CVAR.get()
            except LookupError:  # pragma: no cover - unreachable with default value, defensive code
                delegation_depth = 0

        if delegation_chain is None:
            try:
                delegation_chain = list(_DELEGATION_CHAIN_CVAR.get())
            except LookupError:  # pragma: no cover - unreachable with default value, defensive code
                delegation_chain = []

        manager = cls(
            config=step_limit_config,
            initial_delegation_depth=delegation_depth,
            parent_step_budget=remaining_step_budget,
        )
        manager.context.delegation_chain = list(delegation_chain)
        manager.context.current_step = current_step
        return manager

    def set_context(self) -> None:
        """Set context variables for downstream consumption (e.g. by delegation tools)."""
        _REMAINING_STEP_BUDGET_CVAR.set(self.context.remaining_step_budget)
        _DELEGATION_DEPTH_CVAR.set(self.context.delegation_depth)
        _DELEGATION_CHAIN_CVAR.set(tuple(self.context.delegation_chain))
        _STEP_LIMIT_CONFIG_CVAR.set(self.config)

    def to_state_update(self) -> dict[str, Any]:
        """Convert current context to LangGraph state update.

        Returns:
            Dictionary of state fields to update.
        """
        return {
            "current_step": self.context.current_step,
            "delegation_depth": self.context.delegation_depth,
            "delegation_chain": self.context.delegation_chain,
            "step_limit_config": asdict(self.config),
            "remaining_step_budget": self.context.remaining_step_budget,
        }
