"""Tests for RaindropClient highlight methods."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.models import Highlight, HighlightCreate, HighlightUpdate
from raindropio_mcp.utils.exceptions import APIError


@pytest.fixture
def settings():
    """Sample settings for testing."""
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    return settings


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
async def test_list_highlights(settings, sample_highlight):
    """Test the list_highlights method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "items": [sample_highlight.model_dump(by_alias=True)],
            "count": 1,
        }
    )

    result = await client.list_highlights(456)  # bookmark_id

    assert len(result) == 1
    assert result[0].id == 123
    assert result[0].text == "Sample highlight text"

    client.get_json.assert_called_once_with("GET", "/raindrop/456/highlights")


@pytest.mark.asyncio
async def test_list_highlights_error(settings):
    """Test the list_highlights method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "items": [], "error": "Not found"}
    )

    with pytest.raises(APIError):
        await client.list_highlights(456)


@pytest.mark.asyncio
async def test_get_highlight(settings, sample_highlight):
    """Test the get_highlight method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "item": sample_highlight.model_dump(by_alias=True),
        }
    )

    result = await client.get_highlight(123)  # highlight_id

    assert result.id == 123
    assert result.text == "Sample highlight text"

    client.get_json.assert_called_once_with("GET", "/highlight/123")


@pytest.mark.asyncio
async def test_get_highlight_error(settings):
    """Test the get_highlight method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(return_value={"result": False, "error": "Not found"})

    with pytest.raises(APIError):
        await client.get_highlight(123)


@pytest.mark.asyncio
async def test_create_highlight(settings, sample_highlight):
    """Test the create_highlight method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "item": sample_highlight.model_dump(by_alias=True),
        }
    )

    highlight_data = HighlightCreate(
        text="New highlight text", type="highlight", color="blue"
    )

    result = await client.create_highlight(456, highlight_data)  # bookmark_id and data

    assert result.id == 123
    assert result.text == "Sample highlight text"

    expected_payload = {
        "item": highlight_data.model_dump(exclude_none=True, by_alias=True)
    }
    client.get_json.assert_called_once_with(
        "POST", "/raindrop/456/highlights", json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_create_highlight_error(settings):
    """Test the create_highlight method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "error": "Creation failed"}
    )

    highlight_data = HighlightCreate(text="New highlight text", type="highlight")

    with pytest.raises(APIError):
        await client.create_highlight(456, highlight_data)


@pytest.mark.asyncio
async def test_update_highlight(settings, sample_highlight):
    """Test the update_highlight method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "item": sample_highlight.model_dump(by_alias=True),
        }
    )

    highlight_data = HighlightUpdate(text="Updated highlight text", color="red")

    result = await client.update_highlight(123, highlight_data)  # highlight_id and data

    assert result.id == 123
    assert (
        result.text == "Sample highlight text"
    )  # This reflects the response from the API

    expected_payload = {
        "item": highlight_data.model_dump(exclude_none=True, by_alias=True)
    }
    client.get_json.assert_called_once_with(
        "PUT", "/highlight/123", json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_update_highlight_error(settings):
    """Test the update_highlight method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "error": "Update failed"}
    )

    highlight_data = HighlightUpdate(text="Updated highlight text")

    with pytest.raises(APIError):
        await client.update_highlight(123, highlight_data)


@pytest.mark.asyncio
async def test_delete_highlight(settings):
    """Test the delete_highlight method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(return_value={"result": True})

    result = await client.delete_highlight(123)  # highlight_id

    assert result is True

    client.get_json.assert_called_once_with("DELETE", "/highlight/123")


@pytest.mark.asyncio
async def test_delete_highlight_error(settings):
    """Test the delete_highlight method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "error": "Deletion failed"}
    )

    with pytest.raises(APIError):
        await client.delete_highlight(123)
