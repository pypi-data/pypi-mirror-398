"""Basic Metadata Queries.

Explore available parameters, media types, and data sources.
"""

from guidelinely import (
    get_stats,
    health_check,
    list_media,
    list_parameters,
    list_sources,
    readiness_check,
    search_parameters,
)


def main():
    """Run basic metadata queries."""

    # Check API health status
    print("=== Health Check ===")
    health_status = health_check()
    print(f"Health: {health_status}")
    print()

    # Check if API is ready to handle requests
    print("=== Readiness Check ===")
    readiness_status = readiness_check()
    print(f"Readiness: {readiness_status}")
    print()

    # List all available chemical parameters
    print("=== All Parameters (first 10) ===")
    all_params = list_parameters()
    print(f"Total parameters: {len(all_params)}")
    print(f"First 10: {all_params[:10]}")
    print()

    # Search for specific parameters (e.g., ammonia)
    print("=== Search for 'ammonia' ===")
    ammonia_params = search_parameters("ammonia")
    print(f"Found: {ammonia_params}")
    print()

    # Get all available media types
    print("=== Media Types ===")
    media_types = list_media()
    for key, value in media_types.items():
        print(f"  {key}: {value}")
    print()

    # View guideline sources and documents
    print("=== Guideline Sources (first source) ===")
    sources = list_sources()
    if sources:
        print(f"Total sources: {len(sources)}")
        first_source = sources[0]
        print(f"First source: {first_source.name}")
        print(f"  Documents: {len(first_source.documents)}")
    print()

    # Get database statistics
    print("=== Database Statistics ===")
    stats = get_stats()
    print(f"  parameters: {stats.parameters}")
    print(f"  guidelines: {stats.guidelines}")
    print(f"  sources: {stats.sources}")
    print(f"  documents: {stats.documents}")


if __name__ == "__main__":
    main()
