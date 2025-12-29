from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger
from pydantic import BaseModel

logger: Incomplete

class WeatherToolInputSchema(BaseModel):
    """Schema for weather tool input."""
    city: str

def weather_tool(city: str) -> str:
    """Gets the weather for a specified city.

    Args:
        city: The name of the city to get weather for.

    Returns:
        A string describing the weather conditions.
    """
