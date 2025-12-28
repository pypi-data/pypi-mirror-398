# Outline SDK - Quick Start Guide

Get started with the Outline SDK in minutes!

## Installation

The SDK has been installed in development mode:

```bash
# Already done:
source venv/bin/activate
pip install -e '.[dev]'
```

## Test the Installation

```bash
# Verify imports work
source venv/bin/activate
python -c "from outline import OutlineClient, Collection, Document; print('✅ SDK ready!')"
```

## Basic Usage

### 1. Get Your API Key

1. Go to your Outline instance
2. Click Settings (⚙️) → API & Apps
3. Create a new API key
4. Copy the key (starts with `ol_api_`)

### 2. Set Up Environment

Create a `.env` file:

```bash
cat > .env << 'EOF'
TEST_OUTLINE_URL=https://your-outline-instance.com
TEST_OUTLINE_API_KEY=your-api-key-here
EOF
```

### 3. Run Your First Script

Create `test.py`:

```python
from outline import OutlineClient, Collection

# Initialize client
client = OutlineClient(
    api_url="https://your-instance.com",
    api_key="your-api-key"
)

# List collections
collections = Collection.list(client)
for col in collections:
    print(f"📚 {col.name}")

# Create a collection
new_collection = Collection.create(
    client,
    name="My First Collection",
    icon="🚀"
)
print(f"✅ Created: {new_collection.name}")

# Add a document
doc = new_collection.add_document(
    title="Hello World",
    text="# My First Document\n\nCreated with the SDK!",
    publish=True
)
print(f"✅ Created document: {doc.title}")

# Cleanup
doc.delete(permanent=True)
new_collection.delete()
print("✅ Cleaned up!")
```

Run it:

```bash
python test.py
```

## Common Operations

### Collections

```python
from outline import Collection

# Create
collection = Collection.create(client, name="Docs", icon="📚")

# Get by ID
collection = Collection.get(client, "collection-id")

# List all
collections = Collection.list(client)

# Update
collection.update(name="New Name", description="Updated")

# Delete
collection.delete()
```

### Documents

```python
from outline import Document

# Create
doc = Document.create(
    client,
    title="My Doc",
    collection_id="collection-id",
    text="# Content here",
    publish=True
)

# Update
doc.update(text="# Updated content")

# Move to another collection
doc.move(collection_id="new-collection-id")

# Delete
doc.delete()  # Moves to trash
doc.delete(permanent=True)  # Permanent delete
```

### Comments

```python
# Add comment to a document
comment = doc.add_comment("Great work!")

# Reply to a comment
reply = doc.add_comment(
    "I agree!",
    parent_comment_id=comment.id
)

# List all comments
comments = doc.list_comments()
```

## Error Handling

```python
from outline.exceptions import (
    NotFoundError,
    AuthenticationError,
    RateLimitError
)

try:
    doc = Document.get(client, "invalid-id")
except NotFoundError:
    print("Document not found")
except AuthenticationError:
    print("API key is invalid")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
```

## Running Tests

If you have a test Outline instance:

```bash
# Configure .env first
cp .env.example .env
# Edit .env with your test instance credentials

# Run tests
pytest

# Run with coverage
pytest --cov=src/outline

# Run specific test
pytest tests/test_collections.py -v
```

## Running Examples

```bash
# Run the basic usage example
python examples/basic_usage.py
```

## Next Steps

- Read the [README](README.md) for complete documentation
- Check [examples/](examples/) for more examples
- Review [SETUP.md](SETUP.md) for development setup
- Explore the API spec in [docs/api/spec3.yml](docs/api/spec3.yml)

## Troubleshooting

### "Module not found: outline"

```bash
# Reinstall in editable mode
pip install -e .
```

### "Import errors"

```bash
# Make sure venv is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Type hints errors (Pylance)

The SDK works fine despite some type hint warnings. These are cosmetic issues about using modern Python 3.9+ type hints vs older `typing.Dict`/`typing.List`.

## Getting Help

- 📝 Documentation: [README.md](README.md)
- 🐛 Issues: Create an issue on GitHub
- 💬 Questions: Check the discussions

Happy coding! 🎉
