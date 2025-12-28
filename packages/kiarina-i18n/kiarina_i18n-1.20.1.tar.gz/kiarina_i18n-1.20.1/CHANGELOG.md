# Changelog

All notable changes to kiarina-i18n will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.20.1] - 2025-12-25

### Changed
- **Performance**: Optimized caching strategy to only cache file I/O operations
  - Removed `lru_cache` from `get_catalog()` and `get_translator()`
  - Added `load_catalog_file()` operation with caching for file loading only
  - Settings changes are now reflected immediately without requiring `clear_cache()`
  - `clear_cache()` now only clears the file loading cache

## [1.20.0] - 2025-12-19

### Removed
- **BREAKING**: Removed `create_pydantic_schema()` function from `kiarina.i18n_pydantic`
  - Use `I18n` subclass with `Field(description=...)` instead
  - Example: `class ArgsSchema(I18n, scope="tool.args"): name: str = Field(description="Name")`
  - Then use `translate_pydantic_model()` to translate at runtime

## [1.19.0] - 2025-12-19

### Added
- `kiarina.i18n_pydantic` subpackage with `create_pydantic_schema()` function for creating translated Pydantic model schemas
- Support for translating model docstrings, field descriptions, and field titles in Pydantic schemas
- Comprehensive test coverage for `create_pydantic_schema()` with various model configurations

## [1.18.2] - 2025-12-17

### Added
- `translate_pydantic_model()` now translates model `__doc__` (docstring) in addition to field descriptions
  - Use `__doc__` key in catalog to provide translated docstring
  - Falls back to original docstring if translation is missing

## [1.18.1] - 2025-12-16

### Added
- `clear_cache()` helper function for i18n cache management

## [1.18.0] - 2025-12-16

### Added
- `translate_pydantic_model()` function to translate Pydantic model field descriptions for LLM tool schemas
- `get_catalog()` helper function to get translation catalog independently for custom translation logic
- `translate_pydantic_model()` now supports omitting `scope` parameter when translating `I18n` subclasses (automatically uses `model._scope`)

### Changed
- **BREAKING**: `I18n` class now uses `scope` as a class parameter instead of an instance field
  - Old: `class MyI18n(I18n): scope: str = "my.module"`
  - New: `class MyI18n(I18n, scope="my.module")` or `class MyI18n(I18n)` (auto-generated)
  - This allows `scope` to be used as a regular translation key
  - Internal `_scope` attribute stores the scope value
  - If scope is not provided, it's automatically generated from module and class name
    - Example: `my_app.i18n.UserProfileI18n` → `my_app.i18n.UserProfileI18n`

## [1.17.0] - 2025-12-15

### Added
- `I18n` base class for type-safe translation definitions with Pydantic validation
- `get_i18n()` helper function to get translated instances with full type safety
- Class-based API for better IDE support and auto-completion
- Immutable translation instances (frozen=True) to prevent accidental modifications
- Self-documenting translation keys using class field definitions
- Automatic fallback to default values when translations are missing

### Changed
- Reorganized test files by target module (_helpers/, _models/)
- Converted class-based tests to function-based tests
- Added pytest fixtures for cache management in tests

## [1.16.0] - 2025-12-15

### Added
- Initial release of kiarina-i18n package
- `Translator` class for translation with fallback support
- `get_translator()` function with caching
- Template variable substitution using Python's string.Template
- Configuration management using pydantic-settings-manager
- Support for loading catalog from YAML file
- Type definitions for Language, I18nScope, I18nKey, and Catalog
