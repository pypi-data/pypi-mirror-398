"""Base model class for all Outline API resources."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..client import OutlineClient


class BaseModel:
    """Base class for all Outline API models."""

    def __init__(self, client: "OutlineClient", data: Dict[str, Any]):
        """
        Initialize a model with API client and data.

        Args:
            client: OutlineClient instance for making API requests
            data: Raw data dictionary from API response
        """
        self._client = client
        self._data = data

    @property
    def id(self) -> str:
        """Unique identifier for this resource."""
        return self._data["id"]

    @property
    def created_at(self) -> datetime:
        """When this resource was created."""
        return self._parse_datetime(self._data["createdAt"])

    @property
    def updated_at(self) -> datetime:
        """When this resource was last updated."""
        return self._parse_datetime(self._data["updatedAt"])

    @property
    def deleted_at(self) -> Optional[datetime]:
        """When this resource was deleted (if applicable)."""
        deleted = self._data.get("deletedAt")
        return self._parse_datetime(deleted) if deleted else None

    def _parse_datetime(self, dt_string: str) -> datetime:
        """
        Parse ISO 8601 datetime string to datetime object.

        Args:
            dt_string: ISO 8601 formatted datetime string

        Returns:
            Parsed datetime object
        """
        # Handle both formats: with and without 'Z'
        # Replace 'Z' with '+00:00' for Python's datetime parser
        if dt_string.endswith("Z"):
            dt_string = dt_string[:-1] + "+00:00"
        return datetime.fromisoformat(dt_string)

    def refresh(self) -> None:
        """
        Reload this resource's data from the API.

        Subclasses should implement this to fetch fresh data.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement refresh()")

    def to_dict(self) -> Dict[str, Any]:
        """
        Return the raw data dictionary from the API.

        Returns:
            Dictionary containing all the resource's data
        """
        return self._data.copy()

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(id={self.id!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID and type."""
        if not isinstance(other, BaseModel):
            return False
        return self.id == other.id and type(self) == type(other)

    def __hash__(self) -> int:
        """Hash based on ID and type."""
        return hash((self.id, type(self)))
