# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.20.1] - 2025-12-25

### Changed
- No changes

## [1.20.0] - 2025-12-19

### Changed
- No changes

## [1.19.0] - 2025-12-19

### Changed
- No changes

## [1.18.2] - 2025-12-17

### Changed
- No changes

## [1.18.1] - 2025-12-16

### Changed
- No changes

## [1.18.0] - 2025-12-16

### Changed
- No changes

## [1.17.0] - 2025-12-15

### Changed
- No changes

## [1.16.0] - 2025-12-15

### Changed
- No changes

## [1.15.1] - 2025-12-14

### Changed
- No changes

## [1.15.0] - 2025-12-13

### Changed
- No changes

## [1.14.0] - 2025-12-13

### Changed
- No changes

## [1.13.0] - 2025-12-09

### Changed
- No changes

## [1.12.0] - 2025-12-05

### Changed
- Renamed function parameters for consistency (`config_key` → `settings_key` in `create_redisearch_client()`)

## [1.11.2] - 2025-12-02

### Changed
- No changes

## [1.11.1] - 2025-12-01

### Changed
- No changes

## [1.11.0] - 2025-12-01

### Changed
- No changes

## [1.10.0] - 2025-12-01

### Changed
- No changes

## [1.9.0] - 2025-11-26

### Changed
- **BREAKING**: Separated schema from settings configuration
  - Removed `index_schema` field from `RedisearchSettings`
  - Schema is now passed directly to `create_redisearch_client()` via `field_dicts` parameter
  - Schema is treated as part of application code, not infrastructure configuration
  - This improves code-schema consistency and eliminates the need to maintain schema in both code and config files
  - Migration: Pass schema directly when creating client instead of including it in settings
- **Internal refactoring**: Improved code organization by restructuring internal modules
  - Separated `filter` module into independent `kiarina.lib.redisearch_filter` package
  - Separated `schema` module into independent `kiarina.lib.redisearch_schema` package
  - Reorganized filter module structure:
    - `_field/` → `_models/` (renamed for clarity)
    - `_decorators.py` → `_decorators/check_operator_misuse.py`
    - `_enums.py` → `_enums/redisearch_filter_operator.py`
    - `_utils.py` → `_utils/escape_token.py`
    - `_registry.py` → `_helpers/create_redisearch_filter.py`
    - `_types.py` → `_types/redisearch_filter_conditions.py`
    - Renamed `RedisearchFieldFilter` → `BaseFieldFilter`
  - Reorganized schema module structure:
    - `_field/` → `_schemas/` (renamed for clarity)
    - `_model.py` → `_models/redisearch_schema.py`
    - `_types.py` → `_types/field_schema.py`
    - Renamed `VectorFieldSchema` → `BaseVectorFieldSchema`
  - Reorganized test directory structure:
    - `tests/async/` → `tests/redisearch/async/`
    - `tests/sync/` → `tests/redisearch/sync/`
    - Added `tests/redisearch_filter/` and `tests/redisearch_schema/`
  - Updated all internal imports to use new package structure
  - Removed redundant docstrings and comments for cleaner code
  - Added `py.typed` files for better type checking support

**Note**: This is an internal refactoring. Public API remains unchanged.

## [1.8.0] - 2025-10-24

### Changed
- No changes

## [1.7.0] - 2025-10-21

### Changed
- No changes

## [1.6.3] - 2025-10-13

### Changed
- Updated `pydantic-settings-manager` dependency from `>=2.1.0` to `>=2.3.0`

## [1.6.2] - 2025-10-10

### Changed
- No changes

## [1.6.1] - 2025-10-10

### Changed
- No changes

## [1.6.0] - 2025-10-10

### Changed
- No changes

## [1.5.0] - 2025-10-10

### Changed
- No changes

## [1.4.0] - 2025-10-09

### Changed
- No changes

## [1.3.0] - 2025-10-05

### Changed
- No changes

## [1.2.0] - 2025-09-25

### Changed
- No changes

## [1.1.1] - 2025-09-11

### Changed
- No changes

## [1.1.0] - 2025-09-11

### Changed
- No changes

## [1.0.1] - 2025-09-11

### Changed
- No changes - version bump for consistency with other packages

## [1.0.0] - 2025-09-09

### Added
- Initial release of kiarina-lib-redisearch
- RediSearch client with configuration management using pydantic-settings-manager
- Full-text search and vector search capabilities
- Support for both sync and async operations
- Type safety with full type hints and Pydantic validation
- Environment variable configuration support
- Runtime configuration overrides
- Multiple named configurations support
- Comprehensive schema management with field types:
  - Tag fields for categorical data
  - Numeric fields for numerical data
  - Text fields for full-text search
  - Vector fields for similarity search (FLAT and HNSW algorithms)
- Advanced filtering system with query builder
- Index management operations (create, drop, migrate, reset)
- Document operations (set, get, delete)
- Search operations (find, search, count)
- Automatic schema migration support

### Dependencies
- numpy>=2.3.2
- pydantic>=2.11.7
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
- redis>=6.4.0
