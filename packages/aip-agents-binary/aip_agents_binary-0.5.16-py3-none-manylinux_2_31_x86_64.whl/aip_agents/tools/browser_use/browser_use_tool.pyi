from _typeshed import Incomplete
from aip_agents.tools.browser_use import session_errors as session_errors
from aip_agents.tools.browser_use.action_parser import ActionParser as ActionParser
from aip_agents.tools.browser_use.llm_config import build_browser_use_llm as build_browser_use_llm, configure_browser_use_environment as configure_browser_use_environment
from aip_agents.tools.browser_use.schemas import BrowserUseToolConfig as BrowserUseToolConfig, BrowserUseToolInput as BrowserUseToolInput
from aip_agents.tools.browser_use.session import BrowserSession as BrowserSession
from aip_agents.tools.browser_use.steel_session_recording import SteelSessionRecorder as SteelSessionRecorder
from aip_agents.tools.browser_use.streaming import create_error_response as create_error_response, create_step_response as create_step_response, generate_step_content as generate_step_content, generate_thinking_message as generate_thinking_message, yield_iframe_activity as yield_iframe_activity, yield_status_message as yield_status_message, yield_thinking_marker as yield_thinking_marker
from aip_agents.tools.browser_use.structured_data_parser import detect_structured_data_failure as detect_structured_data_failure
from aip_agents.tools.browser_use.types import BrowserUseFatalError as BrowserUseFatalError, RetryDecision as RetryDecision, StreamingResponse as StreamingResponse, StreamingState as StreamingState, ToolCallInfo as ToolCallInfo
from aip_agents.utils.logger import get_logger as get_logger
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel as BaseModel

logger: Incomplete

class BrowserUseTool(BaseTool):
    """Tool to execute web automation tasks using browser-use framework.

    This tool provides step-by-step execution of browser automation tasks with detailed
    logging of intermediate steps, including the agent's thinking process, goals, and
    results at each step.
    """
    name: str
    description: str
    args_schema: type[BaseModel]
    tool_config_schema: type[BaseModel]
    MAX_SESSION_RELEASE_RETRIES: int
    SESSION_RELEASE_SLEEP_TIME_IN_S: int
    async def arun_streaming(self, task: str = None, config: RunnableConfig | None = None, **kwargs):
        """Execute a web automation task using browser-use asynchronously with streaming output.

        This method creates a Steel browser session, initializes a browser-use agent with
        the specified task, and executes the automation step by step, yielding results
        in streaming fashion. Starts background recording after completion.

        Args:
            task (str, optional): The task prompt for the AI agent to execute in the browser.
                                 If not provided, will attempt to extract from kwargs.
            config (RunnableConfig): RunnableConfig containing tool configuration.
            **kwargs: Additional parameters that may contain the task or other tool-specific arguments.

        Yields:
            dict: Step-by-step results in standardized StreamingResponse format.

        Raises:
            Exception: Any exception that occurs during task execution will be caught
                and yielded as an error message.
        """
