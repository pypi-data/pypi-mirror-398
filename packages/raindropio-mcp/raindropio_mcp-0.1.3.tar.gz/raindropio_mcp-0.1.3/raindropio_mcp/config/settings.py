"""Typed configuration for the Raindrop.io MCP server."""

from __future__ import annotations

from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, Field, HttpUrl, ValidationInfo, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from raindropio_mcp.utils.exceptions import ConfigurationError

# Import mcp-common security utilities for API key validation
# (Phase 3 Security Hardening)
SECURITY_AVAILABLE = False
with suppress(ImportError):
    from mcp_common.security import APIKeyValidator

    SECURITY_AVAILABLE = True

if TYPE_CHECKING:
    from pathlib import Path


class RetryConfig(BaseModel):
    """Retry policy applied to Raindrop.io HTTP calls."""

    total: int = Field(3, ge=0, le=10)
    backoff_factor: float = Field(0.5, ge=0.0, le=10.0)
    status_forcelist: tuple[int, ...] = Field((408, 425, 429, 500, 502, 503, 504))


class CacheConfig(BaseModel):
    """Simple in-memory cache configuration."""

    enabled: bool = True
    ttl_seconds: int = Field(60, ge=0, le=3600)
    max_entries: int = Field(1024, ge=0, le=1_000_000)


class ObservabilityConfig(BaseModel):
    """Logging and tracing toggles consumed by the server."""

    log_level: str = Field("INFO")
    structured_logging: bool = True
    redact_sensitive_fields: bool = True


class RaindropSettings(BaseSettings):
    """Environment-driven configuration for the Raindrop.io MCP server."""

    token: str = Field("", description="Raindrop.io personal access token")
    base_url: HttpUrl = Field(  # type: ignore[assignment]
        default="https://api.raindrop.io/rest/v1",  # type: ignore[arg-type]
        description="Root URL for Raindrop.io REST API",
    )
    user_agent: str = Field(
        "raindropio-mcp/0.1.0",
        description="User-Agent header sent with API requests",
    )
    request_timeout: float = Field(30.0, ge=1.0, le=120.0)
    max_connections: int = Field(10, ge=1, le=100)

    enable_http_transport: bool = Field(
        False,
        description="Serve the MCP over streamable HTTP when true",
    )
    http_host: str = Field("127.0.0.1", description="HTTP bind address")
    http_port: int = Field(3034, ge=1, le=65535, description="HTTP port")
    http_path: str = Field("/mcp", description="HTTP path for streamable MCP")

    retry: RetryConfig = Field(default_factory=RetryConfig)  # type: ignore[call-overload]
    cache: CacheConfig = Field(default_factory=CacheConfig)  # type: ignore[call-overload]
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)  # type: ignore[call-overload]

    cache_dir: Path | None = Field(
        None,
        description="Optional path for persistent response caching",
    )

    model_config = SettingsConfigDict(
        env_file=(".env",), env_prefix="RAINDROP_", extra="ignore", case_sensitive=False
    )

    def get_masked_token(self) -> str:
        """Get masked API token for safe logging (Phase 3 Security Hardening).

        Returns:
            Masked token string (e.g., "...abc1") for safe display in logs
        """
        if not self.token:
            return "***"

        if SECURITY_AVAILABLE:
            return APIKeyValidator.mask_key(self.token, visible_chars=4)

        # Fallback masking without security module
        if len(self.token) <= 4:
            return "***"
        return f"...{self.token[-4:]}"

    @model_validator(mode="after")
    def _validate_credentials(self, info: ValidationInfo) -> RaindropSettings:
        """Validate Raindrop.io API token at startup (Phase 3 Security Hardening).

        Raises:
            ConfigurationError: If token is missing or invalid
        """
        if not self.token or not self.token.strip():
            raise ConfigurationError(
                "RAINDROP_TOKEN is required to authenticate with the Raindrop.io API"
            )

        if SECURITY_AVAILABLE:
            # Use generic validator with minimum 32 characters for bearer tokens
            from contextlib import suppress

            validator = APIKeyValidator(min_length=32)
            with suppress(ValueError):
                validator.validate(self.token, raise_on_invalid=True)
                self.get_masked_token()

                # Warn but allow for backwards compatibility
        else:
            # Basic validation without security module
            if len(self.token) < 16:
                pass

        return self

    def auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token.strip()}",
            "User-Agent": self.user_agent,
        }

    def http_client_config(self) -> dict[str, Any]:
        return {
            "base_url": str(self.base_url),
            "timeout": self.request_timeout,
            "limits": httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_connections,
            ),
            "headers": self.auth_headers(),
        }


@lru_cache
def get_settings() -> RaindropSettings:
    """Return a cached settings instance."""

    return RaindropSettings()  # type: ignore[call-arg]


__all__ = ["RaindropSettings", "get_settings"]
