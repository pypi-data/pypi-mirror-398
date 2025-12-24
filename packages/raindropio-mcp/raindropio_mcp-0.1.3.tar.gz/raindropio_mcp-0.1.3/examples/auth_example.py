"""Simple demonstration of configuring the Raindrop.io MCP settings."""

from __future__ import annotations

import os

from raindropio_mcp.config.settings import RaindropSettings


def main() -> None:
    token = os.getenv("RAINDROP_TOKEN")
    if not token:
        raise SystemExit("Set RAINDROP_TOKEN before running this example")

    RaindropSettings()


if __name__ == "__main__":
    main()
