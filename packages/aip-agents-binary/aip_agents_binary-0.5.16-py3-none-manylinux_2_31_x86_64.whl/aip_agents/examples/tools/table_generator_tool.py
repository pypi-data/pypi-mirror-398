"""Table generator tool for demonstrating artifact generation.

This tool generates sample data tables and returns both a markdown representation
for the agent and a CSV file artifact for the user.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import csv
import io
import random
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from aip_agents.a2a.types import MimeType
from aip_agents.utils.artifact_helpers import create_artifact_response


class TableGeneratorInput(BaseModel):
    """Input schema for table generator tool."""

    rows: int = Field(default=5, description="Number of rows to generate", ge=1, le=100)
    columns: list[str] = Field(default=["Name", "Age", "City"], description="Column names for the table")
    table_name: str = Field(default="sample_data", description="Name for the generated table")


class TableGeneratorTool(BaseTool):
    """Tool that generates sample data tables with artifact support.

    This tool demonstrates the standardized artifact format by:
    1. Generating sample data
    2. Creating a markdown table for the agent's context
    3. Creating a CSV file artifact for the user
    """

    name: str = "table_generator"
    description: str = "Generate sample data tables with specified columns and rows"
    args_schema: type[BaseModel] = TableGeneratorInput

    def _run(self, rows: int = 5, columns: list[str] = None, table_name: str = "sample_data") -> dict[str, Any]:
        """Generate a table synchronously.

        Args:
            rows (int, optional): Number of rows to generate. Defaults to 5.
            columns (list[str], optional): Column names for the table. Defaults to None.
            table_name (str, optional): Name for the generated table. Defaults to "sample_data".

        Returns:
            dict[str, Any]: Response containing artifact data and metadata.
        """
        if columns is None:
            columns = ["Name", "Age", "City"]

        # Generate sample data
        sample_data = self._generate_sample_data(rows, columns)

        # Create markdown table for agent
        markdown_table = self._create_markdown_table(sample_data, columns)

        # Create CSV data for artifact
        csv_data = self._create_csv_data(sample_data, columns)
        csv_bytes = csv_data.encode("utf-8")

        # Return standardized format using utility function
        return create_artifact_response(
            result=f"I have generated a {rows}-row table with columns: {', '.join(columns)}.\n\n{markdown_table}",
            artifact_data=csv_bytes,
            artifact_name=f"{table_name}.csv",
            artifact_description=f"Generated table with {rows} rows and {len(columns)} columns",
            mime_type=MimeType.TEXT_CSV,
        )

    async def _arun(self, rows: int = 5, columns: list[str] = None, table_name: str = "sample_data") -> dict[str, Any]:
        """Generate a table asynchronously.

        Args:
            rows (int, optional): Number of rows to generate. Defaults to 5.
            columns (list[str], optional): Column names for the table. Defaults to None.
            table_name (str, optional): Name for the generated table. Defaults to "sample_data".

        Returns:
            dict[str, Any]: Response containing artifact data and metadata.
        """
        return self._run(rows, columns, table_name)

    def _generate_sample_data(self, rows: int, columns: list[str]) -> list[list[str]]:
        """Generate sample data based on column names.

        Args:
            rows (int): Number of rows to generate.
            columns (list[str]): Column names for the table.

        Returns:
            list[list[str]]: Generated sample data as list of rows.
        """
        data = []
        for i in range(rows):
            row = []
            for col in columns:
                col_lower = col.lower()
                if "name" in col_lower:
                    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
                    row.append(random.choice(names))
                elif "age" in col_lower:
                    row.append(str(random.randint(20, 65)))
                elif "city" in col_lower:
                    cities = ["New York", "London", "Tokyo", "Paris", "Sydney", "Berlin", "Toronto", "Mumbai"]
                    row.append(random.choice(cities))
                elif "email" in col_lower:
                    domains = ["gmail.com", "yahoo.com", "outlook.com", "company.com"]
                    username = f"user{i + 1}"
                    row.append(f"{username}@{random.choice(domains)}")
                elif "score" in col_lower or "rating" in col_lower:
                    row.append(str(random.randint(1, 100)))
                else:
                    row.append(f"Value{i + 1}")
            data.append(row)
        return data

    def _create_markdown_table(self, data: list[list[str]], columns: list[str]) -> str:
        """Create a markdown table representation.

        Args:
            data (list[list[str]]): Table data as list of rows.
            columns (list[str]): Column names for the table.

        Returns:
            str: Markdown formatted table string.
        """
        if not data:
            return "| No data |\n|---------|"

        # Header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        # Rows
        rows = []
        for row in data:
            rows.append("| " + " | ".join(row) + " |")

        return "\n".join([header, separator] + rows)

    def _create_csv_data(self, data: list[list[str]], columns: list[str]) -> str:
        """Create CSV data string.

        Args:
            data (list[list[str]]): Table data as list of rows.
            columns (list[str]): Column names for the table.

        Returns:
            str: CSV formatted data string.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(columns)

        # Write data
        for row in data:
            writer.writerow(row)

        return output.getvalue()
