"""Comment model for Outline API."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import BaseModel

if TYPE_CHECKING:
    from ..client import OutlineClient


class Comment(BaseModel):
    """
    Represents a comment on an Outline document.

    Comments can be either on a selection of text or on the document itself.
    """

    @classmethod
    def create(
        cls,
        client: "OutlineClient",
        document_id: str,
        text: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        parent_comment_id: Optional[str] = None,
    ) -> "Comment":
        """
        Create a new comment or reply.

        Args:
            client: OutlineClient instance
            document_id: Document ID (UUID)
            text: Comment text in Markdown (either text or data required)
            data: Comment body as editor data (either text or data required)
            parent_comment_id: Parent comment ID for replies

        Returns:
            Created Comment instance
        """
        request_data: Dict[str, Any] = {"documentId": document_id}

        if text is not None:
            request_data["text"] = text
        if data is not None:
            request_data["data"] = data
        if parent_comment_id is not None:
            request_data["parentCommentId"] = parent_comment_id

        response = client.request("comments.create", request_data)
        return cls(client, response["data"])

    @classmethod
    def get(cls, client: "OutlineClient", id: str, include_anchor_text: bool = False) -> "Comment":
        """
        Retrieve a comment by ID.

        Args:
            client: OutlineClient instance
            id: Comment ID (UUID)
            include_anchor_text: Include the document text the comment is anchored to

        Returns:
            Comment instance
        """
        data = {
            "id": id,
            "includeAnchorText": include_anchor_text,
        }
        response = client.request("comments.info", data)
        return cls(client, response["data"])

    @classmethod
    def list(
        cls,
        client: "OutlineClient",
        document_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        include_anchor_text: bool = False,
        limit: int = 25,
        offset: int = 0,
        sort: str = "createdAt",
        direction: str = "DESC",
    ) -> List["Comment"]:
        """
        List comments with optional filters.

        Args:
            client: OutlineClient instance
            document_id: Filter by document
            collection_id: Filter by collection
            include_anchor_text: Include anchored text in responses
            limit: Maximum results (default: 25)
            offset: Pagination offset (default: 0)
            sort: Sort field (default: 'createdAt')
            direction: Sort direction ('ASC' or 'DESC')

        Returns:
            List of Comment instances
        """
        data: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "direction": direction,
            "includeAnchorText": include_anchor_text,
        }

        if document_id is not None:
            data["documentId"] = document_id
        if collection_id is not None:
            data["collectionId"] = collection_id

        response = client.request("comments.list", data)
        return [cls(client, item) for item in response["data"]]

    # Properties
    @property
    def document_id(self) -> str:
        """ID of the document this comment belongs to."""
        return self._data["documentId"]

    @property
    def parent_comment_id(self) -> Optional[str]:
        """ID of parent comment (if this is a reply)."""
        return self._data.get("parentCommentId")

    @property
    def data(self) -> Dict[str, Any]:
        """Editor data representing this comment."""
        return self._data.get("data", {})

    @property
    def anchor_text(self) -> Optional[str]:
        """Document text the comment is anchored to (if requested)."""
        return self._data.get("anchorText")

    @property
    def created_by(self) -> Optional[Dict[str, Any]]:
        """User who created this comment."""
        return self._data.get("createdBy")

    @property
    def updated_by(self) -> Optional[Dict[str, Any]]:
        """User who last updated this comment."""
        return self._data.get("updatedBy")

    # Methods
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update comment data.

        Args:
            data: New editor data for the comment
        """
        request_data = {
            "id": self.id,
            "data": data,
        }
        response = self._client.request("comments.update", request_data)
        self._data = response["data"]

    def delete(self) -> None:
        """
        Delete this comment.

        If this is a top-level comment, all replies will be deleted as well.
        """
        self._client.request("comments.delete", {"id": self.id})

    def refresh(self) -> None:
        """Reload comment data from the API."""
        response = self._client.request("comments.info", {"id": self.id})
        self._data = response["data"]

    def __repr__(self) -> str:
        """String representation of Comment."""
        return f"Comment(id={self.id!r}, document_id={self.document_id!r})"
