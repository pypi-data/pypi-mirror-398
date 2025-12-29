"""Tool to get the current time.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

from datetime import datetime

from gllm_core.schema import Chunk
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

FORMAT_STRING = "%m/%d/%y %H:%M:%S"


class TimeToolInput(BaseModel):
    """Input schema for the TimeTool."""

    datetime_format: str = Field(
        default=FORMAT_STRING,
        description="""
        Optional datetime format string. Default: '%m/%d/%y %H:%M:%S'

        Common format codes:
        %Y: Year with century (2024)
        %m: Month as number (01-12)
        %d: Day of month (01-31)
        %A: Full weekday name (Wednesday)
        %a: Short weekday name (Wed)
        %H: Hour (00-23)
        %M: Minute (00-59)
        %S: Second (00-59)
        %Z: Timezone name
        %j: Day of year (001-366)
        %W: Week number (00-53, Monday first)
        %U: Week number (00-53, Sunday first)
        %c: Locale's date and time
        %x: Locale's date
        %X: Locale's time
        """,
    )


class TimeTool(BaseTool):
    """Tool to get the current time."""

    name: str = "time_tool"
    description: str = """
    Useful for getting the current time in a specified format or the default format.
    Default format: '%m/%d/%y %H:%M:%S' (e.g., '05/15/24 17:30:00')
    """
    save_output_history: bool = True
    args_schema: type[BaseModel] = TimeToolInput

    def _run(self, datetime_format: str = FORMAT_STRING) -> str:
        """Get the current time formatted as a string.

        Args:
            datetime_format (str): The format string to use for the datetime output. Defaults to FORMAT_STRING.

        Returns:
            str: The current time formatted according to the provided format string.
        """
        return datetime.now().strftime(datetime_format)

    def _format_agent_reference(self, tool_output: str) -> list[Chunk]:
        """Format the tool output as a reference chunk for agent use.

        Args:
            tool_output (str): The output string from the tool execution.

        Returns:
            list[Chunk]: A list containing a single reference chunk with the tool output and metadata.
        """
        return [
            Chunk(
                content=tool_output,
                metadata={
                    "tool_name": self.name,
                },
            )
        ]
