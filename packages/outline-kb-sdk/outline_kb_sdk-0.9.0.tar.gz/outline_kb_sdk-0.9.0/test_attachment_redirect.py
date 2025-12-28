#!/usr/bin/env python3
"""Test that attachments.redirect works as expected."""

import os
import httpx
from outline import OutlineClient

# Load credentials from environment
url = os.getenv("TEST_OUTLINE_URL", "https://outline.bachi.ch")
key = os.getenv("TEST_OUTLINE_API_KEY", "ol_api_w4L4LQ6KmEjNDyr7PGghkVF8guhH0GrRVhIJiG")

# One of the attachment IDs we found
attachment_id = "af56d3a8-a5d6-475f-b744-348281aa4601"

print("=" * 80)
print("  Testing attachments.redirect Endpoint")
print("=" * 80)
print()
print(f"Attachment ID: {attachment_id}")
print()

# Test 1: Try using the client's request method to call attachments.redirect
client = OutlineClient(url, key)

print("[Test 1] Calling attachments.redirect via client.request()...")
try:
    # According to the API spec, attachments.redirect is a POST endpoint
    response = client.request("attachments.redirect", {"id": attachment_id})
    print(f"✅ Success!")
    print(f"Response: {response}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Try making a direct HTTP request to see the redirect
print("[Test 2] Making direct HTTP request to see redirect behavior...")
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Manually construct the URL
redirect_url = f"{url}/api/attachments.redirect"

# Make request but don't follow redirects automatically
with httpx.Client(follow_redirects=False, timeout=30) as http_client:
    try:
        response = http_client.post(
            redirect_url,
            json={"id": attachment_id},
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['location', 'content-type', 'content-length']:
                print(f"  {key}: {value}")
        
        if response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('location', 'No location header')
            print()
            print(f"✅ Redirects to: {location}")
            print()
            
            # Extract key from JWT if possible
            if 'sig=' in location:
                sig_start = location.find('sig=')
                sig = location[sig_start+4:]
                print(f"JWT token (sig parameter): {sig[:50]}...")
        else:
            print(f"Response body: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

client.close()

print()
print("=" * 80)
