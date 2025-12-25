# msgmodel

[![PyPI version](https://badge.fury.io/py/msgmodel.svg)](https://badge.fury.io/py/msgmodel)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A unified Python library and CLI for interacting with multiple Large Language Model (LLM) providers with a **simple, consistent syntax**.

## Overview

`msgmodel` provides both a **Python library** and a **command-line interface** to interact with major LLM providers:
- **OpenAI** (GPT models) — Zero Data Retention available via automatic header
- **Google Gemini** (Paid tier recommended) — Configurable data policies
- **Anthropic Claude** — Standard API data handling

**Core Principle**: msgmodel itself is entirely stateless and ephemeral—it never retains your data. Provider-level data handling varies; see the Data Retention section for details on each provider's policies and available options.

## Features

- **Unified API**: Single `query()` and `stream()` functions work with all providers
- **Library & CLI**: Use as a Python module or command-line tool
- **Streaming support**: Stream responses in real-time
- **File attachments**: Process images, PDFs, and text files with in-memory BytesIO
- **Flexible configuration**: Dataclass-based configs with sensible defaults
- **Multiple API key sources**: Direct parameter, environment variable, or key file
- **Exception-based error handling**: Clean errors, no `sys.exit()` in library code
- **Type-safe**: Full type hints throughout
- **Stateless design**: msgmodel never retains your data; all processing is ephemeral

## Installation

### From PyPI (Recommended)

```bash
pip install msgmodel
```

### From Source

```bash
# Clone the repository
git clone https://github.com/LeoooDias/msgmodel.git
cd msgmodel

# Install the package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Prerequisites

- Python 3.10 or higher
- API keys from the providers you wish to use

## Quick Start

### As a Library

```python
from msgmodel import query, stream

# Simple query (uses OPENAI_API_KEY env var)
response = query("openai", "What is Python?")
print(response.text)

# With explicit API key
response = query("gemini", "Hello!", api_key="your-api-key")

# Streaming
for chunk in stream("openai", "Tell me a story"):
    print(chunk, end="", flush=True)

# With file attachment (in-memory BytesIO only)
import io
file_obj = io.BytesIO(your_binary_data)
response = query("gemini", "Describe this image", file_like=file_obj, filename="photo.jpg")

# With custom configuration
from msgmodel import OpenAIConfig

config = OpenAIConfig(model="gpt-4o-mini", temperature=0.7, max_tokens=2000)
response = query("openai", "Write a poem", config=config)
```

### As a CLI

```bash
# Basic usage
python -m msgmodel -p openai "What is Python?"

# Using shorthand provider codes
python -m msgmodel -p g "Hello, Gemini!"    # g = gemini
python -m msgmodel -p o "Hello, OpenAI!"    # o = openai
python -m msgmodel -p c "Hello, Claude!"    # c = claude/anthropic

# With streaming
python -m msgmodel -p openai "Tell me a story" --stream

# From a file
python -m msgmodel -p gemini -f prompt.txt

# With system instruction
python -m msgmodel -p claude "Analyze this" -i "You are a data analyst"

# With file attachment (base64 inline)
python -m msgmodel -p gemini "Describe this" -b image.jpg

# Custom parameters
python -m msgmodel -p openai "Hello" -m gpt-4o-mini -t 500 --temperature 0.7

# Get full JSON response instead of just text
python -m msgmodel -p openai "Hello" --json

# Verbose output (shows model, provider, token usage)
python -m msgmodel -p openai "Hello" -v
```

## API Key Configuration

API keys can be provided in three ways (in order of priority):

1. **Direct parameter**: `query("openai", "Hello", api_key="sk-...")`
2. **Environment variable**:
   - `OPENAI_API_KEY` for OpenAI
   - `GOOGLE_API_KEY` for Gemini
   - `ANTHROPIC_API_KEY` for Claude/Anthropic
3. **Key file** in current directory:
   - `openai-api.key`
   - `gemini-api.key`
   - `anthropic-api.key`

## Configuration

Each provider has its own configuration dataclass with sensible defaults:

```python
from msgmodel import OpenAIConfig, GeminiConfig, AnthropicConfig

# OpenAI configuration
openai_config = OpenAIConfig(
    model="gpt-4o",           # Model to use
    temperature=1.0,          # Sampling temperature
    top_p=1.0,                # Nucleus sampling
    max_tokens=1000,          # Max output tokens
)

# Gemini configuration
gemini_config = GeminiConfig(
    model="gemini-2.5-flash",
    temperature=1.0,
    top_p=0.95,
    top_k=40,
    safety_threshold="BLOCK_NONE",
)

# Anthropic/Claude configuration
anthropic_config = AnthropicConfig(
    model="claude-haiku-4-5-20251001",  # Default; also: claude-sonnet-4-20250514
    temperature=1.0,
    top_p=1.0,
    max_tokens=1000,
)
```

## Data Retention & Privacy

`msgmodel` is designed with **statelessness** as a core principle—the library itself never retains your data. Provider-level data handling varies, and this section helps you understand your options.

### OpenAI (Zero Data Retention by Default)

When using OpenAI:

- **Default behavior**: The `X-OpenAI-No-Store` header is automatically sent, opting out of data retention for model training
- **What this means**: OpenAI does **not** use these interactions for service improvements or model training
- **File handling**: All files are base64-encoded and embedded inline in prompts—no server-side uploads

**Note**: OpenAI's API logs may retain minimal metadata (timestamps, API version, token counts) for ~30 days for debugging purposes, but not the actual prompt/response content.

```python
from msgmodel import query

response = query("openai", "Your prompt here")
# Zero Data Retention header is sent automatically
```

### Google Gemini

Google Gemini's data retention policy depends on your service tier:

**Paid Services (Google Cloud Billing + Paid Quota)**
- Data is NOT used for model training or product improvement
- Prompts and responses may be retained temporarily for abuse detection (typically 24-72 hours)
- Base64-encoded inline file embedding—no persistent storage

**Free Tier**
- Google may retain data for model training. Review Google's terms if this matters for your use case.

```python
from msgmodel import query

# Gemini request - data handling depends on your account tier
response = query("gemini", "Your prompt here", api_key="your-api-key")
```

**Learn more**: [Google Gemini API Terms](https://ai.google.dev/gemini-api/terms)

### Anthropic Claude

When using Anthropic Claude:

- **Default behavior**: Anthropic does not use API data for model training by default
- **Data retention**: Data may be retained temporarily for safety monitoring and abuse prevention
- **File handling**: Base64-encoded inline embedding

```python
from msgmodel import query

response = query("claude", "Your prompt here")
# or: query("anthropic", ...) or query("c", ...)
```

**Learn more**: [Anthropic Privacy Policy](https://www.anthropic.com/legal/privacy)

### Summary Comparison

| Provider | Training Data Opt-Out | Data Retention | Notes |
|----------|----------------------|----------------|-------|
| **OpenAI** | ✅ Automatic | None (ZDR header) | Metadata ~30 days |
| **Gemini (Paid)** | ✅ Yes | ~24-72 hours (abuse monitoring) | Requires paid tier |
| **Gemini (Free)** | ❌ No | Per Google's terms | Review terms |
| **Anthropic** | ✅ Default | Temporary (safety) | Standard API behavior |

**For maximum privacy**: Use OpenAI with the default ZDR settings, or Anthropic's API. For Gemini, use the paid tier.

## File Uploads

### The BytesIO-Only Approach

All file uploads in msgmodel v3.2.0+ use **in-memory BytesIO objects** with base64 inline encoding:

```python
import io
from msgmodel import query

# Read file into memory
with open("document.pdf", "rb") as f:
    file_data = f.read()

# Create BytesIO object
file_obj = io.BytesIO(file_data)

# Query with file
response = query(
    "openai",
    "Summarize this document",
    file_like=file_obj,
    filename="document.pdf"  # Enables MIME type detection
)
```

**Why BytesIO?**
- Stateless operation—each request is completely independent
- No server-side file uploads (Files API not used)
- Files are base64-encoded inline in prompts

**File Size Limits**
- **OpenAI**: ~15-20MB practical limit (base64 overhead + token limits)
- **Gemini**: ~22MB practical limit (base64 overhead + token limits)
- **Anthropic**: ~20MB practical limit (base64 overhead + token limits)

If API returns a size-related error, the file exceeds practical limits for that provider.

## Error Handling

The library uses exceptions instead of `sys.exit()`:

```python
from msgmodel import query, MsgModelError, AuthenticationError, APIError

try:
    response = query("openai", "Hello")
except AuthenticationError as e:
    print(f"API key issue: {e}")
except APIError as e:
    print(f"API call failed: {e}")
    print(f"Status code: {e.status_code}")
except MsgModelError as e:
    print(f"General error: {e}")
```

## Response Object

The `query()` function returns an `LLMResponse` object:

```python
response = query("openai", "Hello")

print(response.text)          # The generated text
print(response.model)         # Model used (e.g., "gpt-4o")
print(response.provider)      # Provider name (e.g., "openai")
print(response.usage)         # Token usage dict (if available)
print(response.raw_response)  # Complete API response
```

## Project Structure

```
msgmodel/
├── msgmodel/                    # Python package
│   ├── __init__.py              # Public API exports
│   ├── __main__.py              # CLI entry point
│   ├── core.py                  # Core query/stream functions
│   ├── config.py                # Configuration dataclasses
│   ├── exceptions.py            # Custom exceptions
│   ├── py.typed                 # PEP 561 marker for typed package
│   └── providers/               # Provider implementations
│       ├── __init__.py
│       ├── openai.py
│       └── gemini.py
├── tests/                       # Test suite
│   ├── test_config.py
│   ├── test_core.py
│   └── test_exceptions.py
├── pyproject.toml               # Package configuration
├── LICENSE                      # MIT License
├── MANIFEST.in                  # Distribution manifest
├── requirements.txt             # Dependencies
└── README.md
```

## CLI Usage

After installation, the `msgmodel` command is available:

```bash
# Basic usage
msgmodel -p openai "What is Python?"

# Or using python -m
python -m msgmodel -p openai "What is Python?"

# Provider shortcuts: o=openai, g=gemini
msgmodel -p g "Hello, Gemini!"

# With streaming
msgmodel -p openai "Tell me a story" --stream

# From a file
msgmodel -p gemini -f prompt.txt
```

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=msgmodel
```

## Building & Publishing

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to PyPI (requires PyPI account)
twine upload dist/*

# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Leo Dias

