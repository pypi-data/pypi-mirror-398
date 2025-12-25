# Journalist

[![PyPI version](https://badge.fury.io/py/journ4list.svg)](https://badge.fury.io/py/journ4list)
[![Python Versions](https://img.shields.io/pypi/pyversions/journ4list)](https://pypi.org/project/journ4list/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/username/journalist/workflows/Tests/badge.svg)](https://github.com/username/journalist/actions)
[![Coverage](https://codecov.io/gh/username/journalist/branch/main/graph/badge.svg)](https://codecov.io/gh/username/journalist)

A powerful async news content extraction library with modern API for web scraping and article analysis.

## Features

🚀 **Modern Async API** - Built with asyncio for high-performance concurrent scraping  
📰 **Universal News Support** - Works with news websites and content from any language or region  
🎯 **Smart Content Extraction** - Multiple extraction methods (readability, CSS selectors, JSON-LD)
🔄 **Flexible Persistence** - Memory-only or filesystem persistence modes  
🛡️ **Error Handling** - Robust error handling with custom exception types  
📊 **Session Management** - Built-in session management with race condition protection  
🧪 **Well Tested** - Comprehensive unit tests with high coverage

## Installation

### Option 1: Using pip (Recommended)

```bash
pip install journ4list
```

### Option 2: Using Poetry

```bash
poetry add journ4list
```

### Option 3: Development Installation

#### Using Poetry (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/username/journalist.git
cd journalist

# Install with Poetry
poetry install

# Activate virtual environment
poetry shell
```

#### Using pip-tools (Alternative)

```bash
# Clone the repository
git clone https://github.com/username/journalist.git
cd journalist

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install pip-tools
pip install pip-tools

# Compile and install dependencies
pip-compile requirements.in --output-file requirements.txt
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
import asyncio
from journalist import Journalist

async def main():
    # Create journalist instance
    journalist = Journalist(persist=True, scrape_depth=1)

    # Extract content from news sites
    result = await journalist.read(
        urls=[            "https://www.bbc.com/news",
            "https://www.reuters.com/"
        ],
        keywords=["teknologi", "spor", "ekonomi"]
    )

    # Access extracted articles
    for article in result['articles']:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Content: {article['content'][:200]}...")
        print("-" * 50)

    # Check extraction summary
    summary = result['extraction_summary']
    print(f"Processed {summary['urls_processed']} URLs")
    print(f"Found {summary['articles_extracted']} articles")
    print(f"Extraction took {summary['extraction_time_seconds']} seconds")

# Run the example
asyncio.run(main())
```

### Memory-Only Mode (No File Persistence)

```python
import asyncio
from journalist import Journalist

async def main():
    # Use memory-only mode for temporary scraping
    journalist = Journalist(persist=False)

    result = await journalist.read(        urls=["https://www.cnn.com/"],
        keywords=["news", "breaking"]
    )

    # Articles are stored in memory only
    print(f"Found {len(result['articles'])} articles")
    print(f"Session ID: {result['session_id']}")

asyncio.run(main())
```

### Concurrent Scraping

```python
import asyncio
from journalist import Journalist

async def scrape_multiple_sources():
    """Example of concurrent scraping with multiple journalist instances."""

    # Create tasks for different news sources
    async def scrape_sports():
        journalist = Journalist(persist=True, scrape_depth=2)
        return await journalist.read(
            urls=["https://www.espn.com/", "https://www.skysports.com/"],
            keywords=["futbol", "basketbol"]
        )

    async def scrape_tech():
        journalist = Journalist(persist=True, scrape_depth=1)
        return await journalist.read(
            urls=["https://www.techcrunch.com/", "https://www.wired.com/"],
            keywords=["teknologi", "yazılım"]
        )

    # Run concurrently
    sports_task = asyncio.create_task(scrape_sports())
    tech_task = asyncio.create_task(scrape_tech())

    sports_result, tech_result = await asyncio.gather(sports_task, tech_task)

    print(f"Sports articles: {len(sports_result['articles'])}")
    print(f"Tech articles: {len(tech_result['articles'])}")

asyncio.run(scrape_multiple_sources())
```

## Configuration

### Journalist Parameters

- **`persist`** (bool, default: `True`) - Enable filesystem persistence for session data
- **`scrape_depth`** (int, default: `1`) - Depth level for link discovery and scraping

### Environment Configuration

The library uses sensible defaults but can be configured via the `JournalistConfig` class:

```python
from journalist.config import JournalistConfig

# Get current workspace path
workspace = JournalistConfig.get_base_workspace_path()
print(f"Workspace: {workspace}")  # Output: .journalist_workspace
```

## Error Handling

The library provides custom exception types for better error handling:

```python
import asyncio
from journalist import Journalist
from journalist.exceptions import NetworkError, ExtractionError, ValidationError

async def robust_scraping():
    try:
        journalist = Journalist()
        result = await journalist.read(
            urls=["https://example-news-site.com/"],
            keywords=["important", "news"]
        )
        return result

    except NetworkError as e:
        print(f"Network error: {e}")
        if hasattr(e, 'status_code'):
            print(f"HTTP Status: {e.status_code}")

    except ExtractionError as e:
        print(f"Content extraction failed: {e}")
        if hasattr(e, 'url'):
            print(f"Failed URL: {e.url}")

    except ValidationError as e:
        print(f"Input validation error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(robust_scraping())
```

## API Reference

### Journalist Class

#### `__init__(persist=True, scrape_depth=1)`

Initialize a new Journalist instance.

**Parameters:**

- `persist` (bool): Enable filesystem persistence
- `scrape_depth` (int): Link discovery depth level

#### `async read(urls, keywords=None)`

Extract content from provided URLs with optional keyword filtering.

**Parameters:**

- `urls` (List[str]): List of website URLs to process
- `keywords` (Optional[List[str]]): Keywords for relevance filtering

**Returns:**

- `Dict[str, Any]`: Dictionary containing extracted articles and metadata

**Return Structure:**

```python
{
    'articles': [
        {
            'title': str,
            'url': str,
            'content': str,
            'author': str,
            'published_date': str,
            'keywords_found': List[str]
        }
    ],
    'session_id': str,
    'extraction_summary': {
        'session_id': str,
        'urls_requested': int,
        'urls_processed': int,
        'articles_extracted': int,
        'extraction_time_seconds': float,
        'keywords_used': List[str]
    }
}
```

## Development

### Running Tests

```bash
# Using Poetry
poetry run pytest

# Using pip
pytest

# With coverage
pytest --cov=journalist --cov-report=html
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src

# Linting
pylint src
```

### Development Dependencies

The project supports both Poetry and pip-tools for dependency management:

**Poetry (pyproject.toml):**

```bash
poetry install --with dev
```

**pip-tools (requirements.in):**

```bash
pip-compile requirements.in --output-file requirements.txt
python -m pip install -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure tests pass (`pytest`)
6. Format code (`black src tests`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Changelog

### v0.1.0 (2025-06-17)

- Initial release
- Async API for universal news content extraction
- Support for multiple extraction methods
- Memory and filesystem persistence modes
- Comprehensive error handling
- Session management with race condition protection
- Concurrent scraping support

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Oktay Burak Ertas**  
Email: oktay.burak.ertas@gmail.com

## Acknowledgments

- Built with modern Python async/await patterns
- Optimized for global news websites
- Inspired by newspaper3k and readability libraries
- Uses BeautifulSoup4 and lxml for HTML parsing
