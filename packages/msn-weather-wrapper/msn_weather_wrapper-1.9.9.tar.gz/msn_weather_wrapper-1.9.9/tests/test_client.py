"""Tests for the weather client."""

from unittest.mock import Mock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from msn_weather_wrapper.client import WeatherClient
from msn_weather_wrapper.models import Location


def test_weather_client_initialization() -> None:
    """Test weather client can be initialized."""
    client = WeatherClient(timeout=5)
    assert client.timeout == 5
    assert client.base_url == "https://www.msn.com/en-us/weather/forecast/in-"
    client.close()


def test_weather_client_context_manager() -> None:
    """Test weather client works as context manager."""
    with WeatherClient() as client:
        assert client is not None


@pytest.mark.integration
def test_get_weather_live() -> None:
    """Test getting weather data from live MSN Weather site.

    This is a live integration test that makes a real request to MSN Weather.
    It may fail if the website structure changes or network is unavailable.
    Run with: pytest -m integration
    """
    location = Location(city="London", country="UK")
    with WeatherClient(timeout=15) as client:
        try:
            weather = client.get_weather(location)
            assert weather.location == location
            assert isinstance(weather.temperature, float)
            assert -50 <= weather.temperature <= 60  # Reasonable temperature range in Celsius
            assert isinstance(weather.condition, str)
            assert len(weather.condition) > 0
            assert 0 <= weather.humidity <= 100
            assert weather.wind_speed >= 0
            print(f"\nLive weather data for {location.city}:")
            print(f"  Temperature: {weather.temperature}°C")
            print(f"  Condition: {weather.condition}")
            print(f"  Humidity: {weather.humidity}%")
            print(f"  Wind Speed: {weather.wind_speed} km/h")
        except ValueError as e:
            # Skip test if website structure has changed
            pytest.skip(f"MSN Weather website structure may have changed: {e}")


def test_extract_temperature() -> None:
    """Test temperature extraction from HTML."""
    html = """
    <html>
        <body>
            <span class="temp">72°F</span>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    temp = client._extract_temperature(soup)
    assert isinstance(temp, float)
    assert 20 <= temp <= 25  # 72°F is approximately 22°C
    client.close()


def test_extract_condition() -> None:
    """Test condition extraction from HTML."""
    html = """
    <html>
        <body>
            <div class="condition">Partly Cloudy</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    condition = client._extract_condition(soup)
    assert condition == "Partly Cloudy"
    client.close()


def test_extract_humidity() -> None:
    """Test humidity extraction from HTML."""
    html = """
    <html>
        <body>
            <div>Humidity: 65%</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    humidity = client._extract_humidity(soup)
    assert humidity == 65
    client.close()


def test_extract_wind_speed() -> None:
    """Test wind speed extraction from HTML."""
    html = """
    <html>
        <body>
            <div>Wind: 10 mph</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    wind_speed = client._extract_wind_speed(soup)
    assert isinstance(wind_speed, float)
    assert wind_speed > 0  # 10 mph converted to km/h
    client.close()


def test_extract_weather_from_json_success() -> None:
    """Test successful weather extraction from embedded JSON."""
    html = """
    <html>
        <body>
            <script type="application/json">
            {
                "WeatherData": {
                    "_@STATE@_": {
                        "forecast": [{
                            "hourly": [{
                                "cap": "Partly Cloudy",
                                "temperature": "68",
                                "humidity": "75",
                                "windSpeed": "8"
                            }]
                        }]
                    }
                }
            }
            </script>
        </body>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is not None
    assert "temperature" in result
    assert "condition" in result
    assert "humidity" in result
    assert "wind_speed" in result
    assert result["condition"] == "Partly Cloudy"
    assert result["humidity"] == 75
    client.close()


def test_extract_weather_from_json_no_script_tag() -> None:
    """Test weather extraction when no script tag exists."""
    html = "<html><body>No weather data here</body></html>"
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is None
    client.close()


def test_extract_weather_from_json_invalid_json() -> None:
    """Test weather extraction with invalid JSON."""
    html = """
    <html>
        <body>
            <script type="application/json">
            {invalid json}
            </script>
        </body>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is None
    client.close()


def test_extract_weather_from_json_missing_keys() -> None:
    """Test weather extraction with missing data keys."""
    html = """
    <html>
        <body>
            <script type="application/json">
            {"WeatherData": {}}
            </script>
        </body>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is None
    client.close()


@patch("msn_weather_wrapper.client.requests.Session.get")
def test_get_weather_with_json_extraction(mock_get) -> None:
    """Test get_weather using JSON extraction."""
    html = """
    <html>
        <body>
            <script type="application/json">
            {
                "WeatherData": {
                    "_@STATE@_": {
                        "forecast": [{
                            "hourly": [{
                                "cap": "Sunny",
                                "temperature": "75",
                                "humidity": "60",
                                "windSpeed": "5"
                            }]
                        }]
                    }
                }
            }
            </script>
        </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    location = Location(city="TestCity", country="TestCountry")
    client = WeatherClient()
    weather = client.get_weather(location)

    assert weather.location == location
    assert weather.condition == "Sunny"
    assert weather.humidity == 60
    assert isinstance(weather.temperature, float)
    assert isinstance(weather.wind_speed, float)
    client.close()


@patch("msn_weather_wrapper.client.requests.Session.get")
def test_get_weather_fallback_to_html(mock_get) -> None:
    """Test get_weather falls back to HTML parsing when JSON fails."""
    html = """
    <html>
        <body>
            <span class="temp">68°F</span>
            <div class="condition">Cloudy</div>
            <div>Humidity: 70%</div>
            <div>Wind: 12 mph</div>
        </body>
    </html>
    """
    mock_response = Mock()
    mock_response.text = html
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    location = Location(city="TestCity", country="TestCountry")
    client = WeatherClient()
    weather = client.get_weather(location)

    assert weather.location == location
    assert isinstance(weather.temperature, float)
    assert isinstance(weather.condition, str)
    assert isinstance(weather.humidity, int)
    assert isinstance(weather.wind_speed, float)
    client.close()


@patch("msn_weather_wrapper.client.requests.Session.get")
def test_get_weather_request_exception(mock_get) -> None:
    """Test get_weather handles request exceptions."""
    mock_get.side_effect = requests.RequestException("Network error")

    location = Location(city="TestCity", country="TestCountry")
    client = WeatherClient()

    with pytest.raises(requests.RequestException):
        client.get_weather(location)

    client.close()


def test_fahrenheit_to_celsius_conversion() -> None:
    """Test temperature conversion logic."""
    client = WeatherClient()

    # Test with known values
    html_32f = '<span class="temp">32°F</span>'
    soup = BeautifulSoup(html_32f, "lxml")
    temp = client._extract_temperature(soup)
    assert abs(temp - 0.0) < 0.1  # 32°F = 0°C

    html_212f = '<span class="temp">212°F</span>'
    soup = BeautifulSoup(html_212f, "lxml")
    temp = client._extract_temperature(soup)
    assert abs(temp - 100.0) < 0.1  # 212°F = 100°C

    client.close()


def test_extract_temperature_not_found() -> None:
    """Test temperature extraction when element not found."""
    html = "<html><body>No temperature here</body></html>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    with pytest.raises(ValueError, match="Could not extract temperature from page"):
        client._extract_temperature(soup)
    client.close()


def test_extract_condition_not_found() -> None:
    """Test condition extraction when element not found."""
    html = "<html><body>No condition here</body></html>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    condition = client._extract_condition(soup)
    assert condition == "Unknown"  # Default value
    client.close()


def test_extract_humidity_not_found() -> None:
    """Test humidity extraction when element not found."""
    html = "<html><body>No humidity here</body></html>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    humidity = client._extract_humidity(soup)
    assert humidity == 50  # Default value when not found
    client.close()


def test_extract_wind_speed_not_found() -> None:
    """Test wind speed extraction when element not found."""
    html = "<html><body>No wind data here</body></html>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    wind_speed = client._extract_wind_speed(soup)
    assert wind_speed == 0.0  # Default value
    client.close()


def test_mph_to_kmh_conversion() -> None:
    """Test wind speed conversion from mph to km/h."""
    html = "<div>Wind: 10 mph</div>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    wind_speed = client._extract_wind_speed(soup)
    expected = 10 * 1.60934  # mph to km/h
    assert abs(wind_speed - expected) < 0.1
    client.close()


def test_ms_to_kmh_conversion() -> None:
    """Test wind speed conversion from m/s to km/h."""
    html = "<div>Wind: 10 m/s</div>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    wind_speed = client._extract_wind_speed(soup)
    expected = 10 * 3.6  # m/s to km/h
    assert abs(wind_speed - expected) < 0.1
    client.close()


def test_extract_weather_json_empty_forecast() -> None:
    """Test JSON extraction when forecast array is empty."""
    html = """
    <html>
        <script type="application/json">
        {
            "WeatherData": {
                "_@STATE@_": {
                    "forecast": []
                }
            }
        }
        </script>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is None
    client.close()


def test_extract_weather_json_no_hourly() -> None:
    """Test JSON extraction when hourly data is missing."""
    html = """
    <html>
        <script type="application/json">
        {
            "WeatherData": {
                "_@STATE@_": {
                    "forecast": [{"daily": "data"}]
                }
            }
        }
        </script>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is None
    client.close()


def test_extract_weather_json_empty_hourly() -> None:
    """Test JSON extraction when hourly array is empty."""
    html = """
    <html>
        <script type="application/json">
        {
            "WeatherData": {
                "_@STATE@_": {
                    "forecast": [{"hourly": []}]
                }
            }
        }
        </script>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    assert result is None
    client.close()


def test_extract_weather_json_exception() -> None:
    """Test JSON extraction handles invalid data gracefully by returning defaults."""
    html = """
    <html>
        <script type="application/json">
        {
            "WeatherData": {
                "_@STATE@_": {
                    "forecast": [{"hourly": [{"temp": "invalid"}]}]
                }
            }
        }
        </script>
    </html>
    """
    client = WeatherClient()
    result = client._extract_weather_from_json(html)
    # Should return data with defaults when parsing fails
    assert result is not None
    assert result["condition"] == "Unknown"
    assert result["humidity"] == 50
    client.close()


def test_humidity_extraction_with_parent_element() -> None:
    """Test humidity extraction when found in parent element."""
    html = "<div class='humidity'>75%</div>"
    soup = BeautifulSoup(html, "lxml")
    client = WeatherClient()
    humidity = client._extract_humidity(soup)
    assert humidity == 75
    client.close()


@patch("msn_weather_wrapper.client.Nominatim")
def test_get_weather_by_coordinates_geocode_failure(mock_nominatim: Mock) -> None:
    """Test get_weather_by_coordinates when geocoding fails."""
    mock_geocoder = Mock()
    mock_geocoder.reverse.return_value = None
    mock_nominatim.return_value = mock_geocoder

    client = WeatherClient()
    with pytest.raises(ValueError, match="Could not determine location for coordinates"):
        client.get_weather_by_coordinates(51.5074, -0.1278)
    client.close()


@patch("msn_weather_wrapper.client.Nominatim")
def test_get_weather_by_coordinates_geocode_exception(mock_nominatim: Mock) -> None:
    """Test get_weather_by_coordinates when geocoding raises exception."""
    mock_geocoder = Mock()
    mock_geocoder.reverse.side_effect = Exception("Geocoding API error")
    mock_nominatim.return_value = mock_geocoder

    client = WeatherClient()
    with pytest.raises(ValueError, match="Failed to reverse geocode coordinates"):
        client.get_weather_by_coordinates(51.5074, -0.1278)
    client.close()
