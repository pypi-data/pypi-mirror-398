"""Pydantic models describing Raindrop.io entities."""

from raindropio_mcp.models.batch_payloads import (
    BatchDeleteBookmarks,
    BatchMoveBookmarks,
    BatchOperationResponse,
    BatchTagBookmarks,
    BatchUntagBookmarks,
    BatchUpdateBookmarks,
)
from raindropio_mcp.models.bookmark import Bookmark, BookmarkResponse, BookmarksResponse
from raindropio_mcp.models.collection import (
    Collection,
    CollectionRef,
    CollectionResponse,
    CollectionsResponse,
)
from raindropio_mcp.models.filter_payloads import (
    BookmarkFilter,
    FilteredBookmarksResponse,
)
from raindropio_mcp.models.highlight import (
    Highlight,
    HighlightCreate,
    HighlightResponse,
    HighlightsResponse,
    HighlightUpdate,
)
from raindropio_mcp.models.import_export_payloads import (
    ExportFormat,
    ImportResult,
    ImportSource,
)
from raindropio_mcp.models.payloads import (
    BookmarkCreate,
    BookmarkUpdate,
    CollectionCreate,
    CollectionUpdate,
    TagRename,
)
from raindropio_mcp.models.tag import Tag, TagsResponse
from raindropio_mcp.models.user import User, UserResponse

__all__ = [
    "Bookmark",
    "BookmarkCreate",
    "BookmarkResponse",
    "BookmarkUpdate",
    "BookmarksResponse",
    "BatchDeleteBookmarks",
    "BatchMoveBookmarks",
    "BatchOperationResponse",
    "BatchTagBookmarks",
    "BatchUntagBookmarks",
    "BatchUpdateBookmarks",
    "BookmarkFilter",
    "Collection",
    "CollectionCreate",
    "CollectionRef",
    "CollectionResponse",
    "CollectionUpdate",
    "CollectionsResponse",
    "ExportFormat",
    "FilteredBookmarksResponse",
    "Highlight",
    "HighlightCreate",
    "HighlightResponse",
    "HighlightUpdate",
    "HighlightsResponse",
    "ImportResult",
    "ImportSource",
    "Tag",
    "TagRename",
    "TagsResponse",
    "User",
    "UserResponse",
]


# Rebuild models to resolve forward references after all imports are complete
def _rebuild_models() -> None:
    """Rebuild models to resolve forward references across modules."""
    from datetime import datetime

    from raindropio_mcp.models.bookmark import (
        Bookmark,
        BookmarkResponse,
        BookmarksResponse,
    )
    from raindropio_mcp.models.collection import (
        Collection,
        CollectionRef,
        CollectionResponse,
        CollectionsResponse,
    )
    from raindropio_mcp.models.highlight import (
        Highlight,
        HighlightResponse,
        HighlightsResponse,
    )
    from raindropio_mcp.models.payloads import BookmarkUpdate
    from raindropio_mcp.models.user import User, UserResponse

    # Create namespace with all forward-referenced types
    types_namespace = {"CollectionRef": CollectionRef, "datetime": datetime}

    # Rebuild models that have forward references
    Bookmark.model_rebuild(_types_namespace=types_namespace)
    BookmarkResponse.model_rebuild(_types_namespace=types_namespace)
    BookmarksResponse.model_rebuild(_types_namespace=types_namespace)
    BookmarkUpdate.model_rebuild(_types_namespace=types_namespace)

    Collection.model_rebuild(_types_namespace=types_namespace)
    CollectionResponse.model_rebuild(_types_namespace=types_namespace)
    CollectionsResponse.model_rebuild(_types_namespace=types_namespace)

    Highlight.model_rebuild(_types_namespace=types_namespace)
    HighlightResponse.model_rebuild(_types_namespace=types_namespace)
    HighlightsResponse.model_rebuild(_types_namespace=types_namespace)

    User.model_rebuild(_types_namespace=types_namespace)
    UserResponse.model_rebuild(_types_namespace=types_namespace)


# Call rebuild after all imports are complete
_rebuild_models()
