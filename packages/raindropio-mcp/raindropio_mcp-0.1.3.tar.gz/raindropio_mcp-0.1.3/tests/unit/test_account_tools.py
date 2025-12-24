"""Unit tests for the account tools module."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.models import User
from raindropio_mcp.tools.account import register_account_tools
from raindropio_mcp.tools.tool_registry import FastMCPToolRegistry


@pytest.mark.asyncio
async def test_register_account_tools():
    """Test registration and execution of account tools."""
    # Mock dependencies
    mock_client = AsyncMock(spec=RaindropClient)
    mock_user = User(
        id=123,
        email="test@example.com",
        name="Test User",
        avatar="https://example.com/avatar.jpg",
    )
    mock_client.get_me = AsyncMock(return_value=mock_user)

    # Create a FastMCP app instance to pass to the registry
    app = FastMCP(name="test", version="1.0")

    # Create tool registry
    registry = FastMCPToolRegistry(app)

    # Register tools
    register_account_tools(registry, mock_client)

    # Verify tool was registered
    assert "get_account_profile" in registry._tools

    # Execute the tool - access the coroutine function directly from the registered tool
    tool_registration = registry._tools["get_account_profile"]
    result = await tool_registration.coroutine()

    # Verify the result
    assert result["_id"] == 123  # Model serializes id as _id
    assert result["email"] == "test@example.com"
    assert result["name"] == "Test User"

    # Verify client method was called
    mock_client.get_me.assert_called_once()
