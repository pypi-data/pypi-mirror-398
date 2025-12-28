#!/usr/bin/env python3
"""Extract attachment IDs from Outline document text."""

import json
import os
import re
from outline import OutlineClient

# Load credentials from environment
url = os.getenv("TEST_OUTLINE_URL", "https://outline.bachi.ch")
key = os.getenv("TEST_OUTLINE_API_KEY", "ol_api_w4L4LQ6KmEjNDyr7PGghkVF8guhH0GrRVhIJiG")

# Document ID from the URL
doc_id = "NHm0Ph5e4v"

print("=" * 80)
print("  Extracting Attachment IDs from Document")
print("=" * 80)
print()
print(f"Document ID: {doc_id}")
print()

# Create client
client = OutlineClient(url, key)

# Fetch the document
response = client.request("documents.info", {"id": doc_id})
data = response.get("data", {})
text = data.get("text", "")

print("Document Title:", data.get("title"))
print()

# Regular expression to find attachment IDs in the text
# Pattern: /api/attachments.redirect?id=<uuid>
pattern = r'/api/attachments\.redirect\?id=([a-f0-9-]+)'

# Find all attachment IDs
attachment_ids = re.findall(pattern, text)

print("=" * 80)
print("  EXTRACTED ATTACHMENT IDs")
print("=" * 80)
print()

if attachment_ids:
    print(f"✅ Found {len(attachment_ids)} attachment(s):\n")
    for i, att_id in enumerate(attachment_ids, 1):
        print(f"{i}. {att_id}")
    print()
    
    # Try to get more info about these attachments
    print("=" * 80)
    print("  FETCHING ATTACHMENT DETAILS")
    print("=" * 80)
    print()
    
    for i, att_id in enumerate(attachment_ids, 1):
        try:
            # Try the attachments.info endpoint
            att_response = client.request("attachments.info", {"id": att_id})
            print(f"Attachment {i} ({att_id}):")
            print(json.dumps(att_response.get("data", {}), indent=2))
            print()
        except Exception as e:
            print(f"Attachment {i} ({att_id}):")
            print(f"  Error fetching details: {e}")
            print()
else:
    print("❌ No attachment IDs found in document text")
    print()

# Show the raw text to see the attachment references
print("=" * 80)
print("  DOCUMENT TEXT (showing attachment references)")
print("=" * 80)
print()
print(text)
print()

client.close()
