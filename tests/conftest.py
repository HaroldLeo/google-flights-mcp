import pytest

from mcp_server_google_flights import server


@pytest.fixture(autouse=True)
def disable_live_serpapi_by_default(monkeypatch):
    """Keep unit tests offline even when a developer key is configured locally."""
    monkeypatch.setattr(server, "SERPAPI_ENABLED", False)
