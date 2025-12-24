# Raindrop.io MCP Documentation

This directory collects focused guides for operating and extending the
Raindrop.io MCP server.

## Document Index

- **[overview.md](overview.md)** – architecture summary, tool registry layout,
  and lifecycle management.
- **[clients.md](clients.md)** – details about the `BaseHTTPClient`,
  `RaindropClient`, error handling, and pagination helpers.
- **[operations.md](operations.md)** – environment configuration, logging,
  HTTP transport, and deployment considerations for assistants.

Example MCP configuration files live at the repository root:
`example.mcp.json` and `example.mcp.dev.json`.

## Contributing

When adding new documentation:

1. Use descriptive kebab-case filenames.
1. Update this index with a short synopsis.
1. Link to related docs to help navigation.
1. Keep examples aligned with the current FastMCP tool set.
