from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger
from collections.abc import Awaitable as Awaitable
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker
from typing import Any, TypeVar

logger: Incomplete
FORMATTER_ENV_VAR: str
T = TypeVar('T')

class FormatterInvokerUnavailableError(RuntimeError):
    """Raised when no formatter LLM invoker can be resolved."""
class FormatterInvocationError(RuntimeError):
    """Raised when invoking the formatter LLM fails."""

class FormatterLLMClient:
    """Stateful helper that manages formatter invoker resolution and execution."""
    def __init__(self) -> None:
        """Initialize the formatter LLM client with caching and thread safety."""
    def seed_default(self, default_model_id: str | None) -> None:
        """Populate ``DEFAULT_MODEL_FORMATTER`` when unset.

        Args:
            default_model_id: Preferred formatter model id to use as a fallback.
        """
    def resolve_invoker(self, *, reset_cache: bool = False) -> BaseLMInvoker | None:
        """Return the cached formatter invoker, optionally refreshing it.

        Args:
            reset_cache: When True, clear the cached invoker before resolving.

        Returns:
            BaseLMInvoker | None: Cached invoker if the formatter is configured, otherwise None.
        """
    async def invoke(self, *args: Any, invoker: BaseLMInvoker | None = None, timeout: float | None = None, **kwargs: Any) -> Any:
        """Dispatch formatter prompts asynchronously with timeout/error handling.

        Args:
            *args: Positional arguments forwarded to the invoker.
            invoker: Explicit invoker instance to reuse instead of resolving one.
            timeout: Optional timeout (seconds) enforced with ``asyncio.timeout``.
            **kwargs: Keyword arguments forwarded to the invoker.

        Returns:
            Any: Result returned by the formatter LLM.

        Raises:
            FormatterInvokerUnavailableError: If no formatter model is configured.
            FormatterInvocationError: When the invocation fails or exceeds the timeout.
        """
    def invoke_blocking(self, *args: Any, invoker: BaseLMInvoker | None = None, timeout: float | None = None, **kwargs: Any) -> Any:
        """Invoke the formatter LLM from synchronous contexts.

        Args:
            *args: Positional arguments forwarded to ``invoke``.
            invoker: Optional invoker to reuse.
            timeout: Optional timeout (seconds) for the async invocation.
            **kwargs: Keyword arguments forwarded to ``invoke``.

        Returns:
            Any: Result returned by the formatter LLM.
        """

def get_formatter_llm_client() -> FormatterLLMClient:
    """Return the process-wide formatter LLM client."""
def seed_formatter_llm_default(default_model_id: str | None) -> None:
    """Convenience wrapper for seeding the formatter default model.

    Args:
        default_model_id: Formatter model identifier to seed when missing.
    """
