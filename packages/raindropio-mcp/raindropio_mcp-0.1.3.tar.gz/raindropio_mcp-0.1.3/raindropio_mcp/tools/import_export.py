"""MCP tools for Raindrop.io import/export functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raindropio_mcp.models import ExportFormat, ImportSource
from raindropio_mcp.tools.tool_registry import (
    FastMCPToolRegistry,
    ToolCategory,
    ToolMetadata,
)

if TYPE_CHECKING:
    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_import_export_tools(
    registry: FastMCPToolRegistry,
    client: RaindropClient,
) -> None:
    """Register import/export tools."""

    @registry.register(
        ToolMetadata(
            name="import_bookmarks",
            description="Import bookmarks from an external source into Raindrop.io.",
            category=ToolCategory.UTILS,
            examples=[
                {
                    "args": [
                        {"format": "netscape", "source": "browser"},
                        12345,  # collection_id
                    ],
                    "description": (
                        "Import bookmarks from a browser export "
                        "file into a specific collection."
                    ),
                }
            ],
        )
    )
    async def import_bookmarks(
        payload: dict[str, Any], collection_id: int | None = None
    ) -> dict[str, Any]:
        model = ImportSource.model_validate(payload)
        return (await client.import_bookmarks(model, collection_id)).model_dump(
            by_alias=True, exclude_none=True
        )

    @registry.register(
        ToolMetadata(
            name="export_bookmarks",
            description="Export bookmarks from Raindrop.io in a specified format.",
            category=ToolCategory.UTILS,
        )
    )
    async def export_bookmarks(
        payload: dict[str, Any], collection_id: int | None = None
    ) -> str:
        model = ExportFormat.model_validate(payload)
        result = await client.export_bookmarks(model, collection_id)
        return result


__all__ = ["register_import_export_tools"]
