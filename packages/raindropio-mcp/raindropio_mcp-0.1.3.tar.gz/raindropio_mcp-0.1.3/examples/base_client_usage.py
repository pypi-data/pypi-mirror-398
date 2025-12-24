"""Example usage of the Raindrop.io HTTP client."""

from __future__ import annotations

import asyncio

from raindropio_mcp.clients.client_factory import raindrop_client_context
from raindropio_mcp.models import BookmarkCreate


async def main() -> None:
    async with raindrop_client_context() as client:
        await client.get_me()

        collections = await client.list_collections()
        for _col in collections:
            pass

        bookmark = await client.create_bookmark(
            0,
            BookmarkCreate(
                link="https://mcp.dev",
                title="MCP Specification",
                tags=["mcp", "docs"],
            ),
        )

        await client.delete_bookmark(bookmark.id)


if __name__ == "__main__":
    asyncio.run(main())
