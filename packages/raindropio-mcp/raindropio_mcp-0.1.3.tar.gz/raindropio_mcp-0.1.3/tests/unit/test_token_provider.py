from __future__ import annotations

import pytest

from raindropio_mcp.auth.token_provider import BearerTokenProvider
from raindropio_mcp.utils.exceptions import AuthenticationError


def test_token_provider_strips_whitespace() -> None:
    provider = BearerTokenProvider("  secret-token  ")
    assert provider.authorization_header() == "Bearer secret-token"
    assert provider.headers()["Authorization"] == "Bearer secret-token"


def test_token_provider_rejects_blank() -> None:
    with pytest.raises(AuthenticationError):
        BearerTokenProvider("   ")
