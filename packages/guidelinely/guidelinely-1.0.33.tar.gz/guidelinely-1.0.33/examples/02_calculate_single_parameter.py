"""Calculate Guidelines for a Single Parameter.

Calculate dissolved aluminum guidelines in surface water with specific conditions.
"""

import os

from guidelinely import calculate_guidelines


def main():
    """Calculate dissolved aluminum guidelines in surface water."""

    # Ensure API key is set
    api_key = os.getenv("GUIDELINELY_API_KEY")
    if not api_key:
        print("Note: GUIDELINELY_API_KEY environment variable not set")
        print("API key is optional but recommended for calculation endpoints")
        print()

    print("=== Calculate Dissolved Aluminum in Surface Water ===")
    print()

    # Calculate aluminum guidelines in surface water
    # Note: Parameter names must match exactly - use search_parameters() to find valid names
    result = calculate_guidelines(
        parameter="Aluminum, Dissolved",
        media="surface_water",
        context={
            "pH": "7.5 1",  # pH value (unitless, use "1" as unit)
        },
    )

    # Display summary
    print(f"Total guidelines found: {result.total_count}")
    print(f"Context used: {result.context}")
    print()

    # Display results
    if result.total_count > 0:
        print("Guidelines:")
        print("-" * 80)
        for guideline in result.results:
            print(f"Parameter: {guideline.parameter}")
            print(f"Value: {guideline.value}")
            print(f"Unit: {guideline.unit}")
            print(f"Receptor: {guideline.receptor}")
            print(f"Exposure: {guideline.exposure_duration}")
            print(f"Table: {guideline.table} ({guideline.table_name})")
            print(f"Source: {guideline.source}")
            print(f"Calculated: {guideline.is_calculated}")
            if guideline.lower is not None or guideline.upper is not None:
                print(f"Range: [{guideline.lower}, {guideline.upper}]")
            print("-" * 80)

    # Example with unit conversion
    print("\n=== With Unit Conversion to mg/L ===")
    print()

    result_mg = calculate_guidelines(
        parameter="Aluminum, Dissolved",
        media="surface_water",
        context={"pH": "7.5 1"},
        target_unit="mg/L",  # Convert to mg/L
    )

    print(f"Total guidelines found: {result_mg.total_count}")
    if result_mg.total_count > 0:
        for guideline in result_mg.results[:3]:  # Show first 3
            print(f"  {guideline.parameter}: {guideline.value} ({guideline.source})")


if __name__ == "__main__":
    main()
