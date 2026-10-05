"""Seat-type normalization and airline filtering, with get_flights mocked (no network)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mcp_server_google_flights import server


def _flight(name, price=100):
    carriers = [part.strip() for part in name.split(",")]
    return SimpleNamespace(
        price=price,
        airlines=carriers,
        type=None,
        flights=[],
        carbon=None,
    )


def _fake_get_flights(flights):
    """Return v3-shaped flights. Seat is already validated by create_query."""

    def fake(query, /, *, proxy=None, integration=None):
        return list(flights)

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
    assert all(c.args[0].get_seat_type() == "premium-economy" for c in mock.call_args_list)


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
    _flight("ITA Airways"),
]


def _search_by_airline(airlines, **kwargs):
    with patch.object(server, "SERPAPI_ENABLED", False), \
         patch.object(server, "get_flights", side_effect=_fake_get_flights(FLIGHTS)):
        return _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", airlines, **kwargs))


@pytest.mark.parametrize("airlines, expected", [
    (["AS"], ["Alaska"]),
    (["NH"], ["ANA"]),
    (["AI"], ["Air India"]),
    (["UA", "DL"], ["United, Lufthansa", "Delta"]),
    (["STAR_ALLIANCE"], ["Air Canada", "ANA", "United, Lufthansa", "Air India", "ITA Airways"]),
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
    assert serpapi.call_args.kwargs["max_stops"] == 3
    fast_flights.assert_not_called()


@pytest.mark.parametrize("max_stops, serpapi_stops", [(0, 1), (1, 2), (2, 3), (5, None)])
def test_serpapi_airline_filter_translates_max_stops(max_stops, serpapi_stops):
    serpapi_output = json.dumps({"flights": [], "data_source": "SerpApi (fallback)"})
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "try_serpapi_fallback", return_value=serpapi_output) as serpapi:
        _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["XX"], max_stops=max_stops))
    assert serpapi.call_args.kwargs["max_stops"] == serpapi_stops


def test_serpapi_airline_filter_keeps_flights_key_for_cheapest_only():
    serpapi_output = json.dumps({"cheapest_flight": [{"price": 120}], "data_source": "SerpApi (fallback)"})
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "try_serpapi_fallback", return_value=serpapi_output):
        output = _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["XX"],
                                                       return_cheapest_only=True))
    assert output["flights"] == [{"price": 120}]
    assert "cheapest_flight" not in output


def test_serpapi_airline_filter_returns_airline_tool_schema():
    serpapi_output = json.dumps({
        "search_parameters": {"origin": "SFO", "destination": "JFK", "departure_date": "2026-12-01"},
        "flights": [{"price": 120}],
        "data_source": "SerpApi (fallback)",
        "note": "Results from SerpApi due to fast-flights error",
        "result_metadata": {"total_found": 1, "returned": 1, "truncated": False},
    })
    args = dict(seat_type="business", max_stops=1)
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "try_serpapi_fallback", return_value=serpapi_output):
        serpapi_path = _run(server.search_flights_by_airline("SFO", "JFK", "2026-12-01", ["XX", "Delta"], **args))
    scraper_path = _search_by_airline(["UA"], **args)

    assert serpapi_path["search_parameters"] == {**scraper_path["search_parameters"], "airlines": ["XX", "Delta"]}
    assert serpapi_path["booking_url"] == scraper_path["booking_url"]
    assert serpapi_path["flights"] == [{"price": 120}]
    assert serpapi_path["result_metadata"]["total_found"] == 1
    assert serpapi_path["ignored_airlines"] == ["Delta"]
    assert "note" not in serpapi_path


def _serp_offer(price, duration=330):
    return {
        "flights": [
            {
                "departure_airport": {
                    "id": "SFO",
                    "name": "San Francisco",
                    "time": "2026-12-01 08:15",
                },
                "arrival_airport": {
                    "id": "JFK",
                    "name": "New York",
                    "time": "2026-12-01 16:45",
                },
                "duration": duration,
                "airline": "United",
                "flight_number": "UA 100",
            }
        ],
        "price": price,
        "type": "Round trip",
        "total_duration": duration,
    }


def _recording_search(captured, payload):
    class RecordingSearch:
        def __init__(self, params):
            captured.append(params)

        def get_dict(self):
            return payload

    return RecordingSearch


@pytest.mark.parametrize("exc", [server.FlightsNotFound("missing"), RuntimeError("scraper down")])
@pytest.mark.parametrize("max_stops, serpapi_stops", [(0, 1), (1, 2), (2, 3)])
def test_round_trip_fallback_translates_stops_and_keeps_scraper_shape(exc, max_stops, serpapi_stops):
    captured = []
    payload = {"best_flights": [_serp_offer(480), _serp_offer(210, duration=90)]}
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "GoogleSearch", _recording_search(captured, payload), create=True), \
         patch.object(server, "get_flights", side_effect=exc):
        output = _run(server.search_round_trip_flights(
            "SFO", "JFK", "2026-12-01", "2026-12-08",
            max_stops=max_stops,
            return_cheapest_only=True,
        ))

    assert captured[0]["stops"] == serpapi_stops
    assert captured[0]["type"] == 1
    assert captured[0]["outbound_date"] == "2026-12-01"
    assert captured[0]["return_date"] == "2026-12-08"
    assert len(output["flights"]) == 1
    assert output["flights"][0]["price"] == 210
    assert output["flights"][0]["segments"][0]["duration"] == "1h 30m"
    assert "cheapest_flight" not in output
    assert output["booking_url"] == server._make_google_flights_url(
        "SFO", "JFK", "2026-12-01", return_date="2026-12-08", seat="economy"
    )
    assert output["search_parameters"]["departure_date"] == "2026-12-01"
    assert output["search_parameters"]["return_date"] == "2026-12-08"
    assert "date" not in output["search_parameters"]
    assert output["data_source"] == "SerpApi (fallback)"


def test_one_way_fallback_omits_stops_and_uses_date_key():
    captured = []
    payload = {"best_flights": [_serp_offer(150)]}
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "GoogleSearch", _recording_search(captured, payload), create=True), \
         patch.object(server, "get_flights", side_effect=server.FlightsNotFound("missing")):
        output = _run(server.search_one_way_flights(
            "SFO", "JFK", "2026-12-01", return_cheapest_only=True
        ))

    assert "stops" not in captured[0]
    assert captured[0]["type"] == 2
    assert output["search_parameters"]["date"] == "2026-12-01"
    assert "departure_date" not in output["search_parameters"]
    assert "return_date" not in output["search_parameters"]
    assert output["flights"][0]["price"] == 150
    assert "cheapest_flight" not in output
    assert output["booking_url"] == server._make_google_flights_url(
        "SFO", "JFK", "2026-12-01", seat="economy"
    )


@pytest.mark.parametrize("seat_type", ["premium-economy", "premium_economy"])
def test_round_trip_fallback_maps_premium_economy_travel_class(seat_type):
    captured = []
    payload = {"best_flights": [_serp_offer(300)]}
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "GoogleSearch", _recording_search(captured, payload), create=True), \
         patch.object(server, "get_flights", side_effect=server.FlightsNotFound("missing")):
        output = _run(server.search_round_trip_flights(
            "SFO", "JFK", "2026-12-01", "2026-12-08",
            seat_type=seat_type,
            max_stops=0,
            return_cheapest_only=True,
        ))

    assert captured[0]["travel_class"] == 2
    assert captured[0]["stops"] == 1
    assert "flights" in output
    assert "booking_url" in output


def test_round_trip_does_not_route_unmapped_codes_to_serpapi():
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "try_serpapi_fallback") as serpapi, \
         patch.object(server, "get_flights", side_effect=_fake_get_flights(FLIGHTS)) as fast_flights:
        only_unmapped = _run(server.search_flights_by_airline(
            "SFO", "JFK", "2026-12-01", ["XX"], is_round_trip=True, return_date="2026-12-08"))
        mixed = _run(server.search_flights_by_airline(
            "SFO", "JFK", "2026-12-01", ["UA", "XX"], is_round_trip=True, return_date="2026-12-08"))
    serpapi.assert_not_called()
    assert only_unmapped["error"]["type"] == "ValueError"
    assert fast_flights.call_count == 1
    assert [f["airlines"] for f in mixed["flights"]] == ["United, Lufthansa"]
    assert mixed["ignored_airlines"] == ["XX"]
