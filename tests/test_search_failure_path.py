"""One-way and round-trip scraper failures (get_flights and GoogleSearch mocked, no network)."""

import asyncio
import json
from unittest.mock import patch

import pytest

from mcp_server_google_flights import server


def _run(coro):
    return asyncio.run(coro)


_PARTY = dict(
    adults=2,
    children=1,
    infants_in_seat=1,
    infants_on_lap=1,
    seat_type="business",
    return_cheapest_only=True,
    max_results=3,
)

_SERPAPI_NOTE = "Configure SERPAPI_API_KEY to enable automatic fallback to SerpApi."


def _search(tool):
    if tool == "one-way":
        return server.search_one_way_flights("SFO", "JFK", "2026-12-01", **_PARTY)
    return server.search_round_trip_flights(
        "SFO", "JFK", "2026-12-01", "2026-12-08", max_stops=1, **_PARTY
    )


def _booking_url(tool):
    return server._make_google_flights_url(
        "SFO",
        "JFK",
        "2026-12-01",
        return_date=None if tool == "one-way" else "2026-12-08",
        adults=2,
        children=1,
        infants_in_seat=1,
        infants_on_lap=1,
        seat="business",
    )


def _not_found_parameters(tool):
    if tool == "one-way":
        return {
            "origin": "SFO",
            "destination": "JFK",
            "date": "2026-12-01",
            "adults": 2,
            "children": 1,
            "infants_in_seat": 1,
            "infants_on_lap": 1,
            "seat_type": "business",
        }
    return {
        "origin": "SFO",
        "destination": "JFK",
        "departure_date": "2026-12-01",
        "return_date": "2026-12-08",
        "adults": 2,
        "children": 1,
        "infants_in_seat": 1,
        "infants_on_lap": 1,
        "seat_type": "business",
        "max_stops": 1,
    }


def _expected_without_fallback(tool, exc, serpapi_enabled):
    url = _booking_url(tool)
    note = _SERPAPI_NOTE if not serpapi_enabled else None
    if isinstance(exc, server.FlightsNotFound):
        if tool == "one-way":
            detail = (
                "One-way searches may not return results via scraping. "
                "Click the URL below to view flights in your browser."
            )
        else:
            detail = (
                "Round-trip searches with max 1 stops may not return results via scraping. "
                "Try max_stops=0 or 1 for better reliability, or click the URL below to view flights in your browser."
            )
        return {
            "message": "The scraper couldn't find flights, but you can view results directly on Google Flights.",
            "search_parameters": _not_found_parameters(tool),
            "note": detail,
            "serpapi_note": note,
            "google_flights_url": url,
        }
    return {
        "error": {"message": str(exc), "type": type(exc).__name__},
        "suggestion": "If you encounter issues, try searching with different parameters or check the Google Flights website directly.",
        "serpapi_note": note,
        "google_flights_url": url,
    }


class _EmptySearch:
    def __init__(self, params):
        pass

    def get_dict(self):
        return {}


class _RecordingSearch:
    captured = []

    def __init__(self, params):
        self.captured.append(params)

    def get_dict(self):
        return {
            "best_flights": [
                {
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
                            "duration": 330,
                            "airline": "United",
                            "flight_number": "UA 100",
                        }
                    ],
                    "price": price,
                    "type": "One way",
                    "total_duration": 330,
                }
                for price in (480, 210)
            ]
        }


def _spy_fallback(seen):
    real = server.try_serpapi_fallback

    def spy(**kwargs):
        seen.append(kwargs)
        return real(**kwargs)

    return spy


@pytest.mark.parametrize("tool", ["one-way", "round-trip"])
@pytest.mark.parametrize(
    "exc",
    [server.FlightsNotFound("missing"), RuntimeError("scraper down")],
)
@pytest.mark.parametrize("serpapi_enabled", [False, True], ids=["fallback-none", "fallback-empty"])
def test_scraper_failure_without_fallback_results_returns_url_payload(tool, exc, serpapi_enabled):
    seen = []
    with patch.object(server, "SERPAPI_ENABLED", serpapi_enabled), \
         patch.object(server, "GoogleSearch", _EmptySearch, create=True), \
         patch.object(server, "try_serpapi_fallback", _spy_fallback(seen)), \
         patch.object(server, "get_flights", side_effect=exc):
        raw = _run(_search(tool))

    assert len(seen) == 1
    assert seen[0]["departure_date"] == "2026-12-01"
    assert seen[0]["adults"] == 2
    assert seen[0]["children"] == 1
    assert seen[0]["infants_in_seat"] == 1
    assert seen[0]["infants_on_lap"] == 1
    assert seen[0]["seat_type"] == "business"
    assert seen[0]["return_cheapest_only"] is True
    assert seen[0]["max_results"] == 3
    if tool == "one-way":
        assert seen[0]["return_date"] is None
        assert "max_stops" not in seen[0]
    else:
        assert seen[0]["return_date"] == "2026-12-08"
        assert seen[0]["max_stops"] == server.to_serpapi_stops(1)

    expected = _expected_without_fallback(tool, exc, serpapi_enabled)
    assert raw == json.dumps(expected)


@pytest.mark.parametrize("tool", ["one-way", "round-trip"])
@pytest.mark.parametrize(
    "exc",
    [server.FlightsNotFound("missing"), RuntimeError("scraper down")],
)
def test_scraper_failure_returns_serpapi_fallback_payload(tool, exc):
    seen = []
    _RecordingSearch.captured = []
    with patch.object(server, "SERPAPI_ENABLED", True), \
         patch.object(server, "GoogleSearch", _RecordingSearch, create=True), \
         patch.object(server, "try_serpapi_fallback", _spy_fallback(seen)), \
         patch.object(server, "get_flights", side_effect=exc):
        raw = _run(_search(tool))
        assert len(seen) == 1
        replay = server.try_serpapi_fallback(**seen[0])

    assert raw == replay
    output = json.loads(raw)
    assert output["data_source"] == "SerpApi (fallback)"
    assert output["note"] == "Results from SerpApi due to fast-flights error"
    assert output["flights"][0]["price"] == 210
    assert len(output["flights"]) == 1
    assert output["booking_url"] == _booking_url(tool)
    assert "google_flights_url" not in output
    assert "error" not in output
    assert "suggestion" not in output
    if tool == "one-way":
        assert output["search_parameters"]["date"] == "2026-12-01"
        assert "departure_date" not in output["search_parameters"]
        assert "return_date" not in output["search_parameters"]
        assert "round_trip_note" not in output
        assert "stops" not in _RecordingSearch.captured[0]
    else:
        assert output["search_parameters"]["departure_date"] == "2026-12-01"
        assert output["search_parameters"]["return_date"] == "2026-12-08"
        assert "date" not in output["search_parameters"]
        assert "max_stops" not in output["search_parameters"]
        assert output["round_trip_note"].startswith("⚠️")
        assert _RecordingSearch.captured[0]["stops"] == server.to_serpapi_stops(1)
        assert _RecordingSearch.captured[0]["return_date"] == "2026-12-08"
    assert output["search_parameters"]["adults"] == 2
    assert output["search_parameters"]["infants_on_lap"] == 1
    assert output["search_parameters"]["return_cheapest_only"] is True
