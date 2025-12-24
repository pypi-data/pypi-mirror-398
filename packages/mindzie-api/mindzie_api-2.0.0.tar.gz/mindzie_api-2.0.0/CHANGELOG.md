# Changelog

All notable changes to the Mindzie API Python Client will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-19

### Added
- **TenantController**: Full CRUD operations for tenant management (requires Global API key)
  - `list_tenants`, `get_tenant`, `create_tenant`, `update_tenant`, `delete_tenant`
  - `get_all_tenants` convenience method with auto-pagination
  - Support for tenant expiration dates (trial tenants)
- **UserController**: Comprehensive user management (global and tenant-scoped)
  - Global operations: `list_users`, `create_user`, `get_user`, `update_user`, `get_user_tenants`
  - Tenant-scoped: `list_tenant_users`, `create_tenant_user`, `assign_user_to_tenant`, `remove_user_from_tenant`
  - Support for service accounts with home tenant assignment
- **ConflictError**: New exception for HTTP 409 conflicts (optimistic locking)
- **Investigation cloning**: `clone()` method for cloning investigations across projects/datasets
- **Investigation folders**: Full folder management support
  - `list_folders`, `create_folder`, `update_folder`, `delete_folder`, `move_to_folder`
- **Optimistic locking**: `date_modified` parameter on `investigation.update()` for conflict detection

### Changed
- **BREAKING**: Version bumped to 2.0.0 due to significant new features
- Investigation update method now supports optional `date_modified` parameter for optimistic locking
- Tenant and User models added to models package exports

### Models Added
- `TenantListItem`, `TenantListResponse`, `TenantDetail`, `TenantCreated`, `TenantUpdated`
- `TenantAssignmentDto`, `UserListItemDto`, `UserListResponseDto`, `UserCreatedDto`, `UserTenantsResponseDto`

## [1.0.4] - 2024-12-29

### Fixed
- **CRITICAL**: Fixed incorrect API endpoints for CSV uploads
- CSV upload methods now use the correct `UploadCsv/UpdateLogWithCsvFile` endpoint
- Fixed field name from 'file' to 'File' (capital F) to match API expectations
- Fixed parameter structure - now uses `logId` as query parameter instead of in path

### Changed
- `create_from_csv` and `update_from_csv` now use the actual API endpoint structure
- Both methods now properly pass parameters as query strings
- Added warnings to binary upload methods as these endpoints may not exist

### Known Issues
- Binary upload endpoints (`dataset/binary`) do not appear to exist in current API
- Package upload endpoints (`dataset/package`) may also not exist
- These methods are retained for compatibility but may not function

## [1.0.3] - 2024-12-29

### Fixed
- **CRITICAL**: Fixed Content-Type header issue causing 415 "Unsupported Media Type" errors for all file uploads
- Binary uploads (`create_from_binary`, `update_from_binary`) now work correctly
- CSV uploads (`create_from_csv`, `update_from_csv`) now work correctly
- Package uploads (`create_from_package`, `update_from_package`) now work correctly
- All file upload methods now properly handle multipart/form-data content type

### Changed
- Modified request method in `client.py` to properly remove Content-Type header for file uploads
- Requests library now correctly sets multipart/form-data with boundary for file uploads
- File uploads no longer incorrectly send `application/json` content type

### Technical Details
- When uploading files, the session's default `Content-Type: application/json` header is now properly removed
- This allows the requests library to automatically set the correct `multipart/form-data` header with boundary
- JSON API calls remain unaffected and continue to work as expected

## [1.0.2] - 2024-12-20

### Security
- Security improvements and dependency updates
- Enhanced input validation for API parameters

## [1.0.1] - 2024-12-20

### Fixed
- **CRITICAL**: Fixed authentication header format - now uses `Authorization: Bearer {api_key}` to match server requirements
- Authentication was completely broken in 1.0.0 due to incorrect header format

### Added
- Added `hello_world_with_dotenv.py` example for easier testing with .env files
- Added `test_raw_api.py` diagnostic script for debugging API connectivity issues
- Added support for .env files in authenticated examples

### Changed
- Updated all authentication providers to use Bearer token format
- Updated test fixtures to match new authentication format

## [1.0.0] - 2024-01-15

### Added
- Initial release of the Mindzie API Python Client
- Complete coverage of all Mindzie Studio API endpoints
- Support for multiple authentication methods (API Key, Bearer Token, Azure AD)
- Comprehensive type hints and Pydantic models for all API responses
- Automatic retry logic with exponential backoff
- File upload support for CSV, package, and binary datasets
- Pagination handling for large result sets
- Rate limiting support
- Comprehensive test suite with >90% code coverage
- Detailed documentation and usage examples
- Support for Python 3.8 through 3.12

### Controllers Implemented
- **Project Controller**: List, get, and search projects
- **Dataset Controller**: Create and update datasets from various file formats
- **Investigation Controller**: Full CRUD operations for investigations
- **Notebook Controller**: Manage and execute notebooks
- **Block Controller**: Create and manage different block types
- **Execution Controller**: Monitor and manage execution queue
- **Enrichment Controller**: Handle data enrichment pipelines
- **Dashboard Controller**: Access dashboards and panels
- **Action Controller**: Execute actions
- **Action Execution Controller**: Track action executions
- **Ping Controller**: Connectivity testing

### Features
- Automatic environment variable configuration
- Context manager support for proper resource cleanup
- Comprehensive error handling with custom exception types
- Optional async/await support (with additional dependencies)
- Proxy configuration support
- SSL verification control
- Request timeout configuration
- Custom headers support

## [Unreleased]

### Planned
- WebSocket support for real-time updates
- Batch operations for improved performance
- Caching layer for frequently accessed data
- CLI tool for command-line operations
- GraphQL support (if API adds GraphQL endpoint)
- Additional authentication methods
- Improved async/await implementation
- Data export utilities
- Local data validation before upload