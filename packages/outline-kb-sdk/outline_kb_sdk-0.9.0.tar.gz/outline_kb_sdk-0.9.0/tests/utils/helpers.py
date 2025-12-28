"""Helper functions for Outline SDK tests."""

from uuid import uuid4
from typing import Dict, Any, Optional


def unique_name(prefix: str = "Test") -> str:
    """
    Generate a unique name for test resources.
    
    Args:
        prefix: Prefix for the name
        
    Returns:
        Unique name with prefix and UUID suffix
    """
    return f"{prefix} {uuid4().hex[:8]}"


def assert_base_properties(obj: Any, expected_id: Optional[str] = None) -> None:
    """
    Assert that a model object has expected base properties.
    
    Args:
        obj: Model object to check
        expected_id: Expected ID (optional)
    """
    assert obj.id is not None
    assert len(obj.id) > 0
    
    if expected_id:
        assert obj.id == expected_id
    
    # Check timestamps
    assert obj.created_at is not None
    assert obj.updated_at is not None


def assert_collection_properties(collection: Any, name: Optional[str] = None) -> None:
    """
    Assert that a collection has expected properties.
    
    Args:
        collection: Collection object to check
        name: Expected name (optional)
    """
    assert_base_properties(collection)
    assert collection.name is not None
    
    if name:
        assert collection.name == name


def assert_document_properties(document: Any, title: Optional[str] = None) -> None:
    """
    Assert that a document has expected properties.
    
    Args:
        document: Document object to check
        title: Expected title (optional)
    """
    assert_base_properties(document)
    assert document.title is not None
    assert document.collection_id is not None
    
    if title:
        assert document.title == title


def assert_comment_properties(comment: Any) -> None:
    """
    Assert that a comment has expected properties.
    
    Args:
        comment: Comment object to check
    """
    assert_base_properties(comment)
    assert comment.document_id is not None


def assert_attachment_properties(attachment: Any, name: Optional[str] = None) -> None:
    """
    Assert that an attachment has expected properties.
    
    Args:
        attachment: Attachment object to check
        name: Expected name (optional)
    """
    assert_base_properties(attachment)
    assert attachment.name is not None
    assert attachment.content_type is not None
    assert attachment.size is not None
    
    if name:
        assert attachment.name == name


class ResourceCleaner:
    """
    Helper class to track and cleanup test resources.
    
    Usage:
        cleaner = ResourceCleaner()
        collection = Collection.create(...)
        cleaner.track_collection(collection)
        
        # At end of test
        cleaner.cleanup_all()
    """
    
    def __init__(self):
        self.collections: list = []
        self.documents: list = []
        self.comments: list = []
        self.attachments: list = []
    
    def track_collection(self, collection: Any) -> None:
        """Track a collection for cleanup."""
        self.collections.append(collection)
    
    def track_document(self, document: Any) -> None:
        """Track a document for cleanup."""
        self.documents.append(document)
    
    def track_comment(self, comment: Any) -> None:
        """Track a comment for cleanup."""
        self.comments.append(comment)
    
    def track_attachment(self, attachment: Any) -> None:
        """Track an attachment for cleanup."""
        self.attachments.append(attachment)
    
    def cleanup_all(self) -> None:
        """
        Cleanup all tracked resources.
        
        Order: comments -> documents -> collections -> attachments
        """
        # Comments first (they depend on documents)
        for comment in self.comments:
            try:
                comment.delete()
            except Exception:
                pass  # Ignore errors during cleanup
        
        # Documents (may depend on collections)
        for document in self.documents:
            try:
                document.delete(permanent=True)
            except Exception:
                pass
        
        # Collections
        for collection in self.collections:
            try:
                collection.delete()
            except Exception:
                pass
        
        # Attachments
        for attachment in self.attachments:
            try:
                attachment.delete()
            except Exception:
                pass
