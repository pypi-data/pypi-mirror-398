"""Tests for RaindropClient import/export operations methods."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from raindropio_mcp.clients.raindrop_client import RaindropClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.models import ExportFormat, ImportSource
from raindropio_mcp.utils.exceptions import APIError


@pytest.fixture
def settings():
    """Sample settings for testing."""
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    return settings


@pytest.mark.asyncio
async def test_import_bookmarks(settings):
    """Test the import_bookmarks method."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "imported_count": 5,
            "skipped_count": 1,
            "errors": [],
            "collection_id": 123,
        }
    )

    import_source = ImportSource(format="netscape", source="browser")

    result = await client.import_bookmarks(import_source, collection_id=123)

    assert result.result is True
    assert result.imported_count == 5
    assert result.skipped_count == 1

    expected_payload = import_source.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "POST", "/import", params={"collection": 123}, json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_import_bookmarks_no_collection(settings):
    """Test the import_bookmarks method without specifying a collection."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={
            "result": True,
            "imported_count": 3,
            "skipped_count": 0,
            "errors": [],
            "collection_id": None,
        }
    )

    import_source = ImportSource(
        format="json", source="another_service", options={"merge_duplicates": True}
    )

    result = await client.import_bookmarks(import_source)

    assert result.result is True
    assert result.imported_count == 3

    expected_payload = import_source.model_dump(exclude_none=True, by_alias=True)
    client.get_json.assert_called_once_with(
        "POST", "/import", params={}, json_body=expected_payload
    )


@pytest.mark.asyncio
async def test_import_bookmarks_error(settings):
    """Test the import_bookmarks method with error response."""
    client = RaindropClient(settings)
    client.get_json = AsyncMock(
        return_value={"result": False, "error": "Import failed"}
    )

    import_source = ImportSource(format="netscape", source="browser")

    with pytest.raises(APIError):
        await client.import_bookmarks(import_source)


@pytest.mark.asyncio
async def test_export_bookmarks(settings):
    """Test the export_bookmarks method."""
    from unittest.mock import AsyncMock

    from httpx import Response

    # Mock the HTTP response
    response = Response(
        status_code=200,
        text='{"bookmarks": [{"title": "Test", "link": "https://example.com"}]}',
    )

    client = RaindropClient(settings)
    client.request = AsyncMock(return_value=response)

    export_format = ExportFormat(
        format="json", include_highlights=True, include_notes=False
    )

    result = await client.export_bookmarks(export_format, collection_id=123)

    assert result == '{"bookmarks": [{"title": "Test", "link": "https://example.com"}]}'

    expected_params = export_format.model_dump(exclude_none=True)
    expected_params["collection"] = 123
    client.request.assert_called_once_with("GET", "/export", params=expected_params)


@pytest.mark.asyncio
async def test_export_bookmarks_all_collections(settings):
    """Test the export_bookmarks method for all collections."""
    from unittest.mock import AsyncMock

    from httpx import Response

    # Mock the HTTP response
    response = Response(
        status_code=200,
        text=(
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">'
        ),
    )

    client = RaindropClient(settings)
    client.request = AsyncMock(return_value=response)

    export_format = ExportFormat(format="netscape", include_tags=True)

    result = await client.export_bookmarks(export_format)

    assert "DOCTYPE NETSCAPE-Bookmark-file-1" in result

    expected_params = export_format.model_dump(exclude_none=True)
    client.request.assert_called_once_with("GET", "/export", params=expected_params)
