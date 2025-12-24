# Raindrop.io MCP Server

The Raindrop.io MCP Server is a Python/FastMCP application that exposes the Raindrop.io REST API to Model Context Protocol clients. Key domains include collections, bookmarks, tags, search, account information, highlights, batch operations, filters, and import/export functionality.

## Project Structure

- `raindropio_mcp/config` – environment-driven settings and helpers.
- `raindropio_mcp/auth` – simple bearer token provider.
- `raindropio_mcp/clients` – HTTP abstractions and the Raindrop.io API client.
- `raindropio_mcp/tools` – FastMCP tool definitions grouped by domain.
- `raindropio_mcp/server.py` – FastMCP app factory with tool registration.
- `raindropio_mcp/main.py` – CLI entrypoint for stdio or HTTP transport.
- `tests/` – Pytest suite with fixtures and coverage assertions.

## Setup

```bash
uv sync
export RAINDROP_TOKEN="your-token"
uv run python -m raindropio_mcp
```

Use `example.mcp.json` as a starting point for Claude Desktop or other MCP clients. Switch to HTTP transport with `--http` flags or corresponding env vars.

## Tooling & Quality

- `uv run ruff check --fix`
- `uv run mypy .`
- `uv run pytest --cov=. --cov-report=term-missing`
- `uv run crackerjack`

Coverage threshold is set to 80% in `pyproject.toml`.

## Key Modules To Explore

| Area | File | Notes |
|------|------|-------|
| Settings | `raindropio_mcp/config/settings.py` | Validates env vars and builds httpx config |
| HTTP Client | `raindropio_mcp/clients/base_client.py` | Retry logic and error mapping |
| API Facade | `raindropio_mcp/clients/raindrop_client.py` | Collection/bookmark/tag/highlights/batch operations |
| Tools | `raindropio_mcp/tools/*.py` | FastMCP tools with metadata |
| CLI | `raindropio_mcp/main.py` | Argument parsing, logging, transport selection |

## APIs Implemented

The server implements comprehensive functionality for:

1. **Collections**: List, get, create, update, delete collections
1. **Bookmarks**: List, search, get, create, update, delete bookmarks
1. **Tags**: List, rename, delete tags
1. **Account**: Get authenticated user profile
1. **Highlights**: List, get, create, update, delete highlights/annotations
1. **Batch Operations**: Move, delete, update, tag, untag multiple bookmarks at once
1. **Filters**: Apply complex filters to search and organize bookmarks
1. **Import/Export**: Import bookmarks from external sources and export in various formats

## Available Tools

| Category | Tool | Description |
|----------|------|-------------|
| Collections | `list_collections` | Fetch every collection visible to the token |
| | `get_collection` | Load metadata for a specific collection |
| | `create_collection` | Create a new collection/folder |
| | `update_collection` | Update title, description, or appearance |
| | `delete_collection` | Remove a collection (items move to Inbox) |
| Bookmarks | `list_bookmarks` | List bookmarks inside a collection with paging/search |
| | `search_bookmarks` | Full-text search across all collections |
| | `get_bookmark` | Retrieve a bookmark by id |
| | `create_bookmark` | Add a bookmark to a collection |
| | `update_bookmark` | Edit bookmark metadata or move between collections |
| | `delete_bookmark` | Delete a bookmark |
| Tags | `list_tags` | Fetch tag usage counts |
| | `rename_tag` | Rename a tag globally |
| | `delete_tag` | Remove a tag across all bookmarks |
| Highlights | `list_highlights` | List all highlights for a specific bookmark |
| | `get_highlight` | Fetch a single highlight by its ID |
| | `create_highlight` | Create a new highlight for a bookmark |
| | `update_highlight` | Update an existing highlight |
| | `delete_highlight` | Delete a highlight by its ID |
| Batch | `batch_move_bookmarks` | Move multiple bookmarks to a different collection |
| | `batch_delete_bookmarks` | Delete multiple bookmarks |
| | `batch_update_bookmarks` | Update multiple bookmarks with the same changes |
| | `batch_tag_bookmarks` | Add tags to multiple bookmarks |
| | `batch_untag_bookmarks` | Remove tags from multiple bookmarks |
| Filters | `apply_filters` | Apply various filters to search and organize bookmarks across all collections |
| | `get_filtered_bookmarks_by_collection` | Apply filters to bookmarks within a specific collection |
| Import/Export | `import_bookmarks` | Import bookmarks from an external source into Raindrop.io |
| | `export_bookmarks` | Export bookmarks from Raindrop.io in a specified format |
| Account | `get_account_profile` | Return the authenticated account profile |
| System | `ping` | Lightweight heartbeat including timestamp |

## Development Conventions

- Code follows Ruff linting standards with line length of 88
- Type checking is enforced with mypy
- All code must have comprehensive unit tests with 80%+ coverage
- Models use Pydantic for validation and serialization
- HTTP clients use httpx with retry logic
- FastMCP is used for MCP protocol implementation

## Future Enhancements

- Add optional caching layer for high-volume assistant sessions.
- Consider additional advanced filtering options.
- Potentially add sharing functionality when Raindrop exposes those endpoints.
