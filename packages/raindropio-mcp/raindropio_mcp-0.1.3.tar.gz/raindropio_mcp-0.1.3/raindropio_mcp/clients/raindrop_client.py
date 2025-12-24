"""High-level async client for the Raindrop.io REST API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from raindropio_mcp.clients.base_client import BaseHTTPClient
from raindropio_mcp.config.settings import RaindropSettings, get_settings
from raindropio_mcp.models import (
    BatchDeleteBookmarks,
    BatchMoveBookmarks,
    BatchOperationResponse,
    BatchTagBookmarks,
    BatchUntagBookmarks,
    BatchUpdateBookmarks,
    Bookmark,
    BookmarkCreate,
    BookmarkFilter,
    BookmarkResponse,
    BookmarksResponse,
    BookmarkUpdate,
    Collection,
    CollectionCreate,
    CollectionResponse,
    CollectionsResponse,
    CollectionUpdate,
    ExportFormat,
    FilteredBookmarksResponse,
    Highlight,
    HighlightCreate,
    HighlightResponse,
    HighlightsResponse,
    HighlightUpdate,
    ImportResult,
    ImportSource,
    Tag,
    TagsResponse,
    User,
    UserResponse,
)
from raindropio_mcp.utils.exceptions import APIError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PaginatedBookmarks:
    """Paginated list of bookmarks."""

    items: list[Bookmark]
    count: int
    collection_id: int | None
    page: int
    per_page: int


class RaindropClient(BaseHTTPClient):
    """Typed wrapper around the Raindrop.io API."""

    def __init__(self, settings: RaindropSettings | None = None) -> None:
        super().__init__(settings or get_settings())
        self._page_defaults = {"page": 0, "perpage": 50}

    async def get_me(self) -> User:
        payload = await self.get_json("GET", "/me")
        response = UserResponse.model_validate(payload)
        if not response.result or response.user is None:
            raise APIError("Unexpected response from /me", response_data=payload)
        return response.user

    async def list_collections(self) -> list[Collection]:
        payload = await self.get_json("GET", "/collections")
        response = CollectionsResponse.model_validate(payload)
        if not response.result:
            raise APIError("Failed to list collections", response_data=payload)
        return response.items

    async def get_collection(self, collection_id: int) -> Collection:
        payload = await self.get_json("GET", f"/collection/{collection_id}")
        response = CollectionResponse.model_validate(payload)
        if not response.result or response.collection is None:
            raise APIError(
                f"Collection {collection_id} not returned",
                response_data=payload,
            )
        return response.collection

    async def create_collection(self, data: CollectionCreate) -> Collection:
        payload = await self.get_json(
            "POST",
            "/collection",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        response = CollectionResponse.model_validate(payload)
        if not response.result or response.collection is None:
            raise APIError("Collection creation failed", response_data=payload)
        return response.collection

    async def update_collection(
        self, collection_id: int, data: CollectionUpdate
    ) -> Collection:
        payload = await self.get_json(
            "PUT",
            f"/collection/{collection_id}",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        response = CollectionResponse.model_validate(payload)
        if not response.result or response.collection is None:
            raise APIError(
                f"Collection {collection_id} update failed",
                response_data=payload,
            )
        return response.collection

    async def delete_collection(self, collection_id: int) -> bool:
        payload = await self.get_json("DELETE", f"/collection/{collection_id}")
        if not payload.get("result", False):
            raise APIError(
                f"Failed to delete collection {collection_id}",
                response_data=payload,
            )
        return True

    async def list_bookmarks(
        self,
        collection_id: int,
        *,
        page: int | None = None,
        per_page: int | None = None,
        search: str | None = None,
        sort: str | None = None,
    ) -> PaginatedBookmarks:
        params: dict[str, Any] = {
            "page": page if page is not None else self._page_defaults["page"],
            "perpage": per_page
            if per_page is not None
            else self._page_defaults["perpage"],
        }
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort

        payload = await self.get_json(
            "GET",
            f"/raindrops/{collection_id}",
            params=params,
        )
        response = BookmarksResponse.model_validate(payload)
        if not response.result:
            raise APIError(
                f"Failed to list bookmarks in collection {collection_id}",
                response_data=payload,
            )
        return PaginatedBookmarks(
            items=response.items,
            count=response.count or len(response.items),
            collection_id=response.collection_id,
            page=params["page"],
            per_page=params["perpage"],
        )

    async def search_bookmarks(
        self,
        query: str,
        *,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedBookmarks:
        params: dict[str, Any] = {
            "search": query,
            "page": page if page is not None else self._page_defaults["page"],
            "perpage": per_page
            if per_page is not None
            else self._page_defaults["perpage"],
        }
        payload = await self.get_json("GET", "/raindrops/search", params=params)
        response = BookmarksResponse.model_validate(payload)
        if not response.result:
            raise APIError("Bookmark search failed", response_data=payload)
        return PaginatedBookmarks(
            items=response.items,
            count=response.count or len(response.items),
            collection_id=response.collection_id,
            page=params["page"],
            per_page=params["perpage"],
        )

    async def get_bookmark(self, bookmark_id: int) -> Bookmark:
        payload = await self.get_json("GET", f"/raindrop/{bookmark_id}")
        response = BookmarkResponse.model_validate(payload)
        if not response.result or response.item is None:
            raise APIError(
                f"Failed to load bookmark {bookmark_id}",
                response_data=payload,
            )
        return response.item

    async def create_bookmark(
        self, collection_id: int, data: BookmarkCreate
    ) -> Bookmark:
        payload = await self.get_json(
            "POST",
            f"/raindrops/{collection_id}",
            json_body={"item": data.model_dump(exclude_none=True, by_alias=True)},
        )
        response = BookmarkResponse.model_validate(payload)
        if not response.result or response.item is None:
            raise APIError(
                "Bookmark creation failed",
                response_data=payload,
            )
        return response.item

    async def update_bookmark(self, bookmark_id: int, data: BookmarkUpdate) -> Bookmark:
        payload = await self.get_json(
            "PUT",
            f"/raindrop/{bookmark_id}",
            json_body={"item": data.model_dump(exclude_none=True, by_alias=True)},
        )
        response = BookmarkResponse.model_validate(payload)
        if not response.result or response.item is None:
            raise APIError(
                f"Bookmark {bookmark_id} update failed",
                response_data=payload,
            )
        return response.item

    async def delete_bookmark(self, bookmark_id: int) -> bool:
        payload = await self.get_json("DELETE", f"/raindrop/{bookmark_id}")
        if not payload.get("result", False):
            raise APIError(
                f"Failed to delete bookmark {bookmark_id}",
                response_data=payload,
            )
        return True

    async def list_tags(self) -> list[Tag]:
        payload = await self.get_json("GET", "/tags")
        response = TagsResponse.model_validate(payload)
        if not response.result:
            raise APIError("Failed to list tags", response_data=payload)
        return response.items

    async def rename_tag(self, source_tag: str, new_tag: str) -> bool:
        payload = await self.get_json(
            "PUT",
            f"/tag/{source_tag}",
            json_body={"tag": new_tag},
        )
        if not payload.get("result", False):
            raise APIError(
                f"Failed to rename tag '{source_tag}' to '{new_tag}'",
                response_data=payload,
            )
        return True

    async def delete_tag(self, tag: str) -> bool:
        payload = await self.get_json("DELETE", f"/tag/{tag}")
        if not payload.get("result", False):
            raise APIError(f"Failed to delete tag '{tag}'", response_data=payload)
        return True

    async def list_highlights(self, bookmark_id: int) -> list[Highlight]:
        """List all highlights for a specific bookmark."""
        payload = await self.get_json("GET", f"/raindrop/{bookmark_id}/highlights")
        response = HighlightsResponse.model_validate(payload)
        if not response.result:
            raise APIError(
                f"Failed to list highlights for bookmark {bookmark_id}",
                response_data=payload,
            )
        return response.items

    async def get_highlight(self, highlight_id: int) -> Highlight:
        """Get a single highlight by its ID."""
        payload = await self.get_json("GET", f"/highlight/{highlight_id}")
        response = HighlightResponse.model_validate(payload)
        if not response.result or response.item is None:
            raise APIError(
                f"Failed to get highlight {highlight_id}",
                response_data=payload,
            )
        return response.item

    async def create_highlight(
        self, bookmark_id: int, data: HighlightCreate
    ) -> Highlight:
        """Create a new highlight for a bookmark."""
        payload = await self.get_json(
            "POST",
            f"/raindrop/{bookmark_id}/highlights",
            json_body={"item": data.model_dump(exclude_none=True, by_alias=True)},
        )
        response = HighlightResponse.model_validate(payload)
        if not response.result or response.item is None:
            raise APIError(
                f"Failed to create highlight for bookmark {bookmark_id}",
                response_data=payload,
            )
        return response.item

    async def update_highlight(
        self, highlight_id: int, data: HighlightUpdate
    ) -> Highlight:
        """Update an existing highlight."""
        payload = await self.get_json(
            "PUT",
            f"/highlight/{highlight_id}",
            json_body={"item": data.model_dump(exclude_none=True, by_alias=True)},
        )
        response = HighlightResponse.model_validate(payload)
        if not response.result or response.item is None:
            raise APIError(
                f"Failed to update highlight {highlight_id}",
                response_data=payload,
            )
        return response.item

    async def delete_highlight(self, highlight_id: int) -> bool:
        """Delete a highlight."""
        payload = await self.get_json("DELETE", f"/highlight/{highlight_id}")
        if not payload.get("result", False):
            raise APIError(
                f"Failed to delete highlight {highlight_id}",
                response_data=payload,
            )
        return True

    async def batch_move_bookmarks(
        self, data: BatchMoveBookmarks
    ) -> BatchOperationResponse:
        """Move multiple bookmarks to a different collection."""
        payload = await self.get_json(
            "PUT",
            "/raindrops",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        if "processed_count" not in payload:
            raise APIError(
                f"Failed to move bookmarks {data.bookmark_ids} "
                f"to collection {data.collection_id}",
                response_data=payload,
            )
        return BatchOperationResponse.model_validate(payload)

    async def batch_delete_bookmarks(
        self, data: BatchDeleteBookmarks
    ) -> BatchOperationResponse:
        """Delete multiple bookmarks."""
        payload = await self.get_json(
            "DELETE",
            "/raindrops",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        if "processed_count" not in payload:
            raise APIError(
                f"Failed to delete bookmarks {data.bookmark_ids}",
                response_data=payload,
            )
        return BatchOperationResponse.model_validate(payload)

    async def batch_update_bookmarks(
        self, data: BatchUpdateBookmarks
    ) -> BatchOperationResponse:
        """Update multiple bookmarks with the same changes."""
        payload = await self.get_json(
            "PUT",
            "/raindrops",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        if "processed_count" not in payload:
            raise APIError(
                f"Failed to update bookmarks {data.bookmark_ids}",
                response_data=payload,
            )
        return BatchOperationResponse.model_validate(payload)

    async def batch_tag_bookmarks(
        self, data: BatchTagBookmarks
    ) -> BatchOperationResponse:
        """Add tags to multiple bookmarks."""
        payload = await self.get_json(
            "PUT",
            "/raindrops/tags",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        if "processed_count" not in payload:
            raise APIError(
                f"Failed to tag bookmarks {data.bookmark_ids} with tags {data.tags}",
                response_data=payload,
            )
        return BatchOperationResponse.model_validate(payload)

    async def batch_untag_bookmarks(
        self, data: BatchUntagBookmarks
    ) -> BatchOperationResponse:
        """Remove tags from multiple bookmarks."""
        payload = await self.get_json(
            "DELETE",
            "/raindrops/tags",
            json_body=data.model_dump(exclude_none=True, by_alias=True),
        )
        if "processed_count" not in payload:
            raise APIError(
                f"Failed to untag bookmarks {data.bookmark_ids} from tags {data.tags}",
                response_data=payload,
            )
        return BatchOperationResponse.model_validate(payload)

    async def apply_filters(
        self, filter_params: BookmarkFilter
    ) -> FilteredBookmarksResponse:
        """Apply filters to search and organize bookmarks."""
        params = filter_params.model_dump(exclude_none=True)

        # Convert complex filter parameters to appropriate format
        if "created_after" in params or "created_before" in params:
            # For date range filtering, we might need to use the search endpoint
            payload = await self.get_json("GET", "/raindrops/search", params=params)
        else:
            # For other filters, we might call the general search endpoint
            payload = await self.get_json("GET", "/raindrops/search", params=params)

        if not payload.get("result", False) and "items" not in payload:
            raise APIError(
                f"Failed to apply filters: {params}",
                response_data=payload,
            )

        return FilteredBookmarksResponse.model_validate(payload)

    async def get_filtered_bookmarks_by_collection(
        self, collection_id: int, filter_params: BookmarkFilter
    ) -> FilteredBookmarksResponse:
        """Apply filters to bookmarks within a specific collection."""
        params = filter_params.model_dump(exclude_none=True)

        payload = await self.get_json(
            "GET", f"/raindrops/{collection_id}", params=params
        )

        if not payload.get("result", False) and "items" not in payload:
            raise APIError(
                f"Failed to apply filters in collection {collection_id}: {params}",
                response_data=payload,
            )

        return FilteredBookmarksResponse.model_validate(payload)

    async def import_bookmarks(
        self, import_source: ImportSource, collection_id: int | None = None
    ) -> ImportResult:
        """Import bookmarks from an external source into Raindrop.io."""
        # This would typically involve uploading a file or providing
        # data in a specific format
        # The exact implementation would depend on the Raindrop.io API specifics
        params = {"collection": collection_id} if collection_id is not None else {}
        payload = await self.get_json(
            "POST",
            "/import",
            params=params,
            json_body=import_source.model_dump(exclude_none=True, by_alias=True),
        )

        if not payload.get("result", False) and "imported_count" not in payload:
            raise APIError(
                f"Failed to import bookmarks from source: {import_source.source}",
                response_data=payload,
            )

        return ImportResult.model_validate(payload)

    async def export_bookmarks(
        self, export_format: ExportFormat, collection_id: int | None = None
    ) -> str:
        """Export bookmarks from Raindrop.io in a specified format."""
        # This would typically return a file or data string in the requested format
        params = export_format.model_dump(exclude_none=True)
        if collection_id is not None:
            params["collection"] = collection_id

        # For export, we'll make a direct HTTP request to get the raw content
        # since export operations typically return the actual exported content
        # We use the request method to get the raw response, then extract the text
        response = await self.request("GET", "/export", params=params)
        return response.text


__all__ = ["PaginatedBookmarks", "RaindropClient"]
