"""Tests for RaindropClient batch operations methods."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.models import (
    BatchDeleteBookmarks,
    BatchMoveBookmarks,
    BatchOperationResponse,
    BatchTagBookmarks,
    BatchUntagBookmarks,
    BatchUpdateBookmarks,
)
from raindropio_mcp.utils.exceptions import APIError


@pytest.fixture
def settings():
    """Sample settings for testing."""
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    return settings


@pytest.fixture
def sample_batch_response():
    """Sample batch operation response for testing."""
    return BatchOperationResponse(
        result=True,
        processed_count=5,
        success_count=4,
        error_count=1,
        errors=[{"id": 123, "error": "Not found"}],
    )


@pytest.mark.asyncio
async def test_batch_move_bookmarks(settings, sample_batch_response):
    """Test the batch_move_bookmarks method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_batch_response.model_dump(by_alias=True)
    )

    batch_data = BatchMoveBookmarks(bookmark_ids=[111, 222, 333], collection_id=4)

    result = await client.batch_move_bookmarks(batch_data)

    assert result.result is True
    assert result.processed_count == 5
    assert result.success_count == 4
    assert result.error_count == 1

    expected_payload = batch_data.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "PUT", "/raindrops", json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_batch_move_bookmarks_error(settings):
    """Test the batch_move_bookmarks method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "error": "Operation failed"}
    )

    batch_data = BatchMoveBookmarks(bookmark_ids=[111, 222, 333], collection_id=4)

    with pytest.raises(APIError):
        await client.batch_move_bookmarks(batch_data)


@pytest.mark.asyncio
async def test_batch_delete_bookmarks(settings, sample_batch_response):
    """Test the batch_delete_bookmarks method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_batch_response.model_dump(by_alias=True)
    )

    batch_data = BatchDeleteBookmarks(bookmark_ids=[111, 222, 333])

    result = await client.batch_delete_bookmarks(batch_data)

    assert result.result is True
    assert result.processed_count == 5

    expected_payload = batch_data.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "DELETE", "/raindrops", json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_batch_update_bookmarks(settings, sample_batch_response):
    """Test the batch_update_bookmarks method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_batch_response.model_dump(by_alias=True)
    )

    batch_data = BatchUpdateBookmarks(
        bookmark_ids=[111, 222, 333], title="Updated Title", tags=["new-tag"]
    )

    result = await client.batch_update_bookmarks(batch_data)

    assert result.result is True
    assert result.success_count == 4

    expected_payload = batch_data.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "PUT", "/raindrops", json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_batch_tag_bookmarks(settings, sample_batch_response):
    """Test the batch_tag_bookmarks method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_batch_response.model_dump(by_alias=True)
    )

    batch_data = BatchTagBookmarks(
        bookmark_ids=[111, 222, 333], tags=["important", "readlater"]
    )

    result = await client.batch_tag_bookmarks(batch_data)

    assert result.result is True
    expected_payload = batch_data.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "PUT", "/raindrops/tags", json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_batch_untag_bookmarks(settings, sample_batch_response):
    """Test the batch_untag_bookmarks method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value=sample_batch_response.model_dump(by_alias=True)
    )

    batch_data = BatchUntagBookmarks(bookmark_ids=[111, 222, 333], tags=["old-tag"])

    result = await client.batch_untag_bookmarks(batch_data)

    assert result.result is True
    expected_payload = batch_data.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "DELETE", "/raindrops/tags", json_body=expected_payload
    )
