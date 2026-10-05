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


def _booking_urls(output):
    if "booking_url" in output:
        return [output["booking_url"]]
    return [pair["booking_url"] for pair in output["all_round_trip_options"]]


@pytest.mark.parametrize("call, url_args", [
    (lambda: server.search_round_trips_in_date_range("SFO", "JFK", "2026-12-01", "2026-12-02",
                                                     min_stay_days=1, max_stay_days=1,
                                                     seat_type="premium_economy"),
     ("SFO", "JFK", "2026-12-01", "2026-12-02")),
    (lambda: server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["UA"],
                                              seat_type="premium_economy"),
     ("SFO", "JFK", "2026-12-01", None)),
])
def test_booking_url_keeps_selected_cabin(call, url_args):
    with patch.object(server, "get_flights", side_effect=_fake_get_flights([_flight("United")])):
        output = _run(call())
    expected = server._make_google_flights_url(*url_args, seat="premium_economy")
    assert expected != server._make_google_flights_url(*url_args)
    assert _booking_urls(output) == [expected]


@pytest.mark.parametrize("call, url_args", [
    (lambda: server.search_one_way_flights("SFO", "JFK", "2026-12-01", seat_type="Business"),
     ("SFO", "JFK", "2026-12-01", None)),
    (lambda: server.search_round_trip_flights("SFO", "JFK", "2026-12-01", "2026-12-08",
                                              seat_type="Business"),
     ("SFO", "JFK", "2026-12-01", "2026-12-08")),
])
def test_booking_url_accepts_mixed_case_cabin(call, url_args):
    with patch.object(server, "get_flights", side_effect=_fake_get_flights([_flight("United")])):
        output = _run(call())
    assert "tfs=" in output["booking_url"]
    assert output["booking_url"] == server._make_google_flights_url(*url_args, seat="business")


FLIGHTS = [
    _flight("Qantas"),
    _flight("Alaska"),
    _flight("Air Canada"),
    _flight("ANA"),
    _flight("United, Lufthansa"),
    _flight("Delta"),
    _flight("Air India"),
    _flight("Hawaiian"),
]


def _search_by_airline(airlines):
    with patch.object(server, "SERPAPI_ENABLED", False), \
         patch.object(server, "get_flights", side_effect=_fake_get_flights(FLIGHTS)):
        return _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", airlines))


@pytest.mark.parametrize("airlines, expected", [
    (["AS"], ["Alaska"]),
    (["NH"], ["ANA"]),
    (["AI"], ["Air India"]),
    (["UA", "DL"], ["United, Lufthansa", "Delta"]),
    (["STAR_ALLIANCE"], ["Air Canada", "ANA", "United, Lufthansa", "Air India"]),
    (["SKYTEAM"], ["Delta"]),
    (["oneworld"], ["Qantas", "Alaska", "Hawaiian"]),
])
def test_airline_filter_matches_expanded_names_only(airlines, expected):
    output = _search_by_airline(airlines)
    assert [f["airlines"] for f in output["flights"]] == expected
    assert "ignored_airlines" not in output


def test_raw_code_does_not_substring_match_other_airlines():
    targets, unrecognized = server.expand_airline_filter(["AS"])
    assert unrecognized == []
    assert not server.flight_matches_airlines("Qantas", targets)
    assert server.flight_matches_airlines("Alaska", targets)


def test_carrier_names_match_exactly_per_carrier():
    united, _ = server.expand_airline_filter(["UA"])
    assert not server.flight_matches_airlines("United Nigeria Airlines", united)
    assert server.flight_matches_airlines("United, Lufthansa", united)
    ana, _ = server.expand_airline_filter(["NH"])
    assert not server.flight_matches_airlines("Air Canada", ana)


def test_alliance_members_all_have_name_mappings():
    for codes in server.ALLIANCE_TO_CODES.values():
        assert set(codes) <= set(server.AIRLINE_CODE_TO_NAME)


def test_unmapped_codes_are_reported_alongside_mapped_ones():
    output = _search_by_airline(["UA", "XX"])
    assert [f["airlines"] for f in output["flights"]] == ["United, Lufthansa"]
    assert output["ignored_airlines"] == ["XX"]


def test_unmapped_codes_without_serpapi_return_error_without_searching():
    with patch.object(server, "SERPAPI_ENABLED", False), patch.object(server, "get_flights") as mock:
        output = _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["XX"]))
    assert output["error"]["type"] == "ValueError"
    mock.assert_not_called()


def test_unmapped_codes_use_serpapi_airline_filter_when_enabled():
    serpapi_output = json.dumps({"flights": [{"airline": "Example Air"}], "data_source": "SerpApi (fallback)"})
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "try_serpapi_fallback", return_value=serpapi_output) as serpapi, \
         patch.object(server, "get_flights") as fast_flights:
        output = _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01",
                                                       ["XX", "Star Alliance"],
                                                       seat_type="premium_economy"))
    assert output["data_source"] == "SerpApi (fallback)"
    assert serpapi.call_args.kwargs["airlines"] == ["XX", "STAR_ALLIANCE"]
    assert serpapi.call_args.kwargs["seat_type"] == "premium_economy"
    fast_flights.assert_not_called()
