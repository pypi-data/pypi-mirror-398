"""Utility helpers for loading local .env files in examples and apps."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def load_local_env(override: bool = True) -> None:
    """Load environment variables from a .env file if python-dotenv is available.

    Args:
        override (bool, optional): Whether to override existing environment variables. Defaults to True.
    """
    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError:
        logger.warning("Could not load .env file: python-dotenv not installed")
        return

    try:
        env_path = find_dotenv(usecwd=True)
        load_dotenv(env_path, override=override)
        logger.debug("Successfully loaded .env from %s", env_path)
    except Exception as exc:  # pragma: no cover - behaviour depends on environment
        logger.warning("Could not load .env file: %s", exc)
