"""Tool that wraps a LangGraph agent with time and weather tools.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import os
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from aip_agents.agent.langgraph_react_agent import LangGraphReactAgent
from aip_agents.examples.tools.langchain_weather_tool import weather_tool
from aip_agents.examples.tools.time_tool import TimeTool


class StreamingToolConfig(BaseModel):
    """Tool configuration schema for the LangGraph streaming tool."""

    time_format: str = Field(
        default="%m/%d/%y %H:%M:%S",
        description="DateTime format for time-related queries (e.g., '%Y-%m-%d %H:%M:%S', '%A, %B %d, %Y')",
    )


class LangGraphStreamingToolInput(BaseModel):
    """Input schema for the LangGraphStreamingTool."""

    query: str = Field(..., description="Query prompt for the LangGraph agent to execute")


class LangGraphStreamingTool(BaseTool):
    """Tool that wraps a LangGraph agent with time and weather forecast capabilities."""

    name: str = "langgraph_streaming_tool"
    description: str = (
        "Execute tasks using a LangGraph agent with time and weather capabilities. "
        "Can get current time in various formats and weather information for specific cities. "
        "Supports configuration for time format settings."
    )
    args_schema: type[BaseModel] = LangGraphStreamingToolInput
    tool_config_schema: type[BaseModel] = StreamingToolConfig
    _agent: Any = PrivateAttr()

    def __init__(self, model: Any = None, **kwargs):
        """Initialize the LangGraphStreamingTool.

        Args:
            model: The model to use for the agent.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        if model is None:
            model = os.getenv("DEFAULT_MODEL", "openai/gpt-4o")

        self._agent = LangGraphReactAgent(
            name="internal_time_weather_agent",
            instruction="You are a helpful assistant with access to time and weather tools. "
            "When users ask for both time and weather information, use BOTH tools: "
            "1. Use the time_tool to get current time information "
            "2. Use the weather_tool to get weather for specific cities "
            "Always provide complete answers using all relevant tools.",
            model=model,
            tools=[TimeTool(), weather_tool],
            description="Internal agent for time and weather tasks",
        )

    @property
    def agent(self):
        """Access the internal agent."""
        return self._agent

    def _run(self, query: str) -> str:
        """Run the tool synchronously.

        Args:
            query: The query to execute.

        Returns:
            The final output from the tool execution.
        """
        result = self.agent.run(query)
        if isinstance(result, dict) and "output" in result:
            return str(result["output"])
        return str(result)

    async def _arun(self, query: str) -> str:
        """Run the tool asynchronously.

        Args:
            query: The query to execute.

        Returns:
            The final output from the tool execution.
        """
        result = await self.agent.arun(query)
        if isinstance(result, dict) and "output" in result:
            return str(result["output"])
        return str(result)

    async def arun_streaming(self, query: str = None, config: RunnableConfig = None, **kwargs):
        """Execute the LangGraph agent asynchronously with A2A streaming output.

        Args:
            query: The query to execute.
            config: Tool configuration containing user context and preferences.
            **kwargs: Additional keyword arguments.

        Returns:
            An async generator that yields streaming events.
        """
        if query is None:
            query = kwargs.get("query") or kwargs.get("task")

        effective_config = self.get_tool_config(config)

        if not effective_config:
            effective_config = StreamingToolConfig(time_format="%m/%d/%y %H:%M:%S")

        try:
            enhanced_query = f"[Time format: {effective_config.time_format}] {query}"

            async for event in self.agent.arun_a2a_stream(enhanced_query, **kwargs):
                if event is not None and isinstance(event, dict):
                    yield event
        except Exception as e:
            yield {"event_type": "error", "content": f"Error in agent wrapper streaming: {str(e)}", "is_final": True}
