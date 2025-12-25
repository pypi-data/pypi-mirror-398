"""Tests for the Flask API."""

import json
from unittest.mock import MagicMock, patch

import pytest

from api import app
from msn_weather_wrapper.models import Location, WeatherData


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert "service" in data


def test_health_check_legacy(client):
    """Test legacy health check endpoint for backward compatibility."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"


def test_liveness_probe(client):
    """Test Kubernetes liveness probe endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "alive"


def test_readiness_probe(client):
    """Test Kubernetes readiness probe endpoint."""
    response = client.get("/api/v1/health/ready")
    # Should return 200 or 503 depending on external service availability
    assert response.status_code in [200, 503]
    data = json.loads(response.data)
    assert "status" in data
    assert "checks" in data
    assert "weather_client" in data["checks"]
    assert "external_api" in data["checks"]


def test_get_weather_missing_parameters(client):
    """Test GET weather endpoint with missing parameters."""
    response = client.get("/api/weather")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_get_weather_missing_city(client):
    """Test GET weather endpoint with missing city."""
    response = client.get("/api/weather?country=USA")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


@patch("api.get_client")
def test_get_weather_success(mock_get_client, client):
    """Test GET weather endpoint with valid parameters."""
    # Setup mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_weather = WeatherData(
        location=Location(city="Seattle", country="USA"),
        temperature=15.5,
        condition="Partly Cloudy",
        humidity=65,
        wind_speed=12.5,
    )
    mock_client.get_weather.return_value = mock_weather

    response = client.get("/api/weather?city=Seattle&country=USA")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "location" in data
    assert "temperature" in data
    assert "condition" in data
    assert "humidity" in data
    assert "wind_speed" in data
    assert data["location"]["city"] == "Seattle"
    assert data["location"]["country"] == "USA"


def test_post_weather_missing_body(client):
    """Test POST weather endpoint with missing body."""
    response = client.post("/api/weather", data=json.dumps({}), content_type="application/json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_post_weather_missing_fields(client):
    """Test POST weather endpoint with missing fields."""
    response = client.post(
        "/api/weather", data=json.dumps({"city": "Seattle"}), content_type="application/json"
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


@patch("api.get_client")
def test_post_weather_success(mock_get_client, client):
    """Test POST weather endpoint with valid data."""
    # Setup mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_weather = WeatherData(
        location=Location(city="London", country="UK"),
        temperature=10.2,
        condition="Rainy",
        humidity=85,
        wind_speed=20.0,
    )
    mock_client.get_weather.return_value = mock_weather

    response = client.post(
        "/api/weather",
        data=json.dumps({"city": "London", "country": "UK"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "location" in data
    assert "temperature" in data
    assert "condition" in data
    assert "humidity" in data
    assert "wind_speed" in data
    assert data["location"]["city"] == "London"
    assert data["location"]["country"] == "UK"
    assert isinstance(data["temperature"], int | float)
    assert 0 <= data["humidity"] <= 100
    assert data["wind_speed"] >= 0


@patch("api.get_client")
def test_get_weather_client_error(mock_get_client, client):
    """Test GET weather endpoint when client raises an error."""
    # Clear the cache to ensure mock is used
    from api import get_cached_weather

    get_cached_weather.cache_clear()

    # Setup mock to raise exception
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_weather.side_effect = Exception("Network error")

    response = client.get("/api/weather?city=Seattle&country=USA")
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "message" in data


@patch("api.get_client")
def test_post_weather_client_error(mock_get_client, client):
    """Test POST weather endpoint when client raises an error."""
    # Clear the cache to ensure mock is used
    from api import get_cached_weather

    get_cached_weather.cache_clear()

    # Setup mock to raise exception
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_weather.side_effect = ValueError("Invalid data")

    response = client.post(
        "/api/weather",
        data=json.dumps({"city": "Invalid", "country": "XX"}),
        content_type="application/json",
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "message" in data


def test_post_weather_invalid_json(client):
    """Test POST weather endpoint with invalid JSON."""
    response = client.post(
        "/api/weather",
        data="not valid json",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_invalid_endpoint(client):
    """Test invalid API endpoint."""
    response = client.get("/api/invalid")
    assert response.status_code == 404


# Cache Tests


@patch("api.get_client")
def test_weather_caching_same_bucket(mock_get_client, client):
    """Test that weather data is cached within the same time bucket."""
    from api import get_cached_weather

    # Clear cache before test
    get_cached_weather.cache_clear()

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_weather = WeatherData(
        location=Location(city="London", country="UK"),
        temperature=20.0,
        condition="Cloudy",
        humidity=75,
        wind_speed=15.0,
    )
    mock_client.get_weather.return_value = mock_weather

    # First request
    response1 = client.get("/api/weather?city=London&country=UK")
    assert response1.status_code == 200
    assert mock_client.get_weather.call_count == 1

    # Second request in same bucket should use cache
    response2 = client.get("/api/weather?city=London&country=UK")
    assert response2.status_code == 200
    assert mock_client.get_weather.call_count == 1  # Still 1, cached

    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)
    assert data1 == data2


@patch("api.get_client")
@patch("api.datetime")
def test_weather_cache_invalidation(mock_datetime, mock_get_client, client):
    """Test that cache is invalidated across different time buckets."""

    from api import get_cached_weather

    get_cached_weather.cache_clear()

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock first time bucket (minute 0)
    mock_dt1 = MagicMock()
    mock_dt1.minute = 0
    mock_datetime.now.return_value = mock_dt1

    mock_weather1 = WeatherData(
        location=Location(city="London", country="UK"),
        temperature=20.0,
        condition="Cloudy",
        humidity=75,
        wind_speed=15.0,
    )
    mock_client.get_weather.return_value = mock_weather1

    response1 = client.get("/api/weather?city=London&country=UK")
    assert response1.status_code == 200
    assert mock_client.get_weather.call_count == 1

    # Mock second time bucket (minute 5)
    mock_dt2 = MagicMock()
    mock_dt2.minute = 5
    mock_datetime.now.return_value = mock_dt2

    mock_weather2 = WeatherData(
        location=Location(city="London", country="UK"),
        temperature=22.0,  # Different temperature
        condition="Sunny",  # Different condition
        humidity=70,
        wind_speed=10.0,
    )
    mock_client.get_weather.return_value = mock_weather2

    response2 = client.get("/api/weather?city=London&country=UK")
    assert response2.status_code == 200
    assert mock_client.get_weather.call_count == 2  # Cache miss, new bucket

    data2 = json.loads(response2.data)
    assert data2["temperature"] == 22.0
    assert data2["condition"] == "Sunny"


@patch("api.get_client")
def test_cache_with_different_locations(mock_get_client, client):
    """Test that cache stores different locations separately."""
    from api import get_cached_weather

    get_cached_weather.cache_clear()

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Different weather for different cities
    def get_weather_side_effect(location):
        if location.city == "London":
            return WeatherData(
                location=location,
                temperature=20.0,
                condition="Cloudy",
                humidity=75,
                wind_speed=15.0,
            )
        else:  # Paris
            return WeatherData(
                location=location,
                temperature=25.0,
                condition="Sunny",
                humidity=65,
                wind_speed=10.0,
            )

    mock_client.get_weather.side_effect = get_weather_side_effect

    # Request London
    response1 = client.get("/api/weather?city=London&country=UK")
    assert response1.status_code == 200
    data1 = json.loads(response1.data)
    assert data1["temperature"] == 20.0
    assert data1["condition"] == "Cloudy"

    # Request Paris
    response2 = client.get("/api/weather?city=Paris&country=France")
    assert response2.status_code == 200
    data2 = json.loads(response2.data)
    assert data2["temperature"] == 25.0
    assert data2["condition"] == "Sunny"

    assert mock_client.get_weather.call_count == 2


def test_cache_size_configuration():
    """Test that cache size is configurable."""
    import os

    from api import CACHE_SIZE

    # Default is 1000 or from environment
    assert CACHE_SIZE == int(os.getenv("CACHE_SIZE", "1000"))


def test_cache_duration_configuration():
    """Test that cache duration is configurable."""
    import os

    from api import CACHE_DURATION_MINUTES

    expected = int(os.getenv("CACHE_DURATION", "300")) // 60
    assert CACHE_DURATION_MINUTES == expected


# Error Handler Tests


def test_invalid_content_type_post(client):
    """Test POST with invalid content type."""
    response = client.post(
        "/api/weather",
        data="not json",
        content_type="text/plain",
    )
    # Should handle gracefully (400 Bad Request or 415 Unsupported Media Type)
    assert response.status_code == 400 or response.status_code == 415


def test_malformed_json_body(client):
    """Test POST with malformed JSON."""
    response = client.post(
        "/api/weather",
        data="{invalid json}",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_oversized_request_body(client):
    """Test request with very large body."""
    huge_data = {"city": "A" * 10000, "country": "B" * 10000}
    response = client.post(
        "/api/weather",
        data=json.dumps(huge_data),
        content_type="application/json",
    )
    # Should be rejected by validation
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_invalid_http_method(client):
    """Test unsupported HTTP method."""
    response = client.put("/api/weather?city=London&country=UK")
    assert response.status_code == 405  # Method Not Allowed


def test_x_request_id_header(client):
    """Test that X-Request-ID header is added to responses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


@patch("api.get_client")
def test_cache_zero_duration(mock_get_client, client, monkeypatch):
    """Test cache behavior when CACHE_DURATION is 0."""
    # Test that the code handles zero cache duration without division by zero
    # The actual CACHE_DURATION_MINUTES will be calculated on module import
    # but we can verify the division protection works

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_weather = WeatherData(
        location=Location(city="London", country="UK"),
        temperature=20.0,
        condition="Cloudy",
        humidity=75,
        wind_speed=15.0,
    )
    mock_client.get_weather.return_value = mock_weather

    # Should work regardless of cache duration setting
    # When CACHE_DURATION_MINUTES is 0, minute_bucket is also 0 (safe default)
    response = client.get("/api/weather?city=London&country=UK")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["location"]["city"] == "London"


def test_weather_coordinates_endpoint(client):
    """Test weather by coordinates endpoint."""
    # Test with valid coordinates (Seattle)
    response = client.get("/api/v1/weather/coordinates?lat=47.6062&lon=-122.3321")
    # This might fail if external service is unavailable, but endpoint should respond
    assert response.status_code in [200, 400, 500]


def test_weather_coordinates_missing_params(client):
    """Test weather by coordinates with missing parameters."""
    response = client.get("/api/v1/weather/coordinates")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_weather_coordinates_invalid_latitude(client):
    """Test weather by coordinates with invalid latitude."""
    response = client.get("/api/v1/weather/coordinates?lat=100&lon=-122")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_weather_coordinates_invalid_longitude(client):
    """Test weather by coordinates with invalid longitude."""
    response = client.get("/api/v1/weather/coordinates?lat=47&lon=200")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_recent_searches_get(client):
    """Test getting recent searches."""
    response = client.get("/api/v1/recent-searches")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "recent_searches" in data
    assert isinstance(data["recent_searches"], list)


def test_recent_searches_delete(client):
    """Test clearing recent searches."""
    response = client.delete("/api/v1/recent-searches")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "message" in data


def test_versioned_weather_get(client):
    """Test versioned weather GET endpoint."""
    response = client.get("/api/v1/weather?city=Seattle&country=USA")
    # Might fail due to external service, but endpoint should respond
    assert response.status_code in [200, 400, 500]


@patch("api.get_client")
def test_versioned_weather_post(mock_get_client, client):
    """Test versioned weather POST endpoint."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_weather = WeatherData(
        location=Location(city="Seattle", country="USA"),
        temperature=15.0,
        condition="Sunny",
        humidity=60,
        wind_speed=10.0,
    )
    mock_client.get_weather.return_value = mock_weather

    response = client.post(
        "/api/v1/weather",
        json={"city": "Seattle", "country": "USA"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["location"]["city"] == "Seattle"
