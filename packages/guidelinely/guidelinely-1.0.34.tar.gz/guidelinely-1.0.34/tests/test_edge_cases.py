"""Tests for edge cases and error handling scenarios.

This module provides comprehensive tests for:
- Network timeout handling
- Invalid JSON responses
- HTTP 4xx error codes (400, 401, 403, 404)
- Cache TTL behavior
- Unicode parameter names
- Empty response handling
"""

import pytest

from guidelinely import (
    calculate_batch,
    calculate_guidelines,
    health_check,
    list_parameters,
    search_parameters,
)
from guidelinely.cache import cache
from guidelinely.exceptions import (
    GuidelinelyAPIError,
    GuidelinelyConnectionError,
    GuidelinelyTimeoutError,
)

API_BASE = "https://guidelines.1681248.com/api/v1"


class TestTimeoutHandling:
    """Tests for network timeout scenarios."""

    def test_health_check_timeout(self, httpx_mock):
        """Test that timeout exception is properly wrapped."""
        import httpx

        httpx_mock.add_exception(httpx.TimeoutException("Connection timed out"))

        with pytest.raises(GuidelinelyTimeoutError) as exc_info:
            health_check()

        assert "timed out" in str(exc_info.value).lower()

    def test_list_parameters_timeout(self, httpx_mock):
        """Test timeout handling for list_parameters."""
        import httpx

        httpx_mock.add_exception(httpx.TimeoutException("Read timed out"))

        with pytest.raises(GuidelinelyTimeoutError):
            list_parameters()

    def test_calculate_guidelines_timeout(self, httpx_mock):
        """Test timeout handling for calculate_guidelines."""
        import httpx

        cache.clear()
        httpx_mock.add_exception(httpx.TimeoutException("Connection timed out"))

        with pytest.raises(GuidelinelyTimeoutError):
            calculate_guidelines(parameter="Aluminum", media="surface_water", api_key="test_key")


class TestConnectionErrorHandling:
    """Tests for network connection error scenarios."""

    def test_health_check_connection_error(self, httpx_mock):
        """Test that connection errors are properly wrapped."""
        import httpx

        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        with pytest.raises(GuidelinelyConnectionError) as exc_info:
            health_check()

        assert "Connection failed" in str(exc_info.value)

    def test_list_parameters_connection_error(self, httpx_mock):
        """Test connection error handling for list_parameters."""
        import httpx

        httpx_mock.add_exception(httpx.ConnectError("Network unreachable"))

        with pytest.raises(GuidelinelyConnectionError):
            list_parameters()

    def test_calculate_guidelines_connection_error(self, httpx_mock):
        """Test connection error handling for calculate_guidelines."""
        import httpx

        cache.clear()
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        with pytest.raises(GuidelinelyConnectionError):
            calculate_guidelines(parameter="Aluminum", media="surface_water", api_key="test_key")

    def test_search_parameters_connection_error(self, httpx_mock):
        """Test connection error handling for search_parameters."""
        import httpx

        httpx_mock.add_exception(httpx.RemoteProtocolError("Server disconnected"))

        with pytest.raises(GuidelinelyConnectionError):
            search_parameters("copper")


class TestInvalidJsonResponses:
    """Tests for handling malformed JSON responses."""

    def test_invalid_json_in_error_response(self, httpx_mock):
        """Test handling of non-JSON error response body."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/health",
            content=b"Internal Server Error",
            status_code=500,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            health_check()

        assert exc_info.value.status_code == 500
        # Should fall back to default message when JSON parsing fails
        assert "API request failed" in str(exc_info.value)

    def test_partial_json_in_error_response(self, httpx_mock):
        """Test handling of truncated JSON in error response."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/parameters",
            content=b'{"detail": "Something went',  # Truncated JSON
            status_code=500,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            list_parameters()

        assert exc_info.value.status_code == 500


class TestHttp4xxErrorCodes:
    """Tests for HTTP 4xx client error handling."""

    def test_400_bad_request(self, httpx_mock):
        """Test handling of 400 Bad Request."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={"detail": "Invalid parameter format"},
            status_code=400,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            calculate_guidelines(parameter="Invalid!!!", media="surface_water", api_key="test_key")

        assert exc_info.value.status_code == 400
        assert "Invalid parameter format" in str(exc_info.value)

    def test_401_unauthorized(self, httpx_mock):
        """Test handling of 401 Unauthorized (invalid API key)."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={"detail": "Invalid API key"},
            status_code=401,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            calculate_guidelines(
                parameter="Aluminum",
                media="surface_water",
                api_key="invalid_key",
            )

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    def test_403_forbidden(self, httpx_mock):
        """Test handling of 403 Forbidden (rate limit exceeded)."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={"detail": "Rate limit exceeded"},
            status_code=403,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            calculate_guidelines(parameter="Aluminum", media="surface_water", api_key="test_key")

        assert exc_info.value.status_code == 403
        assert "Rate limit exceeded" in str(exc_info.value)

    def test_404_not_found(self, httpx_mock):
        """Test handling of 404 Not Found (parameter doesn't exist)."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={"detail": "Parameter 'NonExistent' not found"},
            status_code=404,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            calculate_guidelines(parameter="NonExistent", media="surface_water", api_key="test_key")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()

    def test_422_unprocessable_entity(self, httpx_mock):
        """Test handling of 422 Unprocessable Entity (validation error)."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={"detail": "Context pH must include unit"},
            status_code=422,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            calculate_guidelines(
                parameter="Aluminum",
                media="surface_water",
                context={"pH": "7.0"},  # Missing unit
                api_key="test_key",
            )

        assert exc_info.value.status_code == 422


class TestUnicodeParameterNames:
    """Tests for Unicode characters in parameter names and contexts."""

    def test_unicode_parameter_search(self, httpx_mock):
        """Test searching for parameters with Unicode characters."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/parameters/search?q=%CE%BC",  # μ URL-encoded
            json=["μg/L-related"],
            status_code=200,
        )

        results = search_parameters("μ")
        assert len(results) == 1

    def test_unicode_in_context(self, httpx_mock):
        """Test context values with Unicode unit symbols."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={
                "results": [],
                "context": {"temperature": "20 °C"},
                "total_count": 0,
            },
            status_code=200,
        )

        result = calculate_guidelines(
            parameter="Copper",
            media="surface_water",
            context={"temperature": "20 °C"},
            api_key="test_key",
        )

        assert result.context["temperature"] == "20 °C"

    def test_unicode_target_unit(self, httpx_mock):
        """Test target_unit with Unicode symbols (μg/L)."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={
                "results": [
                    {
                        "id": 1,
                        "parameter": "Copper",
                        "parameter_specification": "Copper, Dissolved",
                        "media": "surface_water",
                        "value": "[2.0 μg/L,5.0 μg/L]",
                        "lower": 2.0,
                        "upper": 5.0,
                        "unit": "μg/L",
                        "is_calculated": True,
                        "source": "CCME",
                        "receptor": "Aquatic Life",
                        "exposure_duration": "chronic",
                        "purpose": "long_term",
                        "table": "Table 1",
                        "application": "Freshwater guidelines",
                        "basis": "Chronic toxicity",
                        "use_case": "Protection",
                        "document": "CCME Water Quality Guidelines",
                    }
                ],
                "context": {},
                "total_count": 1,
            },
            status_code=200,
        )

        result = calculate_guidelines(
            parameter="Copper",
            media="surface_water",
            target_unit="μg/L",
            api_key="test_key",
        )

        assert result.results[0].unit == "μg/L"


class TestEmptyResponses:
    """Tests for handling empty or minimal responses."""

    def test_empty_parameters_list(self, httpx_mock):
        """Test handling of empty parameters list."""
        httpx_mock.add_response(
            method="GET", url=f"{API_BASE}/parameters", json=[], status_code=200
        )

        params = list_parameters()
        assert params == []

    def test_empty_search_results(self, httpx_mock):
        """Test handling of empty search results."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/parameters/search?q=nonexistent123",
            json=[],
            status_code=200,
        )

        results = search_parameters("nonexistent123")
        assert results == []

    def test_empty_calculation_results(self, httpx_mock):
        """Test handling of calculation with no matching guidelines."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={"results": [], "context": {}, "total_count": 0},
            status_code=200,
        )

        result = calculate_guidelines(
            parameter="Aluminum", media="surface_water", api_key="test_key"
        )

        assert result.results == []
        assert result.total_count == 0

    def test_empty_batch_results(self, httpx_mock):
        """Test handling of batch calculation with no results."""
        cache.clear()
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate/batch",
            json={"results": [], "context": {}, "total_count": 0},
            status_code=200,
        )

        result = calculate_batch(
            parameters=["NonExistent1", "NonExistent2"],
            media="surface_water",
            api_key="test_key",
        )

        assert result.results == []
        assert result.total_count == 0


class TestCacheBehavior:
    """Tests for cache functionality."""

    def test_cache_hit_returns_cached_response(self, httpx_mock):
        """Test that cached responses are returned without HTTP call."""
        cache.clear()

        # First call - should hit the API
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={
                "results": [
                    {
                        "id": 1,
                        "parameter": "Aluminum",
                        "parameter_specification": "Aluminum, Dissolved",
                        "media": "surface_water",
                        "value": "[87.0 μg/L,100 μg/L]",
                        "lower": 87.0,
                        "upper": 100.0,
                        "unit": "μg/L",
                        "is_calculated": True,
                        "source": "CCME",
                        "receptor": "Aquatic Life",
                        "exposure_duration": "chronic",
                        "purpose": "long_term",
                        "table": "Table 1",
                        "application": "Freshwater guidelines",
                        "basis": "Chronic toxicity",
                        "use_case": "Protection",
                        "document": "CCME Water Quality Guidelines",
                    }
                ],
                "context": {"pH": "7.0 1"},
                "total_count": 1,
            },
            status_code=200,
        )

        result1 = calculate_guidelines(
            parameter="Aluminum",
            media="surface_water",
            context={"pH": "7.0 1"},
            api_key="test_key",
        )

        # Second call with same parameters - should use cache
        result2 = calculate_guidelines(
            parameter="Aluminum",
            media="surface_water",
            context={"pH": "7.0 1"},
            api_key="test_key",
        )

        # Both should have same results
        assert result1.total_count == result2.total_count
        assert result1.results[0].parameter == result2.results[0].parameter

        # Only one HTTP request should have been made
        requests = httpx_mock.get_requests()
        assert len(requests) == 1

    def test_different_context_bypasses_cache(self, httpx_mock):
        """Test that different context creates new cache entry."""
        cache.clear()

        # Response for pH 7.0
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={
                "results": [],
                "context": {"pH": "7.0 1"},
                "total_count": 0,
            },
            status_code=200,
        )

        # Response for pH 8.0
        httpx_mock.add_response(
            method="POST",
            url=f"{API_BASE}/calculate",
            json={
                "results": [],
                "context": {"pH": "8.0 1"},
                "total_count": 0,
            },
            status_code=200,
        )

        # First call with pH 7.0
        calculate_guidelines(
            parameter="Aluminum",
            media="surface_water",
            context={"pH": "7.0 1"},
            api_key="test_key",
        )

        # Second call with pH 8.0 - should make new request
        calculate_guidelines(
            parameter="Aluminum",
            media="surface_water",
            context={"pH": "8.0 1"},
            api_key="test_key",
        )

        # Two HTTP requests should have been made
        requests = httpx_mock.get_requests()
        assert len(requests) == 2


class TestErrorMessageExtraction:
    """Tests for error message extraction from API responses."""

    def test_detail_field_extraction(self, httpx_mock):
        """Test extraction of 'detail' field from error response."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/health",
            json={"detail": "Service unavailable"},
            status_code=503,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            health_check()

        assert "Service unavailable" in str(exc_info.value)

    def test_message_field_extraction(self, httpx_mock):
        """Test extraction of 'message' field from error response."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/health",
            json={"message": "Database connection failed"},
            status_code=500,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            health_check()

        assert "Database connection failed" in str(exc_info.value)
