"""FastMCP entrypoint wiring Raindrop.io tools together."""

from __future__ import annotations

import importlib.util
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Final

from fastmcp import FastMCP

from raindropio_mcp import __version__
from raindropio_mcp.clients.client_factory import build_raindrop_client
from raindropio_mcp.config import get_settings
from raindropio_mcp.tools import register_all_tools

# Check FastMCP rate limiting middleware availability (Phase 3.3 M2: improved pattern)
RATE_LIMITING_AVAILABLE = (
    importlib.util.find_spec("fastmcp.server.middleware.rate_limiting") is not None
)

# Check ServerPanels availability (Phase 3.3 M2: improved pattern)
SERVERPANELS_AVAILABLE = importlib.util.find_spec("mcp_common.ui") is not None

# Import security availability flag (Phase 3 Security Hardening)
try:
    from mcp_common.security import APIKeyValidator

    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

APP_NAME: Final = "raindropio-mcp"
APP_VERSION: Final = __version__


def create_app() -> FastMCP:
    """Create and configure the FastMCP application."""

    settings = get_settings()
    app = FastMCP(name=APP_NAME, version=APP_VERSION)

    # Add rate limiting middleware (Phase 3 Security Hardening)
    if RATE_LIMITING_AVAILABLE and hasattr(app._mcp_server, "add_middleware"):
        from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware

        rate_limiter = RateLimitingMiddleware(
            max_requests_per_second=8.0,  # Sustainable rate for bookmark API
            burst_capacity=16,  # Allow brief bursts
            global_limit=True,  # Protect the Raindrop.io API globally
        )
        app._mcp_server.add_middleware(rate_limiter)
        logger.info("Rate limiting enabled: 8 req/sec, burst 16")

    client = build_raindrop_client(settings)
    register_all_tools(app, client)

    original_lifespan = app._mcp_server.lifespan

    @asynccontextmanager
    async def lifespan(server: Any) -> AsyncGenerator[dict[str, Any]]:
        async with original_lifespan(server) as state:
            try:
                yield state
            finally:
                await client.close()

    app._mcp_server.lifespan = lifespan
    app._raindrop_client = client  # type: ignore[attr-defined]
    logger.debug("Registered Raindrop.io MCP tools")
    return app


# Initialize app lazily to avoid startup errors in testing environment
def __getattr__(name: str) -> Any:
    if name == "app":
        return create_app()
    if name == "http_app":
        # Export ASGI app for uvicorn (same pattern as mailgun-mcp)
        return create_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "create_app",
    "APP_NAME",
    "APP_VERSION",
    "RATE_LIMITING_AVAILABLE",
    "SECURITY_AVAILABLE",
    "SERVERPANELS_AVAILABLE",
]
