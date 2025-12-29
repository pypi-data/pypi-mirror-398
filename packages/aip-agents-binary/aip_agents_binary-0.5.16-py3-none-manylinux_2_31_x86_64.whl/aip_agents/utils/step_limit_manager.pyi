from _typeshed import Incomplete
from aip_agents.schema.step_limit import MaxDelegationDepthExceededError as MaxDelegationDepthExceededError, MaxStepsExceededError as MaxStepsExceededError, StepLimitConfig as StepLimitConfig, StepLimitErrorResponse as StepLimitErrorResponse, StepLimitErrorType as StepLimitErrorType
from dataclasses import dataclass, field
from typing import Any

@dataclass
class StepExecutionContext:
    """Runtime context for tracking step execution and delegation depth.

    Attributes:
        current_step: Current step number (0-indexed).
        delegation_depth: Current depth in delegation chain (0 for root agent).
        remaining_step_budget: Steps remaining before limit is hit.
        delegation_chain: List of agent names in the delegation chain.
    """
    current_step: int = ...
    delegation_depth: int = ...
    remaining_step_budget: int | None = ...
    delegation_chain: list[str] = field(default_factory=list)

class StepLimitManager:
    """Manages step and delegation limit enforcement during agent execution.

    This manager integrates with LangGraph's existing step mechanisms and adds
    delegation depth tracking and budget propagation.

    Attributes:
        config: Step limit configuration.
        context: Current execution context.
    """
    config: Incomplete
    context: Incomplete
    def __init__(self, config: StepLimitConfig | None = None, initial_delegation_depth: int = 0, parent_step_budget: int | None = None) -> None:
        """Initialize step limit manager.

        Args:
            config: Optional step limit configuration. Uses defaults if None.
            initial_delegation_depth: Starting delegation depth (from parent).
            parent_step_budget: Remaining step budget inherited from parent agent.
        """
    def check_step_limit(self, agent_name: str = 'agent', count: int = 1) -> None:
        """Check if taking 'count' steps would exceed limit.

        Args:
            agent_name: Name of the agent to identify in error message.
            count: Number of steps to check (useful for parallel tool batches).

        Raises:
            MaxStepsExceededError: If max_steps limit is exceeded.
        """
    def check_delegation_depth(self, target_agent_name: str) -> None:
        """Check if delegation to target agent would exceed depth limit.

        Args:
            target_agent_name: Name of the agent to delegate to.

        Raises:
            MaxDelegationDepthExceededError: If delegation depth limit exceeded.
        """
    def increment_step(self, count: int = 1) -> None:
        """Increment step counter and update remaining budget.

        Args:
            count: Number of steps to consume (defaults to 1).
        """
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
    def add_to_delegation_chain(self, agent_name: str) -> None:
        """Add agent to delegation chain for tracking.

        Args:
            agent_name: Name of the agent being delegated to.
        """
    @classmethod
    def from_state(cls, state: dict[str, Any], config: StepLimitConfig | None = None) -> StepLimitManager:
        """Create manager from LangGraph state.

        Args:
            state: LangGraph agent state containing remaining_steps, etc.
            config: Optional step limit configuration.

        Returns:
            Initialized step limit manager.
        """
    def set_context(self) -> None:
        """Set context variables for downstream consumption (e.g. by delegation tools)."""
    def to_state_update(self) -> dict[str, Any]:
        """Convert current context to LangGraph state update.

        Returns:
            Dictionary of state fields to update.
        """
