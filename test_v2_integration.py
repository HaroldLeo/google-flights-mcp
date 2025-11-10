#!/usr/bin/env python
"""
Comprehensive test of fast-flights v2.2 integration.

Tests:
1. Basic import and version check
2. One-way flight search
3. Round-trip flight search (does it have the return flight bug?)
4. Direct round-trip search (our workaround)
5. Data structure compatibility
"""

import sys
import json
from datetime import datetime, timedelta

print("="*80)
print("FAST-FLIGHTS V2.2 INTEGRATION TEST")
print("="*80)
print()

# Test 1: Import and version check
print("[1/5] Testing import and version...")
try:
    from fast_flights import FlightQuery, Passengers, get_flights, create_query
    import fast_flights
    print(f"✓ Import successful")
    print(f"  Package location: {fast_flights.__file__}")
    if hasattr(fast_flights, '__version__'):
        print(f"  Version: {fast_flights.__version__}")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print()

# Test 2: One-way flight search
print("[2/5] Testing one-way flight search...")
try:
    # Use future dates
    departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    flights = [
        FlightQuery(date=departure_date, from_airport="SFO", to_airport="LAX")
    ]
    passengers = Passengers(adults=1)
    query = create_query(
        flights=flights,
        trip="one-way",
        seat="economy",
        passengers=passengers
    )

    result = get_flights(query)

    if result and len(result) > 0:
        print(f"✓ One-way search successful: {len(result)} flights found")

        # Examine first flight structure
        first_flight = result[0]
        print(f"  Structure check:")
        print(f"    - has 'price': {hasattr(first_flight, 'price')}")
        print(f"    - has 'name': {hasattr(first_flight, 'name')}")
        print(f"    - has 'is_best': {hasattr(first_flight, 'is_best')}")
        print(f"    - has 'flights' (segments): {hasattr(first_flight, 'flights')}")
        print(f"    - has 'airlines' (list): {hasattr(first_flight, 'airlines')}")

        # Show first flight details
        print(f"  First flight:")
        print(f"    - Price: ${first_flight.price if hasattr(first_flight, 'price') else 'N/A'}")
        print(f"    - Airline: {first_flight.name if hasattr(first_flight, 'name') else 'N/A'}")
        print(f"    - Is Best: {first_flight.is_best if hasattr(first_flight, 'is_best') else 'N/A'}")
        print(f"    - Stops: {first_flight.stops if hasattr(first_flight, 'stops') else 'N/A'}")

        # Determine version structure
        if hasattr(first_flight, 'flights'):
            print(f"  → Detected: v3.0rc0 structure (has segments)")
        else:
            print(f"  → Detected: v2.2 structure (simple)")
    else:
        print(f"✗ No flights found (this may be normal for some routes)")

except Exception as e:
    print(f"✗ One-way search failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Round-trip flight search (check for return flight bug)
print("[3/5] Testing round-trip flight search...")
try:
    outbound_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')

    flights = [
        FlightQuery(date=outbound_date, from_airport="SFO", to_airport="LAX"),
        FlightQuery(date=return_date, from_airport="LAX", to_airport="SFO"),
    ]
    passengers = Passengers(adults=1)
    query = create_query(
        flights=flights,
        trip="round-trip",
        seat="economy",
        passengers=passengers,
        max_stops=2  # Allow connections
    )

    result = get_flights(query)

    if result and len(result) > 0:
        print(f"✓ Round-trip search successful: {len(result)} options found")

        # Check if we have both outbound and return segments
        first_option = result[0]

        if hasattr(first_option, 'flights'):
            # v3.0rc0 structure with segments
            segments = first_option.flights
            print(f"  First option has {len(segments)} segment(s)")

            # Check if we have both directions
            has_outbound = False
            has_return = False

            for i, seg in enumerate(segments):
                from_code = seg.from_airport.code if hasattr(seg, 'from_airport') else None
                to_code = seg.to_airport.code if hasattr(seg, 'to_airport') else None
                print(f"    Segment {i+1}: {from_code} → {to_code}")

                if from_code == "SFO":
                    has_outbound = True
                if to_code == "SFO":
                    has_return = True

            if has_outbound and has_return:
                print(f"  ✓ BOTH outbound and return segments present")
            elif has_outbound and not has_return:
                print(f"  ✗ MISSING return segments! (Only outbound present)")
            else:
                print(f"  ? Unexpected segment pattern")
        else:
            # v2.2 structure - simple
            print(f"  v2.2 structure - doesn't expose segments")
            print(f"  Price: ${first_option.price}")
            print(f"  Airline: {first_option.name}")
            print(f"  Stops: {first_option.stops}")
            print(f"  ⚠️  Cannot verify if return flight is included (segments not exposed)")

    else:
        print(f"✗ No round-trip flights found")

except Exception as e:
    print(f"✗ Round-trip search failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Direct round-trip search (test the bug)
print("[4/5] Testing DIRECT round-trip search (max_stops=0)...")
try:
    outbound_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')

    flights = [
        FlightQuery(date=outbound_date, from_airport="SFO", to_airport="LAX"),
        FlightQuery(date=return_date, from_airport="LAX", to_airport="SFO"),
    ]
    passengers = Passengers(adults=1)
    query = create_query(
        flights=flights,
        trip="round-trip",
        seat="economy",
        passengers=passengers,
        max_stops=0  # Direct flights only
    )

    result = get_flights(query)

    if result and len(result) > 0:
        print(f"✓ Direct round-trip search returned {len(result)} result(s)")

        first_option = result[0]

        if hasattr(first_option, 'flights'):
            # v3.0rc0 structure
            segments = first_option.flights
            print(f"  First option has {len(segments)} segment(s)")

            for i, seg in enumerate(segments):
                from_code = seg.from_airport.code if hasattr(seg, 'from_airport') else "?"
                to_code = seg.to_airport.code if hasattr(seg, 'to_airport') else "?"
                print(f"    Segment {i+1}: {from_code} → {to_code}")

            if len(segments) >= 2:
                print(f"  ✓ Multiple segments present (likely includes return)")
            elif len(segments) == 1:
                print(f"  ✗ BUG CONFIRMED: Only 1 segment (missing return flight)")
                print(f"  → This confirms the direct round-trip bug exists in this version")
        else:
            # v2.2 structure
            print(f"  v2.2 structure - price: ${first_option.price}")
            print(f"  ⚠️  Cannot verify segment count (not exposed in v2.2)")
    else:
        print(f"⚠️  No direct flights found (may be normal for this route)")

except Exception as e:
    print(f"✗ Direct round-trip search failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Test our flight_to_dict compatibility
print("[5/5] Testing flight_to_dict compatibility...")
try:
    sys.path.insert(0, '/home/user/google-flights-mcp/src')
    from mcp_server_google_flights.server import flight_to_dict

    # Get a sample flight
    flights = [FlightQuery(date=outbound_date, from_airport="SFO", to_airport="LAX")]
    query = create_query(flights=flights, trip="one-way", seat="economy", passengers=Passengers(adults=1))
    result = get_flights(query)

    if result and len(result) > 0:
        sample_flight = result[0]

        # Test conversion
        converted = flight_to_dict(sample_flight, compact=False)

        print(f"✓ flight_to_dict conversion successful")
        print(f"  Converted keys: {list(converted.keys())}")
        print(f"  Has 'is_best': {'is_best' in converted}")
        print(f"  Has 'price': {'price' in converted}")
        print(f"  Has 'airlines': {'airlines' in converted}")

        # Show sample output
        print(f"  Sample output:")
        print(f"    Price: {converted.get('price')}")
        print(f"    Airlines: {converted.get('airlines')}")
        print(f"    Is Best: {converted.get('is_best')}")

    else:
        print(f"⚠️  Could not test (no flights available)")

except Exception as e:
    print(f"✗ flight_to_dict test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("TEST SUMMARY")
print("="*80)
print("Review the results above to determine:")
print("1. Whether v2.2 is correctly installed and working")
print("2. Whether the direct round-trip bug exists in v2.2")
print("3. Whether our code correctly handles v2.2 structure")
print("4. Whether our workaround is still needed")
print()
