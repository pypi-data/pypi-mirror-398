from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
WEATHER_DATA: Incomplete

def get_weather(location: str) -> dict:
    """Gets detailed weather information for a specified location.

    Args:
        location: The name of the city to get weather for.

    Returns:
        A dictionary containing:
            - location: The requested location name
            - weather: A dictionary with temperature, conditions, and humidity
    """
weather_tool = get_weather
