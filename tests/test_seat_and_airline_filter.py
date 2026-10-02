"""Seat-type normalization and airline filtering, with get_flights mocked (no network)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fast_flights.flights_impl import TFSData

from mcp_server_google_flights import server


def _flight(name, price="$100"):
    return SimpleNamespace(name=name, price=price, is_best=False, departure="10:00 AM",
                           arrival="6:00 PM", duration="5 hr", stops=0)


def _fake_get_flights(flights):
    """Build the real TFS filter so an unsupported seat raises like fast-flights does."""
    def fake(*, flight_data, trip, passengers, seat, fetch_mode="common", max_stops=None):
        TFSData.from_interface(flight_data=flight_data, trip=trip, passengers=passengers,
                               seat=seat, max_stops=max_stops)
        return SimpleNamespace(flights=list(flights), current_price="typical")
    return fake


def _run(coro):
    return json.loads(asyncio.run(coro))


def test_normalize_seat_type_accepts_underscore_form():
    assert server.normalize_seat_type("premium_economy") == "premium-economy"
    assert server.normalize_seat_type("Business") == "business"


@pytest.mark.parametrize("call", [
    lambda: server.search_one_way_flights("SFO", "JFK", "2026-12-01", seat_type="premium_economy"),
    lambda: server.search_round_trip_flights("SFO", "JFK", "2026-12-01", "2026-12-08",
                                             seat_type="premium_economy"),
    lambda: server.search_round_trips_in_date_range("SFO", "JFK", "2026-12-01", "2026-12-03",
                                                    min_stay_days=1, max_stay_days=1,
                                                    seat_type="premium_economy"),
    lambda: server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["UA"],
                                             seat_type="premium_economy"),
])
def test_premium_economy_reaches_get_flights_normalized(call):
    with patch.object(server, "get_flights", side_effect=_fake_get_flights([_flight("United")])) as mock:
        output = _run(call())
    assert "error" not in output
    assert mock.call_count >= 1
    assert all(c.kwargs["seat"] == "premium-economy" for c in mock.call_args_list)


FLIGHTS = [
    _flight("Qantas"),
    _flight("Alaska"),
    _flight("Air Canada"),
    _flight("ANA"),
    _flight("United, Lufthansa"),
    _flight("Delta"),
]


def _airline_names(airlines):
    with patch.object(server, "get_flights", side_effect=_fake_get_flights(FLIGHTS)):
        output = _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", airlines))
    return [f["airlines"] for f in output.get("flights", [])], output


@pytest.mark.parametrize("airlines, expected", [
    (["AS"], ["Alaska"]),
    (["NH"], ["ANA"]),
    (["UA", "DL"], ["United, Lufthansa", "Delta"]),
    (["STAR_ALLIANCE"], ["Air Canada", "ANA", "United, Lufthansa"]),
    (["SKYTEAM"], ["Delta"]),
    (["oneworld"], ["Qantas", "Alaska"]),
])
def test_airline_filter_matches_expanded_names_only(airlines, expected):
    names, _ = _airline_names(airlines)
    assert names == expected


def test_raw_code_does_not_substring_match_other_airlines():
    targets, unrecognized = server.expand_airline_filter(["AS"])
    assert unrecognized == []
    assert not server.flight_matches_airlines("Qantas", targets)
    assert server.flight_matches_airlines("Alaska", targets)


def test_unrecognized_airlines_return_error_without_searching():
    with patch.object(server, "get_flights") as mock:
        output = _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["XX"]))
    assert output["error"]["type"] == "ValueError"
    mock.assert_not_called()
