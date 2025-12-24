"""Tests for analytics endpoints."""

import pytest
from pytest_httpx import HTTPXMock

from guidelinely import (
    get_analytics_summary,
    get_endpoint_statistics,
    get_error_statistics,
    get_key_statistics,
    get_timeseries_data,
    get_user_agent_statistics,
)
from guidelinely.cache import cache
from guidelinely.exceptions import GuidelinelyAPIError


# Clear cache before each test to ensure fresh requests
@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()


def test_get_analytics_summary(httpx_mock: HTTPXMock):
    """Test getting analytics summary."""
    mock_response = {
        "period_start": "2025-11-16T00:00:00Z",
        "period_end": "2025-12-16T00:00:00Z",
        "overall_stats": {
            "total_requests": 10000,
            "unique_keys": 25,
            "avg_response_time_ms": 125.5,
            "error_rate": 2.5,
            "requests_by_status": {"200": 9750, "400": 150, "500": 100},
        },
        "top_endpoints": [
            {
                "endpoint": "/api/v1/calculate",
                "total_requests": 5000,
                "avg_response_time_ms": 150.0,
                "error_count": 100,
                "success_rate": 98.0,
            }
        ],
        "top_keys": [
            {
                "api_key_id": 1,
                "api_key_name": "test_key",
                "total_requests": 3000,
                "last_request": "2025-12-16T12:00:00Z",
                "avg_response_time_ms": 120.0,
                "error_count": 50,
            }
        ],
        "top_user_agents": [
            {
                "user_agent": "guidelinely-python/0.1.0",
                "total_requests": 4000,
                "avg_response_time_ms": 115.0,
                "error_count": 80,
                "success_rate": 98.0,
            }
        ],
    }

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/summary?days=30",
        json=mock_response,
    )

    result = get_analytics_summary(days=30, api_key="test_key")

    assert result.overall_stats.total_requests == 10000
    assert result.overall_stats.unique_keys == 25
    assert result.overall_stats.error_rate == 2.5
    assert len(result.top_endpoints) == 1
    assert result.top_endpoints[0].endpoint == "/api/v1/calculate"
    assert len(result.top_keys) == 1
    assert result.top_keys[0].api_key_name == "test_key"
    assert len(result.top_user_agents) == 1


def test_get_analytics_summary_default_days(httpx_mock: HTTPXMock):
    """Test analytics summary with default days parameter."""
    mock_response = {
        "period_start": "2025-11-16T00:00:00Z",
        "period_end": "2025-12-16T00:00:00Z",
        "overall_stats": {
            "total_requests": 5000,
            "unique_keys": 10,
            "avg_response_time_ms": 100.0,
            "error_rate": 1.5,
            "requests_by_status": {"200": 4925, "400": 50, "500": 25},
        },
        "top_endpoints": [],
        "top_keys": [],
        "top_user_agents": [],
    }

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/summary?days=30",
        json=mock_response,
    )

    result = get_analytics_summary(api_key="test_key")
    assert result.overall_stats.total_requests == 5000


def test_get_endpoint_statistics(httpx_mock: HTTPXMock):
    """Test getting endpoint statistics."""
    mock_response = [
        {
            "endpoint": "/api/v1/calculate",
            "total_requests": 5000,
            "avg_response_time_ms": 150.0,
            "error_count": 100,
            "success_rate": 98.0,
        },
        {
            "endpoint": "/api/v1/calculate/batch",
            "total_requests": 3000,
            "avg_response_time_ms": 200.0,
            "error_count": 50,
            "success_rate": 98.3,
        },
    ]

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/endpoints?days=30",
        json=mock_response,
    )

    result = get_endpoint_statistics(days=30, api_key="test_key")

    assert len(result) == 2
    assert result[0].endpoint == "/api/v1/calculate"
    assert result[0].total_requests == 5000
    assert result[0].avg_response_time_ms == 150.0
    assert result[0].error_count == 100
    assert result[0].success_rate == 98.0


def test_get_user_agent_statistics(httpx_mock: HTTPXMock):
    """Test getting user agent statistics."""
    mock_response = [
        {
            "user_agent": "guidelinely-python/0.1.0",
            "total_requests": 4000,
            "avg_response_time_ms": 115.0,
            "error_count": 80,
            "success_rate": 98.0,
        },
        {
            "user_agent": "envguidelines-r/1.0.0",
            "total_requests": 3000,
            "avg_response_time_ms": 120.0,
            "error_count": 60,
            "success_rate": 98.0,
        },
    ]

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/user-agents?days=30",
        json=mock_response,
    )

    result = get_user_agent_statistics(days=30, api_key="test_key")

    assert len(result) == 2
    assert result[0].user_agent == "guidelinely-python/0.1.0"
    assert result[0].total_requests == 4000
    assert result[1].user_agent == "envguidelines-r/1.0.0"


def test_get_key_statistics(httpx_mock: HTTPXMock):
    """Test getting API key statistics."""
    mock_response = [
        {
            "api_key_id": 1,
            "api_key_name": "test_key",
            "total_requests": 3000,
            "last_request": "2025-12-16T12:00:00Z",
            "avg_response_time_ms": 120.0,
            "error_count": 50,
        },
        {
            "api_key_id": 2,
            "api_key_name": "another_key",
            "total_requests": 2000,
            "last_request": "2025-12-16T11:00:00Z",
            "avg_response_time_ms": 130.0,
            "error_count": 30,
        },
    ]

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/keys?days=30",
        json=mock_response,
    )

    result = get_key_statistics(days=30, api_key="test_key")

    assert len(result) == 2
    assert result[0].api_key_id == 1
    assert result[0].api_key_name == "test_key"
    assert result[0].total_requests == 3000
    assert result[0].last_request == "2025-12-16T12:00:00Z"


def test_get_timeseries_data(httpx_mock: HTTPXMock):
    """Test getting timeseries data."""
    mock_response = [
        {
            "timestamp": "2025-12-10T00:00:00Z",
            "request_count": 1000,
            "avg_response_time_ms": 120.0,
            "error_count": 20,
        },
        {
            "timestamp": "2025-12-11T00:00:00Z",
            "request_count": 1200,
            "avg_response_time_ms": 115.0,
            "error_count": 25,
        },
    ]

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/timeseries?days=7&interval=daily",
        json=mock_response,
    )

    result = get_timeseries_data(days=7, interval="daily", api_key="test_key")

    assert len(result) == 2
    assert result[0].timestamp == "2025-12-10T00:00:00Z"
    assert result[0].request_count == 1000
    assert result[0].avg_response_time_ms == 120.0
    assert result[0].error_count == 20


def test_get_timeseries_data_hourly(httpx_mock: HTTPXMock):
    """Test getting hourly timeseries data."""
    mock_response = [
        {
            "timestamp": "2025-12-16T00:00:00Z",
            "request_count": 100,
            "avg_response_time_ms": 120.0,
            "error_count": 2,
        },
        {
            "timestamp": "2025-12-16T01:00:00Z",
            "request_count": 150,
            "avg_response_time_ms": 115.0,
            "error_count": 3,
        },
    ]

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/timeseries?days=1&interval=hourly",
        json=mock_response,
    )

    result = get_timeseries_data(days=1, interval="hourly", api_key="test_key")

    assert len(result) == 2
    assert result[0].request_count == 100
    assert result[1].request_count == 150


def test_get_error_statistics(httpx_mock: HTTPXMock):
    """Test getting error statistics."""
    mock_response = {
        "400": {"count": 150, "percentage": 1.5},
        "404": {"count": 50, "percentage": 0.5},
        "500": {"count": 100, "percentage": 1.0},
    }

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/errors?days=30",
        json=mock_response,
    )

    result = get_error_statistics(days=30, api_key="test_key")

    assert "400" in result
    assert result["400"]["count"] == 150
    assert result["400"]["percentage"] == 1.5
    assert "404" in result
    assert "500" in result


def test_analytics_without_api_key(httpx_mock: HTTPXMock):
    """Test that analytics endpoints work without explicit API key (uses env var)."""
    mock_response = {
        "period_start": "2025-11-16T00:00:00Z",
        "period_end": "2025-12-16T00:00:00Z",
        "overall_stats": {
            "total_requests": 100,
            "unique_keys": 1,
            "avg_response_time_ms": 100.0,
            "error_rate": 0.0,
            "requests_by_status": {"200": 100},
        },
        "top_endpoints": [],
        "top_keys": [],
        "top_user_agents": [],
    }

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/summary?days=30",
        json=mock_response,
    )

    # Should use GUIDELINELY_API_KEY from environment
    result = get_analytics_summary()
    assert result.overall_stats.total_requests == 100


def test_analytics_error_handling(httpx_mock: HTTPXMock):
    """Test error handling for analytics endpoints."""
    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/summary?days=30",
        status_code=401,
        json={"detail": "Invalid API key"},
    )

    with pytest.raises(GuidelinelyAPIError, match="Invalid API key"):
        get_analytics_summary(days=30, api_key="invalid_key")


def test_analytics_different_days_parameter(httpx_mock: HTTPXMock):
    """Test analytics with different days parameters."""
    mock_response = [
        {
            "endpoint": "/api/v1/calculate",
            "total_requests": 1000,
            "avg_response_time_ms": 150.0,
            "error_count": 10,
            "success_rate": 99.0,
        }
    ]

    httpx_mock.add_response(
        url="https://guidelines.1681248.com/api/v1/analytics/endpoints?days=7",
        json=mock_response,
    )

    result = get_endpoint_statistics(days=7, api_key="test_key")
    assert len(result) == 1
    assert result[0].total_requests == 1000


def test_get_analytics_summary_timeout(httpx_mock: HTTPXMock):
    """Test analytics summary timeout."""
    import httpx

    from guidelinely.exceptions import GuidelinelyTimeoutError

    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"),
        url="https://guidelines.1681248.com/api/v1/analytics/summary?days=30",
    )

    with pytest.raises(GuidelinelyTimeoutError):
        get_analytics_summary(days=30, api_key="test_key")


def test_get_endpoint_statistics_timeout(httpx_mock: HTTPXMock):
    """Test endpoint statistics timeout."""
    import httpx

    from guidelinely.exceptions import GuidelinelyTimeoutError

    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"),
        url="https://guidelines.1681248.com/api/v1/analytics/endpoints?days=30",
    )

    with pytest.raises(GuidelinelyTimeoutError):
        get_endpoint_statistics(days=30, api_key="test_key")


def test_get_user_agent_statistics_timeout(httpx_mock: HTTPXMock):
    """Test user agent statistics timeout."""
    import httpx

    from guidelinely.exceptions import GuidelinelyTimeoutError

    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"),
        url="https://guidelines.1681248.com/api/v1/analytics/user-agents?days=30",
    )

    with pytest.raises(GuidelinelyTimeoutError):
        get_user_agent_statistics(days=30, api_key="test_key")


def test_get_key_statistics_timeout(httpx_mock: HTTPXMock):
    """Test key statistics timeout."""
    import httpx

    from guidelinely.exceptions import GuidelinelyTimeoutError

    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"),
        url="https://guidelines.1681248.com/api/v1/analytics/keys?days=30",
    )

    with pytest.raises(GuidelinelyTimeoutError):
        get_key_statistics(days=30, api_key="test_key")


def test_get_timeseries_data_timeout(httpx_mock: HTTPXMock):
    """Test timeseries data timeout."""
    import httpx

    from guidelinely.exceptions import GuidelinelyTimeoutError

    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"),
        url="https://guidelines.1681248.com/api/v1/analytics/timeseries?days=7&interval=daily",
    )

    with pytest.raises(GuidelinelyTimeoutError):
        get_timeseries_data(days=7, interval="daily", api_key="test_key")


def test_get_error_statistics_timeout(httpx_mock: HTTPXMock):
    """Test error statistics timeout."""
    import httpx

    from guidelinely.exceptions import GuidelinelyTimeoutError

    httpx_mock.add_exception(
        httpx.TimeoutException("Timeout"),
        url="https://guidelines.1681248.com/api/v1/analytics/errors?days=30",
    )

    with pytest.raises(GuidelinelyTimeoutError):
        get_error_statistics(days=30, api_key="test_key")


def test_get_analytics_summary_connection_error(httpx_mock: HTTPXMock):
    """Test analytics summary connection error."""
    import httpx

    from guidelinely.exceptions import GuidelinelyConnectionError

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://guidelines.1681248.com/api/v1/analytics/summary?days=30",
    )

    with pytest.raises(GuidelinelyConnectionError):
        get_analytics_summary(days=30, api_key="test_key")


def test_get_endpoint_statistics_connection_error(httpx_mock: HTTPXMock):
    """Test endpoint statistics connection error."""
    import httpx

    from guidelinely.exceptions import GuidelinelyConnectionError

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://guidelines.1681248.com/api/v1/analytics/endpoints?days=30",
    )

    with pytest.raises(GuidelinelyConnectionError):
        get_endpoint_statistics(days=30, api_key="test_key")


def test_get_user_agent_statistics_connection_error(httpx_mock: HTTPXMock):
    """Test user agent statistics connection error."""
    import httpx

    from guidelinely.exceptions import GuidelinelyConnectionError

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://guidelines.1681248.com/api/v1/analytics/user-agents?days=30",
    )

    with pytest.raises(GuidelinelyConnectionError):
        get_user_agent_statistics(days=30, api_key="test_key")


def test_get_key_statistics_connection_error(httpx_mock: HTTPXMock):
    """Test key statistics connection error."""
    import httpx

    from guidelinely.exceptions import GuidelinelyConnectionError

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://guidelines.1681248.com/api/v1/analytics/keys?days=30",
    )

    with pytest.raises(GuidelinelyConnectionError):
        get_key_statistics(days=30, api_key="test_key")


def test_get_timeseries_data_connection_error(httpx_mock: HTTPXMock):
    """Test timeseries data connection error."""
    import httpx

    from guidelinely.exceptions import GuidelinelyConnectionError

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://guidelines.1681248.com/api/v1/analytics/timeseries?days=7&interval=daily",
    )

    with pytest.raises(GuidelinelyConnectionError):
        get_timeseries_data(days=7, interval="daily", api_key="test_key")


def test_get_error_statistics_connection_error(httpx_mock: HTTPXMock):
    """Test error statistics connection error."""
    import httpx

    from guidelinely.exceptions import GuidelinelyConnectionError

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://guidelines.1681248.com/api/v1/analytics/errors?days=30",
    )

    with pytest.raises(GuidelinelyConnectionError):
        get_error_statistics(days=30, api_key="test_key")
