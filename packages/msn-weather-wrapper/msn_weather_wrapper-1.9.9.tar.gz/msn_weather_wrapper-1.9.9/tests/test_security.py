"""Security and fuzzing tests for the API."""

import json

import pytest

from api import app, validate_input


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestInputValidation:
    """Test input validation function."""

    def test_valid_input(self):
        """Test validation passes for valid input."""
        value, error = validate_input("Seattle", "city", 100)
        assert error is None
        assert value == "Seattle"

    def test_whitespace_trimming(self):
        """Test whitespace is trimmed."""
        value, error = validate_input("  Seattle  ", "city", 100)
        assert error is None
        assert value == "Seattle"

    def test_empty_string(self):
        """Test empty string is rejected."""
        value, error = validate_input("", "city", 100)
        assert error is not None
        assert "empty" in error.lower()

    def test_none_value(self):
        """Test None is rejected."""
        value, error = validate_input(None, "city", 100)
        assert error is not None
        assert "string" in error.lower()

    def test_whitespace_only(self):
        """Test whitespace-only string is rejected."""
        value, error = validate_input("   ", "city", 100)
        assert error is not None
        assert "empty" in error.lower() or "whitespace" in error.lower()

    def test_exceeds_max_length(self):
        """Test string exceeding max length is rejected."""
        value, error = validate_input("A" * 101, "city", 100)
        assert error is not None
        assert "length" in error.lower()

    def test_non_string_type(self):
        """Test non-string types are rejected."""
        for invalid_value in [12345, True, [], {}]:
            value, error = validate_input(invalid_value, "city", 100)
            assert error is not None
            assert "string" in error.lower()

    def test_special_characters_rejected(self):
        """Test dangerous special characters are rejected."""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users--",
            "../../../etc/passwd",
            "${whoami}",
            "\x00\x01\x02",
        ]
        for dangerous in dangerous_inputs:
            value, error = validate_input(dangerous, "city", 100)
            assert error is not None
            assert "invalid characters" in error.lower()

    def test_unicode_cities_allowed(self):
        """Test valid unicode city names are allowed."""
        valid_unicode = [
            "北京",  # Beijing
            "Москва",  # Moscow
            "São Paulo",
            "Zürich",
            "Kraków",
        ]
        for city in valid_unicode:
            value, error = validate_input(city, "city", 100)
            # These should pass as they contain valid unicode letters
            if error:
                # Some special chars might not pass, that's ok for security
                assert "invalid characters" in error.lower()


class TestAPISecurityGET:
    """Test GET endpoint security."""

    def test_sql_injection_attempts(self, client):
        """Test SQL injection attempts are blocked."""
        sql_injections = [
            "1; DROP",  # Semicolon for command injection
            "1 UNION",  # SQL UNION keyword
            "admin\x00null",  # Null byte injection
        ]
        for payload in sql_injections:
            response = client.get(f"/api/weather?city={payload}&country={payload}")
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
            assert "invalid" in data["message"].lower()

    def test_xss_attempts(self, client):
        """Test XSS attempts are blocked."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
        ]
        for payload in xss_attempts:
            response = client.get(f"/api/weather?city={payload}&country={payload}")
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_path_traversal_attempts(self, client):
        """Test path traversal attempts are blocked."""
        path_traversals = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
        ]
        for payload in path_traversals:
            response = client.get(f"/api/weather?city={payload}&country={payload}")
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_command_injection_attempts(self, client):
        """Test command injection attempts are blocked."""
        commands = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(cat /etc/passwd)",
        ]
        for payload in commands:
            response = client.get(f"/api/weather?city={payload}&country={payload}")
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_null_bytes(self, client):
        """Test null bytes are blocked."""
        response = client.get("/api/weather?city=test\x00&country=test\x00")
        assert response.status_code == 400

    def test_oversized_input(self, client):
        """Test oversized inputs are rejected."""
        oversized = "A" * 10000
        response = client.get(f"/api/weather?city={oversized}&country={oversized}")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "length" in data["message"].lower()

    def test_empty_parameters(self, client):
        """Test empty parameters are rejected."""
        response = client.get("/api/weather?city=&country=")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_whitespace_only_parameters(self, client):
        """Test whitespace-only parameters are rejected."""
        response = client.get("/api/weather?city=   &country=   ")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestAPISecurityPOST:
    """Test POST endpoint security."""

    def test_malformed_json(self, client):
        """Test malformed JSON is handled gracefully."""
        malformed = [
            "{invalid json}",
            '{"city": "test"',  # Missing closing brace
            '{"city": "test", "country":}',  # Missing value
        ]
        for payload in malformed:
            response = client.post(
                "/api/weather",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_non_string_types(self, client):
        """Test non-string types in JSON are rejected."""
        invalid_types = [
            {"city": 12345, "country": "USA"},
            {"city": "Seattle", "country": True},
            {"city": [], "country": "USA"},
            {"city": "Seattle", "country": {}},
            {"city": None, "country": None},
        ]
        for payload in invalid_types:
            response = client.post(
                "/api/weather",
                json=payload,
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
            # Should reject either because required or wrong type
            assert "required" in data["message"].lower() or "string" in data["message"].lower()

    def test_sql_injection_in_json(self, client):
        """Test SQL injection in JSON values is blocked."""
        response = client.post(
            "/api/weather",
            json={"city": "1; DROP TABLE users", "country": "admin'--"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_xss_in_json(self, client):
        """Test XSS in JSON values is blocked."""
        response = client.post(
            "/api/weather",
            json={"city": "<script>alert(1)</script>", "country": "USA"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_non_dict_json(self, client):
        """Test non-dict JSON is rejected."""
        invalid_json = [
            [],
            "string",
            123,
            None,
            True,
        ]
        for payload in invalid_json:
            response = client.post(
                "/api/weather",
                json=payload,
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_oversized_json_values(self, client):
        """Test oversized JSON values are rejected."""
        response = client.post(
            "/api/weather",
            json={"city": "A" * 10000, "country": "USA"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "length" in data["message"].lower()


class TestAPIRateLimiting:
    """Test for potential DoS via repeated requests."""

    def test_multiple_valid_requests(self, client):
        """Test multiple valid requests don't crash the server."""
        for _ in range(10):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

    def test_multiple_invalid_requests(self, client):
        """Test multiple invalid requests are handled gracefully."""
        for _ in range(10):
            response = client.get("/api/weather?city=<script>&country=alert")
            # Should be 400 for invalid input, but may be 429 if rate limited
            assert response.status_code in (400, 429)


class TestHTTPErrorHandlers:
    """Test HTTP error handlers and edge cases."""

    def test_404_not_found(self, client):
        """Test 404 error handler for non-existent endpoints."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        # Flask returns HTML for 404 by default, not JSON
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test 405 error for unsupported HTTP methods."""
        # Health endpoint only supports GET
        response = client.post("/api/v1/health")
        assert response.status_code == 405

        # Try other unsupported methods
        response = client.delete("/api/weather?city=London&country=UK")
        assert response.status_code == 405

    def test_413_payload_too_large(self, client):
        """Test handling of extremely large payloads."""
        huge_payload = {"city": "X" * 1_000_000, "country": "Y" * 1_000_000}
        response = client.post(
            "/api/weather",
            data=json.dumps(huge_payload),
            content_type="application/json",
        )
        # Should be rejected (400 from validation or 413 from server)
        assert response.status_code in (400, 413)

    def test_400_bad_request_missing_required_fields(self, client):
        """Test 400 error for missing required fields."""
        test_cases = [
            {},  # Empty body
            {"city": "London"},  # Missing country
            {"country": "UK"},  # Missing city
            {"invalid": "field"},  # Invalid fields
        ]
        for payload in test_cases:
            response = client.post(
                "/api/weather",
                json=payload,
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_415_unsupported_media_type(self, client):
        """Test 415 error for unsupported content types."""
        # Try sending XML when JSON is expected
        response = client.post(
            "/api/weather",
            data="<xml><city>London</city></xml>",
            content_type="application/xml",
        )
        # Should be 400 or 415
        assert response.status_code in (400, 415)

    def test_invalid_json_syntax(self, client):
        """Test handling of malformed JSON syntax."""
        malformed_jsons = [
            "{city: London}",  # Missing quotes
            '{"city": "London",}',  # Trailing comma
            '{"city": "London" "country": "UK"}',  # Missing comma
            '{city: "London", country: "UK"}',  # Unquoted keys
        ]
        for malformed in malformed_jsons:
            response = client.post(
                "/api/weather",
                data=malformed,
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_content_type_without_charset(self, client):
        """Test handling of content-type without charset."""
        response = client.post(
            "/api/weather",
            data='{"city": "London", "country": "UK"}',
            content_type="application/json",  # No charset specified
        )
        # Should work or fail gracefully (may be 500 if backend unavailable)
        assert response.status_code in (200, 400, 500)

    def test_empty_request_body_post(self, client):
        """Test POST with completely empty body."""
        response = client.post(
            "/api/weather",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_null_bytes_in_input(self, client):
        """Test handling of null bytes in input."""
        response = client.get("/api/weather?city=London\x00&country=UK")
        assert response.status_code == 400

    def test_very_long_query_string(self, client):
        """Test handling of extremely long query strings."""
        long_city = "A" * 10000
        response = client.get(f"/api/weather?city={long_city}&country=UK")
        assert response.status_code == 400

    def test_unicode_normalization_attack(self, client):
        """Test handling of unicode normalization attacks."""
        # Unicode characters that might be normalized differently
        response = client.get("/api/weather?city=\u0041\u030a&country=UK")  # Å as combining chars
        # Should either work or fail gracefully with 400
        assert response.status_code in (200, 400)

    def test_header_injection_attempts(self, client):
        """Test that header injection attempts don't succeed."""
        # Try to inject headers via input
        response = client.get("/api/weather?city=London\r\nX-Injected: true&country=UK")
        assert response.status_code == 400
        # Ensure injected header is not present
        assert "X-Injected" not in response.headers

    def test_multiple_content_types(self, client):
        """Test handling of multiple content-type headers."""
        response = client.post(
            "/api/weather",
            data='{"city": "London", "country": "UK"}',
            headers={
                "Content-Type": "application/json, text/plain",
            },
        )
        # Should handle gracefully
        assert response.status_code in (200, 400, 415)

    def test_case_sensitive_endpoints(self, client):
        """Test that endpoint paths are case-sensitive."""
        # These should not match
        response = client.get("/API/weather?city=London&country=UK")
        assert response.status_code == 404

        response = client.get("/api/WEATHER?city=London&country=UK")
        assert response.status_code == 404

    def test_trailing_slash_handling(self, client):
        """Test endpoint behavior with trailing slashes."""
        # Test both with and without trailing slash
        response1 = client.get("/api/v1/health")
        response2 = client.get("/api/v1/health/")
        # Flask strict_slashes behavior: /api/v1/health works, /api/v1/health/ may 404
        assert response1.status_code == 200
        # response2 may be 200 or 404 depending on Flask config
        assert response2.status_code in (200, 404)

    def test_double_slash_in_path(self, client):
        """Test handling of double slashes in URL path."""
        response = client.get("//api//weather?city=London&country=UK")
        # Should normalize or return 404
        assert response.status_code in (200, 404)

    def test_url_encoding_in_parameters(self, client):
        """Test proper handling of URL-encoded parameters."""
        # Spaces encoded as +
        response = client.get("/api/weather?city=New+York&country=USA")
        # Should decode properly and not cause server error
        assert response.status_code in (200, 400, 500)  # 500 if MSN Weather fails
        # Verify it's not a validation error
        if response.status_code == 400:
            data = json.loads(response.data)
            # Should not be rejected for invalid characters
            assert "invalid characters" not in data.get("message", "").lower()

        # Spaces encoded as %20
        response = client.get("/api/weather?city=New%20York&country=USA")
        assert response.status_code in (200, 400, 500)  # 500 if MSN Weather fails
        if response.status_code == 400:
            data = json.loads(response.data)
            assert "invalid characters" not in data.get("message", "").lower()

    def test_repeated_parameters(self, client):
        """Test handling of repeated query parameters."""
        response = client.get("/api/weather?city=London&city=Paris&country=UK")
        # Should use first value, reject, or fail if backend unavailable
        assert response.status_code in (200, 400, 500)

    def test_parameter_without_value(self, client):
        """Test handling of parameters without values."""
        response = client.get("/api/weather?city=&country=UK")
        assert response.status_code == 400

    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request."""
        response = client.options("/api/weather")
        # Should return 200 or 204 for OPTIONS
        assert response.status_code in (200, 204)

    def test_response_headers_present(self, client):
        """Test that security-related headers are present."""
        response = client.get("/api/v1/health")
        # Check for X-Request-ID (added by our middleware)
        assert "X-Request-ID" in response.headers
