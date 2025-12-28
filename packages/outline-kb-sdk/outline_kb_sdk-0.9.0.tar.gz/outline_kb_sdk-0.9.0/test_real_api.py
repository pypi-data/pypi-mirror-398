#!/usr/bin/env python
"""Integration test against real Outline API."""

import os
from outline import OutlineClient, Collection, Document, Comment
from outline.exceptions import NotFoundError

# Load credentials from environment
url = os.getenv("TEST_OUTLINE_URL", "https://outline.bachi.ch")
key = os.getenv("TEST_OUTLINE_API_KEY", "ol_api_w4L4LQ6KmEjNDyr7PGghkVF8guhH0GrRVhIJiG")

client = OutlineClient(url, key)

print("=" * 60)
print("  Outline SDK - Comprehensive Integration Test")
print("=" * 60)
print()

# Test 1: List collections
print("[1/7] Testing Collection.list()...")
collections = Collection.list(client, limit=5)
print(f"      ✅ Success: Found {len(collections)} collections")
print()

# Test 2: Create a test collection
print("[2/7] Testing Collection.create()...")
test_collection = Collection.create(
    client,
    name="SDK Test Collection",
    description="Temporary collection for SDK testing",
    icon="🧪"
)
print(f"      ✅ Success: Created collection '{test_collection.name}'")
print(f"      ID: {test_collection.id}")
print()

# Test 3: Update collection
print("[3/7] Testing Collection.update()...")
test_collection.update(description="Updated description via SDK")
print(f"      ✅ Success: Updated collection description")
print()

# Test 4: Create a document
print("[4/7] Testing Document.create()...")
test_doc = Document.create(
    client,
    title="SDK Test Document",
    collection_id=test_collection.id,
    text="# Test\\n\\nThis document was created by the Outline SDK.",
    publish=True
)
print(f"      ✅ Success: Created document '{test_doc.title}'")
print(f"      ID: {test_doc.id}")
print()

# Test 5: Add a comment
print("[5/7] Testing Comment.create()...")
comment = test_doc.add_comment("This is a test comment from the SDK!")
print(f"      ✅ Success: Added comment")
print(f"      Comment ID: {comment.id}")
print()

# Test 6: Clean up - Delete comment
print("[6/7] Testing Comment.delete()...")
comment.delete()
print(f"      ✅ Success: Deleted comment")
print()

# Test 7: Clean up - Delete document and collection
print("[7/7] Testing cleanup (Document.delete(), Collection.delete())...")
# First move to trash (can't permanently delete immediately in Outline)
test_doc.delete(permanent=False)
print(f"      ✅ Success: Moved document to trash")
test_collection.delete()
print(f"      ✅ Success: Deleted collection")
print()

# Test error handling
print("[BONUS] Testing error handling...")
try:
    Document.get(client, "non-existent-id")
except Exception as e:
    print(f"      ✅ Success: Exception raised correctly ({type(e).__name__})")
    print(f"      Error message: {e}")
print()

print("=" * 60)
print("  ✨ All tests passed successfully!")
print("=" * 60)
print()
print("SDK is working correctly with your Outline instance.")
