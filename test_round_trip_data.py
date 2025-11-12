#!/usr/bin/env python
"""Test script to investigate what data fast_flights returns for round-trip flights."""

import sys
import json
from fast_flights import FlightQuery, Passengers, get_flights, create_query

def test_round_trip_data():
    """Test what attributes are available on round-trip flight objects."""
    print("Testing fast_flights round-trip data structure...\n")

    # Create a round-trip query
    flights = [
        FlightQuery(date="2025-12-15", from_airport="SFO", to_airport="LAX"),
        FlightQuery(date="2025-12-20", from_airport="LAX", to_airport="SFO"),
    ]
    passengers_info = Passengers(adults=1)

    print("Creating round-trip query: SFO ↔ LAX (2025-12-15 to 2025-12-20)...")
    query = create_query(
        flights=flights,
        trip="round-trip",
        seat="economy",
        passengers=passengers_info,
        max_stops=2
    )

    print("Fetching flights...\n")
    try:
        result = get_flights(query)

        if result:
            print(f"✓ Found {len(result)} flight option(s)\n")

            # Check result type and attributes
            print(f"Result type: {type(result)}")
            print(f"Result is list: {isinstance(result, list)}\n")

            # Get first flight option
            if len(result) > 0:
                flight = result[0]
                print(f"First flight option type: {type(flight)}")
                print(f"Flight attributes: {[a for a in dir(flight) if not a.startswith('_')]}\n")

                # Try to access key attributes
                print("=== Flight Option Data ===")

                # Price
                if hasattr(flight, 'price'):
                    print(f"  Price: {flight.price}")

                # Airlines
                if hasattr(flight, 'airlines'):
                    print(f"  Airlines: {flight.airlines}")

                # Type
                if hasattr(flight, 'type'):
                    print(f"  Type: {flight.type}")

                # Flights/segments
                if hasattr(flight, 'flights'):
                    print(f"  Number of segments: {len(flight.flights)}")
                    print(f"  Flights (segments) type: {type(flight.flights)}")

                    # Examine each segment
                    for i, segment in enumerate(flight.flights):
                        print(f"\n  --- Segment {i+1} ---")
                        print(f"    Type: {type(segment)}")
                        print(f"    Attributes: {[a for a in dir(segment) if not a.startswith('_')]}")

                        if hasattr(segment, 'from_airport'):
                            from_airport = segment.from_airport
                            print(f"    From: {getattr(from_airport, 'code', '?')} - {getattr(from_airport, 'name', '?')}")

                        if hasattr(segment, 'to_airport'):
                            to_airport = segment.to_airport
                            print(f"    To: {getattr(to_airport, 'code', '?')} - {getattr(to_airport, 'name', '?')}")

                        if hasattr(segment, 'departure'):
                            print(f"    Departure: {segment.departure}")

                        if hasattr(segment, 'arrival'):
                            print(f"    Arrival: {segment.arrival}")

                        if hasattr(segment, 'duration'):
                            print(f"    Duration: {segment.duration} min")

                # Print raw object
                print("\n=== Raw Flight Object ===")
                if hasattr(flight, '__dict__'):
                    print(json.dumps(flight.__dict__, indent=2, default=str))
                else:
                    print(f"Flight object: {flight}")

                # Look at second flight option if available
                if len(result) > 1:
                    print("\n\n=== Second Flight Option (for comparison) ===")
                    flight2 = result[1]
                    print(f"  Price: {getattr(flight2, 'price', 'N/A')}")
                    if hasattr(flight2, 'flights'):
                        print(f"  Number of segments: {len(flight2.flights)}")
                        for i, segment in enumerate(flight2.flights):
                            if hasattr(segment, 'from_airport') and hasattr(segment, 'to_airport'):
                                from_code = getattr(segment.from_airport, 'code', '?')
                                to_code = getattr(segment.to_airport, 'code', '?')
                                print(f"    Segment {i+1}: {from_code} → {to_code}")

        else:
            print("✗ No flights found")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_round_trip_data()
