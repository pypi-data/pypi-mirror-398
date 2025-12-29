from _typeshed import Incomplete
from aip_agents.agent.hitl.manager import ApprovalManager as ApprovalManager

class HITLManagerRegistry:
    '''Global registry mapping request_id → owning ApprovalManager.

    Uses weak references to avoid preventing manager garbage collection.
    Thread-safe for concurrent agent execution.

    This singleton registry allows the HITL decision endpoint to route decisions
    to the correct manager in hierarchical agent setups, where a sub-agent may
    create a pending request but the parent agent receives the decision.

    Example:
        >>> from aip_agents.agent.hitl.registry import hitl_registry
        >>> # Manager auto-registers when creating requests
        >>> manager.create_approval_request(...)
        >>> # Later, decision handler looks up the owning manager
        >>> owning_manager = hitl_registry.get_manager(request_id)
        >>> owning_manager.resolve_pending_request(request_id, "approved")
    '''
    def __new__(cls) -> HITLManagerRegistry:
        """Ensure only one instance exists (singleton pattern).

        Returns:
            The singleton HITLManagerRegistry instance.
        """
    def register(self, request_id: str, manager: ApprovalManager) -> None:
        '''Register a pending request with its owning manager.

        This method is typically called automatically by ApprovalManager when
        creating a new pending request. It establishes the ownership mapping
        needed for proper decision routing.

        Args:
            request_id: Unique identifier for the pending request
            manager: ApprovalManager instance that owns this request

        Example:
            >>> hitl_registry.register("req_abc123", my_manager)
        '''
    def unregister(self, request_id: str) -> None:
        '''Remove a request from the registry.

        This method is called when a request is resolved, times out, or expires.
        It\'s important for cleanup to prevent the registry from growing unbounded.

        Args:
            request_id: Unique identifier to remove

        Example:
            >>> hitl_registry.unregister("req_abc123")
        '''
    def get_manager(self, request_id: str) -> ApprovalManager | None:
        '''Retrieve the manager owning a specific request.

        This is the primary lookup method used by decision handlers to route
        decisions to the correct manager in hierarchical agent setups.

        Args:
            request_id: Unique identifier to lookup

        Returns:
            ApprovalManager instance if found, None otherwise. None can indicate
            the request was resolved, timed out, or the manager was garbage collected.

        Example:
            >>> manager = hitl_registry.get_manager("req_abc123")
            >>> if manager:
            ...     manager.resolve_pending_request("req_abc123", "approved")
        '''
    def clear(self) -> None:
        """Clear all registrations.

        This method is primarily intended for testing to ensure a clean state
        between test cases. It removes all registered mappings.

        Warning:
            This should not be called in production code as it will prevent
            pending requests from being resolved.

        Example:
            >>> hitl_registry.clear()  # For testing only
        """
    def list_all(self) -> list[str]:
        '''List all currently registered request IDs.

        Returns:
            List of request IDs currently in the registry.

        Note:
            Due to weak references, managers may be garbage collected between
            calling this method and accessing them, so the actual available
            managers might be fewer than the returned list length.

        Example:
            >>> request_ids = hitl_registry.list_all()
            >>> print(f"Pending requests: {request_ids}")
        '''

hitl_registry: Incomplete
