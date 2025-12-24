"""Batch Calculations for Multiple Parameters.

Calculate guidelines for multiple parameters in surface water.
"""

import os

from guidelinely import calculate_batch


def main():
    """Batch calculate multiple parameters."""

    # Ensure API key is set
    api_key = os.getenv("GUIDELINELY_API_KEY")
    if not api_key:
        print("Note: GUIDELINELY_API_KEY environment variable not set")
        print("API key is optional but recommended for calculation endpoints")
        print()

    print("=== Batch Calculate Multiple Parameters ===")
    print()

    # Calculate multiple parameters in surface water
    # Note: Parameter names must match exactly - use search_parameters() to find valid names
    result = calculate_batch(
        parameters=[
            "Aluminum, Dissolved",
            "Ammonia, un-ionized as N",
            "Lead, Dissolved",
            "Sulfate as SO4",
            "Nitrite as N",
        ],
        media="surface_water",
        context={
            "pH": "7.5 1",  # Slightly alkaline
            "hardness": "150 mg/L",  # Moderately hard water
            "temperature": "15 °C",  # Cool water
            "chloride": "18 mg/L",  # Moderate chloride
        },
    )

    print(f"Total guidelines found: {result.total_count}")
    print(f"Context: {result.context}")
    print()

    # Group by parameter
    by_parameter = {}
    for guideline in result.results:
        param = guideline.parameter
        if param not in by_parameter:
            by_parameter[param] = []
        by_parameter[param].append(guideline)

    # Display grouped results
    for param, guidelines in sorted(by_parameter.items()):
        print(f"\n{param}:")
        print("-" * 60)
        for g in guidelines:
            print(f"  {g.value} | {g.receptor} | {g.exposure_duration} | {g.table_name} | {g.source}")

    # Example with per-parameter unit conversion
    print("\n\n=== With Per-Parameter Unit Conversion ===")
    print()

    result2 = calculate_batch(
        parameters=[
            "Aluminum, Dissolved",
            {"name": "Lead, Dissolved", "target_unit": "mg/L"},
        ],
        media="surface_water",
        context={"hardness": "100 mg/L"},
    )

    print(f"Total guidelines found: {result2.total_count}")

    # Filter to chronic exposure guidelines
    print("\n=== Chronic Exposure Guidelines ===")
    chronic = [g for g in result.results if g.exposure_duration == "Chronic"]

    for guideline in chronic[:10]:  # Show first 10
        upper = guideline.upper if guideline.upper else "unbounded"
        print(f"{guideline.parameter}: ≤{upper} {guideline.unit}")


if __name__ == "__main__":
    main()
