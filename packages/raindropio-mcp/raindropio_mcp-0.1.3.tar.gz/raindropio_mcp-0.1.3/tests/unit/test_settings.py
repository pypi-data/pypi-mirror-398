from __future__ import annotations

import pytest

from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.utils.exceptions import ConfigurationError


def test_missing_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAINDROP_TOKEN", raising=False)
    with pytest.raises(ConfigurationError):
        RaindropSettings()


def test_auth_headers_include_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAINDROP_TOKEN", "test_token_1234567890abcdefghijklmnopqr")
    settings = RaindropSettings()
    headers = settings.auth_headers()
    assert headers["Authorization"] == "Bearer test_token_1234567890abcdefghijklmnopqr"
    assert (
        settings.http_client_config()["headers"]["Authorization"]
        == "Bearer test_token_1234567890abcdefghijklmnopqr"
    )


def test_http_defaults_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAINDROP_ENABLE_HTTP_TRANSPORT", "true")
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    assert settings.enable_http_transport is True
    assert settings.http_host == "127.0.0.1"
    assert settings.http_port == 3034
