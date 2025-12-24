"""Groundwater Guideline Calculations.

Calculate guidelines for parameters in groundwater media.

Note: Currently only surface_water and groundwater guidelines are available in the API.
Soil, sediment, and other media types are planned for future releases.
"""

import os

from guidelinely import calculate_batch, calculate_guidelines


def main():
    """Calculate groundwater guidelines."""

    # Ensure API key is set
    api_key = os.getenv("GUIDELINELY_API_KEY")
    if not api_key:
        print("Note: GUIDELINELY_API_KEY environment variable not set")
        print("API key is optional but recommended for calculation endpoints")
        print()

    print("=== Groundwater Guideline Calculations ===")
    print()

    # Example 1: Single parameter in groundwater
    print("--- Aluminum in Groundwater ---")
    result = calculate_guidelines(
        parameter="Aluminum",
        media="groundwater",
        context={},  # No context parameters needed for this guideline
    )

    print(f"Total guidelines: {result.total_count}")
    print(f"Context: {result.context}")
    print()

    for g in result.results[:5]:  # Show first 5
        print(f"  {g.value} | {g.receptor} | {g.source}")

    # Example 2: Batch groundwater calculations
    print("\n--- Multiple Parameters in Groundwater ---")
    result2 = calculate_batch(
        parameters=["Aluminum", "Antimony", "Arsenic", "Barium", "Benzene"],
        media="groundwater",
        context={},
    )

    print(f"Total guidelines: {result2.total_count}")
    print()

    # Group by parameter
    by_param = {}
    for guideline in result2.results:
        param = guideline.parameter
        if param not in by_param:
            by_param[param] = []
        by_param[param].append(guideline)

    print("Grouped by Parameter:")
    for param, guidelines in sorted(by_param.items()):
        print(f"\n{param} ({len(guidelines)} guidelines):")
        for g in guidelines[:2]:  # Show first 2
            print(f"  {g.value} | {g.source}")

    # Example 3: Compare surface water vs groundwater
    print("\n\n=== Surface Water vs Groundwater (Aluminum) ===")
    print()

    for media_type in ["surface_water", "groundwater"]:
        result = calculate_guidelines(
            parameter="Aluminum",
            media=media_type,
            context={},
        )
        print(f"{media_type}: {result.total_count} guidelines")
        if result.total_count > 0:
            print(f"  First guideline: {result.results[0].value}")


if __name__ == "__main__":
    main()
