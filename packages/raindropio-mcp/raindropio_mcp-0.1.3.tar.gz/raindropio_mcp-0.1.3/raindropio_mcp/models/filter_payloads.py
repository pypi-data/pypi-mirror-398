"""Request payload models for Raindrop.io filter operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BookmarkFilter(BaseModel):
    """Filter parameters for bookmarks."""

    # Text search
    search: str | None = None

    # Tag-based filtering
    tags: list[str] | None = None

    # Date range filtering
    created_after: str | None = Field(None, description="ISO 8601 date string")
    created_before: str | None = Field(None, description="ISO 8601 date string")

    # Status-based filtering
    important: bool | None = None
    favorite: bool | None = None
    has_note: bool | None = None

    # Collection-based filtering
    collection_id: int | None = None

    # Domain filtering
    domain: str | None = None

    # Sort parameters
    sort: str | None = Field(
        None, description="Sorting field (e.g., 'created', 'title', 'lastUpdate')"
    )


class FilteredBookmarksResponse(BaseModel):
    """Response wrapper for filtered bookmarks."""

    result: bool
    items: list[dict[str, Any]]  # Using dict to allow flexible response from API
    count: int
    total: int
    page: int
    per_page: int
    filters_applied: list[str]


__all__ = ["BookmarkFilter", "FilteredBookmarksResponse"]
