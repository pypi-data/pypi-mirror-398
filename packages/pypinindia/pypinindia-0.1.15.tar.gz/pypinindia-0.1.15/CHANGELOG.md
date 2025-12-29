# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased] - 2025-11-19

### Changed
- Updated exception handling for improved error messages

## [Unreleased] - 2025-07-25

### Added
- Method to fetch unique post offices by state in core.py
- Fuzzy matching enhancement for improved search accuracy
- Enhanced search by taluk functionality
- Cache implementation for better performance
- Auto-suggestion feature for user input
- Postal office types and delivery statuses listing
- Taluk listing method for enhanced dataset navigation
- Utility methods for office types by state
- Pincode count summary functionality

### Fixed
- Updated states list in core.py
- Resolved conflict errors in state handling

## [Unreleased] - 2025-07-20

### Removed
- Deleted unwanted sample.py file

## [Unreleased] - 2025-07-16

### Added
- Pincode validation for alphanumeric and special characters
- Delivery status test cases

## [Unreleased] - 2025-07-13

### Added
- `get_postoffice_summary` helper function in core.py
- `SummaryError` exception in exceptions.py
- Example file to test new summary functionality

### Fixed
- Made `_normalize` a static method to resolve test failures

## [0.1.8] - 2025-07-07

### Fixed
- Incremented version to resolve PyPI "File already exists" error.

## [0.1.7] - 2025-07-07

### Changed
- Refactored `PincodeData` methods (`get_state`, `get_district`, `get_taluk`, `get_offices`) to use a common helper method `_get_info_field` for improved code reusability and maintainability.
- Ensured type hint compatibility with `mypy` by explicitly casting return types where necessary.

### Technical Improvements
- Implemented `lru_cache` for `_get_default_instance` to ensure `PincodeData` is a singleton and loaded only once, optimizing performance for repeated calls to convenience functions.
- Removed redundant global variable `_default_pincode_data` for a cleaner and more minimal codebase, leveraging `lru_cache` for instance management.
- Removed duplicate import statements (`os`, `re`).

## [0.1.6] - 2025-01-04

### Added
- **Complete rewrite with modern Python practices**
- Repo links changed
- Author added

### Added
- **Complete rewrite with modern Python practices**
- Comprehensive API with both functional and object-oriented interfaces
- Full-featured CLI tool with extensive options and JSON output support
- Comprehensive test suite with high coverage and mocking
- Type hints throughout the codebase for better IDE support
- Proper exception handling with custom exception classes
- Search functionality by state, district, and office name
- Statistics and data exploration features
- Examples directory with comprehensive usage examples
- Support for custom data files
- Pandas-based data operations for improved performance
- Case-insensitive search operations
- Verbose and JSON output modes in CLI

### Changed
- Migrated from setup.py to modern pyproject.toml configuration
- Updated package structure following modern Python best practices
- Improved error messages with detailed context
- Enhanced documentation with comprehensive API reference
- Updated README with extensive examples and usage instructions

### Technical Improvements
- Added `PincodeData` class for object-oriented usage
- Added convenience functions for quick lookups
- Added comprehensive data validation and error handling
- Added support for both string and integer pincode inputs
- Added statistics functionality for dataset exploration
- Added office name search with partial matching
- Added proper logging and debugging support

### Dependencies
- Added pandas >= 1.0.0 as main dependency
- Added development dependencies (pytest, black, mypy, etc.)
- Removed pypandoc dependency (was causing issues)

### CLI Features
- Added `pypinindia` command-line tool
- Support for pincode lookup, state/district search
- List operations for states and districts
- Statistics display
- JSON and verbose output modes
- Custom data file support

## [0.1.2] - 2018-04-27 (Legacy)

### Added
- Basic pincode lookup functionality
- Simple get_state() and get_location() functions
- Basic CSV data support
- Apache 2.0 license

### Technical Details
- Simple setup.py configuration
- Basic Python 2/3 compatibility
- Minimal error handling
- Limited API surface

---

## Migration Guide from v0.1.2 to v0.2.0

### Breaking Changes
- Package structure changed from simple functions to comprehensive API
- Function signatures updated with type hints
- Error handling improved with custom exceptions

### Migration Steps

**Old usage (v0.1.2):**
```python
from pypinindia.util import get_state, get_location
state = get_state(110001)
location = get_location(110001)
```

**New usage (v0.2.0):**
```python
from pypinindia import get_state, get_district, get_pincode_info
state = get_state("110001")  # Now accepts string or int
district = get_district("110001")  # More specific than location
info = get_pincode_info("110001")  # Complete information
```

### New Features Available
- Comprehensive search capabilities
- CLI tool for command-line usage
- Better error handling and validation
- Type hints for better IDE support
- Extensive documentation and examples

---

## Development Notes

### v0.2.0 Development Process
- Analyzed existing toksum library structure for modern Python practices
- Implemented comprehensive test suite with pytest and mocking
- Added type hints throughout for better developer experience
- Created extensive documentation and examples
- Implemented CLI tool with argparse for command-line usage
- Added pandas for efficient data operations
- Implemented proper exception hierarchy
- Added support for custom data files and configurations

### Future Roadmap
- [ ] Add caching for improved performance
- [ ] Add async support for large-scale operations
- [ ] Add data validation and integrity checks
- [ ] Add support for additional data sources
- [ ] Add geographic coordinate lookup
- [ ] Add distance calculations between pincodes
- [ ] Add data export functionality
- [ ] Add web API interface
