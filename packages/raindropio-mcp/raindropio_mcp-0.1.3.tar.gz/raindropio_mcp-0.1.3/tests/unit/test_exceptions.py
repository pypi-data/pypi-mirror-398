from __future__ import annotations

from raindropio_mcp.utils.exceptions import (
    APIError,
    RateLimitError,
)


def test_api_error_retryable() -> None:
    error = APIError("boom", status_code=503)
    assert error.is_retryable()
    assert error.is_server_error()


def test_rate_limit_backoff_default() -> None:
    error = RateLimitError("throttled")
    assert error.backoff_seconds() == 60
    error = RateLimitError("throttled", retry_after="5")
    assert error.backoff_seconds() == 5
