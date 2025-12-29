from openai.types.shared.chat_model import ChatModel
from pydantic import BaseModel
from typing import Literal

class BrowserUseToolInput(BaseModel):
    """Input schema for Browser Use tool."""
    task: str

class BrowserUseToolConfig(BaseModel):
    """Tool configuration schema for Browser Use tool."""
    steel_api_key: str
    steel_base_url: str
    steel_ws_url: str
    steel_timeout_in_ms: int
    browser_use_llm_openai_api_key: str
    browser_use_llm_openai_model: ChatModel | str
    browser_use_llm_openai_temperature: float | None
    browser_use_llm_openai_reasoning_effort: Literal['minimal', 'low', 'medium', 'high']
    browser_use_llm_openai_base_url: str | None
    browser_use_page_extraction_llm_openai_api_key: str
    browser_use_page_extraction_llm_openai_model: ChatModel | str
    browser_use_page_extraction_llm_openai_temperature: float | None
    browser_use_page_extraction_llm_openai_reasoning_effort: Literal['minimal', 'low', 'medium', 'high']
    browser_use_page_extraction_llm_openai_base_url: str | None
    browser_use_extend_system_message: str | None
    browser_use_vision_detail_level: Literal['auto', 'low', 'high']
    browser_use_enable_cloud_sync: bool
    browser_use_logging_level: Literal['debug', 'info', 'warning', 'error', 'result']
    browser_use_llm_timeout_in_s: int
    browser_use_step_timeout_in_s: int
    browser_use_max_session_retries: int
    browser_use_session_retry_delay_in_s: float
