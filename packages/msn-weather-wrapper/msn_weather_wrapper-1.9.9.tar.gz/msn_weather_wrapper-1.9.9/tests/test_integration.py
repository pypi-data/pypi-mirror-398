"""Integration tests for containerized API deployment."""

import subprocess
import time
from collections.abc import Generator

import pytest
import requests


@pytest.fixture(scope="module")
def api_url() -> str:
    """Return the base URL for the API."""
    return "http://localhost:8080"


@pytest.fixture(scope="module")
def containers() -> Generator[None, None, None]:
    """Use already running containers or skip tests."""
    # Check if containers are already running (try both docker and podman)
    for cmd in [["docker", "ps"], ["podman", "ps"]]:
        try:
            result = subprocess.run(
                cmd + ["--filter", "name=msn-weather-app", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and "msn-weather-app" in result.stdout:
                break
        except FileNotFoundError:
            continue
    else:
        pytest.skip(
            "Container not running. Start with: docker compose up -d or podman-compose up -d"
        )

    # Wait for API to be ready
    max_retries = 15
    for _ in range(max_retries):
        try:
            response = requests.get("http://localhost:8080/api/v1/health", timeout=2)
            if response.status_code == 200:
                break
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(1)
    else:
        pytest.skip("API is not responding")

    yield

    # Don't stop containers - leave them running


@pytest.mark.integration
class TestContainerizedAPI:
    """Integration tests for the containerized API."""

    def test_health_endpoint(self, containers, api_url):
        """Test that health endpoint returns 200."""
        response = requests.get(f"{api_url}/api/v1/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_get_weather_missing_params(self, containers, api_url):
        """Test GET request with missing parameters."""
        response = requests.get(f"{api_url}/api/weather", timeout=10)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "required" in data["message"].lower()

    def test_get_weather_with_valid_params(self, containers, api_url):
        """Test GET request with valid city and country."""
        params = {"city": "Seattle", "country": "USA"}
        response = requests.get(f"{api_url}/api/weather", params=params, timeout=10)
        # Should return either 200 with data or 500 if MSN is unreachable
        assert response.status_code in [200, 500]
        data = response.json()
        if response.status_code == 200:
            assert "location" in data
            assert "temperature" in data
        else:
            assert "error" in data

    def test_post_weather_with_valid_data(self, containers, api_url):
        """Test POST request with valid JSON."""
        payload = {"city": "London", "country": "UK"}
        response = requests.post(
            f"{api_url}/api/weather",
            json=payload,
            timeout=10,
        )
        # Should return either 200 with data or 500 if MSN is unreachable
        assert response.status_code in [200, 500]
        data = response.json()
        if response.status_code == 200:
            assert "location" in data
            assert "temperature" in data
        else:
            assert "error" in data

    def test_sql_injection_blocked(self, containers, api_url):
        """Test that SQL injection attempts are blocked."""
        sql_payloads = [
            "1; DROP",
            "' OR '1'='1",
            "1 UNION",
        ]
        for payload in sql_payloads:
            response = requests.get(
                f"{api_url}/api/weather",
                params={"city": payload, "country": payload},
                timeout=10,
            )
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "invalid" in data["message"].lower()

    def test_xss_blocked(self, containers, api_url):
        """Test that XSS attempts are blocked."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
        ]
        for payload in xss_payloads:
            response = requests.get(
                f"{api_url}/api/weather",
                params={"city": payload, "country": "USA"},
                timeout=10,
            )
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    def test_path_traversal_blocked(self, containers, api_url):
        """Test that path traversal attempts are blocked."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
        ]
        for payload in traversal_payloads:
            response = requests.get(
                f"{api_url}/api/weather",
                params={"city": payload, "country": "USA"},
                timeout=10,
            )
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    def test_command_injection_blocked(self, containers, api_url):
        """Test that command injection attempts are blocked."""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(whoami)",
        ]
        for payload in command_payloads:
            response = requests.get(
                f"{api_url}/api/weather",
                params={"city": payload, "country": "USA"},
                timeout=10,
            )
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    def test_oversized_input_blocked(self, containers, api_url):
        """Test that oversized inputs are blocked."""
        oversized = "A" * 10000
        response = requests.get(
            f"{api_url}/api/weather",
            params={"city": oversized, "country": "USA"},
            timeout=10,
        )
        # Accept both 400 (Bad Request) and 414 (URI Too Long)
        assert response.status_code in [400, 414]
        if response.status_code == 400:
            data = response.json()
            assert "error" in data
            assert "length" in data["message"].lower()

    def test_type_confusion_post(self, containers, api_url):
        """Test that type confusion in POST is blocked."""
        invalid_payloads = [
            {"city": 12345, "country": "USA"},
            {"city": "Seattle", "country": True},
            {"city": [], "country": "USA"},
            {"city": None, "country": None},
        ]
        for payload in invalid_payloads:
            response = requests.post(
                f"{api_url}/api/weather",
                json=payload,
                timeout=10,
            )
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    def test_malformed_json_post(self, containers, api_url):
        """Test that malformed JSON is handled properly."""
        response = requests.post(
            f"{api_url}/api/weather",
            data="{invalid json}",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_empty_parameters_blocked(self, containers, api_url):
        """Test that empty parameters are rejected."""
        response = requests.get(
            f"{api_url}/api/weather",
            params={"city": "", "country": ""},
            timeout=10,
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_whitespace_only_blocked(self, containers, api_url):
        """Test that whitespace-only parameters are rejected."""
        response = requests.get(
            f"{api_url}/api/weather",
            params={"city": "   ", "country": "   "},
            timeout=10,
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_cors_headers_present(self, containers, api_url):
        """Test that CORS headers are present."""
        # Send Origin header to trigger CORS response headers
        response = requests.get(
            f"{api_url}/api/v1/health", headers={"Origin": "http://localhost:3000"}, timeout=10
        )
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    def test_multiple_concurrent_requests(self, containers, api_url):
        """Test that API handles multiple concurrent requests."""
        import concurrent.futures

        def make_request():
            return requests.get(f"{api_url}/api/v1/health", timeout=10)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
        assert len(results) == 10

    def test_container_health_check(self, containers, api_url):
        """Test that container reports healthy status."""
        for cmd in ["docker", "podman"]:
            try:
                result = subprocess.run(
                    [cmd, "ps", "--filter", "name=msn-weather-app", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout:
                    assert "Up" in result.stdout
                    return
            except FileNotFoundError:
                continue
        pytest.fail("Neither docker nor podman available")

    def test_api_logs_no_errors(self, containers, api_url):
        """Test that API logs don't contain critical errors."""
        # Make a valid request first
        requests.get(f"{api_url}/api/v1/health", timeout=10)

        # Check logs
        for cmd in ["docker", "podman"]:
            try:
                result = subprocess.run(
                    [cmd, "logs", "--tail", "20", "msn-weather-app"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    # Should not have Python exceptions or critical errors
                    assert "Traceback" not in result.stdout
                    assert "CRITICAL" not in result.stdout
                    return
            except FileNotFoundError:
                continue
        pytest.fail("Neither docker nor podman available")
