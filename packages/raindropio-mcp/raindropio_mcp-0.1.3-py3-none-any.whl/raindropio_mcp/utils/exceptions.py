"""Domain-specific exception hierarchy for the Raindrop.io MCP server."""

from __future__ import annotations

from typing import Any


class RaindropError(Exception):
    """Base exception for all Raindrop.io MCP errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:  # pragma: no cover - delegated to subclass repr
        if self.details:
            return f"{self.message} (details={self.details})"
        return self.message


class ConfigurationError(RaindropError):
    """Raised when required configuration or credentials are missing."""


class AuthenticationError(RaindropError):
    """Raised when Raindrop.io rejects our credentials."""


class AuthorizationError(RaindropError):
    """Raised when the API denies access to a resource."""


class ValidationError(RaindropError):
    """Raised when caller input fails local validation."""


class APIError(RaindropError):
    """Generic wrapper for HTTP API failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: Any | None = None,
        headers: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.status_code = status_code
        self.response_data = response_data
        self.headers = headers or {}

    def is_client_error(self) -> bool:
        return self.status_code is not None and 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        return self.status_code is not None and self.status_code >= 500

    def is_retryable(self) -> bool:
        if self.status_code is None:
            return True
        if self.is_server_error():
            return True
        return self.status_code in {408, 412, 425, 429}


class NotFoundError(APIError):
    """Raised when a resource cannot be located in the Raindrop.io API."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 404,
        response_data: Any = None,
        headers: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            response_data=response_data,
            headers=headers or {},
            details=details,
        )


class RateLimitError(APIError):
    """Raised when the Raindrop.io API throttles our requests."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: int | float | None = None,
        limit: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int = 429,
        response_data: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            response_data=response_data,
            headers=headers or {},
            details=details,
        )
        self.retry_after = retry_after
        self.limit = limit

    def backoff_seconds(self, default: int = 60) -> int:
        if self.retry_after is None:
            return default
        try:
            return int(float(self.retry_after))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return default


class NetworkError(APIError):
    """Raised when networking libraries fail before reaching the API."""


class SerializationError(RaindropError):
    """Raised when we fail to convert data to or from API payloads."""


__all__ = [
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "NetworkError",
    "NotFoundError",
    "RaindropError",
    "RateLimitError",
    "SerializationError",
    "ValidationError",
]
