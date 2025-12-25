# Changelog

## 1.0.0 – 2025-12-15

### Added

- New client classes: `SharePointSite`, `SharePointUser`, `SharePointList`, `SharePointListItem`, `SharePointFolder`
- `SharePointListField` class for field-level metadata and operations
- Comprehensive type hints throughout the codebase
- Lazy-loaded metadata pattern for all client objects
- Batch operation support for list items and fields
- New documentation examples for field management

### Deprecated

- `SharePointAPI` class and `_compact_init` method - replaced by client pattern
- Legacy method names using camelCase (e.g. `getListByName` -> `get_list_by_name`)

### Changed

- **BREAKING**: Complete restructuring into client pattern
- Unified snake_case naming convention for all methods and properties
- Improved error handling with specific exception types (PermissionError, FileNotFoundError)
- Updated documentation with migration guide and new API examples
- Revised authentication flow to use standard requests.Session

### Security

- Enhanced validation for GUID parameters
- Stricter type checking for all API inputs
- Mandatory form digest validation for write operations

## 0.2.9 – 2025-12-11

### Added

- Using a pre-defined session when initializing.
- Support for merging session-level headers in API calls, preserving custom session headers.

### Changed

- Added deprecation warnings for `_compact_init`.

## 0.2.8 – 2025-12-05

### Added

- Added a central datetime handler method to ensure timezone-aware datetimes.

## 0.2.6 – 2025-12-05

### Added

- Added select_fields option to the `get_site_metadata` method

## 0.2.5 – 2025-12-05

### Changed

- Replace `_resolve_sp_list` with `_resolve_sp_list_url` returning a URL fragment, simplifying GUID handling.
- Update all API calls to use the new URL fragment across list retrieval, item operations, and metadata fetching.
- Simplify `SharePointListItem` constructor by removing explicit `list_guid` argument and adding a lazy `list_guid` property that extracts GUID from the parent list URI.

## 0.2.4 – 2025-12-03

### Added

- New high-level `SharePointSite` object providing lazy-loaded site metadata

## 0.2.3 – 2025-12-02

### Added

- GUID validation for list identifiers with fallback to list title lookup via `GetByTitle`.
- New helper method `_is_valid_guid` in `SharePointAPI`.
- Centralized list resolution helper `_resolve_sp_list` for GUID, title, or `SharePointList` instances.
- New method `get_list_metadata` to fetch only list metadata without items.
- Type hint enhancements: added `Optional`, `Tuple` imports; updated method signatures (e.g., `get_item_versions` now uses `Optional[List[str]]`).
- Updated `get_list` to return the resolved `SharePointList` object after appending items.
- Refactored multiple methods (`get_item`, `create_item`, `update_item`, `attach_file`, `get_item_versions`, `get_case`) to use `_resolve_sp_list`, removing redundant GUID validation logic.

### Changed

- Cleaned up stray `else:` blocks and syntax errors.
- Improved consistency of return objects across list-related methods.
- Updated imports and docstrings accordingly.

## 0.2.2 – 2025-11-28

### Added

- `SharePointList.fields` property to retrieve list field definitions

## 0.2.1 – 2025-11-06

### Added

- Optional `select_fields` parameters to list retrieval methods for more efficient queries.
- New public API methods:
  - `SharePointAPI.get_group_users` – fetch users of a SharePoint group.
- Improved error handling with explicit `TypeError` exceptions.
- Detailed docstrings for core classes and methods (enhances IDE support).

### Changed

- HTTP header handling unified; corrected `X-HTTP-Method: PUT` for full updates.
- Error handling improved: generic `sys.exit(1)` replaced with explicit `TypeError`/`ConnectionError` exceptions.

### Fixed

- Fixed incorrect PUT header that previously sent a MERGE header.
- Minor docstring formatting issues.

### Security

- Enforced NTLM authentication across all request helpers.
