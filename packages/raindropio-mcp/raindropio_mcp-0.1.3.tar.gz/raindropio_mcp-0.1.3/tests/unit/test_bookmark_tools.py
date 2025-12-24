"""Unit tests for the bookmarks tools module."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from raindropio_mcp.clients.raindrop_client import PaginatedBookmarks, RaindropClient
from raindropio_mcp.models import Bookmark
from raindropio_mcp.tools.bookmarks import _serialize_page, register_bookmark_tools
from raindropio_mcp.tools.tool_registry import FastMCPToolRegistry


@pytest.mark.asyncio
async def test_register_bookmark_tools():
    """Test registration and execution of bookmark tools."""
    # Mock dependencies
    mock_client = AsyncMock(spec=RaindropClient)

    # Create sample bookmark
    sample_bookmark = Bookmark(
        id=789,
        title="Test Bookmark",
        link="https://example.com",
        excerpt="A test bookmark",
        tags=["test", "example"],
    )

    # Create updated bookmark for update test
    updated_bookmark = Bookmark(
        id=789,
        title="Updated Title",
        link="https://example.com",
        excerpt="A test bookmark",
        tags=["test", "example"],
    )

    # Set up mock returns
    mock_client.list_bookmarks = AsyncMock(
        return_value=PaginatedBookmarks(
            items=[sample_bookmark], count=1, collection_id=123, page=0, per_page=50
        )
    )

    mock_client.search_bookmarks = AsyncMock(
        return_value=PaginatedBookmarks(
            items=[sample_bookmark], count=1, collection_id=None, page=0, per_page=50
        )
    )

    mock_client.get_bookmark = AsyncMock(return_value=sample_bookmark)
    mock_client.create_bookmark = AsyncMock(return_value=sample_bookmark)
    mock_client.update_bookmark = AsyncMock(
        return_value=updated_bookmark
    )  # Return updated bookmark
    mock_client.delete_bookmark = AsyncMock(return_value=True)

    # Create a FastMCP app instance to pass to the registry
    app = FastMCP(name="test", version="1.0")

    # Create tool registry
    registry = FastMCPToolRegistry(app)

    # Register tools
    register_bookmark_tools(registry, mock_client)

    # Test list_bookmarks
    list_result = await registry._tools["list_bookmarks"].coroutine(collection_id=123)
    assert "items" in list_result
    assert list_result["count"] == 1

    # Test search_bookmarks
    search_result = await registry._tools["search_bookmarks"].coroutine(query="test")
    assert "items" in search_result
    assert search_result["count"] == 1

    # Test get_bookmark
    get_result = await registry._tools["get_bookmark"].coroutine(bookmark_id=789)
    assert get_result["_id"] == 789  # Model serializes id as _id
    assert get_result["title"] == "Test Bookmark"

    # Test create_bookmark
    create_payload = {"link": "https://example.com", "title": "New Bookmark"}
    create_result = await registry._tools["create_bookmark"].coroutine(
        collection_id=123, payload=create_payload
    )
    assert create_result["_id"] == 789  # Model serializes id as _id

    # Test update_bookmark
    update_payload = {
        "link": "https://example.com",  # Required field
        "title": "Updated Title",
    }
    update_result = await registry._tools["update_bookmark"].coroutine(
        bookmark_id=789, payload=update_payload
    )
    assert update_result["_id"] == 789  # Model serializes id as _id
    assert update_result["title"] == "Updated Title"

    # Test delete_bookmark
    delete_result = await registry._tools["delete_bookmark"].coroutine(bookmark_id=789)
    assert delete_result["result"] is True
    assert delete_result["bookmark_id"] == 789

    # Verify all client methods were called
    mock_client.list_bookmarks.assert_called_once()
    mock_client.search_bookmarks.assert_called_once()
    mock_client.get_bookmark.assert_called_once()
    mock_client.create_bookmark.assert_called_once()
    mock_client.update_bookmark.assert_called_once()
    mock_client.delete_bookmark.assert_called_once()


def test_serialize_page():
    """Test the _serialize_page helper function."""
    sample_bookmark = Bookmark(
        id=789,
        title="Test Bookmark",
        link="https://example.com",
        excerpt="A test bookmark",
        tags=["test", "example"],
    )

    paginated_data = PaginatedBookmarks(
        items=[sample_bookmark], count=1, collection_id=123, page=0, per_page=50
    )

    serialized = _serialize_page(paginated_data)

    assert "items" in serialized
    assert serialized["count"] == 1
    assert serialized["collectionId"] == 123
    assert serialized["page"] == 0
    assert serialized["perPage"] == 50
    assert len(serialized["items"]) == 1
    assert serialized["items"][0]["_id"] == 789  # The actual model uses _id, not id
