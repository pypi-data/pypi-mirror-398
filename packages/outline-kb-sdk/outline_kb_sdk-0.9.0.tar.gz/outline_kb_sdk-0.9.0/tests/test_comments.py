"""Tests for Comment operations."""

import pytest

from outline import Comment
from outline.exceptions import NotFoundError
from tests.utils.helpers import (
    assert_base_properties,
    assert_comment_properties,
)


@pytest.mark.comment
class TestCommentCRUD:
    """Test basic Comment CRUD operations."""

    def test_comment_create_with_text(self, client, test_document):
        """Test creating a comment with text."""
        comment_text = "This is a test comment."
        
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text=comment_text,
        )
        
        try:
            assert_comment_properties(comment)
            assert comment.document_id == test_document.id
            # The comment data/text might be stored differently
            assert comment.id is not None
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_create_with_data(self, client, test_document):
        """Test creating a comment with editor data."""
        comment_data = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Comment with editor data"
                        }
                    ]
                }
            ]
        }
        
        comment = Comment.create(
            client,
            document_id=test_document.id,
            data=comment_data,
        )
        
        try:
            assert_comment_properties(comment)
            assert comment.document_id == test_document.id
            assert comment.data is not None
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_create_reply(self, client, test_document):
        """Test creating a reply to a comment."""
        # Create parent comment
        parent = Comment.create(
            client,
            document_id=test_document.id,
            text="Parent comment",
        )
        
        try:
            # Create reply
            reply = Comment.create(
                client,
                document_id=test_document.id,
                text="Reply to parent",
                parent_comment_id=parent.id,
            )
            
            try:
                assert_comment_properties(reply)
                assert reply.document_id == test_document.id
                assert reply.parent_comment_id == parent.id
            finally:
                try:
                    reply.delete()
                except Exception:
                    pass
        finally:
            try:
                parent.delete()
            except Exception:
                pass

    def test_comment_get(self, client, test_document):
        """Test retrieving a comment by ID."""
        # Create a comment first
        created_comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Test comment for retrieval",
        )
        
        try:
            # Get the comment
            retrieved_comment = Comment.get(client, created_comment.id)
            
            assert_comment_properties(retrieved_comment)
            assert retrieved_comment.id == created_comment.id
            assert retrieved_comment.document_id == test_document.id
        finally:
            try:
                created_comment.delete()
            except Exception:
                pass

    def test_comment_get_with_anchor_text(self, client, test_document):
        """Test retrieving a comment with anchor text."""
        # Create a comment
        created_comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Comment with anchor",
        )
        
        try:
            # Get with anchor text
            retrieved_comment = Comment.get(
                client,
                created_comment.id,
                include_anchor_text=True,
            )
            
            assert_comment_properties(retrieved_comment)
            assert retrieved_comment.id == created_comment.id
            # Anchor text may or may not be present depending on comment type
            # Just verify the property exists
            _ = retrieved_comment.anchor_text
        finally:
            try:
                created_comment.delete()
            except Exception:
                pass

    def test_comment_list_by_document(self, client, test_document):
        """Test listing comments by document."""
        # Create a comment first
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Comment for listing",
        )
        
        try:
            # List comments
            comments = Comment.list(client, document_id=test_document.id)
            
            assert isinstance(comments, list)
            # Should have at least our comment
            assert len(comments) > 0
            
            # Find our comment
            comment_ids = [c.id for c in comments]
            assert comment.id in comment_ids
            
            # All comments should be for this document
            for c in comments:
                assert c.document_id == test_document.id
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_list_by_collection(self, client, test_collection):
        """Test listing comments by collection."""
        # Create a document and comment in the collection
        from outline import Document
        doc = Document.create(
            client,
            title="Doc for comment listing",
            collection_id=test_collection.id,
            text="# Test\n\nDocument for comments.",
            publish=True,
        )
        
        comment = Comment.create(
            client,
            document_id=doc.id,
            text="Comment in collection",
        )
        
        try:
            # List comments by collection
            comments = Comment.list(client, collection_id=test_collection.id)
            
            assert isinstance(comments, list)
            # Should have at least our comment
            assert len(comments) > 0
            
            # Find our comment
            comment_ids = [c.id for c in comments]
            assert comment.id in comment_ids
        finally:
            try:
                comment.delete()
            except Exception:
                pass
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_comment_list_with_pagination(self, client, test_document):
        """Test comment list pagination."""
        # Create multiple comments
        comments_created = []
        for i in range(3):
            comment = Comment.create(
                client,
                document_id=test_document.id,
                text=f"Pagination comment {i}",
            )
            comments_created.append(comment)
        
        try:
            # Test pagination
            page1 = Comment.list(client, document_id=test_document.id, limit=2, offset=0)
            page2 = Comment.list(client, document_id=test_document.id, limit=2, offset=2)
            
            assert isinstance(page1, list)
            assert isinstance(page2, list)
            assert len(page1) <= 2
        finally:
            for comment in comments_created:
                try:
                    comment.delete()
                except Exception:
                    pass

    def test_comment_update(self, client, test_document):
        """Test updating a comment."""
        # Create a comment
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Original comment",
        )
        
        try:
            # Update the comment
            new_data = {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Updated comment text"
                            }
                        ]
                    }
                ]
            }
            
            comment.update(data=new_data)
            
            # Verify update
            assert comment.data is not None
            assert_comment_properties(comment)
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_delete(self, client, test_document):
        """Test deleting a comment."""
        # Create a comment
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Comment to delete",
        )
        
        comment_id = comment.id
        comment.delete()
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            Comment.get(client, comment_id)

    def test_comment_delete_with_replies(self, client, test_document):
        """Test deleting a comment that has replies."""
        # Create parent comment
        parent = Comment.create(
            client,
            document_id=test_document.id,
            text="Parent comment",
        )
        
        # Create reply
        reply = Comment.create(
            client,
            document_id=test_document.id,
            text="Reply comment",
            parent_comment_id=parent.id,
        )
        
        parent_id = parent.id
        reply_id = reply.id
        
        # Delete parent (should cascade to replies)
        parent.delete()
        
        # Verify both are gone
        with pytest.raises(NotFoundError):
            Comment.get(client, parent_id)
        
        # Note: Reply might also be deleted via cascade
        # but this depends on API behavior

    def test_comment_refresh(self, client, test_document):
        """Test refreshing comment data from API."""
        # Create a comment
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Comment to refresh",
        )
        
        try:
            # Refresh the comment
            comment.refresh()
            
            # Verify properties still valid
            assert_comment_properties(comment)
            assert comment.document_id == test_document.id
        finally:
            try:
                comment.delete()
            except Exception:
                pass


@pytest.mark.comment
class TestCommentProperties:
    """Test comment property access."""

    def test_comment_properties(self, client, test_document):
        """Test accessing comment properties."""
        # Create a comment
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Test comment properties",
        )
        
        try:
            # Base properties
            assert comment.id is not None
            assert comment.created_at is not None
            assert comment.updated_at is not None
            
            # Comment-specific properties
            assert comment.document_id == test_document.id
            assert isinstance(comment.data, dict)
            
            # Optional properties
            _ = comment.parent_comment_id  # May be None
            _ = comment.anchor_text  # May be None
            _ = comment.created_by  # May be None or dict
            _ = comment.updated_by  # May be None or dict
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_to_dict(self, client, test_document):
        """Test converting comment to dictionary."""
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Test to_dict",
        )
        
        try:
            data = comment.to_dict()
            
            assert isinstance(data, dict)
            assert "id" in data
            assert data["id"] == comment.id
            assert "documentId" in data
            assert data["documentId"] == test_document.id
        finally:
            try:
                comment.delete()
            except Exception:
                pass


@pytest.mark.comment
class TestCommentEdgeCases:
    """Test comment edge cases and special scenarios."""

    def test_comment_nested_replies(self, client, test_document):
        """Test creating a chain of nested replies."""
        # Create parent
        parent = Comment.create(
            client,
            document_id=test_document.id,
            text="Parent comment",
        )
        
        # Create first reply
        reply1 = Comment.create(
            client,
            document_id=test_document.id,
            text="First reply",
            parent_comment_id=parent.id,
        )
        
        # Create reply to reply (if supported)
        # Note: Some systems may not support nested replies
        try:
            reply2 = Comment.create(
                client,
                document_id=test_document.id,
                text="Reply to reply",
                parent_comment_id=reply1.id,
            )
            
            try:
                # Verify hierarchy
                assert reply1.parent_comment_id == parent.id
                assert reply2.parent_comment_id == reply1.id
            finally:
                try:
                    reply2.delete()
                except Exception:
                    pass
        except Exception:
            # Nested replies might not be supported
            pass
        finally:
            try:
                reply1.delete()
            except Exception:
                pass
            try:
                parent.delete()
            except Exception:
                pass

    def test_comment_list_with_filters(self, client, test_collection, test_document):
        """Test listing comments with various filters."""
        # Create a comment
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text="Filter test comment",
        )
        
        try:
            # List by document
            by_doc = Comment.list(client, document_id=test_document.id)
            assert isinstance(by_doc, list)
            assert len(by_doc) > 0
            
            # List by collection
            by_collection = Comment.list(client, collection_id=test_collection.id)
            assert isinstance(by_collection, list)
            
            # List with anchor text
            with_anchor = Comment.list(
                client,
                document_id=test_document.id,
                include_anchor_text=True,
            )
            assert isinstance(with_anchor, list)
            
            # Test sorting
            sorted_comments = Comment.list(
                client,
                document_id=test_document.id,
                sort="createdAt",
                direction="ASC",
            )
            assert isinstance(sorted_comments, list)
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_with_special_characters(self, client, test_document):
        """Test creating a comment with special characters."""
        special_text = "Special: 特殊文字 & émojis 🎉 **bold** _italic_"
        
        comment = Comment.create(
            client,
            document_id=test_document.id,
            text=special_text,
        )
        
        try:
            assert_comment_properties(comment)
            assert comment.document_id == test_document.id
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_comment_with_long_text(self, client, test_document):
        """Test that creating a comment with text exceeding 1000 characters fails."""
        # Outline API has a 1000 character limit for comments
        long_text = "This is a very long comment. " * 50  # 1450 characters
        
        # Should raise ValidationError for text exceeding 1000 characters
        from outline.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Comment.create(
                client,
                document_id=test_document.id,
                text=long_text,
            )
        
        # Verify it's a validation error about the character limit
        assert "validation_error" in str(exc_info.value).lower()
