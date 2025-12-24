"""Shared pytest fixtures."""

import pytest

from raindropio_mcp.config.settings import get_settings


@pytest.fixture(autouse=True)
def raindrop_token_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure a token is present for settings during tests."""
    monkeypatch.setenv("RAINDROP_TOKEN", "test-token")


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
