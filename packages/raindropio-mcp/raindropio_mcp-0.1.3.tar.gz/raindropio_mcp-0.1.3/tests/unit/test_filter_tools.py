"""Tests for Raindrop.io filter tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import FilteredBookmarksResponse
from raindropio_mcp.tools.filters import register_filter_tools
from raindropio_mcp.tools.tool_registry import FastMCPToolRegistry


@pytest.fixture
def mock_client():
    """Mock RaindropClient for testing."""
    client = AsyncMock(spec=RaindropClient)
    return client


@pytest.fixture
def registry():
    """FastMCPToolRegistry for testing."""
    from fastmcp import FastMCP

    app = FastMCP(name="test", version="0.1.0")
    return FastMCPToolRegistry(app)


@pytest.fixture
def sample_filtered_response():
    """Sample filtered bookmarks response for testing."""
    return FilteredBookmarksResponse(
        result=True,
        items=[{"_id": 123, "title": "Test Bookmark", "link": "https://example.com"}],
        count=1,
        total=1,
        page=0,
        per_page=50,
        filters_applied=["important", "tag:ai"],
    )


@pytest.mark.asyncio
async def test_register_filter_tools(registry, mock_client):
    """Test that all filter tools are registered."""
    register_filter_tools(registry, mock_client)

    tool_names = set(registry.tools.keys())
    expected_tools = {"apply_filters", "get_filtered_bookmarks_by_collection"}

    assert expected_tools.issubset(tool_names), (
        f"Missing tools: {expected_tools - tool_names}"
    )


@pytest.mark.asyncio
async def test_apply_filters_tool(registry, mock_client, sample_filtered_response):
    """Test the apply_filters tool."""
    register_filter_tools(registry, mock_client)

    mock_client.apply_filters.return_value = sample_filtered_response

    payload = {"search": "AI research", "tags": ["important", "ai"], "important": True}

    # Execute the tool
    tool = registry.tools["apply_filters"].coroutine
    result = await tool(payload)

    # Verify client was called correctly
    mock_client.apply_filters.assert_called_once()
    args, kwargs = mock_client.apply_filters.call_args
    assert args[0].search == "AI research"
    assert args[0].tags == ["important", "ai"]
    assert args[0].important is True

    # Verify result
    assert result["result"] is True
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_filtered_bookmarks_by_collection_tool(
    registry, mock_client, sample_filtered_response
):
    """Test the get_filtered_bookmarks_by_collection tool."""
    register_filter_tools(registry, mock_client)

    mock_client.get_filtered_bookmarks_by_collection.return_value = (
        sample_filtered_response
    )

    payload = {"tags": ["important"], "favorite": True}

    # Execute the tool
    tool = registry.tools["get_filtered_bookmarks_by_collection"].coroutine
    result = await tool(5, payload)  # collection_id and payload

    # Verify client was called correctly
    mock_client.get_filtered_bookmarks_by_collection.assert_called_once()
    args, kwargs = mock_client.get_filtered_bookmarks_by_collection.call_args
    assert args[0] == 5  # collection_id
    assert args[1].tags == ["important"]
    assert args[1].favorite is True

    # Verify result
    assert result["result"] is True
    assert len(result["items"]) == 1
