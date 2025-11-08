#!/usr/bin/env python
"""Test the new flight parsing with the updated data structure."""

import sys
import json
from dataclasses import dataclass
from typing import Union, Literal, Annotated

# Import the functions we're testing
sys.path.insert(0, 'src')
from mcp_server_google_flights.server import flight_to_dict, format_datetime, format_duration

# Recreate the data classes to match fast-flights 3.0rc0
@dataclass
class Airport:
    name: str
    code: str

@dataclass
class SimpleDatetime:
    date: tuple[int, int, int]  # (year, month, day)
    time: tuple[int, int]        # (hour, minute)

@dataclass
class CarbonEmission:
    typical_on_route: Annotated[int, "(grams)"]
    emission: Annotated[int, "(grams)"]

@dataclass
class SingleFlight:
    from_airport: Airport
    to_airport: Airport
    departure: SimpleDatetime
    arrival: SimpleDatetime
    duration: Annotated[int, "(minutes)"]
    plane_type: str

@dataclass
class Flights:
    type: Union[str, Literal["multi"]]
    price: int
    airlines: list[str]
    flights: list[SingleFlight]
    carbon: CarbonEmission

def test_direct_flight():
    """Test parsing a direct flight."""
    print("=== Test 1: Direct Flight (SFO -> JFK) ===")

    flight = Flights(
        type="one-way",
        price=299,
        airlines=["United"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="San Francisco International", code="SFO"),
                to_airport=Airport(name="John F. Kennedy International", code="JFK"),
                departure=SimpleDatetime(date=(2025, 12, 15), time=(8, 30)),
                arrival=SimpleDatetime(date=(2025, 12, 15), time=(17, 0)),
                duration=330,  # 5h 30m
                plane_type="Boeing 737"
            )
        ],
        carbon=CarbonEmission(typical_on_route=250000, emission=245000)
    )

    result = flight_to_dict(flight, compact=False)
    print(json.dumps(result, indent=2))
    print()

    # Verify key fields
    assert result['price'] == 299, f"Expected price 299, got {result['price']}"
    assert result['airlines'] == "United", f"Expected 'United', got {result['airlines']}"
    assert result['stops'] == 0, f"Expected 0 stops, got {result['stops']}"
    assert result['departure_time'] == "2025-12-15 08:30", f"Expected '2025-12-15 08:30', got {result['departure_time']}"
    assert result['arrival_time'] == "2025-12-15 17:00", f"Expected '2025-12-15 17:00', got {result['arrival_time']}"
    assert result['total_duration'] == "5h 30m", f"Expected '5h 30m', got {result['total_duration']}"
    assert len(result['segments']) == 1, f"Expected 1 segment, got {len(result['segments'])}"

    print("✓ Direct flight test passed!\n")

def test_one_stop_flight():
    """Test parsing a flight with one stop."""
    print("=== Test 2: One Stop Flight (SFO -> ORD -> JFK) ===")

    flight = Flights(
        type="one-way",
        price=189,
        airlines=["American Airlines"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="San Francisco International", code="SFO"),
                to_airport=Airport(name="O'Hare International", code="ORD"),
                departure=SimpleDatetime(date=(2025, 12, 15), time=(7, 0)),
                arrival=SimpleDatetime(date=(2025, 12, 15), time=(13, 15)),
                duration=255,  # 4h 15m
                plane_type="Boeing 777"
            ),
            SingleFlight(
                from_airport=Airport(name="O'Hare International", code="ORD"),
                to_airport=Airport(name="John F. Kennedy International", code="JFK"),
                departure=SimpleDatetime(date=(2025, 12, 15), time=(15, 30)),
                arrival=SimpleDatetime(date=(2025, 12, 15), time=(19, 0)),
                duration=150,  # 2h 30m
                plane_type="Airbus A320"
            )
        ],
        carbon=CarbonEmission(typical_on_route=280000, emission=275000)
    )

    result = flight_to_dict(flight, compact=False)
    print(json.dumps(result, indent=2))
    print()

    # Verify key fields
    assert result['price'] == 189, f"Expected price 189, got {result['price']}"
    assert result['airlines'] == "American Airlines", f"Expected 'American Airlines', got {result['airlines']}"
    assert result['stops'] == 1, f"Expected 1 stop, got {result['stops']}"
    assert result['departure_time'] == "2025-12-15 07:00", f"Expected '2025-12-15 07:00', got {result['departure_time']}"
    assert result['arrival_time'] == "2025-12-15 19:00", f"Expected '2025-12-15 19:00', got {result['arrival_time']}"
    assert result['total_duration'] == "6h 45m", f"Expected '6h 45m', got {result['total_duration']}"
    assert len(result['segments']) == 2, f"Expected 2 segments, got {len(result['segments'])}"

    # Verify stopover details
    assert result['segments'][0]['to']['airport_code'] == "ORD", "Expected stopover at ORD"
    assert result['segments'][1]['from']['airport_code'] == "ORD", "Expected connection from ORD"

    print("✓ One stop flight test passed!\n")

def test_compact_mode():
    """Test compact mode output."""
    print("=== Test 3: Compact Mode ===")

    flight = Flights(
        type="one-way",
        price=199,
        airlines=["Delta"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="Los Angeles International", code="LAX"),
                to_airport=Airport(name="Seattle-Tacoma International", code="SEA"),
                departure=SimpleDatetime(date=(2025, 12, 20), time=(10, 0)),
                arrival=SimpleDatetime(date=(2025, 12, 20), time=(12, 45)),
                duration=165,  # 2h 45m
                plane_type="Boeing 737"
            )
        ],
        carbon=CarbonEmission(typical_on_route=150000, emission=145000)
    )

    result = flight_to_dict(flight, compact=True)
    print(json.dumps(result, indent=2))
    print()

    # Verify compact mode has fewer fields
    expected_keys = {'price', 'airlines', 'departure_time', 'arrival_time', 'duration', 'stops'}
    assert set(result.keys()) == expected_keys, f"Expected keys {expected_keys}, got {set(result.keys())}"
    assert 'segments' not in result, "Compact mode should not include segments"
    assert 'carbon_emissions' not in result, "Compact mode should not include carbon_emissions"

    print("✓ Compact mode test passed!\n")

if __name__ == "__main__":
    print("Running flight parsing tests...\n")
    try:
        test_direct_flight()
        test_one_stop_flight()
        test_compact_mode()
        print("=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
