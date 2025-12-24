"""Request payload models for Raindrop.io batch operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class BatchMoveBookmarks(BaseModel):
    """Payload for moving multiple bookmarks to a different collection."""

    bookmark_ids: list[int]
    collection_id: int


class BatchDeleteBookmarks(BaseModel):
    """Payload for deleting multiple bookmarks."""

    bookmark_ids: list[int]


class BatchUpdateBookmarks(BaseModel):
    """Payload for updating multiple bookmarks with the same changes."""

    bookmark_ids: list[int]
    title: str | None = None
    excerpt: str | None = None
    note: str | None = None
    tags: list[str] | None = None
    important: bool | None = None
    collection_id: int | None = None


class BatchTagBookmarks(BaseModel):
    """Payload for tagging multiple bookmarks with the same tags."""

    bookmark_ids: list[int]
    tags: list[str]


class BatchUntagBookmarks(BaseModel):
    """Payload for removing tags from multiple bookmarks."""

    bookmark_ids: list[int]
    tags: list[str]


class BatchOperationResponse(BaseModel):
    """Response for batch operations."""

    result: bool
    processed_count: int
    success_count: int
    error_count: int
    errors: list[dict[str, Any]] | None = None


__all__ = [
    "BatchMoveBookmarks",
    "BatchDeleteBookmarks",
    "BatchUpdateBookmarks",
    "BatchTagBookmarks",
    "BatchUntagBookmarks",
    "BatchOperationResponse",
]
