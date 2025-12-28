"""
Outline SDK for Python.

A beautiful, elegant SDK for the Outline API with rich models and type safety.
"""

from .client import OutlineClient
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    NotFoundError,
    OutlineError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    Attachment,
    Collection,
    Comment,
    Document,
)

__version__ = "0.9.0"
__all__ = [
    # Client
    "OutlineClient",
    # Exceptions
    "OutlineError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    # Models
    "Collection",
    "Document",
    "Attachment",
    "Comment",
]
