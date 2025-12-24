# HTTP Clients

The `raindropio_mcp.clients` package contains two layers:

1. `BaseHTTPClient` – async helper that wraps `httpx.AsyncClient` with retry
   logic, error mapping, JSON parsing, and rate-limit awareness.
1. `RaindropClient` – typed facade over the Raindrop REST API, returning
   Pydantic models for each call.

## BaseHTTPClient

- Configured via `RaindropSettings.http_client_config()` which injects
  `httpx.Limits`, timeout, and authenticated headers.
- Retries network errors and selected response codes (408, 425, 429, 5xx).
- `_map_error` converts HTTP responses to domain exceptions (`NotFoundError`,
  `RateLimitError`, `APIError`).
- `get_json` ensures payloads are valid JSON and raises `APIError` when parsing
  fails.

Unit tests in `tests/unit/test_base_client.py` cover success paths, retries, and
error handling.

## RaindropClient

- Accepts a `RaindropSettings` instance (defaulting to `get_settings()`).
- Implements account (`get_me`), collection CRUD, bookmark operations, tag
  management, and search helpers.
- Paginated endpoints return the `PaginatedBookmarks` dataclass so callers retain
  page information, counts, and collection context.
- Exceptions bubble as `APIError` (or subclasses) making downstream handling
  straightforward inside FastMCP tools.

Tests in `tests/unit/test_raindrop_client.py` focus on payload validation and the
JSON envelope expectations used by the Raindrop API.
