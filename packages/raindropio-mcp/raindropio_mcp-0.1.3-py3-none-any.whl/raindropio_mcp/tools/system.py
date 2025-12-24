"""System-oriented helper tools."""

from __future__ import annotations

from datetime import UTC, datetime

from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)


def register_system_tools(registry: FastMCPToolRegistry) -> None:
    """Register system/utility tools."""

    @registry.register(
        ToolMetadata(
            name="ping",
            description="Simple heartbeat that returns server timestamp.",
            category=ToolCategory.SYSTEM,
        )
    )
    async def ping() -> dict[str, str]:
        return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


__all__ = ["register_system_tools"]
