"""Unit tests for the tags tools module."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import Tag
from raindropio_mcp.tools.tags import register_tag_tools
from raindropio_mcp.tools.tool_registry import FastMCPToolRegistry


@pytest.mark.asyncio
async def test_register_tag_tools():
    """Test registration and execution of tag tools."""
    # Mock dependencies
    mock_client = AsyncMock(spec=RaindropClient)

    # Create sample tags - Tag model expects string _id
    sample_tags = [
        Tag(_id="1", name="test", count=5),
        Tag(_id="2", name="example", count=3),
    ]

    # Set up mock returns
    mock_client.list_tags = AsyncMock(return_value=sample_tags)
    mock_client.rename_tag = AsyncMock(return_value=True)
    mock_client.delete_tag = AsyncMock(return_value=True)

    # Create a FastMCP app instance to pass to the registry
    app = FastMCP(name="test", version="1.0")

    # Create tool registry
    registry = FastMCPToolRegistry(app)

    # Register tools
    register_tag_tools(registry, mock_client)

    # Test list_tags
    list_result = await registry._tools["list_tags"].coroutine()
    assert len(list_result) == 2
    assert list_result[0]["_id"] == "1"  # Tag model serializes tag field as _id
    assert list_result[0]["count"] == 5

    # Test rename_tag
    rename_result = await registry._tools["rename_tag"].coroutine(
        old_tag="old_tag", new_tag="new_tag"
    )
    assert rename_result["result"] is True
    assert rename_result["from"] == "old_tag"
    assert rename_result["to"] == "new_tag"

    # Test delete_tag
    delete_result = await registry._tools["delete_tag"].coroutine(tag="test_tag")
    assert delete_result["result"] is True
    assert delete_result["tag"] == "test_tag"

    # Verify all client methods were called
    mock_client.list_tags.assert_called_once()
    mock_client.rename_tag.assert_called_once()
    mock_client.delete_tag.assert_called_once()
