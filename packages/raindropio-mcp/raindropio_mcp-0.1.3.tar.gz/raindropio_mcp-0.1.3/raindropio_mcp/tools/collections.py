"""FastMCP tools wrapping Raindrop.io collection endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.models import CollectionCreate, CollectionUpdate
from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_collection_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register collection management MCP tools."""

    @registry.register(
        ToolMetadata(
            name="list_collections",
            description=(
                "List all Raindrop.io collections visible to the authenticated account."
            ),
            category=ToolCategory.COLLECTIONS,
            examples=[
                {
                    "args": [],
                    "description": (
                        "Retrieve metadata for folders to let "
                        "the user choose where to store bookmarks."
                    ),
                }
            ],
        )
    )
    async def list_collections() -> list[dict[str, Any]]:
        return [
            collection.model_dump(by_alias=True, exclude_none=True)
            for collection in await client.list_collections()
        ]

    @registry.register(
        ToolMetadata(
            name="get_collection",
            description="Fetch a single collection by numeric identifier.",
            category=ToolCategory.COLLECTIONS,
            examples=[
                {
                    "args": [12345],
                    "description": (
                        "Load collection metadata before presenting it to the user."
                    ),
                }
            ],
        )
    )
    async def get_collection(collection_id: int) -> dict[str, Any]:
        return (await client.get_collection(collection_id)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="create_collection",
            description="Create a new Raindrop.io collection (folder).",
            category=ToolCategory.COLLECTIONS,
            examples=[
                {
                    "args": [
                        {
                            "title": "AI Research",
                            "description": (
                                "All papers related to retrieval-augmented generation."
                            ),
                        }
                    ],
                    "description": "Create a dedicated folder for AI research links.",
                }
            ],
        )
    )
    async def create_collection(payload: dict[str, Any]) -> dict[str, Any]:
        model = CollectionCreate.model_validate(payload)
        return (await client.create_collection(model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="update_collection",
            description=(
                "Update collection metadata such as title, description, or color."
            ),
            category=ToolCategory.COLLECTIONS,
        )
    )
    async def update_collection(
        collection_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        model = CollectionUpdate.model_validate(payload)
        return (await client.update_collection(collection_id, model)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="delete_collection",
            description=(
                "Delete a collection by id. "
                "Bookmarks inside move to Uncategorized (id=0)."
            ),
            category=ToolCategory.COLLECTIONS,
        )
    )
    async def delete_collection(collection_id: int) -> dict[str, Any]:
        await client.delete_collection(collection_id)
        return {"result": True, "collection_id": collection_id}


__all__ = ["register_collection_tools"]
