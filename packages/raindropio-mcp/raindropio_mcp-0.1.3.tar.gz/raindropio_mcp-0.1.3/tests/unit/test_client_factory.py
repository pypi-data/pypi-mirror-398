"""Unit tests for the client factory module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from raindropio_mcp.clients.client_factory import (
    build_raindrop_client,
    raindrop_client_context,
)
from raindropio_mcp.clients.raindrop_client import RaindropClient


def test_build_raindrop_client():
    """Test building a Raindrop client with settings."""
    mock_settings = MagicMock()

    # Test with provided settings
    client = build_raindrop_client(mock_settings)
    assert isinstance(client, RaindropClient)
    # Can't easily test the settings were passed, but construction should succeed

    # Test with no settings (should call get_settings)
    with patch(
        "raindropio_mcp.clients.client_factory.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value = mock_settings
        build_raindrop_client()
        mock_get_settings.assert_called_once()


@pytest.mark.asyncio
async def test_raindrop_client_context():
    """Test the raindrop client context manager."""
    mock_settings = MagicMock()

    with patch(
        "raindropio_mcp.clients.client_factory.build_raindrop_client"
    ) as mock_build:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_build.return_value = mock_client

        # Use the context manager
        async with raindrop_client_context(mock_settings) as client:
            assert client == mock_client

        # Verify close was called
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_raindrop_client_context_with_none_settings():
    """Test the context manager with None settings."""
    with patch(
        "raindropio_mcp.clients.client_factory.get_settings"
    ) as mock_get_settings:
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        with patch(
            "raindropio_mcp.clients.client_factory.RaindropClient"
        ) as mock_raindrop_client:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            # Make RaindropClient constructor return our mock
            mock_raindrop_client.return_value = mock_client

            # Use the context manager with None settings
            async with raindrop_client_context(None) as client:
                assert client == mock_client
                # The function should call get_settings when settings is None
                mock_get_settings.assert_called_once()

            # Verify close was called
            mock_client.close.assert_called_once()
