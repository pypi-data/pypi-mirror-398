# Setup Guide

## For Users

### Installation

```bash
pip install outline-sdk
```

### Quick Start

```python
from outline import OutlineClient, Collection

client = OutlineClient(
    api_url="https://your.outline.com",
    api_key="your-api-key"
)

# Create a collection
collection = Collection.create(client, name="My Docs", icon="📚")

# Add a document
doc = collection.add_document(
    title="Hello World",
    text="# My First Document",
    publish=True
)
```

Get your API key from Outline: **Settings → API & Apps**

## For Developers

### Prerequisites

- Python 3.9 or higher
- Access to an Outline instance for testing

### Setup Development Environment

1. **Clone and create virtual environment:**

```bash
git clone https://github.com/yourusername/outline-sdk-python
cd outline-sdk-python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

2. **Install dependencies:**

```bash
pip install -e ".[dev]"
```

3. **Configure test environment:**

```bash
cp .env.example .env
# Edit .env with your test credentials
```

⚠️ **Important:** Use a test instance, not production!

### Development Workflow

1. **Run tests:**
```bash
pytest
```

2. **Check code quality:**
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

3. **Run examples:**
```bash
python examples/basic_usage.py
```

### Project Structure

```
outline-sdk-python/
├── src/outline/           # Main SDK code
│   ├── client.py         # HTTP client
│   ├── exceptions.py     # Custom exceptions
│   └── models/           # API models
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation
└── pyproject.toml        # Project config
```

### Building the Package

```bash
pip install build
python -m build
ls dist/
```

## Getting Help

- 📖 [README](README.md) - API documentation
- 🧪 [TESTING](TESTING.md) - Testing guide
- 🚀 [QUICKSTART](QUICKSTART.md) - Quick start guide
