# Raindrop.io MCP Server

[![Code style: crackerjack](https://img.shields.io/badge/code%20style-crackerjack-000042)](https://github.com/lesleslie/crackerjack)
[![Python: 3.13+](https://img.shields.io/badge/python-3.13%2B-green)](https://www.python.org/downloads/)
![Coverage](https://img.shields.io/badge/coverage-88.8%25-brightgreen)

FastMCP-based Model Context Protocol server that exposes the Raindrop.io API to
AI assistants. The server focuses on rich bookmark, collection, tag, highlights,
filters, batch operations, and account operations while following the latest
Raindrop REST documentation.

## Key Capabilities

- **Modern Raindrop API coverage** – typed models for collections, bookmarks,
  tags, highlights/annotations, account profile, and cross-collection search.
- **Batch operations** – tools for moving, deleting, updating, tagging, and
  untagging multiple bookmarks at once.
- **Advanced filtering** – tools for applying complex filters to search and
  organize bookmarks.
- **Import/Export** – functionality to import bookmarks from external sources
  and export them in various formats.
- **FastMCP tooling** – tools registered with rich metadata so assistants can
  browse, filter, create, update, and delete Raindrop entities in natural flows.
- **Typed configuration** – `RaindropSettings` validates environment variables
  and exposes toggles for stdio or streamable HTTP transports.
- **Reusable HTTP client** – retry-aware, rate-limit friendly `RaindropClient`
  with explicit error mapping and pagination helpers.
- **Tested implementation** – pytest suite covering the client, tools, and
  entrypoints with coverage guardrails (≥80%).

## Getting Started

### Prerequisites

- Python 3.13 (managed by [uv](https://docs.astral.sh/uv/))
- A Raindrop.io [personal access token](https://app.raindrop.io/settings/integrations)

### Installation

```bash
# clone and install dependencies
git clone https://github.com/lesleslie/raindropio-mcp.git
cd raindropio-mcp
uv sync
```

### Configuration

Set the `RAINDROP_TOKEN` environment variable before launching the server. You
can export the value or place it inside a `.env` file next to the project root.

```bash
export RAINDROP_TOKEN="your-raindrop-token"
```

Optional environment variables (all prefixed with `RAINDROP_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `RAINDROP_USER_AGENT` | `raindropio-mcp/0.1.0` | HTTP user agent header |
| `RAINDROP_REQUEST_TIMEOUT` | `30.0` | Seconds before an HTTP request times out |
| `RAINDROP_MAX_CONNECTIONS` | `10` | Maximum concurrent HTTP connections |
| `RAINDROP_ENABLE_HTTP_TRANSPORT` | `false` | Enable streamable HTTP transport |
| `RAINDROP_HTTP_HOST` | `127.0.0.1` | HTTP bind host when enabled |
| `RAINDROP_HTTP_PORT` | `3034` | HTTP port when enabled |
| `RAINDROP_HTTP_PATH` | `/mcp` | HTTP path for the MCP endpoint |

### Running the Server

```bash
# stdio (default)
uv run python -m raindropio_mcp

# or via the console script
uv run raindropio-mcp

# HTTP mode
uv run python -m raindropio_mcp --http --http-port 3034
```

`example.mcp.json` and `example.mcp.dev.json` demonstrate how to wire the server
into MCP-enabled clients such as Claude Desktop or PowerShell integrations.

## Available Tools

All tools are declared in `raindropio_mcp/tools` and registered automatically by
`register_all_tools`.

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
| Tags | `list_tags` | Fetch tag usage counts |
| | `rename_tag` | Rename a tag globally |
| | `delete_tag` | Remove a tag across all bookmarks |
| Account | `get_account_profile` | Return the authenticated account profile |
| System | `ping` | Lightweight heartbeat including timestamp |

Each tool returns JSON-serialisable payloads closely matching the official API
shapes so downstream agents can consume data without additional parsing.

## Observability & Shutdown

Logging defaults to structured JSON. Set `RAINDROP_OBSERVABILITY_STRUCTURED_LOGGING=false`
(or override via `.env`) to switch to classic text formatting.

The FastMCP app registers a shutdown hook that gracefully closes the shared
`RaindropClient`, ensuring HTTP connection pools are released when the server
terminates.

## Development Workflow

```bash
# lint + type-check + tests + security
uv run crackerjack

# individual tasks
uv run ruff check --fix
uv run mypy .
uv run pytest --cov=. --cov-report=term-missing
```

Test fixtures live in `tests/` and automatically inject `RAINDROP_TOKEN` so unit
execution never reaches the live API.

## Roadmap

- Add optional caching middleware for high-volume assistant workflows
- Implement sharing functionality when Raindrop exposes those endpoints
- Enhance filter capabilities with additional options

Contributions and feature suggestions are welcome via issues or pull requests.
