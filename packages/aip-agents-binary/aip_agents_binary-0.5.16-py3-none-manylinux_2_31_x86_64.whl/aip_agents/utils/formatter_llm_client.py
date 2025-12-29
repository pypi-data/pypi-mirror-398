"""Utilities for working with the shared formatter LLM invoker.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from gllm_inference.builder import build_lm_invoker
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

FORMATTER_ENV_VAR = "DEFAULT_MODEL_FORMATTER"
T = TypeVar("T")


class FormatterInvokerUnavailableError(RuntimeError):
    """Raised when no formatter LLM invoker can be resolved."""


class FormatterInvocationError(RuntimeError):
    """Raised when invoking the formatter LLM fails."""


class FormatterLLMClient:
    """Stateful helper that manages formatter invoker resolution and execution."""

    def __init__(self) -> None:
        """Initialize the formatter LLM client with caching and thread safety."""
        self._failed_sentinel = object()
        self._invoker_cache: dict[str, BaseLMInvoker | object] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def seed_default(self, default_model_id: str | None) -> None:
        """Populate ``DEFAULT_MODEL_FORMATTER`` when unset.

        Args:
            default_model_id: Preferred formatter model id to use as a fallback.
        """
        current = self._normalize_model_id(os.getenv(FORMATTER_ENV_VAR))
        if current:
            return

        fallback = self._normalize_model_id(default_model_id)
        if fallback:
            os.environ[FORMATTER_ENV_VAR] = fallback

    def resolve_invoker(self, *, reset_cache: bool = False) -> BaseLMInvoker | None:
        """Return the cached formatter invoker, optionally refreshing it.

        Args:
            reset_cache: When True, clear the cached invoker before resolving.

        Returns:
            BaseLMInvoker | None: Cached invoker if the formatter is configured, otherwise None.
        """
        resolved = self._normalize_model_id(os.getenv(FORMATTER_ENV_VAR))
        if not resolved:
            logger.warning("DEFAULT_MODEL_FORMATTER is not set; formatter summaries are disabled.")
            return None

        with self._lock:
            if reset_cache:
                self._invoker_cache.pop(resolved, None)

            cached = self._invoker_cache.get(resolved)
            if cached is self._failed_sentinel:
                return None
            if cached is not None:
                return cached  # type: ignore[return-value]

            try:
                invoker = build_lm_invoker(model_id=resolved)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Failed to initialize formatter LLM invoker (%s): %s", resolved, exc)
                self._invoker_cache[resolved] = self._failed_sentinel
                return None

            self._invoker_cache[resolved] = invoker
            return invoker

    async def invoke(
        self,
        *args: Any,
        invoker: BaseLMInvoker | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any:
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
        resolved = invoker or self.resolve_invoker()
        if not resolved:
            raise FormatterInvokerUnavailableError("Formatter LLM invoker is unavailable.")

        try:
            invocation = resolved.invoke(*args, **kwargs)
            if timeout is not None:
                async with asyncio.timeout(timeout):
                    return await invocation
            return await invocation
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            raise FormatterInvocationError("Formatter LLM invocation timed out") from None
        except Exception as exc:  # pragma: no cover - best effort
            raise FormatterInvocationError(f"Formatter LLM invocation failed: {exc}") from exc

    def invoke_blocking(
        self,
        *args: Any,
        invoker: BaseLMInvoker | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke the formatter LLM from synchronous contexts.

        Args:
            *args: Positional arguments forwarded to ``invoke``.
            invoker: Optional invoker to reuse.
            timeout: Optional timeout (seconds) for the async invocation.
            **kwargs: Keyword arguments forwarded to ``invoke``.

        Returns:
            Any: Result returned by the formatter LLM.
        """

        async def _runner() -> Any:
            return await self.invoke(*args, invoker=invoker, timeout=timeout, **kwargs)

        return self._run_coroutine_blocking(_runner)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_model_id(value: str | None) -> str | None:
        """Strip whitespace and return the model id when a value was provided.

        Args:
            value: Raw model identifier pulled from the environment.

        Returns:
            str | None: Sanitized model id or None when the input was blank.
        """
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        return None

    def _run_coroutine_blocking(self, factory: Callable[[], Awaitable[T]]) -> T:
        """Execute an awaitable from sync code, even when a loop is already running.

        Args:
            factory: Callable returning the coroutine to execute.

        Returns:
            T: Result of the awaited coroutine.
        """

        async def _wrapper() -> T:
            return await factory()

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_wrapper())

        result: dict[str, T] = {}
        error: list[BaseException] = []
        done = threading.Event()

        def _thread_runner() -> None:
            try:
                value = asyncio.run(_wrapper())
                result["value"] = value
            except Exception as exc:
                error.append(exc)
            finally:
                done.set()

        thread = threading.Thread(target=_thread_runner, daemon=True)
        thread.start()
        done.wait()
        thread.join()

        if error:
            raise error[0]
        return result["value"]


_formatter_llm_client = FormatterLLMClient()


def get_formatter_llm_client() -> FormatterLLMClient:
    """Return the process-wide formatter LLM client."""
    return _formatter_llm_client


def seed_formatter_llm_default(default_model_id: str | None) -> None:
    """Convenience wrapper for seeding the formatter default model.

    Args:
        default_model_id: Formatter model identifier to seed when missing.
    """
    get_formatter_llm_client().seed_default(default_model_id)
