"""Account-focused MCP tools for Raindrop.io."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_account_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register account inspection tools."""

    @registry.register(
        ToolMetadata(
            name="get_account_profile",
            description="Return the authenticated Raindrop.io account profile.",
            category=ToolCategory.ACCOUNT,
        )
    )
    async def get_account_profile() -> dict[str, Any]:
        return (await client.get_me()).model_dump(by_alias=True, exclude_none=True)


__all__ = ["register_account_tools"]
