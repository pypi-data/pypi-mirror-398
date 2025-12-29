"""Weather Forecast Tool."""

from typing import Literal

# Predefined weather data for each day
DAILY_WEATHER = {
    "monday": {"condition": "sunny", "temp_low": 28, "temp_high": 32},
    "tuesday": {"condition": "partly cloudy", "temp_low": 25, "temp_high": 28},
    "wednesday": {"condition": "cloudy", "temp_low": 22, "temp_high": 25},
    "thursday": {"condition": "light rain", "temp_low": 20, "temp_high": 23},
    "friday": {"condition": "windy", "temp_low": 19, "temp_high": 24},
    "saturday": {"condition": "sunny", "temp_low": 27, "temp_high": 31},
    "sunday": {"condition": "partly cloudy", "temp_low": 24, "temp_high": 27},
}

DayOfWeek = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def get_weather_forecast(day: DayOfWeek) -> str:
    """Get the weather forecast for a specific day of the week.

    Args:
        day: The day of the week (monday, tuesday, wednesday, etc.)

    Returns:
        str: A weather forecast message including conditions and temperature.
    """
    # Get the predefined weather data for the day
    weather_data = DAILY_WEATHER[day]

    # Format the forecast message
    forecast = (
        f"Weather forecast for {day.capitalize()}: "
        f"{weather_data['condition'].capitalize()} with temperatures between "
        f"{weather_data['temp_low']}°C and {weather_data['temp_high']}°C"
    )

    return forecast
