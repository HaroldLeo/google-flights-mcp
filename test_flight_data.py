#!/usr/bin/env python
"""Test script to investigate what data fast_flights actually returns."""

import sys
import json
from fast_flights import FlightQuery, Passengers, get_flights, create_query

def test_flight_data():
    """Test what attributes are available on flight objects."""
    print("Testing fast_flights data structure...\n")

    # Create a simple test query
    flights = [
        FlightQuery(date="2025-12-15", from_airport="SFO", to_airport="JFK"),
    ]
    passengers_info = Passengers(adults=1)

    print("Creating query for SFO -> JFK on 2025-12-15...")
    query = create_query(
        flights=flights,
        trip="one-way",
        seat="economy",
        passengers=passengers_info
    )

    print("Fetching flights...\n")
    try:
        result = get_flights(query)

        if result:
            print(f"✓ Found {len(result)} flight(s)\n")

            # Check result type and attributes
            print(f"Result type: {type(result)}")
            print(f"Result attributes: {dir(result)}\n")

            # Get first flight
            if len(result) > 0:
                flight = result[0]
                print(f"Flight type: {type(flight)}")
                print(f"Flight attributes: {dir(flight)}\n")

                # Try to access each attribute
                print("=== Flight Data ===")
                attrs = ['is_best', 'name', 'departure', 'arrival', 'arrival_time_ahead',
                        'duration', 'stops', 'delay', 'price', 'airline', 'flight_number',
                        'layover', 'layovers', 'segments', 'legs']

                for attr in attrs:
                    try:
                        value = getattr(flight, attr, "ATTRIBUTE_NOT_FOUND")
                        print(f"  {attr}: {value} (type: {type(value).__name__})")
                    except Exception as e:
                        print(f"  {attr}: ERROR - {e}")

                # Print the entire flight object as dict if possible
                print("\n=== Full Flight Object ===")
                if hasattr(flight, '__dict__'):
                    print(json.dumps(flight.__dict__, indent=2, default=str))
                else:
                    print(f"Flight object: {flight}")

        else:
            print("✗ No flights found")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flight_data()
