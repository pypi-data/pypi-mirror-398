"""Defines a weather tool that can be used to get the weather for a specified city.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

# Combined weather data storage with detailed information
WEATHER_DATA = {
    "Jakarta": {"temperature": "32°C", "conditions": "Partly cloudy with high humidity", "humidity": "78%"},
    "Singapore": {"temperature": "30°C", "conditions": "Scattered thunderstorms", "humidity": "85%"},
    "Tokyo": {"temperature": "25°C", "conditions": "Clear skies", "humidity": "65%"},
    "London": {"temperature": "18°C", "conditions": "Light rain", "humidity": "82%"},
    "New York": {"temperature": "22°C", "conditions": "Sunny", "humidity": "60%"},
    "Sydney": {"temperature": "24°C", "conditions": "Clear", "humidity": "70%"},
}


def get_weather(location: str) -> dict:
    """Gets detailed weather information for a specified location.

    Args:
        location: The name of the city to get weather for.

    Returns:
        A dictionary containing:
            - location: The requested location name
            - weather: A dictionary with temperature, conditions, and humidity
    """
    try:
        city_name = location.split(",")[0].strip().title()
        weather = WEATHER_DATA.get(city_name)

        if weather:
            logger.info(f"Found weather for {city_name}: {weather}")
            return {"location": city_name, "weather": weather}
        else:
            message = f"Weather data not available for {location}"
            logger.warning(message)
            return {
                "location": city_name,
                "weather": {"temperature": "Unknown", "conditions": "No data available", "humidity": "Unknown"},
                "message": message,
            }
    except Exception as e:
        error_msg = f"Error getting weather for {location}: {str(e)}"
        logger.error(error_msg)
        return {
            "location": location,
            "error": error_msg,
            "weather": {"temperature": "Error", "conditions": "Error retrieving data", "humidity": "Error"},
        }


# Alias for backward compatibility
weather_tool = get_weather
