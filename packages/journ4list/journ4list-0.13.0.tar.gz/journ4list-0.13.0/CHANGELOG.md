# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-17

### Added

- Initial release of the journalist package
- Modern async API for news content extraction
- Support for multiple extraction methods (readability, CSS selectors, JSON-LD)
- Flexible persistence modes (memory-only or filesystem)
- Session management with race condition protection
- Comprehensive test suite
- Documentation and examples
- MIT license

### Features

- **Async API**: Built with asyncio for high-performance concurrent scraping
- **Universal News Support**: Works with news websites and content from any language or region
- **Smart Content Extraction**: Multiple extraction methods available
- **Flexible Persistence**: Memory-only or filesystem persistence modes
- **Error Handling**: Robust error handling with custom exception types
- **Session Management**: Built-in session management
- **Well Tested**: Comprehensive unit tests with high coverage

### Technical Details

- Python 3.8+ support
- Modern async/await syntax
- Type hints throughout the codebase
- Comprehensive error handling
- Modular architecture
