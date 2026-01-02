# Zerox Sync

A synchronous Python library for OCR and document extraction using Google's Gemini Vision API. This is a rewrite of [pyzerox](https://github.com/getomni-ai/zerox) that removes async wrappers and replaces litellm with direct Gemini API integration.

## Features

- **Synchronous API**: No async/await complexity, simple function calls
- **Direct Gemini Integration**: Uses Google's Gemini API directly without litellm dependency
- **PDF to Markdown**: Convert PDFs to structured markdown using vision models
- **Concurrent Processing**: Process multiple pages in parallel using ThreadPoolExecutor
- **Selective Page Processing**: Extract specific pages from PDFs
- **Format Consistency**: Maintain formatting across pages
- **Simple Setup**: Just set GOOGLE_API_KEY and go

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add zerox-sync to your project
uv add zerox-sync
```

### Using pip

```bash
pip install zerox-sync
```

### System Dependencies

You'll need poppler installed for PDF processing:

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download and install from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/)

## Quick Start

```python
from zerox_sync import zerox
import os

# Set your Gemini API key
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

# Process a PDF
result = zerox(
    file_path="path/to/document.pdf",
    model="gemini-3-pro",
)

# Access the results
for page in result.pages:
    print(f"Page {page.page}:")
    print(page.content)
    print(f"Length: {page.content_length} chars\n")

print(f"Total time: {result.completion_time}ms")
print(f"Input tokens: {result.input_tokens}")
print(f"Output tokens: {result.output_tokens}")
```

## API Reference

### `zerox()`

Main function to perform OCR on a PDF document.

```python
def zerox(
    cleanup: bool = True,
    concurrency: int = 10,
    file_path: str = "",
    image_density: int = 300,
    image_height: tuple = (None, 1056),
    maintain_format: bool = False,
    model: str = "gemini-3-pro",
    output_dir: Optional[str] = None,
    temp_dir: Optional[str] = None,
    custom_system_prompt: Optional[str] = None,
    select_pages: Optional[Union[int, List[int]]] = None,
    **kwargs
) -> ZeroxOutput:
```

**Parameters:**

- `cleanup` (bool): Whether to cleanup temporary files after processing (default: True)
- `concurrency` (int): Number of concurrent threads for page processing (default: 10)
- `file_path` (str): Path or URL to the PDF file
- `image_density` (int): DPI for PDF to image conversion (default: 300)
- `image_height` (tuple): Image dimensions as (width, height) (default: (None, 1056))
- `maintain_format` (bool): Maintain consistent formatting across pages (default: False)
- `model` (str): Gemini model to use (default: "gemini-3-pro")
- `output_dir` (Optional[str]): Directory to save markdown output (default: None)
- `temp_dir` (Optional[str]): Directory for temporary files (default: system temp)
- `custom_system_prompt` (Optional[str]): Override default system prompt (default: None)
- `select_pages` (Optional[Union[int, List[int]]]): Specific pages to process (default: None)
- `**kwargs`: Additional arguments passed to Gemini API

**Returns:**

`ZeroxOutput` object with:
- `completion_time` (float): Processing time in milliseconds
- `file_name` (str): Processed file name
- `input_tokens` (int): Number of input tokens used
- `output_tokens` (int): Number of output tokens generated
- `pages` (List[Page]): List of Page objects containing:
  - `content` (str): Markdown content
  - `page` (int): Page number
  - `content_length` (int): Content length in characters

## Advanced Usage

### Process Specific Pages

```python
result = zerox(
    file_path="document.pdf",
    select_pages=[1, 3, 5],  # Only process pages 1, 3, and 5
)
```

### Maintain Format Consistency

```python
result = zerox(
    file_path="document.pdf",
    maintain_format=True,  # Process pages sequentially to maintain formatting
)
```

### Save to File

```python
result = zerox(
    file_path="document.pdf",
    output_dir="./output",  # Markdown saved to ./output/{filename}.md
)
```

### Custom System Prompt

```python
result = zerox(
    file_path="document.pdf",
    custom_system_prompt="Extract only tables from this document in markdown format.",
)
```

### Process from URL

```python
result = zerox(
    file_path="https://example.com/document.pdf",
)
```

### Adjust Concurrency

```python
result = zerox(
    file_path="document.pdf",
    concurrency=5,  # Process 5 pages concurrently (default: 10)
)
```

## Available Models

Zerox Sync supports various Gemini models:

- `gemini-3-pro` (default): Most intelligent model
- `gemini-3-flash-preview`: Fast with frontier-class performance
- `gemini-2.5-pro`: Powerful reasoning model
- `gemini-2.5-flash`: Balanced model with 1M token context
- `gemini-2.5-flash-lite`: Fastest and most cost-efficient

## Environment Variables

- `GOOGLE_API_KEY`: Your Google AI Studio API key (required)
  - Get your key from: https://aistudio.google.com/apikey

## Differences from pyzerox

1. **Synchronous**: No `async`/`await` - uses standard function calls
2. **Gemini Direct**: Direct Gemini API integration instead of litellm
3. **Simple Dependencies**: Fewer dependencies, no aiofiles/aiohttp/aioshutil
4. **ThreadPoolExecutor**: Uses standard library threading instead of asyncio
5. **Requests**: Uses requests library for HTTP instead of aiohttp

## Error Handling

```python
from zerox_sync import zerox
from zerox_sync.errors import (
    FileUnavailable,
    MissingEnvironmentVariables,
    ResourceUnreachableException,
    PageNumberOutOfBoundError,
)

try:
    result = zerox(file_path="document.pdf")
except MissingEnvironmentVariables:
    print("Please set GOOGLE_API_KEY environment variable")
except FileUnavailable:
    print("File not found or invalid path")
except ResourceUnreachableException:
    print("Could not download file from URL")
except PageNumberOutOfBoundError:
    print("Invalid page numbers specified")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/zerox-sync.git
cd zerox-sync

# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync all dependencies (including dev)
uv sync
```

### Running Tests

```bash
# Run tests with uv
uv run pytest

# Or activate the virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pytest
```

### Code Formatting

```bash
# Format code
black zerox_sync tests

# Lint
ruff check zerox_sync tests
```

### Building for PyPI Distribution

#### Prerequisites

Install build tools:
```bash
uv add --dev build twine
```

#### Complete Release Workflow

**1. Update version in `pyproject.toml`:**
```toml
[project]
version = "0.1.1"  # Bump this version
```

**2. Commit changes:**
```bash
git add pyproject.toml
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
```

**3. Clean and build:**
```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build distribution files
python -m build
```

This creates:
- `dist/zerox_sync-0.1.1-py3-none-any.whl` (wheel)
- `dist/zerox_sync-0.1.1.tar.gz` (source)

**4. Validate:**
```bash
python -m twine check dist/*
```

**5. Upload to PyPI:**
```bash
# Test on TestPyPI first (optional)
python -m twine upload --repository testpypi dist/*

# Upload to production PyPI
python -m twine upload dist/*
```

#### PyPI Credentials Setup

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

Get API tokens:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

#### Semantic Versioning

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward compatible
- **Patch** (0.0.1): Bug fixes, backward compatible

#### Quick Reference

```bash
# Full release workflow
rm -rf dist/ build/ *.egg-info   # Clean
python -m build                   # Build
python -m twine check dist/*      # Validate
python -m twine upload dist/*     # Upload to PyPI
git push --tags                   # Push version tag
```

## License

MIT License - see LICENSE file for details

## Credits

This project is a synchronous rewrite of [pyzerox](https://github.com/getomni-ai/zerox) by the getomni-ai team. The original project is an excellent async implementation with litellm support.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
