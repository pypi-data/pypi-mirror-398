"""Tests for Document operations."""

import pytest
from unittest.mock import MagicMock

from outline import Document
from outline.exceptions import NotFoundError
from tests.utils.helpers import (
    assert_base_properties,
    assert_document_properties,
    unique_name,
)


@pytest.mark.document
class TestDocumentCRUD:
    """Test basic Document CRUD operations."""

    def test_document_create(self, client, test_collection):
        """Test creating a document."""
        title = unique_name("Test Document")
        text = "# Test Document\n\nThis is test content."
        
        doc = Document.create(
            client,
            title=title,
            collection_id=test_collection.id,
            text=text,
            publish=True,
        )
        
        try:
            assert_document_properties(doc, title=title)
            assert doc.text == text
            assert doc.collection_id == test_collection.id
            assert doc.published_at is not None
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_create_draft(self, client, test_collection):
        """Test creating a draft (unpublished) document."""
        title = unique_name("Draft Document")
        
        doc = Document.create(
            client,
            title=title,
            collection_id=test_collection.id,
            text="# Draft\n\nThis is a draft.",
            publish=False,  # Create as draft
        )
        
        try:
            assert_document_properties(doc, title=title)
            assert doc.published_at is None
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_create_with_parent(self, client, test_collection, test_document):
        """Test creating a nested document with a parent."""
        child_title = unique_name("Child Document")
        
        child_doc = Document.create(
            client,
            title=child_title,
            collection_id=test_collection.id,
            text="# Child Document\n\nNested under parent.",
            publish=True,
            parent_document_id=test_document.id,
        )
        
        try:
            assert_document_properties(child_doc, title=child_title)
            assert child_doc.parent_document_id == test_document.id
        finally:
            try:
                child_doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_create_with_emoji(self, client, test_collection):
        """Test creating a document with emoji and full-width."""
        title = unique_name("Emoji Document")
        
        doc = Document.create(
            client,
            title=title,
            collection_id=test_collection.id,
            text="# Document with emoji 🎨",
            publish=True,
        )
        
        try:
            assert_document_properties(doc, title=title)
            # Note: emoji might be auto-detected from content
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_create_as_template(self, client, test_collection):
        """Test creating a template document."""
        title = unique_name("Template Document")
        
        doc = Document.create(
            client,
            title=title,
            collection_id=test_collection.id,
            text="# Template\n\nThis is a template.",
            publish=True,
            template=True,
        )
        
        try:
            assert_document_properties(doc, title=title)
            assert doc.template is True
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_get(self, client, test_document):
        """Test retrieving a document by ID."""
        retrieved_doc = Document.get(client, test_document.id)
        
        assert_document_properties(retrieved_doc)
        assert retrieved_doc.id == test_document.id
        assert retrieved_doc.title == test_document.title

    def test_document_get_with_url_id(self, client, test_document):
        """Test retrieving a document using urlId."""
        # First get the urlId
        url_id = test_document.url_id
        
        if url_id:
            retrieved_doc = Document.get(client, url_id)
            assert retrieved_doc.id == test_document.id

    def test_document_list(self, client, test_collection):
        """Test listing documents."""
        docs = Document.list(client, collection_id=test_collection.id)
        
        assert isinstance(docs, list)
        # Should have at least the test_document (if fixture is used)

    def test_document_list_with_filters(self, client, test_collection):
        """Test listing documents with filters."""
        # Create a specific document to filter
        specific_doc = Document.create(
            client,
            title=unique_name("Specific Document"),
            collection_id=test_collection.id,
            text="# Specific\n\nFiltrable document.",
            publish=True,
        )
        
        try:
            # List by collection
            docs = Document.list(
                client,
                collection_id=test_collection.id,
                limit=10,
            )
            
            assert isinstance(docs, list)
            assert len(docs) > 0
            
            # All returned docs should be in this collection
            for doc in docs:
                assert doc.collection_id == test_collection.id
        finally:
            try:
                specific_doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_list_with_pagination(self, client, test_collection):
        """Test document list pagination."""
        # Create multiple documents
        docs_created = []
        for i in range(3):
            doc = Document.create(
                client,
                title=unique_name(f"Pagination Doc {i}"),
                collection_id=test_collection.id,
                text=f"# Document {i}\n\nContent.",
                publish=True,
            )
            docs_created.append(doc)
        
        try:
            # Test pagination
            page1 = Document.list(client, collection_id=test_collection.id, limit=2, offset=0)
            page2 = Document.list(client, collection_id=test_collection.id, limit=2, offset=2)
            
            assert isinstance(page1, list)
            assert isinstance(page2, list)
            assert len(page1) <= 2
        finally:
            for doc in docs_created:
                try:
                    doc.delete(permanent=True)
                except Exception:
                    pass

    def test_document_update(self, client, test_document):
        """Test updating a document."""
        original_title = test_document.title
        new_title = unique_name("Updated Document")
        new_text = "# Updated\n\nThis content has been updated."
        
        test_document.update(title=new_title, text=new_text)
        
        assert test_document.title == new_title
        assert test_document.text == new_text
        
        # Restore original title
        test_document.update(title=original_title)

    def test_document_update_with_append(self, client, test_document):
        """Test updating a document with append mode."""
        original_text = test_document.text
        append_text = "\n\n## Appended Section\n\nThis was appended."
        
        test_document.update(text=append_text, append=True)
        
        # Text should contain both original and appended
        assert append_text in test_document.text
        
        # Restore original
        test_document.update(text=original_text)

    def test_document_update_partial_fields(self, client, test_document):
        """Test updating only specific fields."""
        original_title = test_document.title
        original_text = test_document.text
        
        new_title = unique_name("Partial Update")
        test_document.update(title=new_title)
        
        # Title should be updated
        assert test_document.title == new_title
        # Text should remain unchanged
        assert test_document.text == original_text
        
        # Restore
        test_document.update(title=original_title)

    def test_document_delete_permanent(self, client, test_collection):
        """Test permanently deleting a document."""
        from outline.exceptions import AuthorizationError
        
        doc = Document.create(
            client,
            title=unique_name("To Delete"),
            collection_id=test_collection.id,
            text="# Delete Me\n\nThis will be deleted.",
            publish=True,
        )
        
        doc_id = doc.id
        
        try:
            doc.delete(permanent=True)
            
            # Verify document is gone
            with pytest.raises(NotFoundError):
                Document.get(client, doc_id)
        except AuthorizationError:
            # Some Outline instances may not allow permanent deletion
            # In this case, just verify we can trash it instead
            doc.delete(permanent=False)
            pytest.skip("Permanent deletion not authorized - skipping test")

    def test_document_delete_trash(self, client, test_collection):
        """Test moving a document to trash."""
        doc = Document.create(
            client,
            title=unique_name("To Trash"),
            collection_id=test_collection.id,
            text="# Trash Me\n\nThis will be trashed.",
            publish=True,
        )
        
        try:
            doc.delete(permanent=False)
            
            # Document should still exist but be in trash
            # We can restore it
            doc.restore()
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_refresh(self, client, test_document):
        """Test refreshing document data from API."""
        original_title = test_document.title
        
        # Modify via API (simulate external change)
        test_document.refresh()
        
        # Data should be current
        assert_document_properties(test_document)
        assert test_document.title == original_title


@pytest.mark.document
class TestDocumentStateChanges:
    """Test document state transition operations."""

    def test_document_publish(self, client, test_collection):
        """Test publishing a draft document."""
        # Create draft
        doc = Document.create(
            client,
            title=unique_name("Draft to Publish"),
            collection_id=test_collection.id,
            text="# Draft\n\nWill be published.",
            publish=False,
        )
        
        try:
            assert doc.published_at is None
            
            # Publish it
            doc.publish()
            
            # Should now be published
            assert doc.published_at is not None
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_unpublish(self, client, test_collection):
        """Test unpublishing a document back to draft."""
        # Create published document
        doc = Document.create(
            client,
            title=unique_name("Published to Unpublish"),
            collection_id=test_collection.id,
            text="# Published\n\nWill be unpublished.",
            publish=True,
        )
        
        try:
            assert doc.published_at is not None
            
            # Unpublish it
            doc.unpublish()
            
            # Should now be draft
            assert doc.published_at is None
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_archive(self, client, test_document):
        """Test archiving a document."""
        # Archive the document
        test_document.archive()
        
        # Should have archived_at timestamp
        assert test_document.archived_at is not None
        
        # Restore from archive
        test_document.restore()
        assert test_document.archived_at is None

    def test_document_restore_from_trash(self, client, test_collection):
        """Test restoring a document from trash."""
        doc = Document.create(
            client,
            title=unique_name("Trash Restore Test"),
            collection_id=test_collection.id,
            text="# Trash\n\nWill be trashed and restored.",
            publish=True,
        )
        
        try:
            # Move to trash
            doc.delete(permanent=False)
            
            # Restore from trash
            doc.restore()
            
            # Should be restored
            assert_document_properties(doc)
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_restore_from_archive(self, client, test_collection):
        """Test restoring a document from archive."""
        doc = Document.create(
            client,
            title=unique_name("Archive Restore Test"),
            collection_id=test_collection.id,
            text="# Archive\n\nWill be archived and restored.",
            publish=True,
        )
        
        try:
            # Archive
            doc.archive()
            assert doc.archived_at is not None
            
            # Restore
            doc.restore()
            assert doc.archived_at is None
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass


@pytest.mark.document
class TestDocumentMovement:
    """Test document movement operations."""

    def test_document_move_to_different_collection(self, client, make_collection, test_document):
        """Test moving a document to a different collection."""
        # Create a second collection
        collection2 = make_collection(name=unique_name("Target Collection"))
        
        original_collection_id = test_document.collection_id
        
        # Move document to new collection
        test_document.move(collection_id=collection2.id)
        
        # Verify the move
        assert test_document.collection_id == collection2.id
        
        # Move back
        test_document.move(collection_id=original_collection_id)

    def test_document_move_under_parent(self, client, test_collection):
        """Test moving a document under a parent."""
        # Create parent and child
        parent = Document.create(
            client,
            title=unique_name("Parent Document"),
            collection_id=test_collection.id,
            text="# Parent\n\nThis is the parent.",
            publish=True,
        )
        
        child = Document.create(
            client,
            title=unique_name("Child Document"),
            collection_id=test_collection.id,
            text="# Child\n\nThis will be moved under parent.",
            publish=True,
        )
        
        try:
            # Move child under parent
            child.move(parent_document_id=parent.id)
            
            # Verify
            assert child.parent_document_id == parent.id
        finally:
            try:
                child.delete(permanent=True)
            except Exception:
                pass
            try:
                parent.delete(permanent=True)
            except Exception:
                pass

    def test_document_move_to_root(self, client, test_collection, test_document):
        """Test moving a nested document to root level."""
        # Create a child document
        child = Document.create(
            client,
            title=unique_name("Child to Root"),
            collection_id=test_collection.id,
            text="# Child\n\nWill be moved to root.",
            publish=True,
            parent_document_id=test_document.id,
        )
        
        try:
            assert child.parent_document_id == test_document.id
            
            # Move to root (no parent)
            # Note: This might require passing None or empty string
            # depending on API behavior
            child.move(parent_document_id="")
            
            # Should be at root
            assert child.parent_document_id is None or child.parent_document_id == ""
        finally:
            try:
                child.delete(permanent=True)
            except Exception:
                pass


@pytest.mark.document
class TestDocumentExport:
    """Test document export operations."""

    def test_document_export(self, client, test_document):
        """Test exporting a document as Markdown."""
        markdown = test_document.export()
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        # Should contain the document title or content
        assert test_document.title in markdown or "Test Content" in markdown


@pytest.mark.document
class TestDocumentComments:
    """Test comment operations via document."""

    def test_document_add_comment(self, client, test_document):
        """Test adding a comment to a document."""
        comment_text = "This is a test comment."
        
        comment = test_document.add_comment(text=comment_text)
        
        try:
            assert comment.id is not None
            assert comment.document_id == test_document.id
            # Note: Comment text/data might be in different properties
        finally:
            try:
                comment.delete()
            except Exception:
                pass

    def test_document_add_comment_reply(self, client, test_document):
        """Test adding a reply to a comment."""
        # Create parent comment
        parent_comment = test_document.add_comment(text="Parent comment")
        
        try:
            # Add reply
            reply = test_document.add_comment(
                text="Reply to parent",
                parent_comment_id=parent_comment.id,
            )
            
            try:
                assert reply.id is not None
                assert reply.document_id == test_document.id
            finally:
                try:
                    reply.delete()
                except Exception:
                    pass
        finally:
            try:
                parent_comment.delete()
            except Exception:
                pass

    def test_document_list_comments(self, client, test_document):
        """Test listing comments on a document."""
        # Create a comment first
        comment = test_document.add_comment(text="Test comment for listing")
        
        try:
            # List comments
            comments = test_document.list_comments()
            
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


@pytest.mark.document
class TestDocumentProperties:
    """Test document property access."""

    def test_document_properties(self, test_document):
        """Test accessing document properties."""
        # Base properties
        assert test_document.id is not None
        assert test_document.created_at is not None
        assert test_document.updated_at is not None
        
        # Document-specific properties
        assert test_document.title is not None
        assert test_document.collection_id is not None
        assert isinstance(test_document.text, str)
        assert isinstance(test_document.url_id, str)
        assert isinstance(test_document.revision, int)
        assert isinstance(test_document.pinned, bool)
        assert isinstance(test_document.template, bool)
        assert isinstance(test_document.full_width, bool)
        
        # Optional properties
        # These might be None
        _ = test_document.parent_document_id
        _ = test_document.emoji
        _ = test_document.template_id
        _ = test_document.published_at
        _ = test_document.archived_at

    def test_document_to_dict(self, test_document):
        """Test converting document to dictionary."""
        data = test_document.to_dict()
        
        assert isinstance(data, dict)
        assert "id" in data
        assert data["id"] == test_document.id
        assert "title" in data
        assert data["title"] == test_document.title


@pytest.mark.document
class TestDocumentEdgeCases:
    """Test document edge cases and special scenarios."""

    def test_document_nested_hierarchy(self, client, test_collection):
        """Test creating a multi-level document hierarchy."""
        # Create grandparent -> parent -> child
        grandparent = Document.create(
            client,
            title=unique_name("Grandparent"),
            collection_id=test_collection.id,
            text="# Grandparent\n\nTop level.",
            publish=True,
        )
        
        parent = Document.create(
            client,
            title=unique_name("Parent"),
            collection_id=test_collection.id,
            text="# Parent\n\nMiddle level.",
            publish=True,
            parent_document_id=grandparent.id,
        )
        
        child = Document.create(
            client,
            title=unique_name("Child"),
            collection_id=test_collection.id,
            text="# Child\n\nBottom level.",
            publish=True,
            parent_document_id=parent.id,
        )
        
        try:
            # Verify hierarchy
            assert parent.parent_document_id == grandparent.id
            assert child.parent_document_id == parent.id
        finally:
            # Cleanup in reverse order
            for doc in [child, parent, grandparent]:
                try:
                    doc.delete(permanent=True)
                except Exception:
                    pass

    def test_document_with_special_characters(self, client, test_collection):
        """Test creating a document with special characters."""
        special_title = unique_name("Special: 特殊文字 & émojis 🎉")
        special_text = "# Special Characters\n\n特殊文字 & émojis 🎉\n\n**Bold** _italic_ `code`"
        
        doc = Document.create(
            client,
            title=special_title,
            collection_id=test_collection.id,
            text=special_text,
            publish=True,
        )
        
        try:
            assert_document_properties(doc)
            assert doc.title == special_title
            assert special_text in doc.text or "Special Characters" in doc.text
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_with_long_content(self, client, test_collection):
        """Test creating a document with long content."""
        long_text = "# Long Document\n\n" + ("This is a long paragraph. " * 100)
        
        doc = Document.create(
            client,
            title=unique_name("Long Document"),
            collection_id=test_collection.id,
            text=long_text,
            publish=True,
        )
        
        try:
            assert_document_properties(doc)
            assert len(doc.text) > 1000
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass

    def test_document_create_minimal(self, client, test_collection):
        """Test creating a document with minimal parameters."""
        doc = Document.create(
            client,
            title=unique_name("Minimal"),
            collection_id=test_collection.id,
        )
        
        try:
            assert_document_properties(doc)
            # Text might be empty or have default content
            assert isinstance(doc.text, str)
        finally:
            try:
                doc.delete(permanent=True)
            except Exception:
                pass


@pytest.mark.document
class TestDocumentAttachments:
    """Test document attachment discovery."""
    
    def test_list_attachments_with_images(self):
        """Test parsing image attachments from markdown."""
        # Create a mock document with image attachments
        doc_data = {
            "id": "doc-123",
            "title": "Test Doc",
            "text": """
            # Document with Images
            
            ![Screenshot](/api/attachments.redirect?id=edf6501b-aa07-4902-af47-381ccd57b9f3 " =1024x1024")
            
            ![Diagram](/api/attachments.redirect?id=12345678-1234-1234-1234-123456789abc)
            """,
            "collectionId": "col-123",
        }
        
        client = MagicMock()
        doc = Document(client, doc_data)
        
        attachments = doc.list_attachments()
        
        assert len(attachments) == 2
        assert attachments[0].id == "edf6501b-aa07-4902-af47-381ccd57b9f3"
        assert attachments[0].is_image is True
        assert attachments[1].id == "12345678-1234-1234-1234-123456789abc"
        assert attachments[1].is_image is True
    
    def test_list_attachments_with_files(self):
        """Test parsing file attachments from markdown."""
        doc_data = {
            "id": "doc-123",
            "title": "Test Doc",
            "text": """
            # Document with Files
            
            [Pick-Your-Niche-Checklist.pdf 280668](/api/attachments.redirect?id=af56d3a8-a5d6-475f-b744-348281aa4601)
            [Pricing-Value-Checklist.pdf 611349](/api/attachments.redirect?id=0a2fdd1c-3628-433e-b62c-09dd17bc790b)
            """,
            "collectionId": "col-123",
        }
        
        client = MagicMock()
        doc = Document(client, doc_data)
        
        attachments = doc.list_attachments()
        
        assert len(attachments) == 2
        
        # First attachment
        assert attachments[0].id == "af56d3a8-a5d6-475f-b744-348281aa4601"
        assert attachments[0].is_image is False
        assert attachments[0].name == "Pick-Your-Niche-Checklist.pdf"
        assert attachments[0].size == 280668
        
        # Second attachment
        assert attachments[1].id == "0a2fdd1c-3628-433e-b62c-09dd17bc790b"
        assert attachments[1].name == "Pricing-Value-Checklist.pdf"
        assert attachments[1].size == 611349
    
    def test_list_attachments_mixed(self):
        """Test document with both images and files."""
        doc_data = {
            "id": "doc-123",
            "title": "Test Doc",
            "text": """
            ![Image](/api/attachments.redirect?id=11111111-1111-1111-1111-111111111111)
            [file.pdf 12345](/api/attachments.redirect?id=22222222-2222-2222-2222-222222222222)
            """,
            "collectionId": "col-123",
        }
        
        client = MagicMock()
        doc = Document(client, doc_data)
        
        attachments = doc.list_attachments()
        
        assert len(attachments) == 2
        assert attachments[0].is_image is True
        assert attachments[1].is_image is False
    
    def test_list_attachments_empty(self):
        """Test document with no attachments."""
        doc_data = {
            "id": "doc-123",
            "title": "Test Doc",
            "text": "# Just text, no attachments",
            "collectionId": "col-123",
        }
        
        client = MagicMock()
        doc = Document(client, doc_data)
        
        attachments = doc.list_attachments()
        assert len(attachments) == 0
    
    def test_get_attachment_not_found(self):
        """Test getting non-existent attachment raises error."""
        doc_data = {
            "id": "doc-123",
            "title": "Test Doc",
            "text": "No attachments here",
            "collectionId": "col-123",
        }
        
        client = MagicMock()
        doc = Document(client, doc_data)
        
        with pytest.raises(ValueError, match="not found"):
            doc.get_attachment("nonexistent-id")
    
    def test_attachment_reference_properties(self):
        """Test AttachmentReference properties."""
        from outline.models.attachment import AttachmentReference
        
        ref = AttachmentReference(
            id="test-uuid-1234",
            name="test.pdf",
            size=12345,
            is_image=False
        )
        
        assert ref.download_url == "/api/attachments.redirect?id=test-uuid-1234"
        assert "File" in repr(ref)
        assert "test.pdf" in repr(ref)
        assert "12345" in repr(ref)
        
        # Test image reference
        img_ref = AttachmentReference(
            id="img-uuid-5678",
            is_image=True
        )
        
        assert "Image" in repr(img_ref)
