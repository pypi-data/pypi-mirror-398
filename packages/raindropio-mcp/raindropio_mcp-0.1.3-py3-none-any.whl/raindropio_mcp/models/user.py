"""User accounts exposed by the Raindrop.io API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime


class User(BaseModel):
    """Authenticated account summary."""

    id: int = Field(..., alias="_id", serialization_alias="_id")
    name: str | None = None
    email: str | None = None
    pro: bool | None = None
    files: dict[str, Any] | None = None
    groups: list[dict[str, Any]] | None = None
    last_sync: datetime | None = Field(default=None, alias="lastSync")
    avatar: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class UserResponse(BaseModel):
    """Payload returned from /me."""

    result: bool
    user: User | None = None
    error: str | None = None


__all__ = ["User", "UserResponse"]
