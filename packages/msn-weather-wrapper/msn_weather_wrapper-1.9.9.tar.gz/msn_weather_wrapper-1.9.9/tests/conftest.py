"""Pytest configuration and fixtures for all tests."""

import os

import pytest

# Set environment variables before any imports that might use them
# This ensures the Flask app can initialize properly in test mode
os.environ["FLASK_ENV"] = "development"
os.environ["FLASK_DEBUG"] = "1"
os.environ["TESTING"] = "1"

# Optional: Set other test-specific environment variables
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_PER_IP", "100")
os.environ.setdefault("RATE_LIMIT_GLOBAL", "1000")


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear LRU cache before each test to avoid cross-test contamination."""
    # Import after environment variables are set
    from api import get_cached_weather

    # Clear the cache before each test
    get_cached_weather.cache_clear()
    yield
    # Clear again after test for good measure
    get_cached_weather.cache_clear()
