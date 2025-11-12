#!/usr/bin/env python
"""Test what fast-flights returns for direct round-trip searches."""

import sys
import json

# Test with mock data to see structure
test_query = {
    "origin": "SJC",
    "destination": "PHX",
    "departure_date": "2025-11-27",
    "return_date": "2025-12-01",
    "is_round_trip": True,
    "max_stops": 0
}

print("=" * 80)
print("DIRECT ROUND-TRIP FLIGHT ISSUE INVESTIGATION")
print("=" * 80)
print()
print("Query:", json.dumps(test_query, indent=2))
print()
print("Expected behavior:")
print("  For a round-trip search, each result should contain:")
print("  - Outbound segment(s): SJC → PHX on 2025-11-27")
print("  - Return segment(s): PHX → SJC on 2025-12-01")
print("  - Total price for BOTH legs")
print()
print("Actual behavior (from logs):")
print("  Each result only contains:")
print("  - 1 segment: SJC → PHX on 2025-11-27 (outbound only)")
print("  - NO return segment")
print()
print("=" * 80)
print("HYPOTHESIS")
print("=" * 80)
print()
print("fast-flights library with max_stops=0 (direct only) may:")
print()
print("1. Have a bug where it only returns outbound leg for round-trips")
print("2. Return legs separately instead of combined packages")
print("3. Require different query structure for direct round-trips")
print()
print("The query IS correctly structured:")
print("  flights = [")
print("    FlightQuery(date='2025-11-27', from_airport='SJC', to_airport='PHX'),")
print("    FlightQuery(date='2025-12-01', from_airport='PHX', to_airport='SJC'),")
print("  ]")
print("  trip='round-trip', max_stops=0")
print()
print("=" * 80)
print("SOLUTION OPTIONS")
print("=" * 80)
print()
print("Option 1: Check if fast-flights has this limitation")
print("  - Test with max_stops=1 or 2 to see if return flights appear")
print("  - If so, this is a library limitation with direct-only round-trips")
print()
print("Option 2: Workaround - search two one-way direct flights")
print("  - Search outbound: SJC→PHX direct on 2025-11-27")
print("  - Search return: PHX→SJC direct on 2025-12-01")
print("  - Combine results manually")
print()
print("Option 3: Use search_round_trip_flights with max_stops=0")
print("  - Instead of search_direct_flights")
print("  - May return complete round-trip packages")
print()
print("=" * 80)
print("RECOMMENDED FIX")
print("=" * 80)
print()
print("For search_direct_flights with is_round_trip=True:")
print("1. Make TWO separate searches (one for each leg)")
print("2. Combine the results into complete round-trip packages")
print("3. Add clear documentation about this workaround")
print()
print("This ensures users get both outbound AND return direct flight options.")
print()
