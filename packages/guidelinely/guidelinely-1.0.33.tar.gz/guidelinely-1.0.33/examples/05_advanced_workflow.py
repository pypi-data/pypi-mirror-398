"""Advanced Filtering and Analysis Workflow.

Demonstrate filtering, grouping, and analysis of guideline results.
"""

import os
from collections import defaultdict

from guidelinely import calculate_batch


def main():
    """Advanced filtering and analysis workflow."""

    # Ensure API key is set
    api_key = os.getenv("GUIDELINELY_API_KEY")
    if not api_key:
        print("Note: GUIDELINELY_API_KEY environment variable not set")
        print("API key is optional but recommended for calculation endpoints")
        print()

    print("=== Advanced Workflow: Comprehensive Water Quality Analysis ===")
    print()

    # Comprehensive batch calculation
    # Note: Parameter names must match exactly - use search_parameters() to find valid names
    result = calculate_batch(
        parameters=[
            "Aluminum, Dissolved",
            "Ammonia, un-ionized as N",
            "Arsenic, Dissolved",
            "Cadmium, Dissolved",
            "Chloride",
            "Chromium, Dissolved",
            "Copper, Dissolved",
            "Iron, Dissolved",
            "Lead, Dissolved",
            "Mercury, Dissolved",
            "Nickel, Dissolved",
            "Selenium, Dissolved",
            "Silver, Dissolved",
            "Zinc, Dissolved",
        ],
        media="surface_water",
        context={
            "pH": "7.5 1",
            "hardness": "150 mg/L",
            "temperature": "15 °C",
            "chloride": "18 mg/L",
        },
    )

    print(f"Total guidelines retrieved: {result.total_count}")
    print(f"Context: {result.context}")
    print()

    # Analysis 1: Count by source
    print("=== Guidelines by Source ===")
    by_source = defaultdict(int)
    for g in result.results:
        by_source[g.source] += 1

    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    # Analysis 2: Calculated vs Static guidelines
    print("\n=== Calculated vs Static Guidelines ===")
    calculated = sum(1 for g in result.results if g.is_calculated)
    static = sum(1 for g in result.results if not g.is_calculated)
    print(f"  Calculated: {calculated}")
    print(f"  Static: {static}")
    print(f"  Percentage calculated: {calculated/result.total_count*100:.1f}%")

    # Analysis 3: Group by receptor and exposure
    print("\n=== By Receptor and Exposure Duration ===")
    by_receptor_exposure = defaultdict(lambda: defaultdict(int))
    for g in result.results:
        by_receptor_exposure[g.receptor][g.exposure_duration] += 1

    for receptor, exposures in sorted(by_receptor_exposure.items()):
        print(f"\n{receptor}:")
        for exposure, count in sorted(exposures.items()):
            print(f"  {exposure}: {count}")

    # Analysis 4: Most stringent guidelines (aquatic life, chronic)
    print("\n=== Most Stringent Chronic Aquatic Life Guidelines ===")
    chronic_aquatic = [
        g
        for g in result.results
        if g.receptor == "Aquatic Life" and g.exposure_duration == "chronic" and g.upper is not None
    ]

    # Group by parameter and find minimum upper bound
    most_stringent = {}
    for g in chronic_aquatic:
        param = g.parameter
        if param not in most_stringent or g.upper < most_stringent[param]["upper"]:
            most_stringent[param] = {
                "upper": g.upper,
                "unit": g.unit,
                "source": g.source,
                "value": g.value,
            }

    for param, info in sorted(most_stringent.items()):
        print(f"  {param}: ≤{info['upper']} {info['unit']} ({info['source']})")

    # Analysis 5: Parameters with widest range of guidelines
    print("\n=== Parameters with Most Guideline Diversity ===")
    param_counts = defaultdict(int)
    for g in result.results:
        param_counts[g.parameter] += 1

    top_params = sorted(param_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for param, count in top_params:
        print(f"  {param}: {count} guidelines")

    # Analysis 6: Temperature-dependent calculations
    print("\n=== Temperature Sensitivity Analysis ===")
    print("Comparing Ammonia at different temperatures...")

    temps = ["5 °C", "15 °C", "25 °C"]
    ammonia_results = {}

    for temp in temps:
        temp_result = calculate_batch(
            parameters=["Ammonia, un-ionized as N"],
            media="surface_water",
            context={
                "pH": "7.5 1",
                "temperature": temp
            },
        )
        ammonia_results[temp] = temp_result

        # All results will have the same unit
        all_units = {g.unit for g in temp_result.results}
        if len(all_units) != 1:
            raise ValueError("Inconsistent units in ammonia results")

        unit = all_units.pop()
        min_upper = min(
            (g.upper for g in temp_result.results if g.upper is not None), default=None
        )
        max_upper = max(
            (g.upper for g in temp_result.results if g.upper is not None), default=None
        )
        print(
            f"  {temp}: {temp_result.total_count} guidelines "
            f"(Min upper limit: {min_upper:.2f} {unit}, Max upper limit: {max_upper:.2f} {unit})"
        )


if __name__ == "__main__":
    main()
