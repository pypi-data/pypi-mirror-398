"""Tag-related MCP tools for Raindrop.io."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_tag_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register tag management tools."""

    @registry.register(
        ToolMetadata(
            name="list_tags",
            description="Return all tags with usage counts.",
            category=ToolCategory.TAGS,
        )
    )
    async def list_tags() -> list[dict[str, Any]]:
        tags = await client.list_tags()
        return [tag.model_dump(by_alias=True, exclude_none=True) for tag in tags]

    @registry.register(
        ToolMetadata(
            name="rename_tag",
            description="Rename a tag across all bookmarks.",
            category=ToolCategory.TAGS,
        )
    )
    async def rename_tag(old_tag: str, new_tag: str) -> dict[str, Any]:
        await client.rename_tag(old_tag, new_tag)
        return {"result": True, "from": old_tag, "to": new_tag}

    @registry.register(
        ToolMetadata(
            name="delete_tag",
            description="Delete a tag from every bookmark.",
            category=ToolCategory.TAGS,
        )
    )
    async def delete_tag(tag: str) -> dict[str, Any]:
        await client.delete_tag(tag)
        return {"result": True, "tag": tag}


__all__ = ["register_tag_tools"]
