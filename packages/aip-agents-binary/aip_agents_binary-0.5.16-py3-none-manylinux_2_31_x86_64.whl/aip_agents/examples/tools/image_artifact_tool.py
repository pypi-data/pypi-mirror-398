"""Image artifact tool for demonstrating artifact generation.

This tool generates simple images and returns them as artifacts to demonstrate
the standardized artifact format for binary data.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import io
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from aip_agents.a2a.types import MimeType
from aip_agents.utils.artifact_helpers import create_artifact_response, create_error_response

# Optional PIL import for image generation
try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None


class ImageArtifactInput(BaseModel):
    """Input schema for image artifact tool."""

    width: int = Field(default=400, description="Width of the image in pixels", ge=100, le=1000)
    height: int = Field(default=300, description="Height of the image in pixels", ge=100, le=1000)
    color: str = Field(default="blue", description="Primary color for the image")
    text: str = Field(default="Sample Image", description="Text to display on the image")
    image_name: str = Field(default="generated_image", description="Name for the generated image")


class ImageArtifactTool(BaseTool):
    """Tool that generates simple images with artifact support.

    This tool demonstrates the standardized artifact format for binary data by:
    1. Generating a simple image using PIL
    2. Providing a confirmation message for the agent
    3. Creating an image file artifact for the user
    """

    name: str = "image_generator"
    description: str = "Generate simple images with text and colors"
    args_schema: type[BaseModel] = ImageArtifactInput

    def _run(
        self,
        width: int = 400,
        height: int = 300,
        color: str = "blue",
        text: str = "Sample Image",
        image_name: str = "generated_image",
    ) -> dict[str, Any]:
        """Generate an image synchronously.

        Args:
            width (int, optional): Width of the image in pixels. Defaults to 400.
            height (int, optional): Height of the image in pixels. Defaults to 300.
            color (str, optional): Primary color for the image. Defaults to "blue".
            text (str, optional): Text to display on the image. Defaults to "Sample Image".
            image_name (str, optional): Name for the generated image. Defaults to "generated_image".

        Returns:
            dict[str, Any]: Response containing artifact data and metadata.
        """
        if not PIL_AVAILABLE:
            return create_error_response("PIL (Pillow) library is not installed. Cannot generate images.")

        # Create image
        image = Image.new("RGB", (width, height), color=color)
        draw = ImageDraw.Draw(image)

        # Try to use a default font, fall back to basic font if not available
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Calculate text position (center)
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # Rough estimation for basic font
            text_width = len(text) * 6
            text_height = 11

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw text
        draw.text((x, y), text, fill="white", font=font)

        # Convert to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        return create_artifact_response(
            result=f"I have generated a {width}x{height} {color} image with the text '{text}'.",
            artifact_data=img_bytes,
            artifact_name=f"{image_name}.png",
            artifact_description=f"Generated {width}x{height} {color} image with text: {text}",
            mime_type=MimeType.IMAGE_PNG,
        )

    async def _arun(
        self,
        width: int = 400,
        height: int = 300,
        color: str = "blue",
        text: str = "Sample Image",
        image_name: str = "generated_image",
    ) -> dict[str, Any]:
        """Generate an image asynchronously.

        Args:
            width (int, optional): Width of the image in pixels. Defaults to 400.
            height (int, optional): Height of the image in pixels. Defaults to 300.
            color (str, optional): Primary color for the image. Defaults to "blue".
            text (str, optional): Text to display on the image. Defaults to "Sample Image".
            image_name (str, optional): Name for the generated image. Defaults to "generated_image".

        Returns:
            dict[str, Any]: Response containing artifact data and metadata.
        """
        return self._run(width, height, color, text, image_name)
