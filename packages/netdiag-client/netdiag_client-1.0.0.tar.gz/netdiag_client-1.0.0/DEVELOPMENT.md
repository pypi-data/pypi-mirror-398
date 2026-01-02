# Development Guide

## Setup

```bash
# Create virtual environment
py -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Run Tests

```bash
# All tests
pytest tests/ -v

# Single test file
pytest tests/test_client.py -v

# Specific test
pytest tests/test_client.py::TestCheck::test_returns_response_for_valid_hostname -v
```

## Build Package

```bash
# Install build tools
pip install build

# Build sdist and wheel
py -m build
```

## Publish to PyPI

```bash
# Install twine
pip install twine

# Upload to PyPI
twine upload dist/*

# Or upload to TestPyPI first
twine upload --repository testpypi dist/*
```

## Project Structure

```
src/netdiag_client/
├── __init__.py     # Package exports
├── client.py       # NetDiagClient implementation
├── types.py        # Dataclasses for API types
└── errors.py       # Exception classes

tests/
└── test_client.py  # Integration tests (pytest)
```

## Code Style

- Python 3.10+ required
- Type hints everywhere
- Dataclasses for models (no pydantic dependency)
- httpx for HTTP client
