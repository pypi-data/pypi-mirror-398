"""
Basic Usage Example for Outline SDK.

This example demonstrates the core functionality of the SDK.
"""

import os

from dotenv import load_dotenv

from outline import Collection, OutlineClient

# Load environment variables
load_dotenv()


def main():
    """Run basic usage example."""
    # Initialize client
    client = OutlineClient(
        api_url=os.getenv("TEST_OUTLINE_URL", "https://your.outline.com"),
        api_key=os.getenv("TEST_OUTLINE_API_KEY", "your-api-key"),
    )

    print("🚀 Outline SDK - Basic Usage Example\n")

    # Create a collection
    print("📚 Creating a new collection...")
    collection = Collection.create(
        client,
        name="SDK Example Collection",
        description="This collection was created by the Outline SDK example",
        icon="🎯",
        color="#4A90E2",
    )
    print(f"✅ Created collection: {collection.name} (ID: {collection.id})\n")

    # List all collections
    print("📋 Listing all collections...")
    all_collections = Collection.list(client, limit=5)
    for col in all_collections[:5]:
        print(f"  - {col.icon} {col.name}")
    print()

    # Create a document
    print("📝 Creating a new document...")
    doc = collection.add_document(
        title="Welcome to the SDK",
        text="""# Welcome!

This document was created using the Outline SDK for Python.

## Features

- ✨ Rich models with intuitive methods
- 🔒 Type-safe interfaces
- 📝 Comprehensive documentation

## Example Code

```python
from outline import OutlineClient, Collection

client = OutlineClient(api_url, api_key)
collection = Collection.create(client, name="My Docs")
```

Happy documenting! 🎉
""",
        publish=True,
    )
    print(f"✅ Created document: {doc.title} (ID: {doc.id})\n")

    # Update the document
    print("📝 Updating the document...")
    doc.update(text=doc.text + "\n\n## Updates\n\nThis section was added by the SDK!")
    print("✅ Document updated\n")

    # Add a comment
    print("💬 Adding a comment...")
    comment = doc.add_comment("This is a great example document!")
    print(f"✅ Comment added (ID: {comment.id})\n")

    # List comments
    print("📋 Listing comments...")
    comments = doc.list_comments()
    for c in comments:
        print(f"  - Comment {c.id}")
    print()

    # Get document info
    print("ℹ️  Document Information:")
    print(f"  Title: {doc.title}")
    print(f"  Created: {doc.created_at}")
    print(f"  Updated: {doc.updated_at}")
    print(f"  Published: {doc.published_at}")
    print(f"  Collection: {doc.collection_id}")
    print()

    # Cleanup
    print("🧹 Cleaning up...")

    # Delete comment
    comment.delete()
    print("  ✅ Deleted comment")

    # Delete document
    doc.delete(permanent=True)
    print("  ✅ Deleted document")

    # Delete collection
    collection.delete()
    print("  ✅ Deleted collection")

    print("\n✨ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
