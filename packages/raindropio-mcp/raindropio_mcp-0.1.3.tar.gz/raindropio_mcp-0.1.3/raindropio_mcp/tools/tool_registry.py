"""Lightweight registry to organise Raindrop.io MCP tools."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastmcp import FastMCP


class ToolCategory(str, Enum):
    """High-level groupings for the Raindrop.io tools."""

    BOOKMARKS = "bookmarks"
    COLLECTIONS = "collections"
    TAGS = "tags"
    HIGHLIGHTS = "highlights"
    ACCOUNT = "account"
    SEARCH = "search"
    SYSTEM = "system"
    UTILS = "utils"


@dataclass(slots=True)
class ToolMetadata:
    """Metadata describing a registered tool."""

    name: str
    description: str
    category: ToolCategory
    examples: list[dict[str, Any]] = field(default_factory=list)
    is_async: bool = True


@dataclass(slots=True)
class ToolRegistration:
    metadata: ToolMetadata
    coroutine: Any  # Using Any to avoid complex generic typing issues
    decorated: (
        Any  # FunctionTool from FastMCP doesn't match Callable[P, Awaitable[R]] exactly
    )


class FastMCPToolRegistry:
    """Register tools with FastMCP while tracking metadata."""

    def __init__(self, app: FastMCP) -> None:
        self._app = app
        self._tools: dict[str, ToolRegistration] = {}

    def register(
        self, metadata: ToolMetadata
    ) -> Callable[[Any], Any]:  # Simplified type annotation to avoid complex generics
        def decorator(
            func: Any,
        ) -> Any:  # Simplified type annotation to avoid complex generics
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Raindrop.io MCP tools must be async functions")

            decorated = self._app.tool(
                name=metadata.name, description=metadata.description
            )(func)
            self._tools[metadata.name] = ToolRegistration(
                metadata=metadata,
                coroutine=func,
                decorated=decorated,
            )
            return decorated

        return decorator

    @property
    def tools(self) -> dict[str, ToolRegistration]:
        return self._tools.copy()


__all__ = ["FastMCPToolRegistry", "ToolCategory", "ToolMetadata", "ToolRegistration"]
