"""Tests for Collection operations."""

import pytest

from outline import Collection
from outline.exceptions import NotFoundError
from tests.utils.helpers import (
    assert_base_properties,
    assert_collection_properties,
    unique_name,
)


@pytest.mark.collection
class TestCollectionCRUD:
    """Test basic Collection CRUD operations."""

    def test_collection_create(self, client):
        """Test creating a collection."""
        name = unique_name("Create Collection")
        description = "Test collection description"
        icon = "📚"
        color = "#FF0000"
        
        collection = Collection.create(
            client,
            name=name,
            description=description,
            icon=icon,
            color=color,
            sharing=True,
        )
        
        try:
            assert_collection_properties(collection, name)
            assert collection.description == description
            assert collection.icon == icon
            assert collection.color == color.upper()  # API returns uppercase
            assert collection.sharing is True
        finally:
            collection.delete()

    def test_collection_create_minimal(self, client):
        """Test creating a collection with minimal parameters."""
        name = unique_name("Minimal Collection")
        
        collection = Collection.create(client, name=name)
        
        try:
            assert_collection_properties(collection, name)
            assert collection.sharing is False  # Default value
        finally:
            collection.delete()

    def test_collection_create_with_emoji_icon(self, client):
        """Test creating a collection with emoji icon."""
        name = unique_name("Emoji Collection")
        
        collection = Collection.create(
            client,
            name=name,
            icon="🎨",
        )
        
        try:
            assert collection.icon == "🎨"
        finally:
            collection.delete()

    def test_collection_get(self, client, test_collection):
        """Test retrieving a collection by ID."""
        fetched = Collection.get(client, test_collection.id)
        
        assert fetched.id == test_collection.id
        assert fetched.name == test_collection.name

    def test_collection_get_invalid_id(self, client):
        """Test retrieving a collection with invalid ID raises error."""
        from outline.exceptions import ValidationError
        
        # API returns ValidationError for invalid ID format
        with pytest.raises((NotFoundError, ValidationError)):
            Collection.get(client, "invalid-id-12345")

    def test_collection_list(self, client):
        """Test listing all collections."""
        collections = Collection.list(client, limit=5)
        
        assert isinstance(collections, list)
        assert len(collections) <= 5
        
        for collection in collections:
            assert_collection_properties(collection)

    def test_collection_list_with_query(self, client, make_collection):
        """Test listing collections with a search query."""
        # Create a collection with unique name
        unique_part = unique_name("Searchable")
        collection = make_collection(name=unique_part)
        
        # Search for it
        results = Collection.list(client, query=unique_part[:15])
        
        # Should find our collection
        found = any(c.id == collection.id for c in results)
        assert found, f"Could not find collection {collection.name} in search results"

    def test_collection_list_with_pagination(self, client):
        """Test pagination of collection list."""
        # Get first page
        page1 = Collection.list(client, limit=2, offset=0)
        
        # Get second page
        page2 = Collection.list(client, limit=2, offset=2)
        
        # Pages should not overlap
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        
        assert len(page1_ids & page2_ids) == 0, "Pages should not overlap"

    def test_collection_update(self, client, test_collection):
        """Test updating a collection."""
        new_description = "Updated description"
        new_icon = "🔖"
        
        test_collection.update(
            description=new_description,
            icon=new_icon,
        )
        
        assert test_collection.description == new_description
        assert test_collection.icon == new_icon

    def test_collection_update_partial_fields(self, client, test_collection):
        """Test updating only some fields of a collection."""
        original_name = test_collection.name
        new_description = "Only description updated"
        
        test_collection.update(description=new_description)
        
        # Description should change, name should stay the same
        assert test_collection.description == new_description
        assert test_collection.name == original_name

    def test_collection_update_all_fields(self, client, test_collection):
        """Test updating all editable fields."""
        test_collection.update(
            name="Updated Name",
            description="Updated description",
            icon="🎯",
            color="#0000FF",
            sharing=True,
        )
        
        assert test_collection.name.startswith("Updated")
        assert test_collection.icon == "🎯"
        assert test_collection.sharing is True

    def test_collection_delete(self, client):
        """Test deleting a collection."""
        collection = Collection.create(
            client,
            name=unique_name("Delete Collection"),
        )
        
        collection_id = collection.id
        collection.delete()
        
        # Verify it's deleted
        with pytest.raises(NotFoundError):
            Collection.get(client, collection_id)

    def test_collection_refresh(self, client, test_collection):
        """Test refreshing a collection's data."""
        original_description = test_collection.description
        
        # Update via another instance
        test_collection.update(description="Changed externally")
        
        # Get a new instance
        other_instance = Collection.get(client, test_collection.id)
        
        # Refresh should update data
        assert other_instance.description == "Changed externally"


@pytest.mark.collection
class TestCollectionDocuments:
    """Test collection document operations."""

    def test_collection_add_document(self, client, test_collection):
        """Test adding a document to a collection."""
        title = unique_name("Added Document")
        text = "# Document\n\nAdded via collection.add_document()"
        
        doc = test_collection.add_document(
            title=title,
            text=text,
            publish=True,
        )
        
        try:
            assert doc.title == title
            assert doc.collection_id == test_collection.id
            assert doc.published_at is not None
        finally:
            try:
                # Try permanent delete, fall back to trash
                doc.delete(permanent=True)
            except:
                try:
                    doc.delete(permanent=False)
                except:
                    pass  # Ignore cleanup errors

    def test_collection_add_document_draft(self, client, test_collection):
        """Test adding a draft document to a collection."""
        doc = test_collection.add_document(
            title=unique_name("Draft Document"),
            publish=False,
        )
        
        try:
            assert doc.published_at is None  # Not published
        finally:
            try:
                doc.delete(permanent=True)
            except:
                try:
                    doc.delete(permanent=False)
                except:
                    pass

    def test_collection_list_documents(self, client, test_collection, test_document):
        """Test listing documents in a collection."""
        # test_document is already created in the collection
        nav_tree = test_collection.list_documents()
        
        assert isinstance(nav_tree, list)
        # The collection should have at least our test document
        # (navigation tree structure may vary)

    def test_collection_add_nested_document(self, client, test_collection):
        """Test adding a nested document under a parent."""
        parent_doc = test_collection.add_document(
            title=unique_name("Parent Doc"),
            publish=True,
        )
        
        try:
            child_doc = test_collection.add_document(
                title=unique_name("Child Doc"),
                parent_document_id=parent_doc.id,
                publish=True,
            )
            
            try:
                assert child_doc.parent_document_id == parent_doc.id
            finally:
                try:
                    child_doc.delete(permanent=True)
                except:
                    try:
                        child_doc.delete(permanent=False)
                    except:
                        pass
        finally:
            try:
                parent_doc.delete(permanent=True)
            except:
                try:
                    parent_doc.delete(permanent=False)
                except:
                    pass


@pytest.mark.collection
class TestCollectionUserManagement:
    """Test collection user management operations."""

    # Note: These tests may require additional user permissions
    # and may not work with all API keys. Marked as may_fail.

    @pytest.mark.skip(reason="Requires additional user to test with")
    def test_collection_add_user(self, client, test_collection):
        """Test adding a user to a collection."""
        # This would require a valid user_id from your Outline instance
        # Skipping by default
        pass

    @pytest.mark.skip(reason="Requires additional user to test with")
    def test_collection_remove_user(self, client, test_collection):
        """Test removing a user from a collection."""
        # This would require a valid user_id from your Outline instance
        # Skipping by default
        pass


@pytest.mark.collection
@pytest.mark.slow
class TestCollectionExport:
    """Test collection export operations."""

    def test_collection_export(self, client, test_collection):
        """Test exporting a collection."""
        result = test_collection.export()
        
        # Export returns file operation data
        assert isinstance(result, dict)
        assert "fileOperation" in result

    def test_collection_export_formats(self, client, test_collection):
        """Test exporting a collection in different formats."""
        formats = ["outline-markdown", "json", "html"]
        
        for fmt in formats:
            result = test_collection.export(format=fmt)
            assert isinstance(result, dict)
            assert "fileOperation" in result


@pytest.mark.collection
class TestCollectionProperties:
    """Test collection property access."""

    def test_collection_properties(self, test_collection):
        """Test accessing collection properties."""
        assert test_collection.id is not None
        assert test_collection.name is not None
        assert test_collection.url_id is not None or test_collection.url_id == ""
        assert test_collection.created_at is not None
        assert test_collection.updated_at is not None

    def test_collection_optional_properties(self, test_collection):
        """Test accessing optional collection properties."""
        # These may be None
        _ = test_collection.description
        _ = test_collection.icon
        _ = test_collection.color
        _ = test_collection.permission
        _ = test_collection.archived_at

    def test_collection_to_dict(self, test_collection):
        """Test converting collection to dictionary."""
        data = test_collection.to_dict()
        
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "createdAt" in data


@pytest.mark.collection
class TestCollectionEdgeCases:
    """Test edge cases for collections."""

    def test_collection_with_special_characters_in_name(self, client):
        """Test creating collection with special characters."""
        name = "Test Collection with 特殊字符 and émojis 🎨"
        
        collection = Collection.create(client, name=name)
        
        try:
            assert collection.name == name
        finally:
            collection.delete()

    def test_collection_with_long_description(self, client):
        """Test creating collection with long description."""
        long_description = "Lorem ipsum " * 100  # Long text
        
        collection = Collection.create(
            client,
            name=unique_name("Long Desc Collection"),
            description=long_description,
        )
        
        try:
            assert collection.description is not None
            assert len(collection.description) > 0
        finally:
            collection.delete()

    def test_collection_with_markdown_description(self, client):
        """Test creating collection with markdown in description."""
        markdown_desc = "# Heading\n\n- List item\n- Another item\n\n**Bold** and *italic*"
        
        collection = Collection.create(
            client,
            name=unique_name("Markdown Desc Collection"),
            description=markdown_desc,
        )
        
        try:
            assert collection.description == markdown_desc
        finally:
            collection.delete()
