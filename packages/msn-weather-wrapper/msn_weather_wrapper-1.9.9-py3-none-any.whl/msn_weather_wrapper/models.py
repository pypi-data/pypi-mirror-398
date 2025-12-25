"""Data models for weather information."""

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location."""

    city: str = Field(description="City name")
    country: str = Field(description="Country name")
    latitude: float | None = Field(default=None, description="Latitude coordinate")
    longitude: float | None = Field(default=None, description="Longitude coordinate")


class WeatherData(BaseModel):
    """Weather data for a location."""

    location: Location = Field(description="Location information")
    temperature: float = Field(description="Temperature in Celsius")
    condition: str = Field(description="Weather condition description")
    humidity: int = Field(ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(ge=0, description="Wind speed in km/h")
