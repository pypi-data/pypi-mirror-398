from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from raindropio_mcp.clients.base_client import BaseHTTPClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.utils.exceptions import APIError, NotFoundError, RateLimitError


def create_response(
    status_code: int, payload: Any, headers: dict[str, Any] | None = None
) -> httpx.Response:
    """Create a proper httpx.Response mock for testing."""
    if headers is None:
        headers = {}

    if isinstance(payload, json.JSONDecodeError):
        # For JSON decode error tests, we need special handling
        response = httpx.Response(
            status_code=status_code,
            content="",  # Empty content for JSON decode error
            headers=headers,
        )
        # We'll need to mock the json method to raise the error

        response._real_json = response.json  # Store original method

        def mock_json():
            raise payload

        response.json = mock_json
        return response
    elif isinstance(payload, Exception):
        # For other exceptions, return a response with error content
        content = str(payload).encode()
        response = httpx.Response(
            status_code=status_code, content=content, headers=headers
        )
        # Mock the json method to handle the exception appropriately

        def mock_json():
            return {"error": str(payload)}

        response.json = mock_json
        return response
    else:
        # For normal payloads
        import json as json_module

        content = json_module.dumps(payload).encode()
        return httpx.Response(status_code=status_code, content=content, headers=headers)


@pytest.fixture
async def base_client(monkeypatch: pytest.MonkeyPatch) -> BaseHTTPClient:
    settings = RaindropSettings(token="test_token_1234567890abcdefghijklmnopqr")
    client = BaseHTTPClient(settings)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_request_success(
    monkeypatch: pytest.MonkeyPatch, base_client: BaseHTTPClient
) -> None:
    fake = create_response(200, {"ok": True})
    base_client._client.request = AsyncMock(return_value=fake)
    response = await base_client.request("GET", "/collections")
    assert response is fake


@pytest.mark.asyncio
async def test_request_handles_rate_limit(
    monkeypatch: pytest.MonkeyPatch, base_client: BaseHTTPClient
) -> None:
    fake = create_response(429, {"result": False}, headers={"Retry-After": "12"})
    base_client._client.request = AsyncMock(return_value=fake)
    with pytest.raises(RateLimitError) as exc:
        await base_client.request("GET", "/collections")
    assert exc.value.backoff_seconds() == 12


@pytest.mark.asyncio
async def test_request_retries_and_succeeds(
    monkeypatch: pytest.MonkeyPatch, base_client: BaseHTTPClient
) -> None:
    first = create_response(500, {"error": "server"})
    second = create_response(200, {"ok": True})
    base_client._client.request = AsyncMock(side_effect=[first, second])
    sleep = AsyncMock(return_value=None)
    monkeypatch.setattr(asyncio, "sleep", sleep)

    response = await base_client.request("GET", "/collections")
    assert response is second
    sleep.assert_awaited()


@pytest.mark.asyncio
async def test_get_json_not_found(
    monkeypatch: pytest.MonkeyPatch, base_client: BaseHTTPClient
) -> None:
    fake = create_response(404, {"error": "missing"})
    base_client._client.request = AsyncMock(return_value=fake)
    with pytest.raises(NotFoundError):
        await base_client.get_json("GET", "/raindrop/1")


@pytest.mark.asyncio
async def test_get_json_invalid_json(
    monkeypatch: pytest.MonkeyPatch, base_client: BaseHTTPClient
) -> None:
    error = create_response(200, json.JSONDecodeError("invalid", "", 0))
    base_client._client.request = AsyncMock(return_value=error)
    with pytest.raises(APIError):
        await base_client.get_json("GET", "/collections")
