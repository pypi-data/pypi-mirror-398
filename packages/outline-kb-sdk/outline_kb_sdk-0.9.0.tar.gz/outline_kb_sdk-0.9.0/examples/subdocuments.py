"""
Subdocument (nested documents) examples.
"""

from outline import OutlineClient, Document


# Initialize client
client = OutlineClient(
    api_url="https://your-outline.com",
    api_key="your-api-key"
)

# Get parent document
parent = Document.get(client, "your-document-id")


# Example 1: Create a subdocument
child = parent.add_subdocument(
    title="Chapter 1: Introduction",
    text="# Chapter 1\n\nThis is a subdocument.",
    publish=True
)
print(f"Created: {child.title}")


# Example 2: List subdocuments
children = parent.list_subdocuments()
for doc in children:
    print(f"- {doc.title}")


# Example 3: Check if document has subdocuments
if parent.has_subdocuments():
    print(f"{parent.title} has {len(children)} subdocument(s)")
