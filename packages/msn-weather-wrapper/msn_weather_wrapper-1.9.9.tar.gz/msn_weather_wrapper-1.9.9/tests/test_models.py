"""Tests for data models."""

import pytest
from pydantic import ValidationError

from msn_weather_wrapper.models import Location, WeatherData


def test_location_creation() -> None:
    """Test location model creation."""
    location = Location(city="Paris", country="France")
    assert location.city == "Paris"
    assert location.country == "France"
    assert location.latitude is None
    assert location.longitude is None


def test_location_with_coordinates() -> None:
    """Test location with coordinates."""
    location = Location(city="New York", country="USA", latitude=40.7128, longitude=-74.0060)
    assert location.latitude == 40.7128
    assert location.longitude == -74.0060


def test_weather_data_creation() -> None:
    """Test weather data model creation."""
    location = Location(city="Tokyo", country="Japan")
    weather = WeatherData(
        location=location, temperature=25.5, condition="Cloudy", humidity=65, wind_speed=15.0
    )
    assert weather.location == location
    assert weather.temperature == 25.5
    assert weather.condition == "Cloudy"
    assert weather.humidity == 65
    assert weather.wind_speed == 15.0


def test_weather_data_validation() -> None:
    """Test weather data validation."""
    location = Location(city="Berlin", country="Germany")

    # Invalid humidity (>100)
    with pytest.raises(ValidationError):
        WeatherData(
            location=location, temperature=20.0, condition="Rainy", humidity=150, wind_speed=10.0
        )

    # Invalid wind speed (negative)
    with pytest.raises(ValidationError):
        WeatherData(
            location=location, temperature=20.0, condition="Rainy", humidity=50, wind_speed=-5.0
        )
