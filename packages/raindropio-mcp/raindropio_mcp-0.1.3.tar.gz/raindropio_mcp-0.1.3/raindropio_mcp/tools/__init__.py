"""Register FastMCP tools for the Raindrop.io server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from raindropio_mcp.tools.account import register_account_tools
from raindropio_mcp.tools.batch import register_batch_tools
from raindropio_mcp.tools.bookmarks import register_bookmark_tools
from raindropio_mcp.tools.collections import register_collection_tools
from raindropio_mcp.tools.filters import register_filter_tools
from raindropio_mcp.tools.highlights import register_highlight_tools
from raindropio_mcp.tools.import_export import register_import_export_tools
from raindropio_mcp.tools.system import register_system_tools
from raindropio_mcp.tools.tags import register_tag_tools
from raindropio_mcp.tools.tool_registry import FastMCPToolRegistry

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from raindropio_mcp.clients.raindrop_client import RaindropClient


def register_all_tools(app: FastMCP, client: RaindropClient) -> FastMCPToolRegistry:
    """Register every MCP tool and return the registry for inspection."""

    registry = FastMCPToolRegistry(app)
    register_collection_tools(registry, client)
    register_bookmark_tools(registry, client)
    register_tag_tools(registry, client)
    register_highlight_tools(registry, client)
    register_batch_tools(registry, client)
    register_filter_tools(registry, client)
    register_import_export_tools(registry, client)
    register_account_tools(registry, client)
    register_system_tools(registry)
    return registry


__all__ = ["FastMCPToolRegistry", "register_all_tools"]
