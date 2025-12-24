"""Tests for Raindrop.io highlight tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import Highlight
from raindropio_mcp.tools.highlights import register_highlight_tools
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
def sample_highlight():
    """Sample highlight for testing."""
    return Highlight(
        id=123,
        bookmark_id=456,
        text="Sample highlight text",
        type="highlight",
        color="yellow",
        position=100,
    )


@pytest.mark.asyncio
async def test_register_highlight_tools(registry, mock_client):
    """Test that all highlight tools are registered."""
    register_highlight_tools(registry, mock_client)

    tool_names = set(registry.tools.keys())
    expected_tools = {
        "list_highlights",
        "get_highlight",
        "create_highlight",
        "update_highlight",
        "delete_highlight",
    }

    assert expected_tools.issubset(tool_names), (
        f"Missing tools: {expected_tools - tool_names}"
    )


@pytest.mark.asyncio
async def test_list_highlights_tool(registry, mock_client, sample_highlight):
    """Test the list_highlights tool."""
    register_highlight_tools(registry, mock_client)

    mock_client.list_highlights.return_value = [sample_highlight]

    # Execute the tool
    tool = registry.tools["list_highlights"].coroutine
    result = await tool(456)  # bookmark_id

    # Verify result
    assert len(result) == 1
    assert result[0]["_id"] == 123
    assert result[0]["text"] == "Sample highlight text"

    # Verify client was called correctly
    mock_client.list_highlights.assert_called_once_with(456)


@pytest.mark.asyncio
async def test_get_highlight_tool(registry, mock_client, sample_highlight):
    """Test the get_highlight tool."""
    register_highlight_tools(registry, mock_client)

    mock_client.get_highlight.return_value = sample_highlight

    # Execute the tool
    tool = registry.tools["get_highlight"].coroutine
    result = await tool(123)  # highlight_id

    # Verify result
    assert result["_id"] == 123
    assert result["text"] == "Sample highlight text"

    # Verify client was called correctly
    mock_client.get_highlight.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_create_highlight_tool(registry, mock_client, sample_highlight):
    """Test the create_highlight tool."""
    from raindropio_mcp.models import HighlightCreate

    register_highlight_tools(registry, mock_client)

    mock_client.create_highlight.return_value = sample_highlight

    highlight_data = {
        "text": "New highlight text",
        "type": "highlight",
        "color": "blue",
    }

    # Execute the tool
    tool = registry.tools["create_highlight"].coroutine
    result = await tool(456, highlight_data)  # bookmark_id and payload

    # Verify the payload was properly validated as HighlightCreate
    mock_client.create_highlight.assert_called_once()
    args, kwargs = mock_client.create_highlight.call_args
    assert args[0] == 456  # bookmark_id
    assert isinstance(args[1], HighlightCreate)
    assert args[1].text == "New highlight text"

    # Verify result
    assert result["_id"] == 123


@pytest.mark.asyncio
async def test_update_highlight_tool(registry, mock_client, sample_highlight):
    """Test the update_highlight tool."""
    from raindropio_mcp.models import HighlightUpdate

    register_highlight_tools(registry, mock_client)

    mock_client.update_highlight.return_value = sample_highlight

    update_data = {"text": "Updated highlight text", "color": "red"}

    # Execute the tool
    tool = registry.tools["update_highlight"].coroutine
    result = await tool(123, update_data)  # highlight_id and payload

    # Verify the payload was properly validated as HighlightUpdate
    mock_client.update_highlight.assert_called_once()
    args, kwargs = mock_client.update_highlight.call_args
    assert args[0] == 123  # highlight_id
    assert isinstance(args[1], HighlightUpdate)
    assert args[1].text == "Updated highlight text"

    # Verify result
    assert result["_id"] == 123


@pytest.mark.asyncio
async def test_delete_highlight_tool(registry, mock_client):
    """Test the delete_highlight tool."""
    register_highlight_tools(registry, mock_client)

    mock_client.delete_highlight.return_value = True

    # Execute the tool
    tool = registry.tools["delete_highlight"].coroutine
    result = await tool(123)  # highlight_id

    # Verify result
    assert result["result"] is True
    assert result["highlight_id"] == 123

    # Verify client was called correctly
    mock_client.delete_highlight.assert_called_once_with(123)
