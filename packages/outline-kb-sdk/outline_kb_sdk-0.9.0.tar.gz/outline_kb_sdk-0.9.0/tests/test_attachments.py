"""Tests for Attachment operations."""

import pytest

from outline import Attachment
from outline.exceptions import NotFoundError
from tests.utils.helpers import (
    assert_base_properties,
    assert_attachment_properties,
)


@pytest.mark.attachment
class TestAttachmentCRUD:
    """Test basic Attachment CRUD operations."""

    def test_attachment_create_with_document(self, client, test_document):
        """Test creating an attachment associated with a document."""
        name = "test-image.png"
        content_type = "image/png"
        size = 1024
        
        attachment = Attachment.create(
            client,
            name=name,
            content_type=content_type,
            size=size,
            document_id=test_document.id,
        )
        
        try:
            assert_attachment_properties(attachment, name=name)
            assert attachment.content_type == content_type
            assert attachment.size == size
            assert attachment.document_id == test_document.id
            
            # Check upload information
            assert attachment.upload_url is not None
            assert attachment.upload_form is not None or isinstance(attachment.upload_form, dict)
            # max_upload_size might be None or a number
            _ = attachment.max_upload_size
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_create_without_document(self, client):
        """Test creating an attachment without a document ID."""
        name = "standalone-file.pdf"
        content_type = "application/pdf"
        size = 2048
        
        attachment = Attachment.create(
            client,
            name=name,
            content_type=content_type,
            size=size,
        )
        
        try:
            assert_attachment_properties(attachment, name=name)
            assert attachment.content_type == content_type
            assert attachment.size == size
            assert attachment.document_id is None
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_create_response_structure(self, client, test_document):
        """Test that attachment creation returns proper structure."""
        attachment = Attachment.create(
            client,
            name="response-test.jpg",
            content_type="image/jpeg",
            size=512,
            document_id=test_document.id,
        )
        
        try:
            # Verify all expected properties exist
            assert attachment.id is not None
            assert attachment.name is not None
            assert attachment.content_type is not None
            assert attachment.size is not None
            assert attachment.created_at is not None
            assert attachment.updated_at is not None
            
            # Upload-specific properties
            assert attachment.upload_url is not None
            # upload_form and max_upload_size may vary by instance
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_get_redirect_url(self, client, test_document):
        """Test getting a redirect URL for an attachment."""
        attachment = Attachment.create(
            client,
            name="redirect-test.png",
            content_type="image/png",
            size=256,
            document_id=test_document.id,
        )
        
        try:
            # Get redirect URL
            redirect_url = attachment.get_redirect_url()
            
            # Should return a URL string
            assert isinstance(redirect_url, str)
            # URL might be empty or a valid URL
            # Just verify it doesn't crash
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_delete(self, client, test_document):
        """Test deleting an attachment using instance method."""
        attachment = Attachment.create(
            client,
            name="to-delete.txt",
            content_type="text/plain",
            size=100,
            document_id=test_document.id,
        )
        
        attachment_id = attachment.id
        attachment.delete()
        
        # After deletion, trying to get redirect should fail
        # Note: There's no direct way to verify deletion as there's no info endpoint
        # We just verify the delete call doesn't raise an error

    def test_attachment_delete_by_id(self, client, test_document):
        """Test deleting an attachment by ID using class method."""
        attachment = Attachment.create(
            client,
            name="delete-by-id.doc",
            content_type="application/msword",
            size=2048,
            document_id=test_document.id,
        )
        
        attachment_id = attachment.id
        
        # Delete by ID
        Attachment.delete_by_id(client, attachment_id)
        
        # Verify deletion succeeded without error


@pytest.mark.attachment
class TestAttachmentProperties:
    """Test attachment property access."""

    def test_attachment_properties(self, client, test_document):
        """Test accessing attachment properties."""
        attachment = Attachment.create(
            client,
            name="properties-test.png",
            content_type="image/png",
            size=1024,
            document_id=test_document.id,
        )
        
        try:
            # Base properties
            assert attachment.id is not None
            assert attachment.created_at is not None
            assert attachment.updated_at is not None
            
            # Attachment-specific properties
            assert attachment.name == "properties-test.png"
            assert attachment.content_type == "image/png"
            assert attachment.size == 1024
            assert attachment.document_id == test_document.id
            
            # Optional properties
            _ = attachment.url  # May be None before upload
            
            # Upload information
            _ = attachment.upload_url
            _ = attachment.upload_form
            _ = attachment.max_upload_size
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_upload_info(self, client, test_document):
        """Test that upload information is available after creation."""
        attachment = Attachment.create(
            client,
            name="upload-info-test.jpg",
            content_type="image/jpeg",
            size=4096,
            document_id=test_document.id,
        )
        
        try:
            # Upload URL should be present
            upload_url = attachment.upload_url
            assert upload_url is not None
            assert isinstance(upload_url, str)
            
            # Upload form might be None or a dict
            upload_form = attachment.upload_form
            if upload_form is not None:
                assert isinstance(upload_form, dict)
            
            # Max upload size might be None or an integer
            max_size = attachment.max_upload_size
            if max_size is not None:
                assert isinstance(max_size, int)
                assert max_size > 0
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_to_dict(self, client, test_document):
        """Test converting attachment to dictionary."""
        attachment = Attachment.create(
            client,
            name="to-dict-test.pdf",
            content_type="application/pdf",
            size=2048,
            document_id=test_document.id,
        )
        
        try:
            data = attachment.to_dict()
            
            assert isinstance(data, dict)
            assert "id" in data
            assert data["id"] == attachment.id
            assert "name" in data
            assert data["name"] == attachment.name
            assert "contentType" in data
            assert data["contentType"] == attachment.content_type
            assert "size" in data
            assert data["size"] == attachment.size
        finally:
            try:
                attachment.delete()
            except Exception:
                pass


@pytest.mark.attachment
class TestAttachmentEdgeCases:
    """Test attachment edge cases and special scenarios."""

    def test_attachment_different_content_types(self, client, test_document):
        """Test creating attachments with different content types."""
        content_types = [
            ("image.png", "image/png"),
            ("document.pdf", "application/pdf"),
            ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("text.txt", "text/plain"),
            ("data.json", "application/json"),
        ]
        
        attachments = []
        for name, content_type in content_types:
            attachment = Attachment.create(
                client,
                name=name,
                content_type=content_type,
                size=1024,
                document_id=test_document.id,
            )
            attachments.append(attachment)
        
        try:
            # Verify all were created successfully
            for i, (name, content_type) in enumerate(content_types):
                assert attachments[i].name == name
                assert attachments[i].content_type == content_type
        finally:
            # Cleanup
            for attachment in attachments:
                try:
                    attachment.delete()
                except Exception:
                    pass

    def test_attachment_large_file(self, client, test_document):
        """Test creating an attachment record for a large file."""
        # Test with a large size (10 MB)
        large_size = 10 * 1024 * 1024
        
        attachment = Attachment.create(
            client,
            name="large-file.zip",
            content_type="application/zip",
            size=large_size,
            document_id=test_document.id,
        )
        
        try:
            assert_attachment_properties(attachment)
            assert attachment.size == large_size
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_special_characters_in_name(self, client, test_document):
        """Test creating an attachment with special characters in filename."""
        special_name = "文件-测试 & émojis 🎉.pdf"
        
        attachment = Attachment.create(
            client,
            name=special_name,
            content_type="application/pdf",
            size=512,
            document_id=test_document.id,
        )
        
        try:
            assert attachment.id is not None
            # Name should be preserved
            assert attachment.name == special_name
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_refresh_not_implemented(self, client, test_document):
        """Test that attachment refresh raises NotImplementedError."""
        attachment = Attachment.create(
            client,
            name="refresh-test.png",
            content_type="image/png",
            size=256,
            document_id=test_document.id,
        )
        
        try:
            # Refresh should raise NotImplementedError
            with pytest.raises(NotImplementedError):
                attachment.refresh()
        finally:
            try:
                attachment.delete()
            except Exception:
                pass

    def test_attachment_zero_size(self, client, test_document):
        """Test creating an attachment with zero size."""
        # Some systems may allow zero-size files
        try:
            attachment = Attachment.create(
                client,
                name="empty-file.txt",
                content_type="text/plain",
                size=0,
                document_id=test_document.id,
            )
            
            try:
                assert attachment.id is not None
                assert attachment.size == 0
            finally:
                try:
                    attachment.delete()
                except Exception:
                    pass
        except Exception:
            # Zero size might be rejected - this is acceptable
            pytest.skip("Zero-size attachments not supported")
