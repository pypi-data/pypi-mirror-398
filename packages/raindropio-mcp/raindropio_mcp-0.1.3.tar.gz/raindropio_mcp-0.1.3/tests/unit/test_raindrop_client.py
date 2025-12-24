from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import PaginatedBookmarks, RaindropClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.models import BookmarkCreate
from raindropio_mcp.utils.exceptions import APIError


@pytest.fixture
async def client() -> RaindropClient:
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    instance = RaindropClient(settings)
    yield instance
    await instance.close()


@pytest.mark.asyncio
async def test_list_collections_success(client: RaindropClient) -> None:
    payload = {
        "result": True,
        "items": [
            {"_id": 1, "title": "Inbox"},
            {"_id": 2, "title": "Archive"},
        ],
    }
    client.get_json = AsyncMock(return_value=payload)

    collections = await client.list_collections()
    assert [c.title for c in collections] == ["Inbox", "Archive"]
    client.get_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_collections_error(client: RaindropClient) -> None:
    client.get_json = AsyncMock(return_value={"result": False, "items": []})
    with pytest.raises(APIError):
        await client.list_collections()


@pytest.mark.asyncio
async def test_create_bookmark_builds_payload(client: RaindropClient) -> None:
    response_payload = {
        "result": True,
        "item": {
            "_id": 10,
            "link": "https://example.com",
            "title": "Example",
        },
    }
    mock_get_json = AsyncMock(return_value=response_payload)
    client.get_json = mock_get_json

    result = await client.create_bookmark(
        123,
        BookmarkCreate(
            link="https://example.com",
            title="Example",
            tags=["demo"],
        ),
    )

    assert result.link == "https://example.com"
    mock_get_json.assert_awaited_once()
    args, kwargs = mock_get_json.await_args
    assert args[0] == "POST"
    assert args[1] == "/raindrops/123"
    assert kwargs["json_body"]["item"]["tags"] == ["demo"]


@pytest.mark.asyncio
async def test_search_bookmarks_returns_serialisable_page(
    client: RaindropClient,
) -> None:
    payload = {
        "result": True,
        "items": [
            {"_id": 42, "title": "Found", "link": "https://example.com"},
        ],
        "count": 1,
    }
    client.get_json = AsyncMock(return_value=payload)

    page = await client.search_bookmarks("example")
    assert isinstance(page, PaginatedBookmarks)
    assert page.count == 1
    assert page.items[0].title == "Found"


@pytest.mark.asyncio
async def test_rename_tag_failure_raises(client: RaindropClient) -> None:
    client.get_json = AsyncMock(return_value={"result": False})
    with pytest.raises(APIError):
        await client.rename_tag("old", "new")
