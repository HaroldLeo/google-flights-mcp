import asyncio
import datetime
import json

import pytest

from mcp_server_google_flights.server import get_travel_dates


def _run(**kwargs):
    return json.loads(asyncio.run(get_travel_dates(**kwargs)))


def test_rejects_negative_days_from_now():
    payload = _run(days_from_now=-1, trip_length=7)

    assert payload["error"]["type"] == "ValueError"
    assert "days_from_now" in payload["error"]["message"]


@pytest.mark.parametrize("trip_length", [0, -3])
def test_rejects_non_positive_trip_length(trip_length):
    payload = _run(days_from_now=10, trip_length=trip_length)

    assert payload["error"]["type"] == "ValueError"
    assert "trip_length" in payload["error"]["message"]


def test_happy_path_returns_iso_dates():
    payload = _run(days_from_now=0, trip_length=1)

    today = datetime.date.fromisoformat(payload["today"])
    departure = datetime.date.fromisoformat(payload["departure_date"])
    return_date = datetime.date.fromisoformat(payload["return_date"])
    assert departure == today
    assert return_date == departure + datetime.timedelta(days=1)
    assert payload["trip_length_days"] == 1
    assert payload["days_until_departure"] == 0
