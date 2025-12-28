"""
Attachment upload and download examples.
"""

from outline import OutlineClient, Document, Attachment
from pathlib import Path


# Initialize client
client = OutlineClient(
    api_url="https://your-outline.com",
    api_key="your-api-key"
)

# Get document
doc = Document.get(client, "your-document-id")


# Example 1: Upload a file
attachment = Attachment.create_and_upload(
    client,
    "report.pdf",
    document_id=doc.id
)
print(f"Uploaded: {attachment.id}")


# Example 2: Upload from bytes
content = b"Hello, World!"
attachment = Attachment.create(
    client,
    name="hello.txt",
    content_type="text/plain",
    size=len(content),
    document_id=doc.id
)
attachment.upload_from_bytes(content)


# Example 3: List attachments in a document
attachments = doc.list_attachments()
for ref in attachments:
    print(f"- {ref.name}: {ref.size} bytes")


# Example 4: Download an attachment
if attachments:
    # Download to memory
    content = doc.download_attachment(attachments[0].id)
    
    # Download to file
    doc.download_attachment(attachments[0].id, "output.pdf")
