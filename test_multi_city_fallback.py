#!/usr/bin/env python
"""Test script to verify multi-city fallback mechanism."""

import asyncio
import json
import sys

# Add the src directory to the path
sys.path.insert(0, 'src')

from mcp_server_google_flights.server import get_multi_city_flights

async def test_multi_city_fallback():
    """Test the multi-city fallback to individual segments."""
    print("Testing multi-city fallback mechanism...\n")

    # Create a multi-city search that will likely trigger the fallback
    segments = [
        {"date": "2025-11-26", "from": "SFO", "to": "LIH"},
        {"date": "2025-11-28", "from": "LIH", "to": "HNL"},
        {"date": "2025-12-01", "from": "HNL", "to": "SFO"}
    ]

    flight_segments_json = json.dumps(segments)

    print(f"Testing multi-city route:")
    for i, seg in enumerate(segments):
        print(f"  Segment {i+1}: {seg['from']} → {seg['to']} on {seg['date']}")
    print()

    try:
        result = await get_multi_city_flights(
            flight_segments=flight_segments_json,
            adults=1,
            seat_type="economy",
            return_cheapest_only=False,
            max_results=3,
            compact_mode=False
        )

        print("=== RESULT ===")
        result_data = json.loads(result)
        print(json.dumps(result_data, indent=2))
        print()

        # Check if fallback was triggered
        if "segments" in result_data:
            print("✓ Fallback mechanism triggered successfully!")
            print(f"✓ Retrieved {len(result_data['segments'])} segment(s)")
            for segment in result_data['segments']:
                if 'flights' in segment:
                    print(f"  - {segment['route']}: {len(segment['flights'])} flight(s) found")
                else:
                    print(f"  - {segment['route']}: {segment.get('message', 'Error')}")
        elif "multi_city_options" in result_data:
            print("✓ Direct multi-city parsing worked!")
        else:
            print("⚠ Fallback to URL only")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multi_city_fallback())
