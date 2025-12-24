"""Unit tests for the collections tools module."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import Collection
from raindropio_mcp.tools.collections import register_collection_tools
from raindropio_mcp.tools.tool_registry import FastMCPToolRegistry


@pytest.mark.asyncio
async def test_register_collection_tools():
    """Test registration and execution of collection tools."""
    # Mock dependencies
    mock_client = AsyncMock(spec=RaindropClient)

    # Create sample collection
    sample_collection = Collection(
        id=123,
        title="Test Collection",
        description="A test collection",
        color="#FF0000",
    )

    # Set up mock returns
    mock_client.list_collections = AsyncMock(return_value=[sample_collection])
    mock_client.get_collection = AsyncMock(return_value=sample_collection)
    mock_client.create_collection = AsyncMock(return_value=sample_collection)
    mock_client.update_collection = AsyncMock(return_value=sample_collection)
    mock_client.delete_collection = AsyncMock(return_value=True)

    # Create a FastMCP app instance to pass to the registry
    app = FastMCP(name="test", version="1.0")

    # Create tool registry
    registry = FastMCPToolRegistry(app)

    # Register tools
    register_collection_tools(registry, mock_client)

    # Test list_collections
    list_result = await registry._tools["list_collections"].coroutine()
    assert len(list_result) == 1
    assert list_result[0]["_id"] == 123  # Using actual model field name

    # Test get_collection
    get_result = await registry._tools["get_collection"].coroutine(collection_id=123)
    assert get_result["_id"] == 123
    assert get_result["title"] == "Test Collection"

    # Test create_collection
    create_payload = {"title": "New Collection", "description": "A new collection"}
    create_result = await registry._tools["create_collection"].coroutine(
        payload=create_payload
    )
    assert create_result["_id"] == 123

    # Test update_collection
    updated_collection = Collection(
        id=123, title="Updated Title", description="A test collection", color="#FF0000"
    )
    mock_client.update_collection = AsyncMock(return_value=updated_collection)
    update_payload = {"title": "Updated Title"}
    update_result = await registry._tools["update_collection"].coroutine(
        collection_id=123, payload=update_payload
    )
    assert update_result["_id"] == 123
    assert update_result["title"] == "Updated Title"

    # Test delete_collection
    delete_result = await registry._tools["delete_collection"].coroutine(
        collection_id=123
    )
    assert delete_result["result"] is True
    assert delete_result["collection_id"] == 123

    # Verify all client methods were called
    mock_client.list_collections.assert_called_once()
    mock_client.get_collection.assert_called_once()
    # Need to call create and update collection as well
    mock_client.create_collection.assert_called_once()
    mock_client.update_collection.assert_called_once()
    mock_client.delete_collection.assert_called_once()
