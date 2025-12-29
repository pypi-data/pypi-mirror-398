"""Production-ready tool output management system for LangGraph ReAct agents.

This module provides a comprehensive system for managing tool outputs in ReAct agents,
including secure reference resolution, lifecycle management, and hybrid storage patterns.

Key Features:
- Automatic and manual tool output storage with configurable lifecycle management
- Secure reference resolution with validation and sanitization
- LLM-friendly output summaries with data previews and tool context
- Production-ready error handling with specialized exceptions
- Memory management with automatic cleanup based on age and size limits

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import json
import re
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from re import Pattern
from typing import Any

from aip_agents.storage.providers.base import BaseStorageProvider, StorageError
from aip_agents.storage.providers.memory import InMemoryStorageProvider
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

# Constants for display formatting and reference resolution
STRING_TRUNCATION_LENGTH = 100
MAX_TOOL_ARGS_DISPLAY = 5
DATA_PREVIEW_TRUNCATION_LENGTH = 150
TOOL_OUTPUT_REFERENCE_PREFIX = "$tool_output."


class ToolReferenceError(Exception):
    """Specialized exception for tool output reference resolution errors.

    This exception is raised when there are issues with resolving tool output references,
    such as invalid reference syntax, missing outputs, or security violations.

    Attributes:
        reference: The original reference string that caused the error.
        call_id: The call ID that was attempted to be resolved, if applicable.
        details: Additional error details for debugging.
    """

    def __init__(
        self,
        message: str,
        reference: str | None = None,
        call_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize a ToolReferenceError.

        Args:
            message: Human-readable error message describing what went wrong.
            reference: The original reference string that caused the error, if applicable.
            call_id: The call ID that was attempted to be resolved, if applicable.
            details: Additional error details for debugging, if applicable.
        """
        super().__init__(message)
        self.reference = reference
        self.call_id = call_id
        self.details = details or {}

    def __str__(self) -> str:
        """Return a detailed string representation of the error.

        Returns:
            A formatted error message with context information.
        """
        parts = [super().__str__()]
        if self.reference:
            parts.append(f"Reference: {self.reference}")
        if self.call_id:
            parts.append(f"Call ID: {self.call_id}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


@dataclass
class ToolOutputConfig:
    """Configuration for tool output management system.

    This class defines the operational parameters for the tool output management
    system, including storage limits, cleanup intervals, and lifecycle policies.

    Attributes:
        max_stored_outputs: Maximum number of tool outputs to store simultaneously.
            When this limit is reached, oldest outputs are evicted. Defaults to 100.
        max_age_minutes: Maximum age in minutes for stored outputs before they
            become eligible for cleanup. Defaults to 60 minutes.
        cleanup_interval: Number of tool calls between automatic cleanup operations.
            Set to 0 to disable automatic cleanup. Defaults to 20.
        storage_provider: Optional storage provider for persistent storage.
            If None, uses in-memory storage (backward compatible). Defaults to None.
    """

    max_stored_outputs: int = 100
    max_age_minutes: int = 60
    cleanup_interval: int = 20
    storage_provider: BaseStorageProvider | None = None


@dataclass
class ToolOutput:
    """Container for tool outputs with optional data payload.

    This class represents tool output metadata and optionally the actual data.
    When used as metadata only, the data field is None and must be retrieved
    from storage. When loaded with data, it contains the complete output.

    Attributes:
        call_id: Unique identifier for this tool call, used for reference resolution.
        tool_name: Name of the tool that produced this output.
        timestamp: When this output was created and stored.
        size_bytes: Approximate size of the stored data in bytes for memory management.
        tool_args: Input arguments that were passed to the tool for this call.
        data: Optional actual output data. None when used as metadata only.
        data_description: Optional human-readable description of the data content,
            typically provided by the tool itself.
        tags: Optional list of tags for categorization and filtering.
        agent_name: Name of the agent that created this output, for multi-agent context.
    """

    call_id: str
    tool_name: str
    timestamp: datetime
    size_bytes: int
    tool_args: dict[str, Any]
    data: Any | None = None  # None when metadata only, populated when retrieved
    data_description: str | None = None
    tags: list[str] | None = None
    agent_name: str | None = None

    @property
    def is_metadata_only(self) -> bool:
        """Check if this instance contains only metadata without data."""
        return self.data is None

    def is_expired(self, max_age: timedelta) -> bool:
        """Check if this output has expired based on the given maximum age.

        Args:
            max_age (timedelta): The maximum age allowed before expiration.

        Returns:
            bool: True if the output has expired, False otherwise.
        """
        return datetime.now() - self.timestamp > max_age

    def get_data_preview(
        self, max_length: int = 200, storage_provider: BaseStorageProvider | None = None, thread_id: str | None = None
    ) -> str | None:
        """Get a truncated string representation of the stored data.

        Args:
            max_length: Maximum length of the preview string.
            storage_provider: Required only if data is not loaded.
            thread_id: Thread ID required for proper storage key generation.

        Returns:
            A string representation of the data, truncated if necessary. None if data is not found.
        """
        # If we have data, use it directly
        if self.data is not None:
            data_str = str(self.data)
            if len(data_str) <= max_length:
                return data_str
            return data_str[:max_length] + "..."

        if storage_provider is None or thread_id is None:
            return None

        try:
            # Use proper storage key format: thread_id:call_id
            storage_key = f"{thread_id}:{self.call_id}"
            actual_data = storage_provider.retrieve(storage_key)
            data_str = str(actual_data)
            if len(data_str) <= max_length:
                return data_str
            return data_str[:max_length] + "..."
        except Exception:
            return None

    def with_data(self, data: Any) -> "ToolOutput":
        """Create a new instance with data populated.

        Returns a new ToolOutput instance with the same metadata but with
        data field populated. Useful for converting metadata-only instances
        to complete instances.

        Args:
            data (Any): The actual output data to populate.

        Returns:
            ToolOutput: A new instance with data populated.
        """
        return ToolOutput(
            call_id=self.call_id,
            tool_name=self.tool_name,
            timestamp=self.timestamp,
            size_bytes=self.size_bytes,
            tool_args=self.tool_args,
            data=data,
            data_description=self.data_description,
            tags=self.tags,
            agent_name=self.agent_name,
        )


@dataclass
class StoreOutputParams:
    """Parameters for storing tool outputs.

    Reduces the number of arguments passed to store_output method.

    Attributes:
        call_id: Unique identifier for this tool call.
        tool_name: Name of the tool that produced the output.
        data: The actual output data to store.
        tool_args: Input arguments used for the tool call.
        thread_id: Thread/conversation ID to organize outputs by conversation.
        description: Optional human-readable description of the output.
        tags: Optional list of tags for categorization.
        agent_name: Name of the agent that created this output.
    """

    call_id: str
    tool_name: str
    data: Any
    tool_args: dict[str, Any]
    thread_id: str
    description: str | None = None
    tags: list[str] | None = None
    agent_name: str | None = None


class ToolOutputManager:
    """Production-ready tool output manager with comprehensive lifecycle management.

    This class provides centralized management of tool outputs including storage,
    retrieval, lifecycle management, and LLM-friendly summarization. It handles
    memory management through configurable cleanup policies and provides secure
    access to stored outputs.

    Key Features:
    - Automatic and manual storage of tool outputs with metadata
    - Configurable lifecycle management with age and size-based eviction
    - LLM-friendly summary generation with data previews and context
    - Memory management with size tracking and cleanup
    - Thread-safe operations with proper error handling and locking
    - Concurrent access support for multi-agent and parallel processing scenarios

    Attributes:
        config: Configuration object defining operational parameters.
    """

    def __init__(self, config: ToolOutputConfig):
        """Initialize the ToolOutputManager with the given configuration.

        Args:
            config: Configuration object defining storage limits and cleanup policies.
        """
        self.config = config
        self._outputs: dict[str, dict[str, ToolOutput]] = {}  # thread_id -> {call_id -> ToolOutput}
        self._call_count = 0
        self._total_size_bytes = 0
        self._lock = threading.RLock()  # Reentrant lock for nested operations

        # Initialize storage provider (backward compatible)
        self._storage_provider = config.storage_provider or InMemoryStorageProvider()

    def _get_storage_key(self, thread_id: str, call_id: str) -> str:
        """Generate storage key for thread-scoped tool output storage.

        Args:
            thread_id: The thread/conversation ID.
            call_id: The tool call ID.

        Returns:
            Storage key in the format "thread_id:call_id".
        """
        return f"{thread_id}:{call_id}"

    def _is_external_storage(self) -> bool:
        """Check if the current storage provider is external (not in-memory).

        Returns:
            True if using external storage, False if using in-memory storage.
        """
        return not isinstance(self._storage_provider, InMemoryStorageProvider)

    def store_output(
        self,
        params: StoreOutputParams,
    ) -> None:
        """Store a tool output with automatic cleanup and size management.

        This method stores a tool output along with its metadata, automatically
        handling size limits, cleanup, and memory management. If the same call_id
        is used multiple times within the same thread, the previous output will be overwritten.

        Thread-safe: This method uses internal locking to ensure safe concurrent access.

        Args:
            params: StoreOutputParams containing all necessary parameters including thread_id.

        Raises:
            Exception: If storage operation fails for any reason.
        """
        with self._lock:
            try:
                # Initialize thread storage if it doesn't exist
                if params.thread_id not in self._outputs:
                    self._outputs[params.thread_id] = {}

                if params.call_id in self._outputs[params.thread_id]:
                    logger.warning(
                        f"Overwriting existing tool output for call_id: {params.call_id} in thread: {params.thread_id}"
                    )
                    self._cleanup_single_output(params.call_id, params.thread_id)

                # Ensure thread still exists after cleanup (in case it became empty)
                if params.thread_id not in self._outputs:
                    self._outputs[params.thread_id] = {}

                thread_outputs = self._outputs[params.thread_id]

                size_bytes = self._calculate_size(params.data)

                # Check if we need to evict oldest across all threads
                total_outputs = sum(len(thread_outputs) for thread_outputs in self._outputs.values())
                if total_outputs >= self.config.max_stored_outputs:
                    self._evict_oldest()

                try:
                    # Use thread_id + call_id as storage key to avoid conflicts across threads
                    storage_key = self._get_storage_key(params.thread_id, params.call_id)
                    logger.debug(f"Storing data with key: {storage_key}")
                    self._storage_provider.store(storage_key, params.data)

                    logger.debug(
                        f"Stored in {type(self._storage_provider).__name__} for {params.call_id} "
                        f"(thread: {params.thread_id}): {size_bytes} bytes"
                    )

                except StorageError as e:
                    logger.error(f"Storage error for {params.call_id} in thread {params.thread_id}: {e}")
                    raise
                except Exception as e:
                    logger.error(
                        f"Unexpected error storing output for {params.call_id} in thread {params.thread_id}: {e}"
                    )
                    raise

                # Store metadata only (actual data is in storage provider)
                thread_outputs[params.call_id] = ToolOutput(
                    call_id=params.call_id,
                    tool_name=params.tool_name,
                    timestamp=datetime.now(),
                    size_bytes=size_bytes,
                    tool_args=params.tool_args,
                    data=None,  # Metadata only - data stays in storage provider
                    data_description=params.description,
                    tags=params.tags,
                    agent_name=params.agent_name,
                )

                # Update size tracking and call count
                self._total_size_bytes += size_bytes
                self._call_count += 1

                # Perform periodic cleanup if configured
                if self.config.cleanup_interval > 0 and self._call_count % self.config.cleanup_interval == 0:
                    self._cleanup_expired()

                storage_type = type(self._storage_provider).__name__
                total_outputs_after = sum(len(thread_outputs) for thread_outputs in self._outputs.values())
                logger.debug(
                    f"Stored output for {params.call_id} (thread: {params.thread_id}): {size_bytes} bytes "
                    f"in {storage_type}, total: {total_outputs_after} outputs ({self._total_size_bytes} bytes)"
                )

            except Exception as e:
                logger.error(f"Failed to store tool output for {params.call_id} in thread {params.thread_id}: {e}")
                raise

    def get_output(self, call_id: str, thread_id: str) -> ToolOutput | None:
        """Retrieve a stored tool output by its call ID and thread ID.

        Thread-safe: This method uses internal locking to ensure safe concurrent access.

        Args:
            call_id: The unique identifier for the tool call.
            thread_id: The thread/conversation ID to search in.

        Returns:
            The ToolOutput object with data if found, None otherwise.
        """
        with self._lock:
            thread_outputs = self._outputs.get(thread_id, {})
            if call_id not in thread_outputs:
                logger.debug(f"Call ID {call_id} not found in thread {thread_id}")
                return None

            try:
                # Get metadata
                metadata = thread_outputs[call_id]

                # Retrieve data using thread-specific storage key
                storage_key = self._get_storage_key(thread_id, call_id)
                logger.debug(f"Retrieving data with key: {storage_key}")
                data = self._storage_provider.retrieve(storage_key)
                return metadata.with_data(data)

            except KeyError:
                # Data missing from storage, clean up metadata
                logger.warning(f"Data missing for {call_id} in thread {thread_id}, cleaning up metadata")
                thread_outputs.pop(call_id, None)
                return None
            except StorageError as e:
                logger.error(f"Storage error retrieving {call_id} from thread {thread_id}: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error retrieving {call_id} from thread {thread_id}: {e}")
                return None

    def has_outputs(self, thread_id: str | None = None) -> bool:
        """Check if any outputs are currently stored.

        Thread-safe: This method uses internal locking to ensure safe concurrent access.

        Args:
            thread_id: Optional thread ID to check for outputs in a specific thread.
                If None, checks across all threads.

        Returns:
            True if there are stored outputs, False otherwise.
        """
        with self._lock:
            if thread_id:
                return len(self._outputs.get(thread_id, {})) > 0
            else:
                return any(len(thread_outputs) > 0 for thread_outputs in self._outputs.values())

    def generate_summary(self, thread_id: str, max_entries: int = 10) -> str:
        """Generate an LLM-friendly structured summary as JSON.

        This method creates a comprehensive, structured summary of stored outputs that
        can be easily parsed by LLMs and other systems. The JSON format provides rich
        metadata and context about each tool output.

        Thread-safe: This method uses internal locking to ensure safe concurrent access.

        Args:
            thread_id: Thread ID to generate summary for.
            max_entries: Maximum number of entries to include in the summary.
                Defaults to 10.

        Returns:
            A JSON string containing structured data about tool outputs. Always returns
            valid JSON, even when no outputs are stored (empty entries list).
        """
        return self._generate_json_summary(thread_id, max_entries)

    def _generate_json_summary(self, thread_id: str, max_entries: int) -> str:
        """Generate simplified JSON summary optimized for LLM prompts.

        Args:
            thread_id: Thread ID to generate summary for.
            max_entries: Maximum number of entries to include in the summary.
            Defaults to 10.

        Returns:
            A JSON string containing structured data about tool outputs. Always returns
            valid JSON, even when no outputs are stored (empty entries list).
        """
        with self._lock:
            thread_outputs = self._outputs.get(thread_id, {})

            sorted_outputs = sorted(
                thread_outputs.values(),
                key=lambda x: x.timestamp,
                reverse=True,
            )[:max_entries]

            outputs = []
            for output in sorted_outputs:
                data_preview = output.get_data_preview(
                    DATA_PREVIEW_TRUNCATION_LENGTH, self._storage_provider, thread_id
                )

                entry = {
                    "reference": f"{TOOL_OUTPUT_REFERENCE_PREFIX}{output.call_id}",
                    "tool": output.tool_name,
                }
                if output.data_description:
                    entry["description"] = output.data_description
                if output.agent_name:
                    entry["agent"] = output.agent_name
                if data_preview:
                    entry["data_preview"] = data_preview
                outputs.append(entry)

            return json.dumps(outputs, indent=2)

    def _format_tool_args(self, tool_args: dict[str, Any]) -> dict[str, Any]:
        """Format tool arguments with preview values for display in LLM context.

        Creates a dictionary with truncated values that provides a preview of tool
        arguments without overwhelming the LLM context. Limits to first 3 arguments
        and recursively truncates large values within those arguments.

        Args:
            tool_args: Dictionary of tool arguments to format.

        Returns:
            Dictionary with same keys but truncated/preview values. If more than
            3 arguments provided, includes "..." key with count of remaining args.
            None if tool_args is empty.

        Examples:
            Simple arguments (no truncation):
            >>> args = {"x": 5, "y": 10, "operation": "add"}
            >>> manager._format_tool_args(args)
            {'x': 5, 'y': 10, 'operation': 'add'}

            Arguments with large data:
            >>> args = {"data": list(range(100)), "format": "json"}
            >>> manager._format_tool_args(args)
            {'data': [0, 1, 2, '... and 97 more items'], 'format': 'json'}

            Many arguments (limited to 3):
            >>> args = {f"param_{i}": f"value_{i}" for i in range(5)}
            >>> manager._format_tool_args(args)
            {'param_0': 'value_0', 'param_1': 'value_1', 'param_2': 'value_2', '...': 'and 2 more args'}

            Empty arguments:
            >>> manager._format_tool_args({})
            {}

            Mixed argument types:
            >>> args = {"query": ("very long search query that definitely exceeds the "
            ...              "fifty character limit"), "limit": 100,
            ...              "filters": {"status": "active", "type": ["user", "admin", "guest"]}}
            >>> manager._format_tool_args(args)
            {'query': 'very long search query that definitely ex...', 'limit': 100,
             'filters': {'status': 'active', 'type': ['user', 'admin', 'guest']}}
        """
        if not tool_args:
            return {}

        formatted_args = {}

        # Show first 3 arguments with truncation for long values
        for key, value in list(tool_args.items())[:MAX_TOOL_ARGS_DISPLAY]:
            formatted_args[key] = self._truncate_value(value)

        # Add indicator if there are more arguments
        if len(tool_args) > MAX_TOOL_ARGS_DISPLAY:
            formatted_args["..."] = f"and {len(tool_args) - MAX_TOOL_ARGS_DISPLAY} more args"

        return formatted_args

    def _truncate_string(self, value: str) -> str:
        """Truncate a string if it exceeds the maximum length.

        Args:
            value: The string to potentially truncate.

        Returns:
            The truncated string with "..." suffix if needed, otherwise the original string.
        """
        if len(value) > STRING_TRUNCATION_LENGTH:
            return value[: STRING_TRUNCATION_LENGTH - 3] + "..."
        return value

    def _truncate_collection(self, collection: list | tuple, item_type: str) -> list:
        """Truncate a collection (list or tuple) if it exceeds the maximum display size.

        Args:
            collection: The collection to truncate.
            item_type: Type name for the collection items (used in truncation message).

        Returns:
            Truncated collection with recursive value truncation.
        """
        if len(collection) > MAX_TOOL_ARGS_DISPLAY:
            truncated_items = [self._truncate_value(item) for item in collection[:MAX_TOOL_ARGS_DISPLAY]]
            truncated_items.append(f"... and {len(collection) - MAX_TOOL_ARGS_DISPLAY} more {item_type}")
            return truncated_items
        return [self._truncate_value(item) for item in collection]

    def _truncate_dict(self, value: dict) -> dict:
        """Truncate a dictionary if it exceeds the maximum display size.

        Args:
            value: The dictionary to truncate.

        Returns:
            Truncated dictionary with recursive value truncation.
        """
        if len(value) > MAX_TOOL_ARGS_DISPLAY:
            truncated = {}
            for key in list(value.keys())[:MAX_TOOL_ARGS_DISPLAY]:
                truncated[key] = self._truncate_value(value[key])
            truncated["..."] = f"and {len(value) - MAX_TOOL_ARGS_DISPLAY} more keys"
            return truncated
        return {key: self._truncate_value(val) for key, val in value.items()}

    def _truncate_value(self, value: Any) -> Any:
        """Truncate a single value for preview display in LLM context.

        Recursively truncates values to prevent overwhelming the LLM context with
        large data structures. Uses configurable limits for strings (50 chars) and
        collections (3 items/keys). Preserves data structure while limiting size.

        Args:
            value: The value to truncate. Can be any type (str, list, dict, etc.).

        Returns:
            Truncated version of the value maintaining the same type where possible.
            Large strings get "..." suffix, large collections show first 3 items
            with count of remaining items.

        Examples:
            String truncation:
            >>> manager._truncate_value("This is a very long string that definitely "
            ...                              "exceeds the fifty character limit we have set")
            'This is a very long string that definitely ex...'

            >>> manager._truncate_value("short string")
            'short string'

            List truncation:
            >>> manager._truncate_value([1, 2, 3, 4, 5, 6, 7])
            [1, 2, 3, '... and 4 more items']

            >>> manager._truncate_value([1, 2])
            [1, 2]

            Dictionary truncation:
            >>> data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
            >>> manager._truncate_value(data)
            {'a': 1, 'b': 2, 'c': 3, '...': 'and 2 more keys'}

            >>> manager._truncate_value({"x": 1, "y": 2})
            {'x': 1, 'y': 2}

            Nested structure truncation:
            >>> nested = {"data": [1, 2, 3, 4, 5], "meta": {"type": "test", "count": 100}}
            >>> manager._truncate_value(nested)
            {'data': [1, 2, 3, '... and 2 more items'], 'meta': {'type': 'test', 'count': 100}}

            Non-collection types:
            >>> manager._truncate_value(42)
            42

            >>> manager._truncate_value(None)
            None
        """
        if isinstance(value, str):
            return self._truncate_string(value)
        elif isinstance(value, list | tuple):
            return self._truncate_collection(value, "items")
        elif isinstance(value, dict):
            return self._truncate_dict(value)
        else:
            # For other types, convert to string and truncate if needed
            str_value = str(value)
            if len(str_value) > STRING_TRUNCATION_LENGTH:
                return str_value[: STRING_TRUNCATION_LENGTH - 3] + "..."
            return value

    def _cleanup_single_output(self, call_id: str, thread_id: str) -> None:
        """Clean up a single output from all storage.

        Args:
            call_id: The call ID to clean up
            thread_id: The thread ID containing the output
        """
        thread_outputs = self._outputs.get(thread_id, {})
        if call_id in thread_outputs:
            output = thread_outputs.pop(call_id)
            self._total_size_bytes -= output.size_bytes

            # Clean up empty thread
            if not thread_outputs:
                self._outputs.pop(thread_id, None)

        try:
            storage_key = self._get_storage_key(thread_id, call_id)
            self._storage_provider.delete(storage_key)
        except Exception as e:
            logger.warning(f"Failed to delete {call_id} from thread {thread_id} storage: {e}")

    def _cleanup_expired(self) -> None:
        """Remove expired outputs based on the configured maximum age.

        This method is called periodically to remove outputs that have exceeded
        the maximum age configured in the system. It helps prevent unbounded
        memory growth in long-running agent sessions.

        Note: This method assumes it's called within a lock context from store_output.
        """
        max_age = timedelta(minutes=self.config.max_age_minutes)
        expired_count = 0

        # Iterate through all threads and find expired outputs
        for thread_id, thread_outputs in list(self._outputs.items()):
            expired_call_ids = [call_id for call_id, output in thread_outputs.items() if output.is_expired(max_age)]

            for call_id in expired_call_ids:
                self._cleanup_single_output(call_id, thread_id)
                logger.debug(f"Cleaned up expired output: {call_id} from thread {thread_id}")
                expired_count += 1

        if expired_count > 0:
            logger.debug(f"Cleaned up {expired_count} expired outputs across all threads")

    def _evict_oldest(self) -> None:
        """Evict the oldest output to make room for a new one.

        This method is called when the storage limit is reached and removes
        the output with the earliest timestamp to maintain the size limit.

        Note: This method assumes it's called within a lock context from store_output.
        """
        oldest_output = None
        oldest_thread_id = None
        oldest_call_id = None

        # Find the oldest output across all threads
        for thread_id, thread_outputs in self._outputs.items():
            for call_id, output in thread_outputs.items():
                if oldest_output is None or output.timestamp < oldest_output.timestamp:
                    oldest_output = output
                    oldest_thread_id = thread_id
                    oldest_call_id = call_id

        if oldest_output and oldest_thread_id and oldest_call_id:
            # Clean up the oldest output
            self._cleanup_single_output(oldest_call_id, oldest_thread_id)
            logger.debug(f"Evicted oldest output: {oldest_call_id} from thread {oldest_thread_id}")

    def _calculate_size(self, data: Any) -> int:
        """Calculate the approximate size of data in bytes for memory management.

        This method provides a simple approximation of data size for memory
        management purposes. It handles common data types efficiently without
        the overhead of serialization libraries like pickle.

        Args:
            data: The data to calculate size for.

        Returns:
            Approximate size in bytes.
        """
        try:
            if isinstance(data, str):
                return len(data.encode("utf-8"))
            elif isinstance(data, dict | list):
                return len(json.dumps(data, default=str).encode("utf-8"))
            else:
                return sys.getsizeof(str(data))
        except Exception:
            # Fallback for any JSON serialization issues
            return sys.getsizeof(str(data))

    def clear_all(self) -> None:
        """Clear all stored outputs from both metadata and storage.

        Warning:
            This operation is irreversible and will remove all stored tool outputs.
        """
        # Clear storage
        try:
            self._storage_provider.clear()
        except NotImplementedError:
            # Fall back to individual deletes for storage providers that don't support clear
            for thread_id, thread_outputs in self._outputs.items():
                for call_id in thread_outputs.keys():
                    try:
                        storage_key = self._get_storage_key(thread_id, call_id)
                        self._storage_provider.delete(storage_key)
                    except Exception as e:
                        logger.warning(f"Failed to delete {call_id} from thread {thread_id} during clear_all: {e}")
        except Exception as e:
            logger.error(f"Failed to clear storage: {e}")

        # Clear metadata
        self._outputs.clear()
        self._total_size_bytes = 0

        logger.info("Cleared all stored outputs")

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics for monitoring and debugging.

        Returns:
            Dictionary containing storage statistics.
        """
        # Count total outputs across all threads
        total_outputs = sum(len(thread_outputs) for thread_outputs in self._outputs.values())

        # All outputs use the same storage type, so calculate based on storage provider
        external_count = total_outputs if self._is_external_storage() else 0

        return {
            "total_outputs": total_outputs,
            "total_size_bytes": self._total_size_bytes,
            "external_storage_count": external_count,
            "memory_storage_count": total_outputs - external_count,
            "storage_provider_type": type(self._storage_provider).__name__,
        }


class ToolReferenceResolver:
    """Secure and efficient tool output reference resolution system.

    This class handles the resolution of tool output references in a secure manner,
    preventing injection attacks while providing simple and reliable access to
    stored tool outputs. It uses a whitelist approach with regex validation to
    ensure only safe references are processed.

    Security Features:
    - Strict regex pattern matching for reference syntax
    - Whitelist-based validation to prevent injection attacks
    - Fail-fast error handling with detailed error messages
    - Input sanitization and validation at multiple levels

    Supported Reference Syntax:
    - $tool_output.<call_id> - Direct reference to a tool output by call ID

    Attributes:
        config: Configuration object for operational parameters.
    """

    def __init__(self, config: ToolOutputConfig):
        """Initialize the ToolReferenceResolver with security configuration.

        Args:
            config: Configuration object defining operational parameters.
        """
        self.config = config

        # Compile regex pattern for performance
        self._pattern: Pattern = re.compile(r"^\$tool_output\.([a-zA-Z0-9_-]{1,50})$")

    def resolve_references(
        self,
        args: dict[str, Any],
        manager: ToolOutputManager,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve all tool output references in the given arguments dictionary.

        This method recursively processes a dictionary of tool arguments, finding
        and resolving any tool output references. It supports nested dictionaries
        and lists, providing comprehensive reference resolution.

        Args:
            args: Dictionary of tool arguments that may contain references.
            manager: ToolOutputManager instance to resolve references against.
            thread_id: Optional thread ID for context-aware resolution.

        Returns:
            New dictionary with all references resolved to their actual values.

        Raises:
            ToolReferenceError: If any reference is invalid or cannot be resolved.
        """
        resolved = {}

        for key, value in args.items():
            resolved[key] = self._resolve_value(value, manager, thread_id)

        return resolved

    def _resolve_value(self, value: Any, manager: ToolOutputManager, thread_id: str | None = None) -> Any:
        """Resolve a single value that may be a reference, dict, list, or primitive.

        Args:
            value: The value to resolve.
            manager: ToolOutputManager instance to resolve references against.
            thread_id: Optional thread ID for context-aware resolution.

        Returns:
            The resolved value.
        """
        if isinstance(value, str) and value.startswith(TOOL_OUTPUT_REFERENCE_PREFIX):
            logger.debug(f"Resolved reference {value}")
            return self._resolve_single_reference(value, manager, thread_id)
        elif isinstance(value, dict):
            return self.resolve_references(value, manager, thread_id)
        elif isinstance(value, list):
            return self._resolve_list(value, manager, thread_id)
        else:
            return value

    def _resolve_list(self, items: list[Any], manager: ToolOutputManager, thread_id: str | None = None) -> list[Any]:
        """Resolve all items in a list that may contain references.

        Args:
            items: List of items to resolve.
            manager: ToolOutputManager instance to resolve references against.
            thread_id: Optional thread ID for context-aware resolution.

        Returns:
            List with all references resolved.
        """
        resolved_list = []
        for item in items:
            resolved_list.append(self._resolve_value(item, manager, thread_id))
        return resolved_list

    def _resolve_single_reference(
        self,
        reference: str,
        manager: ToolOutputManager,
        thread_id: str | None = None,
    ) -> Any:
        """Resolve a single tool output reference with comprehensive validation.

        This method handles the resolution of individual references with full
        security validation and error handling.

        Args:
            reference: The reference string to resolve (e.g., "$tool_output.abc123").
            manager: ToolOutputManager instance to resolve against.
            thread_id: Optional thread ID for context-aware resolution.

        Returns:
            The actual data stored for the referenced call ID.

        Raises:
            ToolReferenceError: If the reference is invalid or cannot be resolved.
        """
        # Validate reference format with regex
        match = self._pattern.match(reference)
        if not match:
            raise ToolReferenceError(
                f"Invalid reference format: {reference}. Expected: $tool_output.<call_id>",
                reference=reference,
            )

        call_id = match.group(1)

        # Retrieve the stored output with thread context
        stored_output = manager.get_output(call_id, thread_id)
        if not stored_output:
            context_msg = f" in thread {thread_id}" if thread_id else ""
            raise ToolReferenceError(
                f"Tool output not found for call ID: {call_id}{context_msg}",
                reference=reference,
                call_id=call_id,
            )

        return stored_output.data
