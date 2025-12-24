"""Highlight models for Raindrop.io annotations and highlights."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime


class Highlight(BaseModel):
    """Highlight (annotation) associated with a bookmark."""

    id: int = Field(..., alias="_id", serialization_alias="_id")
    bookmark_id: int = Field(..., alias="raindropId")
    text: str
    type: str  # Could be "highlight", "note", "comment", etc.
    created: datetime | None = None
    last_update: datetime | None = Field(default=None, alias="lastUpdate")
    color: str | None = None
    position: int | None = (
        None  # Character position in the content where highlight starts
    )
    tags: list[str] = Field(default_factory=list)
    important: bool | None = None
    user: dict[str, Any] | None = None  # User information who created the highlight

    model_config = ConfigDict(populate_by_name=True)


class HighlightCreate(BaseModel):
    """Request payload for creating a highlight."""

    text: str
    type: str = "highlight"
    color: str | None = None
    position: int | None = None
    tags: list[str] | None = None
    important: bool | None = None


class HighlightUpdate(HighlightCreate):
    """Request payload for updating a highlight."""

    pass


class HighlightsResponse(BaseModel):
    """Response wrapper for multiple highlights."""

    result: bool
    items: list[Highlight]
    count: int | None = None
    error: str | None = None


class HighlightResponse(BaseModel):
    """Response wrapper for a single highlight."""

    result: bool
    item: Highlight | None = None
    error: str | None = None


__all__ = [
    "Highlight",
    "HighlightCreate",
    "HighlightUpdate",
    "HighlightResponse",
    "HighlightsResponse",
]
