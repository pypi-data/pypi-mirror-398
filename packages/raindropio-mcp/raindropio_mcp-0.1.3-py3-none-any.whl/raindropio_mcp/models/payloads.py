"""Request payload models for Raindrop.io operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class CollectionCreate(BaseModel):
    title: str
    description: str | None = None
    parent_id: int | None = Field(default=None, alias="parentId")
    public: bool | None = None
    view: str | None = None
    sort: str | None = None
    color: str | None = None


class CollectionUpdate(CollectionCreate):
    pass


class BookmarkCreate(BaseModel):
    link: str
    title: str | None = None
    excerpt: str | None = None
    note: str | None = None
    tags: list[str] | None = None
    important: bool | None = None
    media: list[dict[str, Any]] | None = None
    please_parse: dict[str, Any] | None = Field(default=None, alias="pleaseParse")


class BookmarkUpdate(BookmarkCreate):
    collection_id: int | None = Field(default=None, alias="collectionId")
    created: datetime | None = None


class TagRename(BaseModel):
    from_tag: str = Field(..., alias="from")
    to_tag: str = Field(..., alias="to")


__all__ = [
    "BookmarkCreate",
    "BookmarkUpdate",
    "CollectionCreate",
    "CollectionUpdate",
    "TagRename",
]
