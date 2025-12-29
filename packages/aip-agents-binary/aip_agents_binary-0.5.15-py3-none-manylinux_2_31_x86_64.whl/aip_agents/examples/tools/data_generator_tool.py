"""Tool that generates sample data with automatic output storage.

This tool demonstrates the tool output management system by generating
data that can be referenced by other tools.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import random
from typing import Any, Literal

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class DataInput(BaseModel):
    """Input schema for data generation."""

    data_type: Literal["sales", "scores", "growth"] = Field(
        default="sales",
        description="Type of data to generate",
    )
    size: int = Field(
        default=5,
        description="Number of data points",
        ge=1,
    )


class DataGeneratorTool(BaseTool):
    """Tool that generates sample datasets with automatic output storage."""

    name: str = "data_generator"
    description: str = "Generate sample datasets (sales, scores, growth data)"
    args_schema: type[BaseModel] = DataInput
    store_final_output: bool = True  # Enable automatic storage

    def _run(
        self,
        data_type: str = "sales",
        size: int = 5,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a sample dataset.

        Args:
            data_type: Type of data to generate
            size: Number of data points
            **kwargs: Additional arguments including tool output context

        Returns:
            Dictionary containing the generated data
        """
        if data_type == "sales":
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return {
                "title": "Monthly Sales Data",
                "labels": months[:size],
                "values": [random.randint(1000, 5000) for _ in range(size)],
                "units": "dollars",
            }

        elif data_type == "scores":
            students = [f"Student {i + 1}" for i in range(size)]
            return {
                "title": "Student Test Scores",
                "labels": students,
                "values": [random.randint(60, 100) for _ in range(size)],
                "units": "points",
            }

        else:  # growth
            quarters = [f"Q{i + 1}" for i in range(size)]
            base = 1000
            values = []
            for _ in range(size):
                base *= random.uniform(1.05, 1.25)  # Growth factor
                values.append(int(base))
            return {
                "title": "Quarterly Growth",
                "labels": quarters,
                "values": values,
                "units": "units",
            }

    async def _arun(
        self,
        data_type: str = "sales",
        size: int = 5,
        **kwargs,
    ) -> dict[str, Any]:
        """Async version of _run.

        Args:
            data_type (str, optional): Type of data to generate. Defaults to "sales".
            size (int, optional): Number of data points. Defaults to 5.
            **kwargs: Additional arguments including tool output context.

        Returns:
            dict[str, Any]: Dictionary containing the generated data.
        """
        return self._run(data_type, size, **kwargs)
