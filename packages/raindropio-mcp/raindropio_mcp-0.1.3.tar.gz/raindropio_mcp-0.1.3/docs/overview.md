# Overview

The Raindrop.io MCP server is built with FastMCP and organised around a small
set of Python packages:

- `raindropio_mcp.config` – `RaindropSettings` for environment-driven
  configuration. The settings object is cached via `get_settings()` and validates
  the presence of `RAINDROP_TOKEN`.
- `raindropio_mcp.clients` – shared HTTP utilities plus `RaindropClient`, a thin
  wrapper over the Raindrop REST API with typed responses and error handling.
- `raindropio_mcp.tools` – tool registry, tool groups, and metadata for the
  Model Context Protocol. `register_all_tools` wires every tool into FastMCP.
- `raindropio_mcp.server` – creates the FastMCP application, registers tools, and
  exposes an `app` object for import by MCP clients or HTTP servers.
- `raindropio_mcp.main` – CLI entrypoint used by `python -m raindropio_mcp` and
  the `raindropio-mcp` console script.

## Tool Registration Flow

1. `create_app()` (server.py) instantiates a FastMCP app.
1. We build a shared `RaindropClient` using `build_raindrop_client()`.
1. `register_all_tools()` receives the app and client, registering tools grouped
   by category (collections, bookmarks, tags, account, system).
1. A shutdown hook closes the `RaindropClient` to release `httpx` resources.

Tools use the minimal wrappers in `raindropio_mcp.tools.*` to validate payloads
with Pydantic models (`BookmarkCreate`, `CollectionUpdate`, etc.) before calling
into `RaindropClient`.

## Data Models

`raindropio_mcp.models` mirrors the responses documented by Raindrop.io. Each
model honours nested identifiers (e.g. `_id` mapped via aliases) and optional
fields so the serialized output from tools matches the API closely.
