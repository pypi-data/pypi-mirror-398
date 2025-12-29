"""Configuration schemas for Browser Use tool.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

import os
from typing import Literal

from openai.types.shared.chat_model import ChatModel
from pydantic import BaseModel, Field


class BrowserUseToolInput(BaseModel):
    """Input schema for Browser Use tool."""

    task: str = Field(..., description="Task prompt for the AI agent to execute in the browser")


class BrowserUseToolConfig(BaseModel):
    """Tool configuration schema for Browser Use tool."""

    steel_api_key: str = Field(
        default_factory=lambda: os.getenv("STEEL_API_KEY"),
        description="Steel API key for Steel access",
    )
    steel_base_url: str = Field(
        default="https://api.steel.dev",
        description="Steel API base URL",
    )
    steel_ws_url: str = Field(
        default="wss://connect.steel.dev",
        description="Steel WebSocket URL for browser connection",
    )
    steel_timeout_in_ms: int = Field(
        default=600_000,
        description="Timeout for Steel operations in milliseconds",
    )

    browser_use_llm_openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API key for browser-use access",
    )
    browser_use_llm_openai_model: ChatModel | str = Field(
        default="o3",
        description="OpenAI model to use for browser-use agent",
    )
    browser_use_llm_openai_temperature: float | None = Field(
        default=None,
        description="Temperature setting for OpenAI model (None uses provider default)",
    )
    browser_use_llm_openai_reasoning_effort: Literal["minimal", "low", "medium", "high"] = Field(
        default="low",
        description="Reasoning effort for OpenAI model",
    )
    browser_use_llm_openai_base_url: str | None = Field(
        default=None,
        description="Base URL for OpenAI model (None uses provider default)",
    )

    browser_use_page_extraction_llm_openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API key for page extraction access",
    )
    browser_use_page_extraction_llm_openai_model: ChatModel | str = Field(
        default="gpt-5-mini",
        description="OpenAI model to use for page extraction",
    )
    browser_use_page_extraction_llm_openai_temperature: float | None = Field(
        default=None,
        description="Temperature setting for OpenAI model (None uses provider default)",
    )
    browser_use_page_extraction_llm_openai_reasoning_effort: Literal["minimal", "low", "medium", "high"] = Field(
        default="minimal",
        description="Reasoning effort for OpenAI model",
    )
    browser_use_page_extraction_llm_openai_base_url: str | None = Field(
        default=None,
        description="Base URL for OpenAI model (None uses provider default)",
    )

    browser_use_extend_system_message: str | None = Field(
        default=None,
        description="Extend system message for browser-use agent",
    )

    browser_use_vision_detail_level: Literal["auto", "low", "high"] = Field(
        default="auto",
        description="Detail level for vision",
    )

    browser_use_enable_cloud_sync: bool = Field(
        default=False,
        description="Enable Browser Use cloud sync and telemetry events",
    )

    browser_use_logging_level: Literal["debug", "info", "warning", "error", "result"] = Field(
        default="info",
        description="Logging verbosity for browser-use internals",
    )

    browser_use_llm_timeout_in_s: int = Field(
        default=60,
        description="Timeout for LLM in seconds",
    )
    browser_use_step_timeout_in_s: int = Field(
        default=180,
        description="Timeout for step in seconds",
    )
    browser_use_max_session_retries: int = Field(
        default=2,
        ge=0,
        description="How many times to recreate the Steel session after recoverable disconnects.",
    )
    browser_use_session_retry_delay_in_s: float = Field(
        default=3.0,
        ge=0.0,
        description="Delay (in seconds) before attempting to recover from a lost Steel session.",
    )
