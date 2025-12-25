"""Performance benchmarks using pytest-benchmark.

These tests measure the performance of core operations to track
performance regressions over time.
"""

import pytest

from msn_weather_wrapper import Location, WeatherClient
from msn_weather_wrapper.models import WeatherData


@pytest.mark.benchmark(group="client")
def test_client_initialization_benchmark(benchmark):
    """Benchmark WeatherClient initialization time."""
    result = benchmark(WeatherClient)
    assert result is not None


@pytest.mark.benchmark(group="client")
def test_client_context_manager_benchmark(benchmark):
    """Benchmark WeatherClient context manager overhead."""

    def context_manager_usage():
        with WeatherClient() as client:
            return client

    result = benchmark(context_manager_usage)
    assert result is not None


@pytest.mark.benchmark(group="models")
def test_location_creation_benchmark(benchmark):
    """Benchmark Location model instantiation."""
    result = benchmark(Location, city="London", country="UK")
    assert result.city == "London"
    assert result.country == "UK"


@pytest.mark.benchmark(group="models")
def test_location_with_coordinates_benchmark(benchmark):
    """Benchmark Location creation with coordinates."""
    result = benchmark(
        Location, city="Tokyo", country="Japan", latitude=35.6762, longitude=139.6503
    )
    assert result.latitude == 35.6762
    assert result.longitude == 139.6503


@pytest.mark.benchmark(group="models")
def test_weather_data_creation_benchmark(benchmark):
    """Benchmark WeatherData model instantiation."""
    location = Location(city="Paris", country="France")

    def create_weather():
        return WeatherData(
            location=location,
            temperature=20.5,
            condition="Partly Cloudy",
            humidity=65,
            wind_speed=15.2,
        )

    result = benchmark(create_weather)
    assert result.temperature == 20.5
    assert result.condition == "Partly Cloudy"


@pytest.mark.benchmark(group="parsing")
def test_temperature_parsing_benchmark(benchmark):
    """Benchmark temperature value parsing."""
    from bs4 import BeautifulSoup

    from msn_weather_wrapper.client import WeatherClient

    client = WeatherClient()
    html_content = '<span class="cur-temp">72°</span>'
    soup = BeautifulSoup(html_content, "html.parser")

    def parse_temp():
        return client._extract_temperature(soup)

    result = benchmark(parse_temp)
    assert result == 72.0


@pytest.mark.benchmark(group="parsing")
def test_condition_parsing_benchmark(benchmark):
    """Benchmark weather condition extraction."""
    from bs4 import BeautifulSoup

    from msn_weather_wrapper.client import WeatherClient

    client = WeatherClient()
    html_content = '<div class="condition">Sunny</div>'
    soup = BeautifulSoup(html_content, "html.parser")

    def parse_condition():
        return client._extract_condition(soup)

    result = benchmark(parse_condition)
    assert result == "Sunny"


@pytest.mark.benchmark(group="conversion")
def test_fahrenheit_to_celsius_benchmark(benchmark):
    """Benchmark temperature conversion from Fahrenheit to Celsius."""

    def convert_temp():
        fahrenheit = 72
        celsius = (fahrenheit - 32) * 5 / 9
        return round(celsius, 2)

    result = benchmark(convert_temp)
    assert abs(result - 22.22) < 0.01


@pytest.mark.benchmark(group="conversion")
def test_mph_to_kmh_benchmark(benchmark):
    """Benchmark wind speed conversion from MPH to km/h."""

    def convert_speed():
        mph = 10
        kmh = mph * 1.60934
        return round(kmh, 2)

    result = benchmark(convert_speed)
    assert abs(result - 16.09) < 0.01


@pytest.mark.benchmark(group="validation")
def test_location_validation_benchmark(benchmark):
    """Benchmark Location model validation."""

    def create_and_validate():
        return Location(
            city="New York",
            country="USA",
            latitude=40.7128,
            longitude=-74.0060,
        )

    result = benchmark(create_and_validate)
    assert result.city == "New York"


@pytest.mark.benchmark(group="validation")
def test_weather_data_validation_benchmark(benchmark):
    """Benchmark WeatherData model validation with all fields."""
    location = Location(city="Berlin", country="Germany")

    def create_and_validate():
        return WeatherData(
            location=location,
            temperature=15.5,
            condition="Cloudy",
            humidity=70,
            wind_speed=20.0,
        )

    result = benchmark(create_and_validate)
    assert result.humidity == 70
    assert result.wind_speed == 20.0


@pytest.mark.benchmark(group="string-ops")
def test_location_repr_benchmark(benchmark):
    """Benchmark Location __repr__ method."""
    location = Location(city="Sydney", country="Australia")

    def get_repr():
        return repr(location)

    result = benchmark(get_repr)
    assert "Sydney" in result
    assert "Australia" in result


@pytest.mark.benchmark(group="string-ops")
def test_weather_data_repr_benchmark(benchmark):
    """Benchmark WeatherData __repr__ method."""
    location = Location(city="Mumbai", country="India")
    weather = WeatherData(
        location=location,
        temperature=28.0,
        condition="Hot",
        humidity=80,
        wind_speed=10.0,
    )

    def get_repr():
        return repr(weather)

    result = benchmark(get_repr)
    assert "Mumbai" in result
    assert "28.0" in result
