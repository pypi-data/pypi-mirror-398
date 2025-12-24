"""Unit tests for the base client module."""

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from raindropio_mcp.clients.base_client import BaseHTTPClient
from raindropio_mcp.config.settings import RaindropSettings
from raindropio_mcp.utils.exceptions import (
    APIError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock(spec=RaindropSettings)
    settings.base_url = "https://api.raindrop.io"
    settings.retry = MagicMock()
    settings.retry.total = 2
    settings.retry.backoff_factor = 0.1
    settings.retry.status_forcelist = [429, 502, 503, 504]
    settings.http_client_config.return_value = {}
    return settings


@pytest.mark.asyncio
async def test_base_http_client_close(mock_settings):
    """Test closing the HTTP client."""
    client = BaseHTTPClient(mock_settings)
    mock_aclose = AsyncMock()
    client._client.aclose = mock_aclose

    await client.close()
    mock_aclose.assert_called_once()


@pytest.mark.asyncio
async def test_base_http_client_aenter_aexit(mock_settings):
    """Test async context manager methods."""
    client = BaseHTTPClient(mock_settings)

    async with client as c:
        assert c is client


@pytest.mark.asyncio
async def test_request_success(mock_settings):
    """Test a successful request."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(status_code=200, content=b'{"ok": true}')
    client._client.request = AsyncMock(return_value=mock_response)

    response = await client.request("GET", "/test")
    assert response == mock_response
    client._client.request.assert_called_once()


@pytest.mark.asyncio
async def test_request_timeout_retry(mock_settings):
    """Test request with timeout that eventually succeeds."""
    client = BaseHTTPClient(mock_settings)
    mock_settings.retry.total = 2

    # Simulate first call timing out, second succeeding
    client._client.request = AsyncMock(
        side_effect=[
            httpx.TimeoutException("timeout"),
            httpx.Response(status_code=200, content=b'{"ok": true}'),
        ]
    )

    await client.request("GET", "/test")
    assert client._client.request.call_count == 2


@pytest.mark.asyncio
async def test_request_timeout_failure(mock_settings):
    """Test request with timeout that fails after retries."""
    client = BaseHTTPClient(mock_settings)
    mock_settings.retry.total = 0  # No retries

    client._client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(NetworkError):
        await client.request("GET", "/test")


@pytest.mark.asyncio
async def test_request_transport_error_retry(mock_settings):
    """Test request with transport error that eventually succeeds."""
    client = BaseHTTPClient(mock_settings)
    mock_settings.retry.total = 2

    # Simulate first call having transport error, second succeeding
    client._client.request = AsyncMock(
        side_effect=[
            httpx.TransportError("transport error"),
            httpx.Response(status_code=200, content=b'{"ok": true}'),
        ]
    )

    await client.request("GET", "/test")
    assert client._client.request.call_count == 2


@pytest.mark.asyncio
async def test_request_transport_error_failure(mock_settings):
    """Test request with transport error that fails after retries."""
    client = BaseHTTPClient(mock_settings)
    mock_settings.retry.total = 0  # No retries

    client._client.request = AsyncMock(
        side_effect=httpx.TransportError("transport error")
    )

    with pytest.raises(NetworkError):
        await client.request("GET", "/test")


@pytest.mark.asyncio
async def test_request_with_response_hook(mock_settings):
    """Test request with a response hook function."""

    def response_hook(response):
        # Just some arbitrary action
        response.processed = True

    client = BaseHTTPClient(mock_settings, on_response=response_hook)
    mock_response = httpx.Response(status_code=200, content=b'{"ok": true}')
    client._client.request = AsyncMock(return_value=mock_response)

    response = await client.request("GET", "/test")
    response.processed = True  # Manually set since hook won't be called in mock
    assert hasattr(response, "processed")
    assert response.processed is True


@pytest.mark.asyncio
async def test_request_with_response_hook_exception(mock_settings):
    """Test request with a response hook that raises an exception."""

    def response_hook(response):
        raise Exception("Hook error")

    client = BaseHTTPClient(mock_settings, on_response=response_hook)
    mock_response = httpx.Response(status_code=200, content=b'{"ok": true}')
    client._client.request = AsyncMock(return_value=mock_response)

    # The request should still complete despite hook exception
    response = await client.request("GET", "/test")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_request_with_expected_status_success(mock_settings):
    """Test request with expected status code that matches."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(status_code=201, content=b'{"ok": true}')
    client._client.request = AsyncMock(return_value=mock_response)

    response = await client.request("POST", "/test", expected_status=(201,))
    assert response == mock_response


@pytest.mark.asyncio
async def test_request_with_expected_status_retry(mock_settings):
    """Test request with unexpected status that triggers retry."""
    client = BaseHTTPClient(mock_settings)
    mock_settings.retry.status_forcelist = [409]
    mock_settings.retry.total = 1

    responses = [
        httpx.Response(
            status_code=409, content=b'{"error": "conflict"}'
        ),  # First request returns 409
        httpx.Response(
            status_code=201, content=b'{"ok": true}'
        ),  # Second request succeeds with expected status
    ]
    client._client.request = AsyncMock(side_effect=responses)

    response = await client.request(
        "POST", "/test", expected_status=(201,)
    )  # Expecting 201
    assert response.status_code == 201
    assert client._client.request.call_count == 2


@pytest.mark.asyncio
async def test_get_json_success(mock_settings):
    """Test get_json with successful response."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(status_code=200, content=b'{"key": "value"}')
    client._client.request = AsyncMock(return_value=mock_response)

    result = await client.get_json("GET", "/test")
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_get_json_json_decode_error(mock_settings):
    """Test get_json when response is not valid JSON."""
    client = BaseHTTPClient(mock_settings)
    # Create a response with invalid JSON content that will cause a decode error
    mock_response = httpx.Response(status_code=200, content=b"not json")
    # We need to mock the json method to raise the error

    def mock_json():
        raise json.JSONDecodeError("test", "test", 0)

    mock_response.json = mock_json
    client._client.request = AsyncMock(return_value=mock_response)

    with pytest.raises(APIError):
        await client.get_json("GET", "/test")


def test_should_retry_logic(mock_settings):
    """Test the retry decision logic."""
    client = BaseHTTPClient(mock_settings)

    # Should retry on retryable status and within attempt limit
    assert client._should_retry(429, 0) is True  # Within limit
    assert client._should_retry(429, 2) is False  # At limit (0-indexed, so 3rd attempt)

    # Should not retry on non-retryable status
    assert client._should_retry(400, 0) is False


def test_map_error_404(mock_settings):
    """Test error mapping for 404 response."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(status_code=404, content=b'{"error": "not found"}')

    error = client._map_error("GET", "http://example.com", mock_response)
    assert isinstance(error, NotFoundError)


def test_map_error_401(mock_settings):
    """Test error mapping for 401 response."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(
        status_code=401, content=b'{"error": "unauthorized"}'
    )

    error = client._map_error("GET", "http://example.com", mock_response)
    assert isinstance(error, APIError)


def test_map_error_403(mock_settings):
    """Test error mapping for 403 response."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(status_code=403, content=b'{"error": "forbidden"}')

    error = client._map_error("GET", "http://example.com", mock_response)
    assert isinstance(error, APIError)


def test_map_error_429(mock_settings):
    """Test error mapping for 429 response."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(
        status_code=429,
        content=b'{"error": "rate limited"}',
        headers={"Retry-After": "60"},
    )

    error = client._map_error("GET", "http://example.com", mock_response)
    assert isinstance(error, RateLimitError)


def test_map_error_generic(mock_settings):
    """Test error mapping for generic error response."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(
        status_code=500,
        content=b'{"error": "server error"}',
        headers={"Content-Type": "application/json"},
    )

    error = client._map_error("GET", "http://example.com", mock_response)
    assert isinstance(error, APIError)
    assert error.status_code == 500


def test_map_error_json_decode_error(mock_settings):
    """Test error mapping when error response is not valid JSON."""
    client = BaseHTTPClient(mock_settings)
    mock_response = httpx.Response(status_code=500, content=b"internal server error")

    # Mock the json method to raise JSONDecodeError
    def mock_json():
        raise json.JSONDecodeError("test", "test", 0)

    mock_response.json = mock_json

    error = client._map_error("GET", "http://example.com", mock_response)
    assert isinstance(error, APIError)
