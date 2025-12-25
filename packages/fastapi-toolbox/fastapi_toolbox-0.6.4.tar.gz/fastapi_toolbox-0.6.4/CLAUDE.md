# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 使用语言

使用中文

## Project Overview

This is a Python library (`fastapi-toolbox`) that provides common utilities for working with FastAPI applications. The project is in early development stage with minimal structure currently in place.

## Development Environment

- **Python Version**: 3.12 (specified in `.python-version`)
- **Package Manager**: uv (modern Python package and project manager)
- **Dependencies**: FastAPI and Starlette for web framework functionality

## Project Structure

- `__init__.py`: Package initialization, exports StaticFilesCache
- `static_files.py`: Static files utilities including StaticFilesCache class
- `main.py`: Entry point with basic hello world functionality
- `pyproject.toml`: Project configuration and metadata
- `.python-version`: Specifies Python 3.12 requirement

## Common Commands

- **Install dependencies**: `uv sync`
- **Add new dependency**: `uv add <package-name>`
- **Add development dependency**: `uv add --dev <package-name>`
- **Run the main module**: `uv run python main.py`
- **Install in development mode**: `uv pip install -e .`
- **Create virtual environment**: `uv venv`

## Publishing to PyPI

1. **Build the package**: `uv build`
2. **Upload to TestPyPI (recommended first)**: `uv publish --repository testpypi --token pypi-your-token`
3. **Upload to PyPI**: `uv publish --token pypi-your-token`

Before publishing:
- Update author information in pyproject.toml
- Check if package name is available on PyPI
- Test the package locally

## Available Utilities

### StaticFilesCache

A FastAPI StaticFiles subclass that adds configurable cache control headers for HTML and text files.

```python
from fastapi_utils import StaticFilesCache

# Use with custom cache control
app.mount("/static", StaticFilesCache(directory="static", cachecontrol="max-age=3600"))
```

## Notes

- StaticFilesCache automatically adds cache control headers to .html and .txt files
- Other file types use the default StaticFiles behavior
- Cache control header is configurable via the `cachecontrol` parameter