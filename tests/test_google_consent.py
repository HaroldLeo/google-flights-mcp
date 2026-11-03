from unittest.mock import Mock, patch

import pytest

from mcp_server_google_flights import server


def test_consent_interstitial_returns_actionable_error():
    response = Mock(
        url="https://consent.google.com/m?continue=https://www.google.com/travel/flights",
        status_code=200,
        text="consent page",
    )
    with patch.object(server, "_PrimpClient") as client_factory:
        client_factory.return_value.get.return_value = response
        with pytest.raises(RuntimeError, match="GOOGLE_FLIGHTS_SOCS_COOKIE"):
            server._fetch_flights_html_with_consent_handling("NAP to LHR")


def test_configured_consent_cookie_is_sent_and_results_html_returned():
    response = Mock(
        url="https://www.google.com/travel/flights/search",
        status_code=200,
        text="results page",
    )
    with (
        patch.object(server, "_GOOGLE_SOCS_COOKIE", "owner-selected-value"),
        patch.object(server, "_PrimpClient") as client_factory,
    ):
        client_factory.return_value.get.return_value = response
        html = server._fetch_flights_html_with_consent_handling("NAP to LHR")

    assert html == "results page"
    assert client_factory.call_args.kwargs["cookies"] == {
        "SOCS": "owner-selected-value"
    }


def test_http_errors_are_reported():
    response = Mock(
        url="https://www.google.com/travel/flights/search",
        status_code=503,
        text="unavailable",
    )
    with patch.object(server, "_PrimpClient") as client_factory:
        client_factory.return_value.get.return_value = response
        with pytest.raises(RuntimeError, match="HTTP 503"):
            server._fetch_flights_html_with_consent_handling("NAP to LHR")
