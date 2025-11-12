#!/usr/bin/env python
"""
Test what fast-flights v3.0rc0 ACTUALLY returns for round-trip searches.

We need to answer:
1. Does it return complete round-trip packages?
2. Are both outbound AND return segments included?
3. Is the price the total round-trip price?
"""

import sys
from datetime import datetime, timedelta

print("="*80)
print("FAST-FLIGHTS V3.0RC0 ROUND-TRIP DATA INSPECTION")
print("="*80)
print()

try:
    from fast_flights import FlightQuery, Passengers, create_query, get_flights
    print("✓ Imports successful (v3.0rc0 API)")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print()

# Test: Round-trip search with connections allowed
print("[TEST 1] Round-trip with max_stops=2 (connections allowed)")
print("-" * 80)

try:
    outbound_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')

    print(f"Search: SFO ↔ LAX")
    print(f"Outbound: {outbound_date}")
    print(f"Return: {return_date}")
    print()

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
        max_stops=2
    )

    result = get_flights(query)

    if result and len(result) > 0:
        print(f"✓ Got {len(result)} results")
        print()

        # Examine first result in detail
        first = result[0]
        print("FIRST RESULT STRUCTURE:")
        print(f"  Type: {type(first)}")
        print(f"  Price: ${first.price if hasattr(first, 'price') else 'N/A'}")
        print(f"  Has 'flights' (segments): {hasattr(first, 'flights')}")

        if hasattr(first, 'flights'):
            segments = first.flights
            print(f"  Number of segments: {len(segments)}")
            print()
            print("  SEGMENTS:")

            for i, seg in enumerate(segments):
                from_code = seg.from_airport.code if hasattr(seg, 'from_airport') else "?"
                from_name = seg.from_airport.name if hasattr(seg, 'from_airport') else "?"
                to_code = seg.to_airport.code if hasattr(seg, 'to_airport') else "?"
                to_name = seg.to_airport.name if hasattr(seg, 'to_airport') else "?"

                print(f"    [{i+1}] {from_code} ({from_name}) → {to_code} ({to_name})")

            print()

            # Analysis
            has_sfo_to_lax = any(
                hasattr(seg, 'from_airport') and hasattr(seg, 'to_airport') and
                seg.from_airport.code == "SFO" and seg.to_airport.code == "LAX"
                for seg in segments
            )
            has_lax_to_sfo = any(
                hasattr(seg, 'from_airport') and hasattr(seg, 'to_airport') and
                seg.from_airport.code == "LAX" and seg.to_airport.code == "SFO"
                for seg in segments
            )

            print("  ANALYSIS:")
            print(f"    Has SFO → LAX segment: {has_sfo_to_lax}")
            print(f"    Has LAX → SFO segment: {has_lax_to_sfo}")

            if has_sfo_to_lax and has_lax_to_sfo:
                print(f"    ✓ COMPLETE: Both outbound and return segments present!")
            elif has_sfo_to_lax and not has_lax_to_sfo:
                print(f"    ✗ INCOMPLETE: Only outbound, missing return!")
            elif has_lax_to_sfo and not has_sfo_to_lax:
                print(f"    ✗ INCOMPLETE: Only return, missing outbound!")
            else:
                print(f"    ? UNEXPECTED: Neither direction matches expected route")

    else:
        print("✗ No results returned")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# Test: Direct round-trip (max_stops=0) - the problematic case
print("[TEST 2] DIRECT round-trip with max_stops=0")
print("-" * 80)

try:
    outbound_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')

    print(f"Search: SFO ↔ LAX (DIRECT ONLY)")
    print(f"Outbound: {outbound_date}")
    print(f"Return: {return_date}")
    print()

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
        max_stops=0  # DIRECT ONLY
    )

    result = get_flights(query)

    if result and len(result) > 0:
        print(f"✓ Got {len(result)} results")
        print()

        # Examine first result
        first = result[0]
        print("FIRST RESULT STRUCTURE:")
        print(f"  Price: ${first.price if hasattr(first, 'price') else 'N/A'}")

        if hasattr(first, 'flights'):
            segments = first.flights
            print(f"  Number of segments: {len(segments)}")
            print()
            print("  SEGMENTS:")

            for i, seg in enumerate(segments):
                from_code = seg.from_airport.code if hasattr(seg, 'from_airport') else "?"
                to_code = seg.to_airport.code if hasattr(seg, 'to_airport') else "?"
                print(f"    [{i+1}] {from_code} → {to_code}")

            print()

            # Analysis
            has_outbound = any(
                hasattr(seg, 'from_airport') and seg.from_airport.code == "SFO"
                for seg in segments
            )
            has_return = any(
                hasattr(seg, 'to_airport') and seg.to_airport.code == "SFO"
                for seg in segments
            )

            print("  ANALYSIS:")
            print(f"    Has outbound (from SFO): {has_outbound}")
            print(f"    Has return (to SFO): {has_return}")

            if has_outbound and has_return:
                print(f"    ✓ COMPLETE: Both directions present")
            else:
                print(f"    ✗ BUG CONFIRMED: Missing direction(s)")
                print(f"    → This is the max_stops=0 round-trip bug")

    else:
        print("⚠️  No results (may be no direct flights available)")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("CONCLUSION")
print("="*80)
print("Check the analysis above to determine:")
print("1. Whether v3.0rc0 returns complete round-trips with connections")
print("2. Whether the bug only affects max_stops=0 (direct flights)")
print("3. What the actual data structure looks like")
print()
