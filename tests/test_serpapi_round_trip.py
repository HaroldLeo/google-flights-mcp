import asyncio
import json
from unittest.mock import patch

from mcp_server_google_flights import server


def test_round_trip_uses_serpapi_when_google_results_omit_return_segments():
    serpapi_result = json.dumps(
        {
            "data_source": "SerpApi (fallback)",
            "round_trip_note": "complete outbound and return legs",
            "flights": [{"segments": [{"from": "NAP"}, {"from": "CDG"}]}],
        }
    )
    with (
        patch.object(server, "SERPAPI_ENABLED", True),
        patch.object(server, "get_flights", return_value=[object()]),
        patch.object(
            server, "try_serpapi_fallback", return_value=serpapi_result
        ) as serpapi,
    ):
        result = asyncio.run(
            server.search_round_trip_flights(
                origin="NAP",
                destination="CDG",
                departure_date="2026-12-10",
                return_date="2026-12-13",
                max_stops=1,
                max_results=2,
            )
        )

    assert result == serpapi_result
    kwargs = serpapi.call_args.kwargs
    assert kwargs["origin"] == "NAP"
    assert kwargs["destination"] == "CDG"
    assert kwargs["return_date"] == "2026-12-13"
    assert kwargs["max_stops"] == server.to_serpapi_stops(1)
    assert kwargs["fallback_reason"] == "round-trip return-leg selection"
