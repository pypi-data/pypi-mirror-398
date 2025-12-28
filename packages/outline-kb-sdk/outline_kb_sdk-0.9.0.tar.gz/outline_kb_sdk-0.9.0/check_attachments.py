#!/usr/bin/env python3
"""Script to fetch a document and check for attachment information."""

import json
import os
from outline import OutlineClient

# Load credentials from environment
url = os.getenv("TEST_OUTLINE_URL", "https://outline.bachi.ch")
key = os.getenv("TEST_OUTLINE_API_KEY", "ol_api_w4L4LQ6KmEjNDyr7PGghkVF8guhH0GrRVhIJiG")

# Document ID from the URL: https://outline.bachi.ch/doc/test-with-attachments-NHm0Ph5e4v
doc_id = "NHm0Ph5e4v"

print("=" * 80)
print("  Examining Document API Response for Attachment Information")
print("=" * 80)
print()
print(f"Document ID: {doc_id}")
print(f"Outline URL: {url}")
print()

# Create client
client = OutlineClient(url, key)

# Fetch the document using the raw API request
print("Fetching document data...")
response = client.request("documents.info", {"id": doc_id})

print()
print("=" * 80)
print("  RAW API RESPONSE")
print("=" * 80)
print()
print(json.dumps(response, indent=2))
print()

# Check for attachment-related fields
print("=" * 80)
print("  ATTACHMENT-RELATED FIELDS")
print("=" * 80)
print()

data = response.get("data", {})
attachment_fields = [
    "attachments",
    "attachment",
    "attachmentIds",
    "files",
    "uploads",
    "embeds"
]

found_fields = []
for field in attachment_fields:
    if field in data:
        found_fields.append(field)
        print(f"✅ Found field: {field}")
        print(f"   Value: {json.dumps(data[field], indent=6)}")
        print()

if not found_fields:
    print("❌ No attachment-related fields found in the response")
    print()
    print("Available top-level fields in 'data':")
    for key in sorted(data.keys()):
        print(f"   - {key}")
    print()

# Check if there are attachment references in the text content
print("=" * 80)
print("  CHECKING TEXT CONTENT FOR ATTACHMENT REFERENCES")
print("=" * 80)
print()

text = data.get("text", "")
if "![](" in text or "![" in text:
    print("✅ Found image markdown references in text")
    print()
    print("Text content (first 500 chars):")
    print(text[:500])
    print()
else:
    print("❌ No image markdown references found in text")
    print()

client.close()
