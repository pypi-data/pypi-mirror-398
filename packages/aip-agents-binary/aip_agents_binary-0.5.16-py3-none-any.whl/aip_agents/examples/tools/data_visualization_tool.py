"""Tool that creates visualizations from data with automatic output storage.

This tool demonstrates the tool output management system by creating
visual charts from data (including referenced data from other tools).

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import io
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import BaseModel, Field

from aip_agents.a2a.types import MimeType
from aip_agents.utils.artifact_helpers import create_artifact_command

# Optional PIL import for image generation
try:
    from PIL import Image, ImageDraw  # type: ignore

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None


class ChartInput(BaseModel):
    """Input schema for chart generation."""

    data_source: Any = Field(
        description="Data to visualize (can be a reference like $tool_output.xyz)",
    )
    chart_type: str = Field(
        default="bar",
        description="Type of chart to generate (bar or line).",
        pattern="^(bar|line)$",
    )
    title: str = Field(
        default="Chart",
        description="Title for the visualization",
    )


class DataVisualizerTool(BaseTool):
    """Tool that creates visualizations with automatic output storage."""

    name: str = "data_visualizer"
    description: str = "Create visual charts from data (supports tool output references)"
    args_schema: type[BaseModel] = ChartInput

    def _run(
        self,
        data_source: Any,
        chart_type: str = "bar",
        title: str = "Chart",
        **kwargs,
    ) -> Command:
        """Create a visualization from data.

        Args:
            data_source: Data to visualize (can be a reference)
            chart_type: Type of chart (bar or line)
            title: Chart title
            **kwargs: Additional arguments including tool output context

        Returns:
            Command with visualization artifact and metadata
        """
        try:
            # Extract chartable data
            chart_data = self._extract_chart_data(data_source)
            if not chart_data:
                return Command(
                    update={
                        "result": f"❌ Cannot create {chart_type} chart: No valid data found",
                        "metadata": {"error": "No valid data found"},
                    }
                )

            # Generate the image
            image_bytes = self._create_chart_image(chart_data, chart_type, title)

            # Create artifact with proper encoding
            return create_artifact_command(
                result=f"✅ Created {chart_type} chart '{title}' with {len(chart_data['values'])} data points",
                artifact_data=image_bytes,
                artifact_name=f"{title.lower().replace(' ', '_')}_{chart_type}.png",
                artifact_description=f"{chart_type.capitalize()} chart: {title}",
                mime_type=MimeType.IMAGE_PNG,
                metadata_update={
                    "visualization": {
                        "success": True,
                        "chart_type": chart_type,
                        "title": title,
                        "data_points": len(chart_data["values"]),
                    }
                },
            )

        except Exception as e:
            return Command(
                update={"result": f"❌ Error creating visualization: {str(e)}", "metadata": {"error": str(e)}}
            )

    async def _arun(
        self,
        data_source: Any,
        chart_type: str = "bar",
        title: str = "Chart",
        **kwargs,
    ) -> Command:
        """Async version of _run.

        Args:
            data_source (Any): Data to visualize (can be a reference).
            chart_type (str, optional): Type of chart (bar or line). Defaults to "bar".
            title (str, optional): Chart title. Defaults to "Chart".
            **kwargs: Additional arguments including tool output context.

        Returns:
            Command: Command with visualization artifact and metadata.
        """
        return self._run(data_source, chart_type, title, **kwargs)

    def _extract_chart_data(self, data_source: Any) -> dict[str, Any]:
        """Extract chartable data from various formats.

        Args:
            data_source (Any): Data source to extract chartable data from.

        Returns:
            dict[str, Any]: Dictionary containing labels and values for charting.
        """
        if isinstance(data_source, dict):
            # Handle dict with values
            if "values" in data_source:
                return {
                    "values": data_source["values"][:10],  # Limit to 10 points
                    "labels": data_source.get("labels", [f"Point {i + 1}" for i in range(len(data_source["values"]))]),
                }
            # Handle dict with numbers
            numeric_items = [(str(k), float(v)) for k, v in data_source.items() if isinstance(v, int | float)][:10]
            if numeric_items:
                return {
                    "labels": [k for k, v in numeric_items],
                    "values": [v for k, v in numeric_items],
                }

        elif isinstance(data_source, list | tuple):
            # Handle numeric lists
            if all(isinstance(x, int | float) for x in data_source):
                return {
                    "values": data_source[:10],
                    "labels": [f"Point {i + 1}" for i in range(len(data_source[:10]))],
                }

        # Fallback for strings - character frequency
        elif isinstance(data_source, str):
            char_counts = {}
            for c in data_source[:100]:  # Limit input size
                if c.isalnum():
                    char_counts[c] = char_counts.get(c, 0) + 1
            if char_counts:
                items = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                return {
                    "labels": [k for k, v in items],
                    "values": [v for k, v in items],
                }

        return {}

    def _create_chart_image(
        self,
        chart_data: dict[str, Any],
        chart_type: str,
        title: str,
    ) -> bytes:
        """Create a chart image using PIL.

        Args:
            chart_data (dict[str, Any]): Data to visualize containing labels and values.
            chart_type (str): Type of chart to create.
            title (str): Title for the chart.

        Returns:
            bytes: Image data as PNG bytes.
        """
        if not PIL_AVAILABLE:
            # Fallback to text representation
            return self._create_text_chart(chart_data, chart_type, title)

        # Canvas setup
        width, height = 400, 300
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Draw title
        draw.text((10, 10), title[:40], fill="black")

        # Chart area
        chart_x, chart_y = 40, 40
        chart_width = width - 60
        chart_height = height - 80

        values = chart_data.get("values", [])
        labels = chart_data.get("labels", [])

        if not values:
            draw.text((chart_x, chart_y + 50), "No data to visualize", fill="red")
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            return buf.getvalue()

        # Normalize values
        max_val = max(values)
        min_val = min(values)
        val_range = max_val - min_val if max_val != min_val else 1

        if chart_type == "bar":
            # Bar chart
            bar_width = chart_width // len(values)
            for i, (label, value) in enumerate(zip(labels, values, strict=False)):
                x = chart_x + i * bar_width
                normalized_height = ((value - min_val) / val_range) * chart_height
                y = chart_y + chart_height - normalized_height

                # Draw bar
                draw.rectangle(
                    [x + 2, y, x + bar_width - 2, chart_y + chart_height],
                    fill="#4C78A8",
                    outline="black",
                )

                # Draw label
                label_text = str(label)[:8]
                draw.text(
                    (x + 2, chart_y + chart_height + 5),
                    label_text,
                    fill="black",
                )

        else:  # line chart
            # Calculate points
            points = []
            step = chart_width / (len(values) - 1) if len(values) > 1 else chart_width
            for i, value in enumerate(values):
                x = chart_x + i * step
                normalized_height = ((value - min_val) / val_range) * chart_height
                y = chart_y + chart_height - normalized_height
                points.append((x, y))

            # Draw lines
            MIN_POINTS_FOR_LINE = 2
            if len(points) >= MIN_POINTS_FOR_LINE:
                draw.line(points, fill="#F58518", width=2)

            # Draw points
            for x, y in points:
                draw.ellipse(
                    [x - 3, y - 3, x + 3, y + 3],
                    fill="#F58518",
                    outline="black",
                )

                # Draw value
                draw.text((x - 10, y - 15), str(round(values[points.index((x, y))], 1)), fill="black")

        # Save to bytes
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def _create_text_chart(
        self,
        chart_data: dict[str, Any],
        chart_type: str,
        title: str,
    ) -> bytes:
        """Fallback text-based chart when PIL is not available.

        Args:
            chart_data (dict[str, Any]): Data to visualize containing labels and values.
            chart_type (str): Type of chart to create.
            title (str): Title for the chart.

        Returns:
            bytes: Text chart data encoded as UTF-8 bytes.
        """
        values = chart_data.get("values", [])
        labels = chart_data.get("labels", [])

        lines = [
            f"=== {title} ===",
            f"Chart Type: {chart_type}",
            f"Data Points: {len(values)}",
            "",
        ]

        if values:
            max_val = max(values)
            for label, value in zip(labels, values, strict=False):
                bar_length = int((value / max_val) * 20) if max_val > 0 else 0
                bar = "█" * bar_length
                lines.append(f"{label[:10]:10} |{bar:20}| {value}")
        else:
            lines.append("No data to display")

        return "\n".join(lines).encode("utf-8")
