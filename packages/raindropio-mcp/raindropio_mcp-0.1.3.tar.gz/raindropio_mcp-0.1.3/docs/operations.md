# Operations & Deployment

## Configuration

Set `RAINDROP_TOKEN` for all environments. Optional variables control timeouts,
connection pools, and HTTP transport. See the project README for the full table.

Use `.env` during development:

```
RAINDROP_TOKEN=your-token-here
RAINDROP_ENABLE_HTTP_TRANSPORT=true
RAINDROP_HTTP_PORT=3034
```

## Transport Modes

- **STDIO** (default) – ideal for local MCP clients such as desktops and CLI
  assistants.
- **Streamable HTTP** – enable with `--http` or `RAINDROP_ENABLE_HTTP_TRANSPORT`.
  The server listens on the configured host/port/path and exposes the FastMCP
  streamable endpoint.

## Logging

`configure_logging()` reads `settings.observability`:

- Structured JSON logging by default.
- Switch to classic log format by setting
  `RAINDROP_OBSERVABILITY_STRUCTURED_LOGGING=false`.
- Log level is controlled through `RAINDROP_OBSERVABILITY_LOG_LEVEL`.

## Shutdown Handling

The FastMCP app registers an `on_shutdown` handler to close the shared
`RaindropClient`. This prevents hanging sockets when assistants disconnect or
HTTP servers redeploy.

## Testing & Quality Gates

- Run `uv run pytest` before releases (coverage threshold 80%).
- `uv run crackerjack` bundles Ruff, mypy, pytest, and Bandit scans.
- Coverage HTML is written to `htmlcov/` for review.

## Deployment Tips

- For container deployments, forward the MCP protocol over stdio or run the
  HTTP transport behind a reverse proxy that terminates TLS.
- Avoid sharing tokens between assistants; generate dedicated Raindrop tokens
  with least privilege where possible.
- Rotate tokens periodically and keep them outside version control.
