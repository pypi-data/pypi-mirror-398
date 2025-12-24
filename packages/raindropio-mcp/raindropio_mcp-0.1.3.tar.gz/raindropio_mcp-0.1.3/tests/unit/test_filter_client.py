"""Tests for RaindropClient filter operations methods."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.models import BookmarkFilter, FilteredBookmarksResponse
from raindropio_mcp.utils.exceptions import APIError


@pytest.fixture
def settings():
    """Sample settings for testing."""
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    return settings


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
async def test_apply_filters(settings, sample_filtered_response):
    """Test the apply_filters method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_filtered_response.model_dump(by_alias=True)
    )

    filter_params = BookmarkFilter(
        search="AI research", tags=["important", "ai"], important=True
    )

    result = await client.apply_filters(filter_params)

    assert result.result is True
    assert len(result.items) == 1
    assert result.filters_applied == ["important", "tag:ai"]

    expected_params = filter_params.model_dump(exclude_none=True)
    client.get_json.assert_called_once_with(
        "GET", "/raindrops/search", params=expected_params
    )


@pytest.mark.asyncio
async def test_apply_filters_error(settings):
    """Test the apply_filters method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "error": "Filter operation failed"}
    )

    filter_params = BookmarkFilter(search="AI research")

    with pytest.raises(APIError):
        await client.apply_filters(filter_params)


@pytest.mark.asyncio
async def test_get_filtered_bookmarks_by_collection(settings, sample_filtered_response):
    """Test the get_filtered_bookmarks_by_collection method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_filtered_response.model_dump(by_alias=True)
    )

    filter_params = BookmarkFilter(tags=["important"], favorite=True)

    result = await client.get_filtered_bookmarks_by_collection(5, filter_params)

    assert result.result is True
    assert len(result.items) == 1

    expected_params = filter_params.model_dump(exclude_none=True)
    client.get_json.assert_called_once_with(
        "GET", "/raindrops/5", params=expected_params
    )
