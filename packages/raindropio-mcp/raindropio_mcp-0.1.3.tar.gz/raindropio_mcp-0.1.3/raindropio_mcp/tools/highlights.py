"""MCP tools for Raindrop.io highlights functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.models import HighlightCreate, HighlightUpdate
from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_highlight_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register highlights management tools."""

    @registry.register(
        ToolMetadata(
            name="list_highlights",
            description="List all highlights for a specific bookmark.",
            category=ToolCategory.HIGHLIGHTS,
        )
    )
    async def list_highlights(bookmark_id: int) -> list[dict[str, Any]]:
        return [
            highlight.model_dump(by_alias=True, exclude_none=True)
            for highlight in await client.list_highlights(bookmark_id)
        ]

    @registry.register(
        ToolMetadata(
            name="get_highlight",
            description="Fetch a single highlight by its ID.",
            category=ToolCategory.HIGHLIGHTS,
        )
    )
    async def get_highlight(highlight_id: int) -> dict[str, Any]:
        return (await client.get_highlight(highlight_id)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="create_highlight",
            description="Create a new highlight for a bookmark.",
            category=ToolCategory.HIGHLIGHTS,
        )
    )
    async def create_highlight(
        bookmark_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        model = HighlightCreate.model_validate(payload)
        return (await client.create_highlight(bookmark_id, model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="update_highlight",
            description="Update an existing highlight.",
            category=ToolCategory.HIGHLIGHTS,
        )
    )
    async def update_highlight(
        highlight_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        model = HighlightUpdate.model_validate(payload)
        return (await client.update_highlight(highlight_id, model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="delete_highlight",
            description="Delete a highlight by its ID.",
            category=ToolCategory.HIGHLIGHTS,
        )
    )
    async def delete_highlight(highlight_id: int) -> dict[str, Any]:
        await client.delete_highlight(highlight_id)
        return {"result": True, "highlight_id": highlight_id}


__all__ = ["register_highlight_tools"]
