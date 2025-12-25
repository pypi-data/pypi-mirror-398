"""MSN Weather Wrapper - A Python wrapper for MSN Weather services."""

__version__ = "1.9.9"

from msn_weather_wrapper.client import WeatherClient
from msn_weather_wrapper.models import Location, WeatherData

__all__ = ["WeatherClient", "WeatherData", "Location"]
