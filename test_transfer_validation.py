#!/usr/bin/env python3
"""
Test script to verify transfer API location validation fix.
"""

import sys
from typing import Dict, Any, Optional, Tuple

# Mock airport locations for testing
AIRPORT_LOCATIONS = {
    "JFK": {"name": "JFK Airport", "cityName": "New York", "countryCode": "US",
            "geoCode": "40.6413,-73.7781", "addressLine": "Queens, NY 11430"},
    "LAX": {"name": "LAX Airport", "cityName": "Los Angeles", "countryCode": "US",
            "geoCode": "33.9416,-118.4085", "addressLine": "Los Angeles, CA 90045"},
}


def format_location_for_transfer(location: str, is_start: bool = True) -> tuple[Dict[str, Any], Optional[str]]:
    """Test version of format_location_for_transfer"""
    location_upper = location.upper().strip()

    # Check if it's an airport code in our database
    if location_upper in AIRPORT_LOCATIONS:
        airport_data = AIRPORT_LOCATIONS[location_upper]
        if is_start:
            return {"startLocationCode": location_upper}, None
        else:
            return {
                "endLocationCode": location_upper,
                "endAddressLine": airport_data["addressLine"],
                "endCityName": airport_data["cityName"],
                "endCountryCode": airport_data["countryCode"],
                "endGeoCode": airport_data["geoCode"],
                "endName": airport_data["name"]
            }, None

    # Check if it's coordinates (lat,long format)
    if "," in location and len(location.split(",")) == 2:
        try:
            lat, lon = location.split(",")
            lat_float = float(lat.strip())
            lon_float = float(lon.strip())

            # Validate coordinate ranges
            if not (-90 <= lat_float <= 90) or not (-180 <= lon_float <= 180):
                return {}, f"Invalid coordinates: latitude must be -90 to 90, longitude must be -180 to 180"

            if is_start:
                return {"startGeoCode": location.strip()}, None
            else:
                return {"endGeoCode": location.strip()}, None
        except ValueError:
            return {}, f"Invalid coordinate format: '{location}'. Expected format: 'latitude,longitude' (e.g., '40.7128,-74.0060')"

    # If we get here, it's likely a free-text address which is not supported
    location_type = "start" if is_start else "end"

    # Check if it looks like an airport code that's not in our database
    if len(location_upper) == 3 and location_upper.isalpha():
        available_airports = ", ".join(sorted(AIRPORT_LOCATIONS.keys()))
        return {}, (
            f"Airport code '{location_upper}' not found in database. "
            f"Available airports: {available_airports}."
        )

    # It's a free-text address
    return {}, (
        f"Invalid {location_type}_location format: '{location}'. "
        f"The Amadeus Transfer API requires either:\n"
        f"  1. Airport code (e.g., 'JFK', 'LAX')\n"
        f"  2. Coordinates in 'latitude,longitude' format (e.g., '40.7128,-74.0060')\n"
        f"\n"
        f"Free-text addresses are NOT supported."
    )


def test_validation():
    """Test the validation logic"""
    print("Testing transfer location validation...")
    print("=" * 70)

    tests = [
        # (location, is_start, should_succeed, description)
        ("JFK", True, True, "Valid airport code as start"),
        ("LAX", False, True, "Valid airport code as end"),
        ("40.7128,-74.0060", True, True, "Valid coordinates as start"),
        ("51.5074,-0.1278", False, True, "Valid coordinates as end"),
        ("CDG", True, False, "Airport code not in database"),
        ("Times Square", True, False, "Free-text address (not supported)"),
        ("New York, NY", False, False, "Free-text address (not supported)"),
        ("invalid,coords", True, False, "Invalid coordinate format"),
        ("200,300", False, False, "Out of range coordinates"),
    ]

    passed = 0
    failed = 0

    for location, is_start, should_succeed, description in tests:
        location_type = "start" if is_start else "end"
        result, error = format_location_for_transfer(location, is_start)

        success = error is None

        if success == should_succeed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"\n{status}: {description}")
        print(f"  Input: {location} ({location_type})")
        print(f"  Expected: {'success' if should_succeed else 'error'}")
        print(f"  Got: {'success' if success else 'error'}")

        if error:
            print(f"  Error: {error[:100]}...")
        elif result:
            print(f"  Result keys: {list(result.keys())}")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_validation())
