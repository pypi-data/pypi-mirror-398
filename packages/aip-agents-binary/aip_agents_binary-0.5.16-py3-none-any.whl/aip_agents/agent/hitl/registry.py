"""Registry for tracking HITL approval manager ownership across agent hierarchies.

This module provides a thread-safe singleton registry that maps request IDs to their
owning ApprovalManager instances. This enables proper decision routing in hierarchical
agent architectures where sub-agents have HITL enabled but parents do not.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING
from weakref import WeakValueDictionary

if TYPE_CHECKING:
    from aip_agents.agent.hitl.manager import ApprovalManager


class HITLManagerRegistry:
    """Global registry mapping request_id → owning ApprovalManager.

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
    """

    _instance: HITLManagerRegistry | None = None
    _lock = threading.RLock()
    _registry: WeakValueDictionary[str, ApprovalManager]
    _registry_lock: threading.RLock

    def __new__(cls) -> HITLManagerRegistry:
        """Ensure only one instance exists (singleton pattern).

        Returns:
            The singleton HITLManagerRegistry instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._registry = WeakValueDictionary()
                    instance._registry_lock = threading.RLock()
                    cls._instance = instance
        return cls._instance

    def register(self, request_id: str, manager: ApprovalManager) -> None:
        """Register a pending request with its owning manager.

        This method is typically called automatically by ApprovalManager when
        creating a new pending request. It establishes the ownership mapping
        needed for proper decision routing.

        Args:
            request_id: Unique identifier for the pending request
            manager: ApprovalManager instance that owns this request

        Example:
            >>> hitl_registry.register("req_abc123", my_manager)
        """
        with self._registry_lock:
            self._registry[request_id] = manager

    def unregister(self, request_id: str) -> None:
        """Remove a request from the registry.

        This method is called when a request is resolved, times out, or expires.
        It's important for cleanup to prevent the registry from growing unbounded.

        Args:
            request_id: Unique identifier to remove

        Example:
            >>> hitl_registry.unregister("req_abc123")
        """
        with self._registry_lock:
            self._registry.pop(request_id, None)

    def get_manager(self, request_id: str) -> ApprovalManager | None:
        """Retrieve the manager owning a specific request.

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
        """
        with self._registry_lock:
            return self._registry.get(request_id)

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
        with self._registry_lock:
            self._registry.clear()

    def list_all(self) -> list[str]:
        """List all currently registered request IDs.

        Returns:
            List of request IDs currently in the registry.

        Note:
            Due to weak references, managers may be garbage collected between
            calling this method and accessing them, so the actual available
            managers might be fewer than the returned list length.

        Example:
            >>> request_ids = hitl_registry.list_all()
            >>> print(f"Pending requests: {request_ids}")
        """
        with self._registry_lock:
            return list(self._registry.keys())


# Global singleton instance
hitl_registry = HITLManagerRegistry()
