# Testing Guide

This guide explains how to run and write tests for the Outline SDK.

## Quick Start

### Prerequisites

1. **Install dependencies:**
   ```bash
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Configure test environment:**
   
   Create or update `.env` file in project root:
   ```bash
   TEST_OUTLINE_URL=https://your-outline-instance.com
   TEST_OUTLINE_API_KEY=ol_api_your_key_here
   ```

### Running Tests

**Run all tests:**
```bash
pytest tests/
```

**Run specific test file:**
```bash
pytest tests/test_collections.py -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=src/outline --cov-report=html --cov-report=term
```

## Test Structure

```
tests/
├── conftest.py              # Fixtures and test configuration
├── test_collections.py      # Collection operation tests
├── test_documents.py        # Document operation tests
├── test_comments.py         # Comment operation tests
├── test_attachments.py      # Attachment operation tests
├── test_error_handling.py   # Error handling tests
├── test_integration.py      # Integration/workflow tests
└── utils/
    └── helpers.py           # Test helper functions
```

## Writing Tests

### Basic Test Template

```python
import pytest
from outline import Collection
from tests.utils.helpers import unique_name

def test_collection_create(client):
    """Test creating a collection."""
    name = unique_name("Collection")
    collection = Collection.create(client, name=name)
    
    try:
        assert collection.name == name
        assert collection.id is not None
    finally:
        collection.delete()
```

### Using Fixtures

```python
def test_with_fixture(test_collection):
    """Test using fixture - auto cleanup."""
    assert test_collection.name is not None
    # No manual cleanup needed
```

## Available Fixtures

- `client` - Configured OutlineClient instance
- `test_collection` - Auto-cleanup test collection
- `test_document` - Auto-cleanup test document
- `make_collection()` - Create multiple collections
- `make_document()` - Create multiple documents
- `make_comment()` - Create multiple comments

## Troubleshooting

### Tests are Skipped

Check `.env` file has correct credentials:
```bash
TEST_OUTLINE_URL=https://your-instance.com
TEST_OUTLINE_API_KEY=ol_api_...
```

### Import Errors

Install package in development mode:
```bash
source venv/bin/activate
pip install -e .
```

### Coverage Reports

Generate HTML coverage report:
```bash
pytest tests/ --cov=src/outline --cov-report=html
open htmlcov/index.html  # View report
```

## More Information

- [README](README.md) - Main documentation
- [QUICKSTART](QUICKSTART.md) - Quick start guide
- [SETUP](SETUP.md) - Development setup
