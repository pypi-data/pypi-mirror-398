"""Tests for Raindrop.io batch operation tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import BatchOperationResponse
from raindropio_mcp.tools.batch import register_batch_tools
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
def sample_batch_response():
    """Sample batch operation response for testing."""
    return BatchOperationResponse(
        result=True, processed_count=3, success_count=3, error_count=0
    )


@pytest.mark.asyncio
async def test_register_batch_tools(registry, mock_client):
    """Test that all batch tools are registered."""
    register_batch_tools(registry, mock_client)

    tool_names = set(registry.tools.keys())
    expected_tools = {
        "batch_move_bookmarks",
        "batch_delete_bookmarks",
        "batch_update_bookmarks",
        "batch_tag_bookmarks",
        "batch_untag_bookmarks",
    }

    assert expected_tools.issubset(tool_names), (
        f"Missing tools: {expected_tools - tool_names}"
    )


@pytest.mark.asyncio
async def test_batch_move_bookmarks_tool(registry, mock_client, sample_batch_response):
    """Test the batch_move_bookmarks tool."""
    register_batch_tools(registry, mock_client)

    mock_client.batch_move_bookmarks.return_value = sample_batch_response

    payload = {"bookmark_ids": [111, 222, 333], "collection_id": 4}

    # Execute the tool
    tool = registry.tools["batch_move_bookmarks"].coroutine
    result = await tool(payload)

    # Verify client was called correctly
    mock_client.batch_move_bookmarks.assert_called_once()
    args, kwargs = mock_client.batch_move_bookmarks.call_args
    assert args[0].bookmark_ids == [111, 222, 333]
    assert args[0].collection_id == 4

    # Verify result
    assert result["result"] is True
    assert result["processed_count"] == 3


@pytest.mark.asyncio
async def test_batch_delete_bookmarks_tool(
    registry, mock_client, sample_batch_response
):
    """Test the batch_delete_bookmarks tool."""
    register_batch_tools(registry, mock_client)

    mock_client.batch_delete_bookmarks.return_value = sample_batch_response

    payload = {"bookmark_ids": [111, 222, 333]}

    # Execute the tool
    tool = registry.tools["batch_delete_bookmarks"].coroutine
    result = await tool(payload)

    # Verify client was called correctly
    mock_client.batch_delete_bookmarks.assert_called_once()
    args, kwargs = mock_client.batch_delete_bookmarks.call_args
    assert args[0].bookmark_ids == [111, 222, 333]

    # Verify result
    assert result["result"] is True


@pytest.mark.asyncio
async def test_batch_update_bookmarks_tool(
    registry, mock_client, sample_batch_response
):
    """Test the batch_update_bookmarks tool."""
    register_batch_tools(registry, mock_client)

    mock_client.batch_update_bookmarks.return_value = sample_batch_response

    payload = {
        "bookmark_ids": [111, 222, 333],
        "title": "New Title",
        "tags": ["important"],
    }

    # Execute the tool
    tool = registry.tools["batch_update_bookmarks"].coroutine
    result = await tool(payload)

    # Verify client was called correctly
    mock_client.batch_update_bookmarks.assert_called_once()
    args, kwargs = mock_client.batch_update_bookmarks.call_args
    assert args[0].bookmark_ids == [111, 222, 333]
    assert args[0].title == "New Title"
    assert args[0].tags == ["important"]

    # Verify result
    assert result["result"] is True


@pytest.mark.asyncio
async def test_batch_tag_bookmarks_tool(registry, mock_client, sample_batch_response):
    """Test the batch_tag_bookmarks tool."""
    register_batch_tools(registry, mock_client)

    mock_client.batch_tag_bookmarks.return_value = sample_batch_response

    payload = {"bookmark_ids": [111, 222, 333], "tags": ["important", "readlater"]}

    # Execute the tool
    tool = registry.tools["batch_tag_bookmarks"].coroutine
    result = await tool(payload)

    # Verify client was called correctly
    mock_client.batch_tag_bookmarks.assert_called_once()
    args, kwargs = mock_client.batch_tag_bookmarks.call_args
    assert args[0].bookmark_ids == [111, 222, 333]
    assert args[0].tags == ["important", "readlater"]

    # Verify result
    assert result["result"] is True


@pytest.mark.asyncio
async def test_batch_untag_bookmarks_tool(registry, mock_client, sample_batch_response):
    """Test the batch_untag_bookmarks tool."""
    register_batch_tools(registry, mock_client)

    mock_client.batch_untag_bookmarks.return_value = sample_batch_response

    payload = {"bookmark_ids": [111, 222, 333], "tags": ["old-tag"]}

    # Execute the tool
    tool = registry.tools["batch_untag_bookmarks"].coroutine
    result = await tool(payload)

    # Verify client was called correctly
    mock_client.batch_untag_bookmarks.assert_called_once()
    args, kwargs = mock_client.batch_untag_bookmarks.call_args
    assert args[0].bookmark_ids == [111, 222, 333]
    assert args[0].tags == ["old-tag"]

    # Verify result
    assert result["result"] is True
