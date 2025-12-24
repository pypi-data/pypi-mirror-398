"""Factory helpers for creating Raindrop.io API clients."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.config.settings import RaindropSettings, get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def build_raindrop_client(settings: RaindropSettings | None = None) -> RaindropClient:
    """Instantiate a new :class:`RaindropClient` with provided settings."""

    return RaindropClient(settings or get_settings())


@asynccontextmanager
async def raindrop_client_context(
    settings: RaindropSettings | None = None,
) -> AsyncIterator[RaindropClient]:
    """Async context manager yielding a configured :class:`RaindropClient`."""

    client = build_raindrop_client(settings)
    try:
        yield client
    finally:
        await client.close()


__all__ = ["build_raindrop_client", "raindrop_client_context"]
