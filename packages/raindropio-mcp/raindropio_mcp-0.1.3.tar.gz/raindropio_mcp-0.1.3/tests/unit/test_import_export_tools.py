"""Tests for Raindrop.io import/export tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import ImportResult
from raindropio_mcp.tools.import_export import register_import_export_tools
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


@pytest.mark.asyncio
async def test_register_import_export_tools(registry, mock_client):
    """Test that all import/export tools are registered."""
    register_import_export_tools(registry, mock_client)

    tool_names = set(registry.tools.keys())
    expected_tools = {"import_bookmarks", "export_bookmarks"}

    assert expected_tools.issubset(tool_names), (
        f"Missing tools: {expected_tools - tool_names}"
    )


@pytest.mark.asyncio
async def test_import_bookmarks_tool(registry, mock_client):
    """Test the import_bookmarks tool."""
    register_import_export_tools(registry, mock_client)

    mock_result = ImportResult(
        result=True, imported_count=5, skipped_count=1, errors=[], collection_id=123
    )
    mock_client.import_bookmarks.return_value = mock_result

    payload = {
        "format": "netscape",
        "source": "browser",
        "options": {"merge_duplicates": True},
    }

    # Execute the tool
    tool = registry.tools["import_bookmarks"].coroutine
    result = await tool(payload, 123)  # payload and collection_id

    # Verify client was called correctly
    mock_client.import_bookmarks.assert_called_once()
    args, kwargs = mock_client.import_bookmarks.call_args
    assert args[0].format == "netscape"
    assert args[0].source == "browser"
    assert args[0].options == {"merge_duplicates": True}
    assert args[1] == 123  # collection_id

    # Verify result
    assert result["result"] is True
    assert result["imported_count"] == 5


@pytest.mark.asyncio
async def test_export_bookmarks_tool(registry, mock_client):
    """Test the export_bookmarks tool."""
    register_import_export_tools(registry, mock_client)

    expected_export_data = (
        '{"bookmarks": [{"title": "Test", "link": "https://example.com"}]}'
    )
    mock_client.export_bookmarks.return_value = expected_export_data

    payload = {"format": "json", "include_highlights": True, "include_notes": False}

    # Execute the tool
    tool = registry.tools["export_bookmarks"].coroutine
    result = await tool(payload, 123)  # payload and collection_id

    # Verify client was called correctly
    mock_client.export_bookmarks.assert_called_once()
    args, kwargs = mock_client.export_bookmarks.call_args
    assert args[0].format == "json"
    assert args[0].include_highlights is True
    assert args[0].include_notes is False
    assert args[1] == 123  # collection_id

    # Verify result
    assert "bookmarks" in result
