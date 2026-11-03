from unittest.mock import patch

import pytest

from mcp_server_google_flights import server


def test_serpapi_key_loads_from_owner_only_config_file(tmp_path):
    key_path = tmp_path / ".config/google-flights-mcp/serpapi_api_key"
    key_path.parent.mkdir(parents=True)
    key_path.write_text("local-test-key\n", encoding="utf-8")
    key_path.chmod(0o600)

    with (
        patch.object(server.Path, "home", return_value=tmp_path),
        patch.dict("os.environ", {"SERPAPI_API_KEY": ""}),
    ):
        assert server._load_serpapi_api_key() == "local-test-key"


def test_serpapi_key_file_rejects_group_or_world_access(tmp_path):
    key_path = tmp_path / ".config/google-flights-mcp/serpapi_api_key"
    key_path.parent.mkdir(parents=True)
    key_path.write_text("local-test-key", encoding="utf-8")
    key_path.chmod(0o644)

    with (
        patch.object(server.Path, "home", return_value=tmp_path),
        patch.dict("os.environ", {"SERPAPI_API_KEY": ""}),
        pytest.raises(RuntimeError, match="mode 0600"),
    ):
        server._load_serpapi_api_key()


def test_serpapi_environment_key_takes_precedence_over_private_file(tmp_path):
    key_path = tmp_path / ".config/google-flights-mcp/serpapi_api_key"
    key_path.parent.mkdir(parents=True)
    key_path.write_text("file-key", encoding="utf-8")
    key_path.chmod(0o600)

    with (
        patch.object(server.Path, "home", return_value=tmp_path),
        patch.dict("os.environ", {"SERPAPI_API_KEY": " environment-key "}),
    ):
        assert server._load_serpapi_api_key() == "environment-key"


def test_serpapi_key_is_redacted_from_error_text():
    with patch.object(server, "SERPAPI_API_KEY", "secret-test-key"):
        assert server._redact_serpapi_key("request secret-test-key failed") == (
            "request [REDACTED] failed"
        )
