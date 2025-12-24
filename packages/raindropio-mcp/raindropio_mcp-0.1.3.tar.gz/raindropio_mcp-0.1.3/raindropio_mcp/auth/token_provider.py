"""Simple bearer-token auth provider for Raindrop.io."""

from __future__ import annotations

from dataclasses import dataclass, field

from raindropio_mcp.utils.exceptions import AuthenticationError


@dataclass
class BearerTokenProvider:
    """Wrap a static Raindrop.io bearer token."""

    token: str
    _sanitized: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.token or not self.token.strip():
            raise AuthenticationError("Raindrop.io token may not be empty")
        self._sanitized = self.token.strip()

    def authorization_header(self) -> str:
        return f"Bearer {self._sanitized}"

    def headers(self) -> dict[str, str]:
        return {"Authorization": self.authorization_header()}


__all__ = ["BearerTokenProvider"]
