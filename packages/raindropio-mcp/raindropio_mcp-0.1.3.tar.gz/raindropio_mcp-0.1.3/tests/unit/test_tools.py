from __future__ import annotations

import pytest
from fastmcp import FastMCP

from raindropio_mcp.clients.raindrop_client import PaginatedBookmarks
from raindropio_mcp.models import Bookmark, Collection, Tag, User
from raindropio_mcp.tools import register_all_tools


class DummyClient:
    async def list_collections(self):
        return [Collection.model_validate({"_id": 1, "title": "Inbox"})]

    async def get_collection(self, collection_id: int):
        return Collection.model_validate({"_id": collection_id, "title": "Inbox"})

    async def create_collection(self, data):
        return Collection.model_validate({"_id": 2, "title": data.title})

    async def update_collection(self, collection_id: int, data):
        return Collection.model_validate({"_id": collection_id, "title": data.title})

    async def delete_collection(self, collection_id: int):  # noqa: ARG002
        return True

    async def list_bookmarks(self, collection_id: int, **kwargs):  # noqa: ARG002
        bookmark = Bookmark.model_validate(
            {"_id": 7, "title": "Example", "link": "https://example.com"}
        )
        return PaginatedBookmarks(
            items=[bookmark], count=1, collection_id=collection_id, page=0, per_page=50
        )

    async def search_bookmarks(self, query: str, **kwargs):  # noqa: ARG002
        bookmark = Bookmark.model_validate(
            {"_id": 9, "title": "Search", "link": "https://example.com"}
        )
        return PaginatedBookmarks(
            items=[bookmark], count=1, collection_id=None, page=0, per_page=50
        )

    async def get_bookmark(self, bookmark_id: int):  # noqa: ARG002
        return Bookmark.model_validate(
            {"_id": bookmark_id, "title": "Example", "link": "https://example.com"}
        )

    async def create_bookmark(self, collection_id: int, data):  # noqa: ARG002
        payload = {"_id": 11, "title": data.title or "", "link": data.link}
        return Bookmark.model_validate(payload)

    async def update_bookmark(self, bookmark_id: int, data):  # noqa: ARG002
        payload = {
            "_id": bookmark_id,
            "title": data.title or "",
            "link": data.link or "https://example.com",
        }
        return Bookmark.model_validate(payload)

    async def delete_bookmark(self, bookmark_id: int):  # noqa: ARG002
        return True

    async def list_tags(self):
        return [Tag.model_validate({"_id": "news", "count": 3})]

    async def rename_tag(self, old_tag: str, new_tag: str):  # noqa: ARG002
        return True

    async def delete_tag(self, tag: str):  # noqa: ARG002
        return True

    async def get_me(self):
        return User.model_validate(
            {"_id": 1, "name": "Demo", "email": "demo@example.com"}
        )


@pytest.mark.asyncio
async def test_register_all_tools() -> None:
    app = FastMCP("test")
    registry = register_all_tools(app, DummyClient())

    expected_tools = {
        "list_collections",
        "get_collection",
        "create_collection",
        "update_collection",
        "delete_collection",
        "list_bookmarks",
        "search_bookmarks",
        "get_bookmark",
        "create_bookmark",
        "update_bookmark",
        "delete_bookmark",
        "list_tags",
        "rename_tag",
        "delete_tag",
        "get_account_profile",
        "ping",
    }
    assert expected_tools.issubset(registry.tools.keys())

    collections_tool = registry.tools["list_collections"].coroutine
    result = await collections_tool()
    assert result[0]["title"] == "Inbox"

    ping_tool = registry.tools["ping"].coroutine
    ping_result = await ping_tool()
    assert ping_result["status"] == "ok"
