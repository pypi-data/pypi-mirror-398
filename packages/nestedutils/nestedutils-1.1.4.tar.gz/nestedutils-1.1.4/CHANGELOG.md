# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.4]

### Added

- Custom MkDocs theme overrides for enhanced SEO and social media integration
- Comprehensive meta tags including Open Graph and Twitter Card support for better link previews
- Structured data (JSON-LD) with SoftwareApplication schema for improved search engine visibility
- Dynamic keywords meta tag support that combines page-specific and global keywords

### Changed

- Fixed Open Graph image URL in documentation to use correct repository path
- Synchronized keywords between `pyproject.toml` and `mkdocs.yml` for consistent SEO across PyPI and documentation
- Configured MkDocs to use custom theme directory for template customization

## [1.1.3]

### Fixed

- Fixed CONTRIBUTING link in README to use absolute GitHub URL instead of relative path

## [1.1.2]

### Fixed

- Corrected package image link in README

## [1.1.1]

### Changed

- Updated documentation badge in README to include `/nestedutils` path

## [1.1.0]

### Added

- `exists_at()` function to check if a path exists in nested data structures
- Safety limits: Maximum path depth (100 levels) and maximum list index (10,000) to prevent resource exhaustion
- Comprehensive MkDocs documentation with Material theme
- CONTRIBUTING.md guide for contributors
- GitHub Actions workflow for automated documentation deployment

### Changed

- **BREAKING**: Renamed API functions for consistency:
  - `get_path()` → `get_at()`
  - `set_path()` → `set_at()`
  - `del_path()` → `delete_at()`
- Improved docstrings across all functions with detailed examples and parameter descriptions
- Enhanced path validation with better error messages for edge cases
- Refactored fill strategy handling using enums for better type safety
- Updated README with improved documentation and examples

### Fixed

- Fixed bugs with negative index handling in `get_at()`, `set_at()`, and `delete_at()` methods
- Improved validation in path normalization function
- Fixed edge cases with empty paths and empty keys

## [1.0.1]

### Added

- GitHub Actions workflow enhancement to automatically create releases on publish

### Changed

- Updated package description for better clarity and discoverability
- Expanded keywords in `pyproject.toml` for improved PyPI searchability
- Updated README with enhanced description and OG image

## [1.0.0]

### Added

- Initial release of nestedutils
- `get_path()` function for accessing nested values in dictionaries, lists
- `set_path()` function for setting nested values with automatic container creation
- `del_path()` function for deleting nested values
- Support for dot-notation string paths (`"a.b.c"`) and list paths (`["a", "b", "c"]`)
- List index support with positive and negative indices
- Multiple fill strategies for `set_path()`:
  - `"auto"`: Intelligently creates containers based on next key type
  - `"none"`: Fills missing list items with `None`
  - `"dict"`: Always creates dictionaries
  - `"list"`: Always creates lists
- Comprehensive error handling with `PathError` exception and `PathErrorCode` enum
- Support for navigating through `None` values (replaces with appropriate containers)
- Sparse list creation when setting values at high indices
- Full test coverage with comprehensive test suite

### Features

- Zero external dependencies
- Python 3.8+ compatibility
- Immutable container protection (tuples cannot be modified)
- Safe list deletion (requires explicit `allow_list_mutation=True` flag)

[1.1.4]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.1.4
[1.1.3]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.1.3
[1.1.2]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.1.2
[1.1.1]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.1.1
[1.1.0]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.1.0
[1.0.1]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.0.1
[1.0.0]: https://github.com/ysskrishna/nestedutils/releases/tag/v1.0.0
