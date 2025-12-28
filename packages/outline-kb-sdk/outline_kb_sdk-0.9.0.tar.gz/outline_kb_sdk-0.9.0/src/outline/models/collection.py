"""Collection model for Outline API."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import BaseModel

if TYPE_CHECKING:
    from ..client import OutlineClient
    from .document import Document


class Collection(BaseModel):
    """
    Represents an Outline collection.

    Collections are groupings of documents that offer a way to structure
    information in a nested hierarchy with permissions.
    """

    @classmethod
    def create(
        cls,
        client: "OutlineClient",
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        permission: Optional[str] = None,
        sharing: bool = False,
    ) -> "Collection":
        """
        Create a new collection.

        Args:
            client: OutlineClient instance
            name: Collection name
            description: Optional description (markdown supported)
            icon: Optional icon (emoji or outline-icons package name)
            color: Optional hex color code (e.g., '#123123')
            permission: Optional permission level ('read' or 'read_write')
            sharing: Whether public sharing of documents is allowed

        Returns:
            Created Collection instance
        """
        data: Dict[str, Any] = {"name": name, "sharing": sharing}

        if description is not None:
            data["description"] = description
        if icon is not None:
            data["icon"] = icon
        if color is not None:
            data["color"] = color
        if permission is not None:
            data["permission"] = permission

        response = client.request("collections.create", data)
        return cls(client, response["data"])

    @classmethod
    def get(cls, client: "OutlineClient", id: str) -> "Collection":
        """
        Retrieve a collection by ID.

        Args:
            client: OutlineClient instance
            id: Collection ID (UUID)

        Returns:
            Collection instance
        """
        response = client.request("collections.info", {"id": id})
        return cls(client, response["data"])

    @classmethod
    def list(
        cls,
        client: "OutlineClient",
        query: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> List["Collection"]:
        """
        List all collections.

        Args:
            client: OutlineClient instance
            query: Optional search query to filter collections
            limit: Maximum number of results (default: 25)
            offset: Offset for pagination (default: 0)

        Returns:
            List of Collection instances
        """
        data: Dict[str, Any] = {"limit": limit, "offset": offset}

        if query is not None:
            data["query"] = query

        response = client.request("collections.list", data)
        return [cls(client, item) for item in response["data"]]

    # Properties
    @property
    def name(self) -> str:
        """Collection name."""
        return self._data["name"]

    @property
    def description(self) -> Optional[str]:
        """Collection description (may contain markdown)."""
        return self._data.get("description")

    @property
    def icon(self) -> Optional[str]:
        """Collection icon (emoji or icon name)."""
        return self._data.get("icon")

    @property
    def color(self) -> Optional[str]:
        """Collection color (hex code)."""
        return self._data.get("color")

    @property
    def url_id(self) -> str:
        """Short unique identifier (alternative to UUID)."""
        return self._data.get("urlId", "")

    @property
    def permission(self) -> Optional[str]:
        """Permission level for this collection."""
        return self._data.get("permission")

    @property
    def sharing(self) -> bool:
        """Whether public document sharing is enabled."""
        return self._data.get("sharing", False)

    @property
    def archived_at(self) -> Optional[datetime]:
        """When this collection was archived."""
        archived = self._data.get("archivedAt")
        return self._parse_datetime(archived) if archived else None

    # Methods
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        permission: Optional[str] = None,
        sharing: Optional[bool] = None,
    ) -> None:
        """
        Update collection properties.

        Args:
            name: New collection name
            description: New description
            icon: New icon
            color: New color
            permission: New permission level
            sharing: New sharing setting

        Raises:
            ValidationError: If validation fails
            AuthorizationError: If not authorized
        """
        data: Dict[str, Any] = {"id": self.id}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if icon is not None:
            data["icon"] = icon
        if color is not None:
            data["color"] = color
        if permission is not None:
            data["permission"] = permission
        if sharing is not None:
            data["sharing"] = sharing

        response = self._client.request("collections.update", data)
        self._data = response["data"]

    def delete(self) -> None:
        """
        Delete this collection and all its documents.

        Warning: This action cannot be undone!

        Raises:
            AuthorizationError: If not authorized
            NotFoundError: If collection doesn't exist
        """
        self._client.request("collections.delete", {"id": self.id})

    def add_document(
        self,
        title: str,
        text: Optional[str] = None,
        publish: bool = False,
        parent_document_id: Optional[str] = None,
        template: bool = False,
        template_id: Optional[str] = None,
    ) -> "Document":
        """
        Create a document in this collection.

        Args:
            title: Document title
            text: Document content (markdown)
            publish: Whether to publish immediately
            parent_document_id: ID of parent document for nesting
            template: Whether this is a template
            template_id: ID of template to use

        Returns:
            Created Document instance
        """
        from .document import Document

        return Document.create(
            self._client,
            title=title,
            collection_id=self.id,
            text=text,
            publish=publish,
            parent_document_id=parent_document_id,
            template=template,
            template_id=template_id,
        )

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Get the document structure (navigation tree) for this collection.

        Returns:
            List of navigation nodes with document structure
        """
        response = self._client.request("collections.documents", {"id": self.id})
        return response["data"]

    def add_user(self, user_id: str, permission: str = "read_write") -> Dict[str, Any]:
        """
        Add a user to this collection.

        Args:
            user_id: User ID (UUID)
            permission: Permission level ('read' or 'read_write')

        Returns:
            Dict with users and memberships
        """
        data = {
            "id": self.id,
            "userId": user_id,
            "permission": permission,
        }
        response = self._client.request("collections.add_user", data)
        return response["data"]

    def remove_user(self, user_id: str) -> None:
        """
        Remove a user from this collection.

        Args:
            user_id: User ID (UUID)
        """
        data = {
            "id": self.id,
            "userId": user_id,
        }
        self._client.request("collections.remove_user", data)

    def export(self, format: str = "outline-markdown") -> Dict[str, Any]:
        """
        Export this collection.

        Args:
            format: Export format ('outline-markdown', 'json', or 'html')

        Returns:
            File operation data with export status
        """
        data = {
            "id": self.id,
            "format": format,
        }
        response = self._client.request("collections.export", data)
        return response["data"]

    def refresh(self) -> None:
        """Reload collection data from the API."""
        response = self._client.request("collections.info", {"id": self.id})
        self._data = response["data"]

    def __repr__(self) -> str:
        """String representation of Collection."""
        return f"Collection(id={self.id!r}, name={self.name!r})"
