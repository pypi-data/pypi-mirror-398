"""MCP tools for Raindrop.io filters functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.models import BookmarkFilter
from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_filter_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register filters and advanced search tools."""

    @registry.register(
        ToolMetadata(
            name="apply_filters",
            description=(
                "Apply various filters to search and "
                "organize bookmarks across all collections."
            ),
            category=ToolCategory.SEARCH,
            examples=[
                {
                    "args": [
                        {
                            "search": "AI research",
                            "tags": ["important", "ai"],
                            "important": True,
                            "created_after": "2023-01-01",
                        }
                    ],
                    "description": (
                        "Find important AI research bookmarks created this year."
                    ),
                }
            ],
        )
    )
    async def apply_filters(payload: dict[str, Any]) -> dict[str, Any]:
        model = BookmarkFilter.model_validate(payload)
        return (await client.apply_filters(model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="get_filtered_bookmarks_by_collection",
            description="Apply filters to bookmarks within a specific collection.",
            category=ToolCategory.SEARCH,
        )
    )
    async def get_filtered_bookmarks_by_collection(
        collection_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        model = BookmarkFilter.model_validate(payload)
        return (
            await client.get_filtered_bookmarks_by_collection(collection_id, model)
        ).model_dump(by_alias=True, exclude_none=True)


__all__ = ["register_filter_tools"]
