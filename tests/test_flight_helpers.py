import json
from types import SimpleNamespace

import pytest

from mcp_server_google_flights.server import (
    InvalidDateFormat,
    _google_flights_query_url,
    _make_google_flights_url,
    cap_results,
    combine_outbound_and_return_flights,
    flight_to_dict,
    generate_google_flights_url,
    normalize_seat_type,
    normalize_serpapi_flight,
    parse_iso_date,
    parse_price,
)


def _segment(origin_code, destination_code, duration=205):
    departure = SimpleNamespace(date=(2026, 11, 2), time=(8, 15))
    arrival = SimpleNamespace(date=(2026, 11, 2), time=(11, 40))
    return SimpleNamespace(
        from_airport=SimpleNamespace(code=origin_code, name=f"{origin_code} Airport"),
        to_airport=SimpleNamespace(
            code=destination_code, name=f"{destination_code} Airport"
        ),
        departure=departure,
        arrival=arrival,
        duration=duration,
        plane_type="737",
    )


def _flight():
    return SimpleNamespace(
        price=450,
        airlines=["United"],
        type="UA",
        flights=[_segment("SFO", "DEN"), _segment("DEN", "JFK")],
        carbon=None,
    )


def test_cap_results_keeps_first_n():
    assert cap_results(["a", "b", "c"], 2) == ["a", "b"]
    assert cap_results(["a", "b", "c"], 0) == ["a", "b", "c"]
    assert cap_results(["a", "b", "c"], -1) == ["a", "b", "c"]


def test_normalize_seat_type_premium_economy():
    assert normalize_seat_type("premium_economy") == "premium-economy"


def test_parse_price_literals():
    assert parse_price(None) == float("inf")
    assert parse_price("$1,200") == 1200
    assert parse_price(99) == 99
    assert parse_price(float("nan")) == float("inf")
    assert parse_price(float("inf")) == float("inf")


def test_parse_iso_date_accepts_calendar_day():
    parsed = parse_iso_date("2026-11-02")
    assert (parsed.year, parsed.month, parsed.day) == (2026, 11, 2)


def test_parse_iso_date_rejects_garbage():
    with pytest.raises(InvalidDateFormat):
        parse_iso_date("not-a-date")


def test_json_decode_error_is_not_invalid_date_format():
    with pytest.raises(json.JSONDecodeError) as caught:
        json.loads("{")
    assert not isinstance(caught.value, InvalidDateFormat)


def test_flight_to_dict_round_trip_marks_outbound_selection():
    payload = flight_to_dict(_flight(), trip="round-trip")

    assert payload["flight_type"] == "round-trip (outbound selection)"
    assert [segment["leg"] for segment in payload["segments"]] == [
        "outbound",
        "outbound",
    ]
    assert payload["price_note"] == (
        "Price is the round-trip total for this outbound option; "
        "return flight segments are not included in fast-flights results."
    )


def test_flight_to_dict_one_way_has_no_price_note():
    payload = flight_to_dict(_flight(), trip="one-way")

    assert payload["flight_type"] == "one-way"
    assert "price_note" not in payload


def test_flight_to_dict_compact_round_trip_keeps_price_note():
    payload = flight_to_dict(_flight(), compact=True, trip="round-trip")

    assert payload["price_note"] == (
        "Price is the round-trip total for this outbound option; "
        "return flight segments are not included in fast-flights results."
    )


def test_flight_to_dict_does_not_use_carrier_as_flight_type():
    payload = flight_to_dict(_flight())

    assert payload["flight_type"] is None


def test_flight_to_dict_duration_includes_layover():
    first = _segment("SFO", "DEN", duration=205)
    second = _segment("DEN", "JFK", duration=320)
    second.departure = SimpleNamespace(date=(2026, 11, 2), time=(14, 40))
    second.arrival = SimpleNamespace(date=(2026, 11, 2), time=(20, 0))
    flight = _flight()
    flight.flights = [first, second]

    payload = flight_to_dict(flight, trip="one-way")
    compact = flight_to_dict(flight, compact=True, trip="one-way")

    assert payload["total_duration"] == "11h 45m"
    assert compact["duration"] == "11h 45m"


def test_flight_to_dict_duration_ignores_timezone_skewed_wall_clock():
    segment = _segment("SFO", "JFK", duration=330)
    segment.departure = SimpleNamespace(date=(2026, 11, 2), time=(8, 0))
    segment.arrival = SimpleNamespace(date=(2026, 11, 2), time=(16, 30))
    flight = _flight()
    flight.flights = [segment]

    payload = flight_to_dict(flight, trip="one-way")

    assert payload["total_duration"] == "5h 30m"


def test_normalize_serpapi_flight_keeps_departure_token():
    payload = normalize_serpapi_flight(
        {
            "flights": [
                {
                    "departure_airport": {
                        "id": "SFO",
                        "name": "San Francisco",
                        "time": "2026-11-02 08:15",
                    },
                    "arrival_airport": {
                        "id": "JFK",
                        "name": "New York",
                        "time": "2026-11-02 16:45",
                    },
                    "duration": 330,
                    "airline": "United",
                    "flight_number": "UA 100",
                }
            ],
            "price": 450,
            "type": "Round trip",
            "total_duration": 330,
            "departure_token": "token-abc",
        }
    )

    assert payload["departure_token"] == "token-abc"


def test_combine_round_trip_uses_return_selection_price():
    outbound = {
        "price": 450,
        "airlines": "United",
        "flight_type": "Round trip",
        "departure_time": "2026-11-02 08:15",
        "arrival_time": "2026-11-02 16:45",
        "segments": [{"segment_number": 1}],
        "is_best_flight": True,
    }
    returning = {
        "price": 520,
        "airlines": "United",
        "flight_type": "Round trip",
        "departure_time": "2026-11-09 10:00",
        "arrival_time": "2026-11-09 13:00",
        "segments": [{"segment_number": 1}],
    }

    combined = combine_outbound_and_return_flights(outbound, returning)

    assert combined["price"] == 520
    assert combined["flight_type"] == "Round trip"
    assert combined["stops"] == 0


def test_combine_round_trip_counts_stops_per_leg():
    outbound = {
        "price": 450,
        "airlines": "United",
        "flight_type": "Round trip",
        "segments": [{"segment_number": 1}, {"segment_number": 2}],
    }
    returning = {
        "price": 520,
        "airlines": "United",
        "flight_type": "Round trip",
        "segments": [{"segment_number": 1}],
    }

    combined = combine_outbound_and_return_flights(outbound, returning)

    assert combined["stops"] == 1


def test_google_flights_query_url_rejects_unknown_seat():
    with pytest.raises(Exception):
        _google_flights_query_url("SFO", "JFK", "2026-11-02", seat="not-a-cabin")


def test_make_google_flights_url_falls_back_on_unknown_seat():
    url = _make_google_flights_url("SFO", "JFK", "2026-11-02", seat="not-a-cabin")

    assert url == "https://www.google.com/travel/flights?q=SFO+to+JFK"


def test_generate_google_flights_url_reports_encoding_failure():
    import asyncio

    payload = json.loads(
        asyncio.run(
            generate_google_flights_url(
                "SFO", "JFK", "2026-11-02", seat_type="not-a-cabin"
            )
        )
    )

    assert "error" in payload
    assert payload["error"]["type"] != "success"


def test_round_trip_url_includes_tfs_and_tfu():
    url = _make_google_flights_url(
        "SFO",
        "JFK",
        "2026-11-02",
        return_date="2026-11-09",
    )

    assert "tfs=" in url
    assert "tfu=EgQIABABIgA" in url
