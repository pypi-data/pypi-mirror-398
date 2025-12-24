"""MCP tools for Raindrop.io batch operations functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.models import (
    BatchDeleteBookmarks,
    BatchMoveBookmarks,
    BatchTagBookmarks,
    BatchUntagBookmarks,
    BatchUpdateBookmarks,
)
from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_batch_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register batch operations tools."""

    @registry.register(
        ToolMetadata(
            name="batch_move_bookmarks",
            description="Move multiple bookmarks to a different collection.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def batch_move_bookmarks(payload: dict[str, Any]) -> dict[str, Any]:
        model = BatchMoveBookmarks.model_validate(payload)
        return (await client.batch_move_bookmarks(model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="batch_delete_bookmarks",
            description="Delete multiple bookmarks.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def batch_delete_bookmarks(payload: dict[str, Any]) -> dict[str, Any]:
        model = BatchDeleteBookmarks.model_validate(payload)
        return (await client.batch_delete_bookmarks(model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="batch_update_bookmarks",
            description="Update multiple bookmarks with the same changes.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def batch_update_bookmarks(payload: dict[str, Any]) -> dict[str, Any]:
        model = BatchUpdateBookmarks.model_validate(payload)
        return (await client.batch_update_bookmarks(model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="batch_tag_bookmarks",
            description="Add tags to multiple bookmarks.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def batch_tag_bookmarks(payload: dict[str, Any]) -> dict[str, Any]:
        model = BatchTagBookmarks.model_validate(payload)
        return (await client.batch_tag_bookmarks(model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="batch_untag_bookmarks",
            description="Remove tags from multiple bookmarks.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def batch_untag_bookmarks(payload: dict[str, Any]) -> dict[str, Any]:
        model = BatchUntagBookmarks.model_validate(payload)
        return (await client.batch_untag_bookmarks(model)).model_dump(
            by_alias=True, exclude_none=True
        )


__all__ = ["register_batch_tools"]
