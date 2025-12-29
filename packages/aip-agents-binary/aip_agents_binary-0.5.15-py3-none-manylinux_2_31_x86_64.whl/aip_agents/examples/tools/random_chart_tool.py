"""Tool that generates random bar chart artifacts for streaming demos."""

import io
import random
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import BaseModel, Field

from aip_agents.a2a.types import MimeType
from aip_agents.utils.artifact_helpers import create_artifact_command

DEFAULT_RANDOM_CHART_TITLE = "Random Insights"

try:
    from PIL import Image, ImageDraw  # type: ignore

    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover - PIL optional
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None


class RandomChartInput(BaseModel):
    """Input schema for random chart generation."""

    title: str = Field(
        default=DEFAULT_RANDOM_CHART_TITLE,
        description="Title rendered at the top of the chart.",
    )
    num_bars: int = Field(
        default=5,
        ge=3,
        le=10,
        description="How many bars to render.",
    )
    min_value: int = Field(
        default=10,
        ge=0,
        description="Minimum possible value for a bar.",
    )
    max_value: int = Field(
        default=100,
        gt=10,
        description="Maximum possible value for a bar.",
    )


class RandomChartTool(BaseTool):
    """Generate random bar chart images without relying on upstream data."""

    name: str = "random_chart_tool"
    description: str = "Create a random bar chart image artifact to showcase image streaming."
    args_schema: type[BaseModel] = RandomChartInput

    def _run(  # noqa: D401
        self,
        title: str = DEFAULT_RANDOM_CHART_TITLE,
        num_bars: int = 5,
        min_value: int = 10,
        max_value: int = 100,
        **kwargs: Any,
    ) -> Command:
        """Generate the chart synchronously."""
        if min_value >= max_value:
            return Command(
                update={"result": "❌ min_value must be less than max_value", "metadata": {"error": "invalid_range"}}
            )

        rng = random.Random()
        values = [rng.randint(min_value, max_value) for _ in range(num_bars)]
        labels = [f"Bar {i + 1}" for i in range(num_bars)]

        if PIL_AVAILABLE:
            image_bytes = self._create_image_with_pil(title, labels, values)
        else:
            image_bytes = self._create_text_artifact(title, labels, values)

        artifact_mime_type = MimeType.IMAGE_PNG if PIL_AVAILABLE else MimeType.TEXT_PLAIN
        return create_artifact_command(
            result=f"📊 Generated random bar chart '{title}' with {num_bars} bars",
            artifact_data=image_bytes,
            artifact_name=f"{title.lower().replace(' ', '_')}_random_chart.png",
            artifact_description=f"Random bar chart ({num_bars} bars)",
            mime_type=artifact_mime_type,
            metadata_update={
                "visualization": {
                    "chart_type": "bar",
                    "title": title,
                    "data_points": num_bars,
                    "randomized": True,
                }
            },
        )

    async def _arun(
        self,
        title: str = DEFAULT_RANDOM_CHART_TITLE,
        num_bars: int = 5,
        min_value: int = 10,
        max_value: int = 100,
        **kwargs: Any,
    ) -> Command:
        """Async wrapper for random chart generation."""
        return self._run(title=title, num_bars=num_bars, min_value=min_value, max_value=max_value, **kwargs)

    def _create_image_with_pil(self, title: str, labels: list[str], values: list[int]) -> bytes:
        width, height = 400, 300
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), title[:40], fill="black")

        chart_x, chart_y = 40, 50
        chart_width = width - 80
        chart_height = height - 100

        max_val = max(values)
        min_val = min(values)
        val_range = max_val - min_val if max_val != min_val else 1
        bar_width = chart_width // len(values)

        for idx, (label, value) in enumerate(zip(labels, values, strict=False)):
            x = chart_x + idx * bar_width
            normalized = (value - min_val) / val_range
            y = chart_y + chart_height - (normalized * chart_height)

            draw.rectangle([x + 2, y, x + bar_width - 4, chart_y + chart_height], fill="#4C78A8", outline="black")
            draw.text((x + 2, chart_y + chart_height + 5), label[:8], fill="black")

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def _create_text_artifact(self, title: str, labels: list[str], values: list[int]) -> bytes:
        max_val = max(values)
        lines = [f"=== {title} ===", "", "Random bar chart artifact", ""]
        for label, value in zip(labels, values, strict=False):
            length = int((value / max_val) * 30) if max_val else 0
            lines.append(f"{label:>8}: {'█' * length} ({value})")
        return "\n".join(lines).encode("utf-8")
