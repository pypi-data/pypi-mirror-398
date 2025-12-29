"""This is a tool that generates a tiny bar/line chart and returns it as a Command artifact.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

# Optional imports for chart rendering
import io

from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import BaseModel, Field

from aip_agents.a2a.types import MimeType
from aip_agents.utils.artifact_helpers import create_artifact_command

try:
    from PIL import Image, ImageDraw  # type: ignore

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None


class GraphCommandInput(BaseModel):
    """Input schema for a tiny bar/line chart artifact tool.

    Note: width/height are clamped to a small size to keep artifacts lightweight.
    """

    chart_type: str = Field(
        default="bar",
        description="Type of chart to generate (bar or line).",
        pattern="^(bar|line)$",
    )
    labels: list[str] = Field(
        default_factory=lambda: ["A", "B", "C"],
        description="Labels for categories",
    )
    values: list[float] = Field(
        default_factory=lambda: [10.0, 20.0, 15.0],
        description="Values corresponding to labels",
    )
    title: str = Field(default="Chart", description="Chart title (metadata only)")
    width: int = Field(default=64, ge=16, le=128, description="Desired image width in px (will be clamped)")
    height: int = Field(default=64, ge=16, le=128, description="Desired image height in px (will be clamped)")
    image_name: str = Field(default="chart", description="Base filename (without extension)")


class GraphArtifactCommandTool(BaseTool):
    """Generate a very small PNG chart and return it as a Command artifact."""

    name: str = "graph_generator_command"
    description: str = "Generate a tiny bar/line chart and return a lightweight PNG artifact using Command."
    args_schema: type[BaseModel] = GraphCommandInput

    def _run(  # noqa: PLR0913
        self,
        chart_type: str = "bar",
        labels: list[str] | None = None,
        values: list[float] | None = None,
        title: str = "Chart",
        width: int = 64,
        height: int = 64,
        image_name: str = "chart",
    ) -> Command:
        labels = labels or ["A", "B", "C"]
        values = values or [10.0, 20.0, 15.0]

        if not labels or len(labels) != len(values):
            return Command(update={"result": "Invalid input: labels and values must be non-empty and equal length."})

        # Clamp to very small size to keep base64 short
        img_w = max(16, min(int(width), 64))
        img_h = max(16, min(int(height), 64))

        png_bytes = self._render_tiny_chart(chart_type, labels, values, img_w, img_h)

        result_text = f"Generated tiny {chart_type} chart '{title}' with {len(labels)} points as {image_name}.png"
        metadata_delta = {
            "last_chart": {
                "name": f"{image_name}.png",
                "chart_type": chart_type,
                "title": title,
                "num_points": len(labels),
                "size": f"{img_w}x{img_h}",
            }
        }

        return create_artifact_command(
            result=result_text,
            artifact_data=png_bytes,
            artifact_name=f"{image_name}.png",
            artifact_description=f"Tiny {chart_type} chart: {title}",
            mime_type=MimeType.IMAGE_PNG,
            metadata_update=metadata_delta,
        )

    @staticmethod
    def _render_tiny_chart(
        chart_type: str,
        labels: list[str],
        values: list[float],
        width: int,
        height: int,
    ) -> bytes:
        """Render a tiny chart using only PIL to keep artifact size minimal.

        Args:
            chart_type (str): Type of chart to render ("bar" or "line").
            labels (list[str]): Labels for the data points.
            values (list[float]): Values to plot.
            width (int): Width of the chart image in pixels.
            height (int): Height of the chart image in pixels.

        Returns:
            bytes: PNG image data as bytes.
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL is not available for chart rendering")

        # Canvas and basic layout
        image = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(image)

        # Small margins for axes
        margin_left = max(3, width // 12)
        margin_right = max(2, width // 20)
        margin_top = max(3, height // 12)
        margin_bottom = max(6, height // 8)

        plot_w = max(1, width - margin_left - margin_right)
        plot_h = max(1, height - margin_top - margin_bottom)

        # Axes
        x0, y0 = margin_left, height - margin_bottom
        x1, y1 = width - margin_right, margin_top
        draw.line((x0, y0, x1, y0), fill="black")
        draw.line((x0, y0, x0, y1), fill="black")

        # Normalize values to plot height
        max_val = max(values + [1.0])
        n = len(values)
        if chart_type == "bar":
            # Thin bars to keep readable at tiny sizes
            bar_spacing = plot_w / max(n, 1)
            bar_w = max(1, int(bar_spacing * 0.6))
            for i, val in enumerate(values):
                x_center = x0 + int((i + 0.5) * bar_spacing)
                bar_h = int((val / max_val) * plot_h)
                x_left = x_center - bar_w // 2
                x_right = x_center + bar_w // 2
                y_top = y0 - bar_h
                draw.rectangle((x_left, y_top, x_right, y0), fill="#4C78A8")
        else:
            # Polyline with small points
            points = []
            step = plot_w / max(n, 1)
            for i, val in enumerate(values):
                x = x0 + int((i + 0.5) * step)
                y = y0 - int((val / max_val) * plot_h)
                points.append((x, y))
            if len(points) >= 2:  # noqa: PLR2004
                draw.line(points, fill="#F58518")
            for px, py in points:
                draw.ellipse((px - 1, py - 1, px + 1, py + 1), fill="#F58518")

        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
