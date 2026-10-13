"""Paging contract for search_round_trips_in_date_range (get_flights mocked, no network)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mcp_server_google_flights import server


def _flight():
    return SimpleNamespace(price=100, airlines=["United"], type=None, flights=[], carbon=None)


def _run(coro):
    return json.loads(asyncio.run(coro))


def _search(**kwargs):
    # Three calendar days and no stay filter => 6 date pairs, under the 30-request
    # cap even when a non-positive limit returns every remaining pair.
    params = {
        "origin": "SFO",
        "destination": "JFK",
        "start_date_str": "2026-12-01",
        "end_date_str": "2026-12-03",
    }
    params.update(kwargs)
    with patch.object(server, "get_flights", return_value=[_flight()]) as mock:
        output = _run(server.search_round_trips_in_date_range(**params))
    return output, mock


@pytest.mark.parametrize("limit", [0, -1])
def test_nonpositive_limit_returns_all_remaining_and_has_more_false(limit):
    output, mock = _search(limit=limit)
    assert "error" not in output
    page = output["pagination"]
    assert page["total_date_pairs"] == 6
    assert page["returned"] == 6
    assert page["has_more"] is False
    assert mock.call_count == 6


def test_nonpositive_limit_from_offset_returns_only_the_rest():
    output, mock = _search(offset=4, limit=0)
    page = output["pagination"]
    assert page["returned"] == 2
    assert page["has_more"] is False
    assert mock.call_count == 2


def test_normal_page_has_more_true_when_pairs_remain():
    output, mock = _search(offset=0, limit=2)
    page = output["pagination"]
    assert page["total_date_pairs"] == 6
    assert page["returned"] == 2
    assert page["has_more"] is True
    assert mock.call_count == 2


def test_normal_page_has_more_false_when_offset_plus_limit_reaches_total():
    output, mock = _search(offset=4, limit=2)
    page = output["pagination"]
    assert page["total_date_pairs"] == 6
    assert page["returned"] == 2
    assert page["offset"] + page["limit"] == page["total_date_pairs"]
    assert page["has_more"] is False
    assert mock.call_count == 2


def test_default_limit_pages_a_range_larger_than_the_request_cap():
    # 14 calendar days, no stay filter => 105 pairs. Default limit=20 stays
    # under the per-call cap of 30, so the range is paged rather than rejected.
    with patch.object(server, "get_flights", return_value=[_flight()]) as mock:
        output = _run(server.search_round_trips_in_date_range(
            "SFO", "JFK", "2026-12-01", "2026-12-14",
        ))
    assert "error" not in output
    page = output["pagination"]
    assert page["limit"] == 20
    assert page["total_date_pairs"] == 105
    assert page["returned"] == 20
    assert page["has_more"] is True
    assert mock.call_count == 20
