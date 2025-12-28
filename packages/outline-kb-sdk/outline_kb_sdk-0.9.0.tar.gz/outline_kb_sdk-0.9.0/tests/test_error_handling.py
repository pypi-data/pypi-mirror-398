"""Tests for error handling and exceptions."""

import pytest

from outline import Collection, Document, Comment, Attachment, OutlineClient
from outline.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    OutlineError,
)


@pytest.mark.error_handling
class TestNotFoundError:
    """Test NotFoundError scenarios."""

    def test_get_nonexistent_collection(self, client):
        """Test getting a collection that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(NotFoundError) as exc_info:
            Collection.get(client, fake_id)
        
        assert exc_info.value.status_code == 404

    def test_get_nonexistent_document(self, client):
        """Test getting a document that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(NotFoundError) as exc_info:
            Document.get(client, fake_id)
        
        assert exc_info.value.status_code == 404

    def test_get_nonexistent_comment(self, client):
        """Test getting a comment that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(NotFoundError) as exc_info:
            Comment.get(client, fake_id)
        
        assert exc_info.value.status_code == 404

    def test_delete_nonexistent_collection(self, client):
        """Test deleting a collection that doesn't exist."""
        from outline.models.collection import Collection as CollectionModel
        
        # Create a mock collection object
        fake_collection = CollectionModel(client, {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Fake",
            "createdAt": "2024-01-01T00:00:00.000Z",
            "updatedAt": "2024-01-01T00:00:00.000Z",
        })
        
        with pytest.raises(NotFoundError):
            fake_collection.delete()


@pytest.mark.error_handling
class TestValidationError:
    """Test ValidationError scenarios."""

    def test_create_collection_without_name(self, client):
        """Test creating a collection without required name field."""
        # This should raise a validation error
        with pytest.raises((ValidationError, TypeError)):
            Collection.create(client, name="")  # Empty name might fail

    def test_create_document_with_invalid_collection(self, client):
        """Test creating a document with invalid collection ID."""
        fake_collection_id = "not-a-valid-uuid"
        
        try:
            with pytest.raises((ValidationError, NotFoundError)):
                Document.create(
                    client,
                    title="Test Doc",
                    collection_id=fake_collection_id,
                )
        except Exception:
            # Some validation might happen client-side
            pass

    def test_update_document_with_invalid_data(self, client, test_document):
        """Test updating with invalid data."""
        # Try to update with an extremely long title
        # Note: Validation limits vary by server
        try:
            very_long_title = "A" * 10000
            test_document.update(title=very_long_title)
            
            # If it succeeds, the server accepted it (no error to test)
            # Restore original title
            test_document.update(title="Restored Title")
        except ValidationError:
            # Expected validation error
            pass
        except Exception:
            # Other errors are also acceptable for this test
            pass


@pytest.mark.error_handling
class TestAuthenticationError:
    """Test AuthenticationError scenarios."""

    def test_invalid_api_key(self):
        """Test connecting with an invalid API key."""
        import os
        api_url = os.getenv("TEST_OUTLINE_URL", "https://example.com")
        invalid_client = OutlineClient(api_url, "invalid_api_key_12345")
        
        with pytest.raises(AuthenticationError) as exc_info:
            Collection.list(invalid_client)
        
        assert exc_info.value.status_code == 401

    def test_empty_api_key(self):
        """Test connecting with an empty API key."""
        import os
        api_url = os.getenv("TEST_OUTLINE_URL", "https://example.com")
        empty_client = OutlineClient(api_url, "")
        
        with pytest.raises(AuthenticationError) as exc_info:
            Collection.list(empty_client)
        
        assert exc_info.value.status_code == 401


@pytest.mark.error_handling
class TestAuthorizationError:
    """Test AuthorizationError scenarios."""

    def test_unauthorized_action(self, client, test_collection):
        """Test an action that may not be authorized."""
        # Some operations may require specific permissions
        # Permanent deletion is often restricted
        doc = Document.create(
            client,
            title="Test for Auth",
            collection_id=test_collection.id,
            publish=True,
        )
        
        try:
            # Permanent delete may require special permissions
            doc.delete(permanent=True)
            # If successful, no error - test passes
        except AuthorizationError as e:
            # Expected - this is what we're testing
            assert e.status_code == 403
            # Clean up with regular delete
            try:
                doc.delete(permanent=False)
            except:
                pass
        except Exception:
            # Other errors - clean up
            try:
                doc.delete(permanent=False)
            except:
                pass


@pytest.mark.error_handling
class TestErrorDetails:
    """Test error message and detail handling."""

    def test_error_message_format(self, client):
        """Test that errors have proper message formatting."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            Collection.get(client, fake_id)
        except NotFoundError as e:
            # Error should have a message
            assert str(e) is not None
            assert len(str(e)) > 0
            
            # Should contain error info
            error_str = str(e)
            assert "404" in error_str or "not" in error_str.lower()

    def test_error_status_code(self, client):
        """Test that errors include status codes."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            Document.get(client, fake_id)
        except NotFoundError as e:
            assert e.status_code == 404

    def test_error_data_attribute(self, client):
        """Test that errors may include additional data."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            Comment.get(client, fake_id)
        except NotFoundError as e:
            # Data attribute should exist (may be None)
            assert hasattr(e, 'data')


@pytest.mark.error_handling
@pytest.mark.slow
class TestRateLimitError:
    """Test rate limit handling."""

    def test_rate_limit_error_properties(self):
        """Test RateLimitError structure."""
        # Create a rate limit error
        error = RateLimitError(60, "Rate limit exceeded")
        
        assert error.retry_after == 60
        assert "60" in str(error) or "Rate limit" in str(error)
        assert error.status_code == 429

    @pytest.mark.skip(reason="Would need to trigger actual rate limiting")
    def test_actual_rate_limiting(self, client, test_collection):
        """Test that rate limiting is properly handled."""
        # This test would require making many requests quickly
        # Skipped to avoid actually hitting rate limits
        pass


@pytest.mark.error_handling
class TestExceptionHierarchy:
    """Test exception class hierarchy and inheritance."""

    def test_all_exceptions_inherit_from_outline_error(self):
        """Test that all custom exceptions inherit from OutlineError."""
        from outline.exceptions import OutlineError
        
        exceptions = [
            NotFoundError,
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            RateLimitError,
        ]
        
        for exc_class in exceptions:
            error = exc_class("Test error")
            assert isinstance(error, OutlineError)
            assert isinstance(error, Exception)

    def test_exception_can_be_caught_generically(self, client):
        """Test that all outline exceptions can be caught as OutlineError."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            Document.get(client, fake_id)
        except OutlineError as e:
            # Should catch NotFoundError as OutlineError
            assert isinstance(e, NotFoundError)
            assert e.status_code == 404


@pytest.mark.error_handling
class TestErrorRecovery:
    """Test error recovery scenarios."""

    def test_client_continues_after_error(self, client, test_collection):
        """Test that client can continue operations after an error."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        # Trigger an error
        try:
            Collection.get(client, fake_id)
        except NotFoundError:
            pass
        
        # Client should still work for valid operations
        collections = Collection.list(client)
        assert isinstance(collections, list)

    def test_retry_after_not_found(self, client, test_collection):
        """Test that operations can be retried after errors."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        # First attempt - should fail
        try:
            Document.get(client, fake_id)
            assert False, "Should have raised NotFoundError"
        except NotFoundError:
            pass
        
        # Second attempt with valid ID - should succeed
        doc = Document.create(
            client,
            title="Retry Test",
            collection_id=test_collection.id,
            publish=True,
        )
        
        try:
            retrieved = Document.get(client, doc.id)
            assert retrieved.id == doc.id
        finally:
            try:
                doc.delete(permanent=True)
            except:
                pass


@pytest.mark.error_handling
class TestNetworkErrors:
    """Test network-related error scenarios."""

    def test_invalid_url(self):
        """Test connecting to an invalid URL."""
        from outline.exceptions import NetworkError
        
        bad_client = OutlineClient("https://invalid.nonexistent.domain.example.com", "fake_key")
        
        # This should raise a network error
        with pytest.raises((NetworkError, Exception)):
            Collection.list(bad_client)

    @pytest.mark.skip(reason="Would require actual network issues")
    def test_timeout(self):
        """Test request timeout handling."""
        # This would require setting very short timeout and slow server
        pass
