"""Tag models returned by Raindrop.io."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Tag(BaseModel):
    """Single tag summary."""

    tag: str = Field(..., alias="_id", serialization_alias="_id")
    count: int | None = None


class TagsResponse(BaseModel):
    """Response payload for tag listing."""

    result: bool
    items: list[Tag]
    count: int | None = None
    error: str | None = None


__all__ = ["Tag", "TagsResponse"]
