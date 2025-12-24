"""FastMCP tools for interacting with Raindrop.io bookmarks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.models import BookmarkCreate, BookmarkUpdate
from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import (
        PaginatedBookmarks,
        RaindropClient,
    )


def _serialize_page(page: PaginatedBookmarks) -> dict[str, Any]:
    return {
        "items": [
            item.model_dump(by_alias=True, exclude_none=True) for item in page.items
        ],
        "count": page.count,
        "collectionId": page.collection_id,
        "page": page.page,
        "perPage": page.per_page,
    }


def register_bookmark_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register bookmark CRUD and search tools."""

    @registry.register(
        ToolMetadata(
            name="list_bookmarks",
            description="List bookmarks inside a specific collection.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def list_bookmarks(
        collection_id: int,
        page: int | None = None,
        per_page: int | None = None,
        search: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        page_data = await client.list_bookmarks(
            collection_id,
            page=page,
            per_page=per_page,
            search=search,
            sort=sort,
        )
        return _serialize_page(page_data)

    @registry.register(
        ToolMetadata(
            name="search_bookmarks",
            description="Search bookmarks across all collections.",
            category=ToolCategory.SEARCH,
        )
    )
    async def search_bookmarks(
        query: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        page_data = await client.search_bookmarks(query, page=page, per_page=per_page)
        return _serialize_page(page_data)

    @registry.register(
        ToolMetadata(
            name="get_bookmark",
            description="Fetch a single bookmark by id.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def get_bookmark(bookmark_id: int) -> dict[str, Any]:
        return (await client.get_bookmark(bookmark_id)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="create_bookmark",
            description="Create a new bookmark within the given collection.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def create_bookmark(
        collection_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        model = BookmarkCreate.model_validate(payload)
        return (await client.create_bookmark(collection_id, model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="update_bookmark",
            description="Update bookmark metadata (title, tags, notes, etc.).",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def update_bookmark(
        bookmark_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        model = BookmarkUpdate.model_validate(payload)
        return (await client.update_bookmark(bookmark_id, model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="delete_bookmark",
            description="Delete a bookmark by id.",
            category=ToolCategory.BOOKMARKS,
        )
    )
    async def delete_bookmark(bookmark_id: int) -> dict[str, Any]:
        await client.delete_bookmark(bookmark_id)
        return {"result": True, "bookmark_id": bookmark_id}


__all__ = ["register_bookmark_tools"]
