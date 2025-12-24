"""Unit tests for the raindrop client module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from raindropio_mcp.clients.raindrop_client import PaginatedBookmarks, RaindropClient
from raindropio_mcp.models import (
    Bookmark,
    BookmarkCreate,
    BookmarkUpdate,
    Collection,
    CollectionCreate,
    CollectionUpdate,
    Tag,
    User,
)
from raindropio_mcp.utils.exceptions import APIError


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.http_client_config.return_value = {}
    settings.retry = MagicMock()
    settings.retry.total = 2
    settings.retry.backoff_factor = 0.1
    settings.retry.status_forcelist = [429, 502, 503, 504]
    return settings


@pytest.mark.asyncio
async def test_raindrop_client_init(mock_settings):
    """Test RaindropClient initialization."""
    client = RaindropClient(mock_settings)
    assert client._page_defaults["page"] == 0
    assert client._page_defaults["perpage"] == 50


@pytest.mark.asyncio
async def test_get_me_success(mock_settings):
    """Test successful retrieval of user profile."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "user": {"_id": 123, "email": "test@example.com", "name": "Test User"},
        }
    )

    user = await client.get_me()
    assert isinstance(user, User)
    client.get_json.assert_called_once_with("GET", "/me")


@pytest.mark.asyncio
async def test_get_me_api_error(mock_settings):
    """Test get_me with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False})

    with pytest.raises(APIError):
        await client.get_me()


@pytest.mark.asyncio
async def test_list_collections_success(mock_settings):
    """Test successful listing of collections."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "items": [
                {
                    "_id": 123,
                    "title": "Test Collection",
                    "description": "A test collection",
                }
            ],
        }
    )

    collections = await client.list_collections()
    assert len(collections) == 1
    assert isinstance(collections[0], Collection)
    client.get_json.assert_called_once_with("GET", "/collections")


@pytest.mark.asyncio
async def test_list_collections_api_error(mock_settings):
    """Test list_collections with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False, "items": []})

    with pytest.raises(APIError):
        await client.list_collections()


@pytest.mark.asyncio
async def test_get_collection_success(mock_settings):
    """Test successful retrieval of a collection."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "collection": {
                "_id": 123,
                "title": "Test Collection",
                "description": "A test collection",
            },
        }
    )

    collection = await client.get_collection(123)
    assert isinstance(collection, Collection)
    assert collection.id == 123
    client.get_json.assert_called_once_with("GET", "/collection/123")


@pytest.mark.asyncio
async def test_get_collection_api_error(mock_settings):
    """Test get_collection with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False})

    with pytest.raises(APIError):
        await client.get_collection(123)


@pytest.mark.asyncio
async def test_create_collection_success(mock_settings):
    """Test successful creation of a collection."""
    client = RaindropClient(mock_settings)
    collection_data = CollectionCreate(
        title="New Collection", description="A new collection"
    )

    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "collection": {
                "_id": 456,
                "title": "New Collection",
                "description": "A new collection",
            },
        }
    )

    created_collection = await client.create_collection(collection_data)
    assert isinstance(created_collection, Collection)
    assert created_collection.id == 456
    client.get_json.assert_called_once()


@pytest.mark.asyncio
async def test_update_collection_success(mock_settings):
    """Test successful update of a collection."""
    client = RaindropClient(mock_settings)
    update_data = CollectionUpdate(title="Updated Title")

    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "collection": {
                "_id": 123,
                "title": "Updated Title",
                "description": "A test collection",
            },
        }
    )

    updated_collection = await client.update_collection(123, update_data)
    assert isinstance(updated_collection, Collection)
    assert updated_collection.title == "Updated Title"
    client.get_json.assert_called_once_with(
        "PUT",
        "/collection/123",
        json_body=update_data.model_dump(exclude_none=True, by_alias=True),
    )


@pytest.mark.asyncio
async def test_delete_collection_success(mock_settings):
    """Test successful deletion of a collection."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": True})

    result = await client.delete_collection(123)
    assert result is True
    client.get_json.assert_called_once_with("DELETE", "/collection/123")


@pytest.mark.asyncio
async def test_delete_collection_api_error(mock_settings):
    """Test delete_collection with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False})

    with pytest.raises(APIError):
        await client.delete_collection(123)


@pytest.mark.asyncio
async def test_list_bookmarks_success(mock_settings):
    """Test successful listing of bookmarks."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "items": [
                {"_id": 789, "title": "Test Bookmark", "link": "https://example.com"}
            ],
            "count": 1,
        }
    )

    bookmarks = await client.list_bookmarks(123)
    assert isinstance(bookmarks, PaginatedBookmarks)
    assert len(bookmarks.items) == 1
    assert isinstance(bookmarks.items[0], Bookmark)
    client.get_json.assert_called_once()


@pytest.mark.asyncio
async def test_search_bookmarks_success(mock_settings):
    """Test successful bookmark search."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "items": [
                {"_id": 789, "title": "Test Bookmark", "link": "https://example.com"}
            ],
            "count": 1,
        }
    )

    bookmarks = await client.search_bookmarks("test query")
    assert isinstance(bookmarks, PaginatedBookmarks)
    assert len(bookmarks.items) == 1
    client.get_json.assert_called_once()


@pytest.mark.asyncio
async def test_get_bookmark_success(mock_settings):
    """Test successful retrieval of a bookmark."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "item": {
                "_id": 789,
                "title": "Test Bookmark",
                "link": "https://example.com",
            },
        }
    )

    bookmark = await client.get_bookmark(789)
    assert isinstance(bookmark, Bookmark)
    assert bookmark.id == 789
    client.get_json.assert_called_once_with("GET", "/raindrop/789")


@pytest.mark.asyncio
async def test_create_bookmark_success(mock_settings):
    """Test successful creation of a bookmark."""
    client = RaindropClient(mock_settings)
    bookmark_data = BookmarkCreate(link="https://example.com", title="Test Bookmark")

    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "item": {
                "_id": 999,
                "title": "Test Bookmark",
                "link": "https://example.com",
            },
        }
    )

    created_bookmark = await client.create_bookmark(123, bookmark_data)
    assert isinstance(created_bookmark, Bookmark)
    assert created_bookmark.id == 999
    client.get_json.assert_called_once()


@pytest.mark.asyncio
async def test_update_bookmark_success(mock_settings):
    """Test successful update of a bookmark."""
    client = RaindropClient(mock_settings)
    update_data = BookmarkUpdate(link="https://example.com", title="Updated Title")

    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "item": {
                "_id": 789,
                "title": "Updated Title",
                "link": "https://example.com",
            },
        }
    )

    updated_bookmark = await client.update_bookmark(789, update_data)
    assert isinstance(updated_bookmark, Bookmark)
    assert updated_bookmark.title == "Updated Title"
    client.get_json.assert_called_once_with(
        "PUT",
        "/raindrop/789",
        json_body={"item": update_data.model_dump(exclude_none=True, by_alias=True)},
    )


@pytest.mark.asyncio
async def test_delete_bookmark_success(mock_settings):
    """Test successful deletion of a bookmark."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": True})

    result = await client.delete_bookmark(789)
    assert result is True
    client.get_json.assert_called_once_with("DELETE", "/raindrop/789")


@pytest.mark.asyncio
async def test_delete_bookmark_api_error(mock_settings):
    """Test delete_bookmark with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False})

    with pytest.raises(APIError):
        await client.delete_bookmark(789)


@pytest.mark.asyncio
async def test_list_tags_success(mock_settings):
    """Test successful listing of tags."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "items": [{"_id": "test", "count": 5}, {"_id": "example", "count": 2}],
        }
    )

    tags = await client.list_tags()
    assert len(tags) == 2
    assert all(isinstance(tag, Tag) for tag in tags)
    client.get_json.assert_called_once_with("GET", "/tags")


@pytest.mark.asyncio
async def test_rename_tag_success(mock_settings):
    """Test successful renaming of a tag."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": True})

    result = await client.rename_tag("old_tag", "new_tag")
    assert result is True
    client.get_json.assert_called_once_with(
        "PUT",
        "/tag/old_tag",
        json_body={"tag": "new_tag"},
    )


@pytest.mark.asyncio
async def test_delete_tag_success(mock_settings):
    """Test successful deletion of a tag."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": True})

    result = await client.delete_tag("test_tag")
    assert result is True
    client.get_json.assert_called_once_with("DELETE", "/tag/test_tag")


@pytest.mark.asyncio
async def test_rename_tag_api_error(mock_settings):
    """Test rename_tag with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False})

    with pytest.raises(APIError):
        await client.rename_tag("old_tag", "new_tag")


@pytest.mark.asyncio
async def test_delete_tag_api_error(mock_settings):
    """Test delete_tag with API error response."""
    client = RaindropClient(mock_settings)
    client.get_json = AsyncMock(return_value={"result": False})

    with pytest.raises(APIError):
        await client.delete_tag("test_tag")
