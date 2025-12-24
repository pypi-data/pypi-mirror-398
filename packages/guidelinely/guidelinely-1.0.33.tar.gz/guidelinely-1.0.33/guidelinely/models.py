"""Pydantic models for Guidelinely API requests and responses."""

from typing import Any, Optional, Union

from pydantic import BaseModel, model_validator

__all__ = [
    # Response models
    "GuidelineResponse",
    "CalculationResponse",
    "SourceResponse",
    "SourceDocument",
    "StatsResponse",
    "MediaResponse",
    "GuidelineSearchResult",
    # Analytics models
    "UsageStatistics",
    "EndpointStatistics",
    "APIKeyUsage",
    "UserAgentStatistics",
    "TimeSeriesData",
    "AnalyticsSummary",
    # Request models
    "CalculateRequest",
    "BatchCalculateRequest",
    "ParameterWithUnit",
    "SearchParametersRequest",
    # Parameter matching models
    "ParameterMatch",
    "ParameterMatchQueryResult",
    "ParameterMatchResponse",
]


class GuidelineSearchResult(BaseModel):
    """Result from guideline search endpoint.

    Contains guideline metadata without calculated values.
    """

    parameter: str
    parameter_specification: Optional[str] = None
    receptor: Optional[str] = None
    media: Optional[str] = None
    purpose: Optional[str] = None
    exposure_duration: Optional[str] = None
    table: Optional[str] = None
    table_name: Optional[str] = None
    application: Optional[str] = None
    basis: Optional[str] = None
    modifier: Optional[str] = None
    sector: Optional[str] = None
    grouping: Optional[str] = None
    use_case: Optional[str] = None
    sample_fraction: Optional[str] = None
    method_speciation: Optional[str] = None
    season: Optional[str] = None
    location: Optional[str] = None
    narrative: Optional[str] = None
    comment: Optional[str] = None
    source: Optional[str] = None  # Source organization name
    source_abbreviation: Optional[str] = None
    document: Optional[str] = None  # Document title
    document_abbreviation: Optional[str] = None
    document_url: Optional[str] = None


class GuidelineResponse(GuidelineSearchResult):
    """Single guideline result with calculated or static value.

    Represents a guideline value in PostgreSQL unitrange format (e.g., '[10 μg/L,100 μg/L]').
    """

    value: str  # PostgreSQL unitrange format: '[10 μg/L,100 μg/L]', '(,87.0 μg/L]', '[5.0 mg/L,)'
    lower: Optional[float] = None  # Parsed lower bound or None if unbounded
    upper: Optional[float] = None  # Parsed upper bound or None if unbounded
    unit: str
    is_calculated: bool
    calculation_used: Optional[str] = None
    formula_svg: Optional[str] = None
    use_case: Optional[str] = None
    error: Optional[str] = None  # Error message if resolution failed
    error_type: Optional[str] = None  # Error type: validation, lookup, or unexpected
    context_index: Optional[int] = None  # Index of context used when multiple contexts provided


class CalculationResponse(BaseModel):
    """Response from calculation endpoints (/calculate and /calculate/batch)."""

    results: list[GuidelineResponse]
    context: dict[str, Any]  # Environmental context used for calculation
    contexts: Optional[list[dict[str, Any]]] = None  # List of contexts when multiple provided
    total_count: int


class CalculateRequest(BaseModel):
    """Request body for single parameter calculation."""

    parameter: str
    media: str
    # Single context dict or list of dicts for multiple contexts
    context: Optional[Union[dict[str, str], list[dict[str, str]]]] = None
    target_unit: Optional[str] = None  # Optional unit conversion
    include_formula_svg: bool = False  # Whether to include SVG formula representations


class ParameterWithUnit(BaseModel):
    """Parameter specification with optional target unit for batch requests."""

    name: str
    target_unit: Optional[str] = None


class BatchCalculateRequest(BaseModel):
    """Request body for batch parameter calculation."""

    parameters: list[Union[str, ParameterWithUnit]]  # Mix of strings and objects
    media: str
    # Single context dict or list of dicts for multiple contexts
    context: Optional[Union[dict[str, str], list[dict[str, str]]]] = None
    include_formula_svg: bool = False  # Whether to include SVG formula representations

    @model_validator(mode="after")
    def validate_parameter_count(self) -> "BatchCalculateRequest":
        """Ensure batch doesn't exceed 50 parameters.

        This validation runs automatically when the model is instantiated,
        raising ValueError if more than 50 parameters are provided.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If parameters list contains more than 50 items.
        """
        if len(self.parameters) > 50:
            raise ValueError("Maximum 50 parameters per batch request")
        return self


class SearchParametersRequest(BaseModel):
    """Request body for parameter search with optional filters."""

    media: Optional[list[str]] = None
    source: Optional[list[str]] = None  # Filter by source abbreviation (e.g., AEPA, CCME)
    document: Optional[list[str]] = None  # Filter by document abbreviation (e.g., PAL, MDMER)


class MediaResponse(BaseModel):
    """Response from /media endpoint mapping enum names to display names."""

    # Dynamic keys, so use dict directly in practice
    pass


class SourceDocument(BaseModel):
    """Nested document information within a source."""

    id: int
    name: str
    url: Optional[str] = None
    abbreviation: Optional[str] = None


class SourceResponse(BaseModel):
    """Guideline source with nested documents."""

    id: int
    name: str
    abbreviation: str
    documents: list[SourceDocument]


class StatsResponse(BaseModel):
    """Database statistics response."""

    parameters: int
    guidelines: int
    sources: int
    documents: int


class UsageStatistics(BaseModel):
    """Overall API usage statistics."""

    total_requests: int
    unique_keys: int
    avg_response_time_ms: float
    error_rate: float
    requests_by_status: dict[str, Any]


class EndpointStatistics(BaseModel):
    """Statistics for a specific endpoint."""

    endpoint: str
    total_requests: int
    avg_response_time_ms: float
    error_count: int
    success_rate: float


class APIKeyUsage(BaseModel):
    """Usage statistics for an API key."""

    api_key_id: int
    api_key_name: str
    total_requests: int
    last_request: Optional[str] = None
    avg_response_time_ms: float
    error_count: int


class UserAgentStatistics(BaseModel):
    """Statistics for a specific User-Agent."""

    user_agent: str
    total_requests: int
    avg_response_time_ms: float
    error_count: int
    success_rate: float


class TimeSeriesData(BaseModel):
    """Time-series data point."""

    timestamp: str
    request_count: int
    avg_response_time_ms: float
    error_count: int


class AnalyticsSummary(BaseModel):
    """Comprehensive analytics summary."""

    period_start: str
    period_end: str
    overall_stats: UsageStatistics
    top_endpoints: list[EndpointStatistics]
    top_keys: list[APIKeyUsage]
    top_user_agents: list[UserAgentStatistics]


class ParameterMatch(BaseModel):
    """Single parameter match result."""

    parameter_specification: str
    parameter: str
    confidence: float  # 0.0-1.0 confidence score
    media_types: list[str]  # Available media types for this parameter
    match_type: str  # Type of match (e.g., 'abbreviation', 'exact', 'fuzzy')
    strategy_used: str  # Strategy that produced this match ('simple', 'alias', 'llm', 'auto')


class ParameterMatchQueryResult(BaseModel):
    """Match results for a single query parameter."""

    query: str  # Original query parameter
    matches: list[ParameterMatch]  # List of matches for this query


class ParameterMatchResponse(BaseModel):
    """Response from /parameters/match endpoint."""

    results: list[ParameterMatchQueryResult]  # Results for each query parameter
    total_queries: int  # Total number of parameters queried
    timestamp: str  # Timestamp of the match operation
