# Guidelinely Python Client

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python client library for the [Guidelinely API](https://guidelines.1681248.com/docs) - an environmental guideline calculation and search API.

Calculate context-dependent environmental guideline values for chemical parameters (Aluminum, Copper, Lead, etc.) in various media (water, soil, sediment) based on environmental conditions (pH, hardness, temperature, etc.).

This Python client mirrors the functionality of the [R client](https://github.com/mpdavison/envguidelines).

## Features

- **Metadata Queries**: List parameters, search, explore media types and sources
- **Parameter Matching**: Intelligent fuzzy matching for chemical abbreviations and spelling variants
- **Single Calculations**: Calculate guidelines for individual parameters
- **Batch Calculations**: Efficiently calculate multiple parameters (up to 50)
- **Context-Aware**: Support for pH, hardness, temperature, and other environmental factors
- **Unit Conversion**: Optional target unit specification
- **Analytics**: Monitor API usage and performance (requires authentication)
- **Type Safety**: Full Pydantic model support for request/response validation
- **Comprehensive Tests**: Mock-based test suite with pytest-httpx
- **Persistent Caching**: Automatic caching of calculation results with configurable TTL

## Installation

Requires **Python 3.9+**.

```bash
# Install from PyPI (when available)
pip install guidelinely

# Or install from source
git clone https://github.com/mpdavison/envguidelines-py.git
cd envguidelines-py
pip install -e .            # Development mode
pip install -e ".[dev]"     # With dev dependencies
```

## Quick Start

```python
from guidelinely import calculate_guidelines

# Calculate dissolved aluminum guidelines in surface water
result = calculate_guidelines(
    parameter="Aluminum, Dissolved",
    media="surface_water",
    context={
        "hardness": "100 mg/L"   # Water hardness as CaCO3
    }
)

print(f"Found {result.total_count} guidelines")
for guideline in result.results:
    print(f"{guideline.parameter}: {guideline.value} ({guideline.source})")
```

## API Key

Calculation endpoints optionally accept an API key. Set it as an environment variable:

```bash
export GUIDELINELY_API_KEY="your_api_key_here"
```

Metadata endpoints (list parameters, search, etc.) work without authentication.

## Environment Variables

The library supports the following environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `GUIDELINELY_API_KEY` | API key for calculation endpoints | None (optional) |
| `GUIDELINELY_CACHE_DIR` | Directory for persistent caching | `~/.guidelinely_cache` |
| `GUIDELINELY_CACHE_TTL` | Cache time-to-live in seconds | `604800` (7 days) |
| `GUIDELINELY_TIMEOUT` | HTTP request timeout in seconds | `30` |

### Cache Configuration

By default, calculation results are cached to `~/.guidelinely_cache` for 7 days. You can customize the location and TTL:

```bash
export GUIDELINELY_CACHE_DIR="/path/to/custom/cache"
export GUIDELINELY_CACHE_TTL="86400"  # 1 day in seconds
```

To manually clear the cache:

```python
from guidelinely.cache import cache
cache.clear()
```

## Usage Examples

### Basic Metadata Queries

```python
from guidelinely import (
    health_check,
    list_parameters,
    search_parameters,
    match_parameters,
    list_media,
    list_sources,
    get_stats,
)

# Check API health
status = health_check()

# List all chemical parameters
params = list_parameters()
print(f"Available parameters: {len(params)}")

# Search for ammonia-related parameters
ammonia = search_parameters("ammon")
print(ammonia)  # ['Ammonia', 'Ammonium', ...]

# Match parameter names with intelligent fuzzy matching
result = match_parameters(["NH3", "Cu", "Al"])
for query_result in result.results:
    print(f"{query_result.query} -> {query_result.matches[0].parameter}")
# NH3 -> Ammonia
# Cu -> Copper
# Al -> Aluminum

# Get available media types
media = list_media()
# {'surface_water': 'Surface Water', 'soil': 'Soil', ...}

# View guideline sources
sources = list_sources()

# Database statistics
stats = get_stats()
```

### Single Parameter Calculation

```python
from guidelinely import calculate_guidelines
import os

os.environ["GUIDELINELY_API_KEY"] = "your_key"

result = calculate_guidelines(
    parameter="Ammonia, un-ionized as N",
    media="surface_water",
    context={
        "pH": "7.5 1",
        "temperature": "15 °C"
    },
    target_unit="mg/L"  # Optional unit conversion
)

# Filter results
chronic_aquatic = [
    g for g in result.results
    if g.basis == "aquatic biota" and g.exposure_duration == "Chronic"
]
```

### Batch Calculations

```python
from guidelinely import calculate_batch

# Calculate multiple parameters at once (more efficient)
result = calculate_batch(
    parameters=["Aluminum, Dissolved", "Ammonia, un-ionized as N", "Lead, Dissolved", "Sulfate as SO4", "Nitrite as N"],
    media="surface_water",
    context={
        "pH": "7.5 1",
        "hardness": "150 mg/L",
        "temperature": "15 °C",
        "chloride": "18 mg/L"
    }
)

print(f"Total: {result.total_count} guidelines")

# With per-parameter unit conversion
result = calculate_batch(
    parameters=[
        "Aluminum, Dissolved",
        {"name": "Lead, Dissolved", "target_unit": "mg/L"}
    ],
    media="surface_water",
    context={
        "hardness": "100 mg/L",
    }
)
```

## Environmental Context Parameters

> **Note**: Currently, only **surface_water** and **groundwater** guidelines are present in the API database. Soil, sediment, and other media types are planned for future releases.

All context parameters **must be strings with units** (Pint format):

### Water (surface_water, groundwater)
```python
context = {
    "pH": "7.0 1",           # Dimensionless - use "1" as unit
    "hardness": "100 mg/L",  # mg/L as CaCO3
    "temperature": "20 °C",
    "chloride": "50 mg/L"
}
```

### Soil (coming soon)
```python
context = {
    "pH": "6.5 1",
    "organic_matter": "3.5 %",
    "cation_exchange_capacity": "15 meq/100g"
}
```

### Sediment (coming soon)
```python
context = {
    "pH": "7.0 1",
    "organic_matter": "2.5 %",
    "grain_size": "0.5 mm"
}
```

## Analytics (Requires API Key)

The library provides access to API analytics endpoints for monitoring usage and performance:

```python
from guidelinely import (
    get_analytics_summary,
    get_endpoint_statistics,
    get_user_agent_statistics,
    get_key_statistics,
    get_timeseries_data,
    get_error_statistics,
)

# Get comprehensive analytics summary for the last 30 days
summary = get_analytics_summary(days=30, api_key="your_api_key")
print(f"Total requests: {summary.overall_stats.total_requests}")
print(f"Error rate: {summary.overall_stats.error_rate}%")

# Get endpoint usage statistics
endpoints = get_endpoint_statistics(days=30, api_key="your_api_key")
for ep in endpoints[:5]:  # Top 5 endpoints
    print(f"{ep.endpoint}: {ep.total_requests} requests")

# Get time-series data for graphing
data = get_timeseries_data(days=7, interval="daily", api_key="your_api_key")
for point in data:
    print(f"{point.timestamp}: {point.request_count} requests")

# Get error statistics
errors = get_error_statistics(days=30, api_key="your_api_key")
print(f"Errors by status code: {errors}")
```

### Analytics Functions

- `get_analytics_summary(days, api_key)` - Comprehensive analytics overview
- `get_endpoint_statistics(days, api_key)` - Usage by endpoint
- `get_user_agent_statistics(days, api_key)` - Usage by User-Agent
- `get_key_statistics(days, api_key)` - Usage by API key
- `get_timeseries_data(days, interval, api_key)` - Time-series data (hourly/daily)
- `get_error_statistics(days, api_key)` - Error statistics by status code

All analytics endpoints require a valid API key and return data for the specified time period (1-365 days).

## Error Handling

The library provides custom exceptions for structured error handling:

```python
from guidelinely import (
    calculate_guidelines,
    GuidelinelyError,
    GuidelinelyAPIError,
    GuidelinelyTimeoutError,
)

try:
    result = calculate_guidelines(
        parameter="Copper",
        media="surface_water",
        context={"pH": "7.0 1", "hardness": "100 mg/L"}
    )
except GuidelinelyTimeoutError:
    print("Request timed out, please try again")
except GuidelinelyAPIError as e:
    if e.status_code == 404:
        print("Parameter not found")
    elif e.status_code == 401:
        print("Invalid API key")
    else:
        print(f"API error {e.status_code}: {e.message}")
except GuidelinelyError as e:
    print(f"Guidelinely error: {e}")
```

### Exception Types

- `GuidelinelyError` - Base exception for all library errors
- `GuidelinelyAPIError` - API returned an error response (has `status_code` and `message` attributes)
- `GuidelinelyTimeoutError` - Request timed out

## Data Models

The library uses Pydantic for type-safe data handling:

```python
from guidelinely.models import GuidelineResponse, CalculationResponse

# All API responses are strongly typed
result: CalculationResponse = calculate_guidelines(...)

# Access typed fields
for guideline in result.results:
    guideline.parameter  # str
    guideline.value      # str (PostgreSQL unitrange format)
    guideline.lower      # Optional[float]
    guideline.upper      # Optional[float]
    guideline.unit       # str
    guideline.is_calculated  # bool
```

## Guideline Value Format

Guidelines use [postgresql-unit](https://github.com/df7cb/postgresql-unit) `unitrange` format:
- `[10 μg/L,100 μg/L]` - Range from 10 to 100 μg/L
- `(,87.0 μg/L]` - Upper limit only (≤87.0 μg/L)
- `[5.0 mg/L,)` - Lower limit only (≥5.0 mg/L)

Parsed into `lower`, `upper`, and `unit` fields.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run all quality checks (formatting, linting, type checking, tests with coverage)
pre-commit run --all-files

# Or run individually:

# Run tests
pytest

# Run tests with coverage (minimum 85% required)
pytest --cov=guidelinely --cov-report=html --cov-fail-under=85

# Format code
black guidelinely/ tests/ examples/

# Type checking
mypy guidelinely/

# Linting
ruff check guidelinely/ tests/
```

## API Reference

### Client Functions

#### Metadata (No Authentication Required)
- `health_check()` - Service health check
- `readiness_check()` - Database readiness check
- `list_parameters()` - List all chemical parameters
- `search_parameters(q, media, source, document)` - Search parameters with filters
- `match_parameters(parameters, threshold, include_media, strategy)` - Match parameter names using multi-strategy approach
- `search_guidelines(**filters)` - Search guidelines by any field
- `list_media()` - List media types
- `list_sources()` - List guideline sources
- `get_stats()` - Database statistics

#### Calculations (Optional Authentication)
- `calculate_guidelines(parameter, media, context, target_unit, api_key)` - Calculate single parameter
- `calculate_batch(parameters, media, context, api_key)` - Batch calculate (max 50 parameters)

#### Analytics (Requires Authentication)
- `get_analytics_summary(days, api_key)` - Comprehensive analytics overview
- `get_endpoint_statistics(days, api_key)` - Usage statistics by endpoint
- `get_user_agent_statistics(days, api_key)` - Usage statistics by User-Agent
- `get_key_statistics(days, api_key)` - Usage statistics by API key
- `get_timeseries_data(days, interval, api_key)` - Time-series data (hourly/daily)
- `get_error_statistics(days, api_key)` - Error statistics by status code

### Models

#### Response Models
- `GuidelineResponse` - Single guideline result
- `GuidelineSearchResult` - Search result metadata
- `CalculationResponse` - Calculation endpoint response
- `SourceResponse` - Guideline source information
- `StatsResponse` - Database statistics
- `ParameterMatch` - Single parameter match result
- `ParameterMatchQueryResult` - Matches for a query parameter
- `ParameterMatchResponse` - Parameter matching response
- `AnalyticsSummary` - Comprehensive analytics overview
- `UsageStatistics` - Overall usage statistics
- `EndpointStatistics` - Per-endpoint statistics
- `APIKeyUsage` - Per-key usage statistics
- `UserAgentStatistics` - Per-user-agent statistics
- `TimeSeriesData` - Time-series data point

#### Request Models
- `CalculateRequest` - Single calculation request body
- `BatchCalculateRequest` - Batch calculation request body
- `ParameterWithUnit` - Parameter with optional target unit
- `SearchParametersRequest` - Parameter search filters

## Parameter Name Matching

The `match_parameters()` function helps handle naming inconsistencies across domains, geographies, and languages:

```python
from guidelinely import match_parameters

# Match chemical abbreviations
result = match_parameters(["NH3", "Cu", "Al", "Pb"])
for query_result in result.results:
    if query_result.matches:
        match = query_result.matches[0]
        print(f"{query_result.query} → {match.parameter} (confidence: {match.confidence:.0%})")

# Handle spelling variations with alias strategy
result = match_parameters(
    ["Aluminium", "sulphate"],
    strategy="alias",
    threshold=0.3
)

# Fast matching without media types
result = match_parameters(
    ["copper", "lead", "zinc"],
    include_media=False
)
```

### Matching Strategies

- **simple** (default): Fuzzy matching with hardcoded abbreviations (NH3 → Ammonia)
- **alias**: Uses curated database table for translations and variants
- **llm**: Semantic matching using Large Language Models (future)
- **auto**: Tries strategies in sequence for best results

### Parameters

- `parameters`: List of parameter names to match (1-50 parameters)
- `threshold`: Confidence threshold 0.0-1.0 (default 0.5, lower = more matches)
- `include_media`: Include available media types (default True)
- `strategy`: Matching strategy (default "auto")

## Examples

See the `examples/` directory for complete working examples:

1. `01_basic_metadata.py` - Basic metadata queries
2. `02_calculate_single_parameter.py` - Single parameter calculations
3. `03_batch_calculations.py` - Batch calculations
4. `04_groundwater_calculations.py` - Groundwater calculations (soil guidelines coming soon)
5. `05_advanced_workflow.py` - Advanced filtering and analysis
6. `06_analytics.py` - API usage analytics
7. `07_parameter_matching.py` - Parameter name matching and validation

## Resources

- **API Documentation**: https://guidelines.1681248.com/docs
- **OpenAPI Spec**: https://guidelines.1681248.com/openapi.json
- **R Client**: https://github.com/mpdavison/envguidelines
- **Issue Tracker**: https://github.com/mpdavison/envguidelines-py/issues

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style guidelines, and the pull request process.