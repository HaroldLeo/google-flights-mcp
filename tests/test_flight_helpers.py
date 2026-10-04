import json
from types import SimpleNamespace

import pytest

from mcp_server_google_flights.server import (
    InvalidDateFormat,
    _make_google_flights_url,
    flight_to_dict,
    normalize_seat_type,
    parse_iso_date,
    parse_price,
)


def _segment(origin_code, destination_code):
    departure = SimpleNamespace(date=(2026, 11, 2), time=(8, 15))
    arrival = SimpleNamespace(date=(2026, 11, 2), time=(11, 40))
    return SimpleNamespace(
        from_airport=SimpleNamespace(code=origin_code, name=f"{origin_code} Airport"),
        to_airport=SimpleNamespace(
            code=destination_code, name=f"{destination_code} Airport"
        ),
        departure=departure,
        arrival=arrival,
        duration=205,
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


def test_round_trip_url_includes_tfs_and_tfu():
    url = _make_google_flights_url(
        "SFO",
        "JFK",
        "2026-11-02",
        return_date="2026-11-09",
    )

    assert "tfs=" in url
    assert "tfu=EgQIABABIgA" in url
