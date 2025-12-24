"""Pydantic models describing Raindrop.io collections."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime


class CollectionRef(BaseModel):
    """Lightweight representation used in bookmark payloads."""

    id: int = Field(..., alias="$id", serialization_alias="$id")
    title: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class Collection(BaseModel):
    """Full Raindrop.io collection entity."""

    id: int = Field(..., alias="_id", serialization_alias="_id")
    title: str
    description: str | None = None
    slug: str | None = None
    created: datetime | None = None
    last_update: datetime | None = Field(default=None, alias="lastUpdate")
    parent_id: int | None = Field(default=None, alias="parentId")
    public: bool | None = None
    view: str | None = None
    sort: str | None = None
    count: int | None = None
    cover: str | None = None
    color: str | None = None
    permissions: dict[str, bool] | None = None

    model_config = ConfigDict(populate_by_name=True)


class CollectionResponse(BaseModel):
    """Standard response wrapper returned by Raindrop.io for collections."""

    result: bool
    collection: Collection | None = None
    error: str | None = None


class CollectionsResponse(BaseModel):
    """List response for collections endpoints."""

    result: bool
    items: list[Collection]
    count: int | None = None
    error: str | None = None


__all__ = [
    "Collection",
    "CollectionRef",
    "CollectionResponse",
    "CollectionsResponse",
]
