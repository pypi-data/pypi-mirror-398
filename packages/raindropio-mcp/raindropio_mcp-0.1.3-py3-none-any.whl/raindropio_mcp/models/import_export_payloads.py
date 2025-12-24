"""Request payload models for Raindrop.io import/export operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ImportSource(BaseModel):
    """Information about the source of import."""

    format: str  # e.g., "netscape", "html", "json", "csv"
    source: str  # e.g., "browser", "another_service", "file"
    options: dict[str, Any] | None = None  # Additional import options


class ImportResult(BaseModel):
    """Result of an import operation."""

    result: bool
    imported_count: int
    skipped_count: int
    errors: list[dict[str, Any]]
    collection_id: int | None = None


class ExportFormat(BaseModel):
    """Specification for export format."""

    format: str  # e.g., "netscape", "html", "json", "csv", "markdown"
    include_highlights: bool = False
    include_notes: bool = False
    include_tags: bool = True
    collections_only: bool = False  # If True, only export collection structure


__all__ = ["ImportSource", "ImportResult", "ExportFormat"]
