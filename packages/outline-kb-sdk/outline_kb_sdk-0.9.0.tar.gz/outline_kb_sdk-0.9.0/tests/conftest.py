"""Pytest configuration and fixtures for Outline SDK tests."""

import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from outline import Attachment, Collection, Comment, Document, OutlineClient
from tests.utils.helpers import unique_name, ResourceCleaner

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session")
def client():
    """
    Create OutlineClient instance from environment variables.

    Requires TEST_OUTLINE_URL and TEST_OUTLINE_API_KEY to be set in .env file.
    Tests will be skipped if these are not available.
    """
    api_url = os.getenv("TEST_OUTLINE_URL")
    api_key = os.getenv("TEST_OUTLINE_API_KEY")
    rate_limit_delay = float(os.getenv("TEST_RATE_LIMIT_DELAY", "1.0"))

    if not api_url or not api_key:
        pytest.skip(
            "TEST_OUTLINE_URL and TEST_OUTLINE_API_KEY environment variables required for integration tests"
        )

    return OutlineClient(api_url, api_key, rate_limit_delay=rate_limit_delay)


@pytest.fixture
def test_collection(client):
    """
    Create a test collection for testing.

    Automatically deleted after the test completes.
    """
    collection = Collection.create(
        client,
        name=unique_name("Test Collection"),
        description="Temporary collection for SDK tests",
        icon="🧪",
    )

    yield collection

    # Cleanup
    try:
        collection.delete()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def test_document(client, test_collection):
    """
    Create a test document for testing.

    Automatically deleted after the test completes.
    """
    doc = Document.create(
        client,
        title=unique_name("Test Document"),
        collection_id=test_collection.id,
        text="# Test Content\n\nThis is a test document for SDK testing.",
        publish=True,
    )

    yield doc

    # Cleanup
    try:
        doc.delete(permanent=True)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def resource_cleaner():
    """
    Provide a resource cleaner for tracking and cleaning up test resources.
    
    Usage in tests:
        def test_example(client, resource_cleaner):
            collection = Collection.create(...)
            resource_cleaner.track_collection(collection)
            # Collection will be automatically cleaned up
    """
    cleaner = ResourceCleaner()
    
    yield cleaner
    
    # Cleanup all tracked resources
    cleaner.cleanup_all()


@pytest.fixture
def make_collection(client, resource_cleaner):
    """
    Factory fixture to create collections with automatic cleanup.
    
    Usage:
        def test_example(make_collection):
            collection1 = make_collection(name="Collection 1")
            collection2 = make_collection(name="Collection 2", icon="📚")
    """
    def _make_collection(**kwargs):
        defaults = {
            "name": unique_name("Test Collection"),
            "description": "Temporary test collection",
            "icon": "🧪",
        }
        defaults.update(kwargs)
        
        collection = Collection.create(client, **defaults)
        resource_cleaner.track_collection(collection)
        return collection
    
    return _make_collection


@pytest.fixture
def make_document(client, test_collection, resource_cleaner):
    """
    Factory fixture to create documents with automatic cleanup.
    
    Usage:
        def test_example(make_document):
            doc1 = make_document(title="Doc 1")
            doc2 = make_document(title="Doc 2", publish=False)
    """
    def _make_document(**kwargs):
        defaults = {
            "title": unique_name("Test Document"),
            "collection_id": test_collection.id,
            "text": "# Test Content\n\nTest document for SDK testing.",
            "publish": True,
        }
        defaults.update(kwargs)
        
        document = Document.create(client, **defaults)
        resource_cleaner.track_document(document)
        return document
    
    return _make_document


@pytest.fixture
def make_comment(client, test_document, resource_cleaner):
    """
    Factory fixture to create comments with automatic cleanup.
    
    Usage:
        def test_example(make_comment):
            comment1 = make_comment(text="First comment")
            comment2 = make_comment(text="Second comment")
    """
    def _make_comment(**kwargs):
        defaults = {
            "document_id": test_document.id,
            "text": "Test comment",
        }
        defaults.update(kwargs)
        
        comment = Comment.create(client, **defaults)
        resource_cleaner.track_comment(comment)
        return comment
    
    return _make_comment


@pytest.fixture
def make_attachment(client, test_document, resource_cleaner):
    """
    Factory fixture to create attachments with automatic cleanup.
    
    Usage:
        def test_example(make_attachment):
            att1 = make_attachment(name="image.png")
            att2 = make_attachment(name="doc.pdf", content_type="application/pdf")
    """
    def _make_attachment(**kwargs):
        defaults = {
            "name": f"test-{uuid4().hex[:8]}.png",
            "content_type": "image/png",
            "size": 1024,
            "document_id": test_document.id,
        }
        defaults.update(kwargs)
        
        attachment = Attachment.create(client, **defaults)
        resource_cleaner.track_attachment(attachment)
        return attachment
    
    return _make_attachment
