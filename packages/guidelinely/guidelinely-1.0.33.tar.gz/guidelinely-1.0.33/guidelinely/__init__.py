"""Guidelinely - Python client for the Guidelinely Environmental Guidelines API.

Provides programmatic access to environmental guideline calculations and searches
for chemical parameters in various media (water, soil, sediment).
"""

from guidelinely.auth import get_api_key
from guidelinely.client import (
    calculate_batch,
    calculate_guidelines,
    get_analytics_summary,
    get_endpoint_statistics,
    get_error_statistics,
    get_key_statistics,
    get_stats,
    get_timeseries_data,
    get_user_agent_statistics,
    health_check,
    list_media,
    list_parameters,
    list_sources,
    match_parameters,
    readiness_check,
    search_guidelines,
    search_parameters,
)
from guidelinely.exceptions import (
    GuidelinelyAPIError,
    GuidelinelyConnectionError,
    GuidelinelyError,
    GuidelinelyTimeoutError,
)
from guidelinely.models import (
    AnalyticsSummary,
    APIKeyUsage,
    CalculationResponse,
    EndpointStatistics,
    GuidelineResponse,
    GuidelineSearchResult,
    ParameterMatch,
    ParameterMatchQueryResult,
    ParameterMatchResponse,
    SourceDocument,
    SourceResponse,
    StatsResponse,
    TimeSeriesData,
    UsageStatistics,
    UserAgentStatistics,
)

try:
    from importlib.metadata import version

    __version__ = version("guidelinely")
except Exception:
    __version__ = "0.0.0"  # Not installed

__all__ = [
    # Client functions
    "health_check",
    "readiness_check",
    "list_parameters",
    "search_parameters",
    "match_parameters",
    "search_guidelines",
    "list_media",
    "list_sources",
    "get_stats",
    "calculate_guidelines",
    "calculate_batch",
    # Analytics functions
    "get_analytics_summary",
    "get_endpoint_statistics",
    "get_user_agent_statistics",
    "get_key_statistics",
    "get_timeseries_data",
    "get_error_statistics",
    # Models
    "GuidelineResponse",
    "CalculationResponse",
    "GuidelineSearchResult",
    "SourceResponse",
    "SourceDocument",
    "StatsResponse",
    # Parameter matching models
    "ParameterMatch",
    "ParameterMatchQueryResult",
    "ParameterMatchResponse",
    # Analytics models
    "AnalyticsSummary",
    "UsageStatistics",
    "EndpointStatistics",
    "APIKeyUsage",
    "UserAgentStatistics",
    "TimeSeriesData",
    # Exceptions
    "GuidelinelyError",
    "GuidelinelyAPIError",
    "GuidelinelyConnectionError",
    "GuidelinelyTimeoutError",
    # Auth
    "get_api_key",
]
