"""Defines a weather tool that can be used to get the weather for a specified city.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from langchain_core.tools import tool
from pydantic import BaseModel

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherToolInputSchema(BaseModel):
    """Schema for weather tool input."""

    city: str


@tool(args_schema=WeatherToolInputSchema)
def weather_tool(city: str) -> str:
    """Gets the weather for a specified city.

    Args:
        city: The name of the city to get weather for.

    Returns:
        A string describing the weather conditions.
    """
    weather_data = {
        "Jakarta": "32°C, Partly cloudy with high humidity",
        "Singapore": "30°C, Scattered thunderstorms",
        "Tokyo": "25°C, Clear skies",
        "London": "18°C, Light rain",
        "New York": "22°C, Sunny",
    }

    city_name = city.strip().title()

    weather = weather_data.get(city_name)
    if weather:
        logger.info(f"Found weather for {city_name}: {weather}")
        return weather
    else:
        message = f"Weather data not available for {city}"
        logger.warning(message)
        return message
