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
- Refactored internal module structure following project architecture rules
- Renamed function parameters for consistency (`config_key` → `settings_key`)

## [1.11.2] - 2025-12-02

### Changed
- No changes

## [1.11.1] - 2025-12-01

### Changed
- No changes

## [1.11.0] - 2025-12-01

### Changed
- Add environment variable prefix `KIARINA_LIB_GOOGLE_CLOUD_STORAGE_` to `GoogleCloudStorageSettings` for better configuration management

## [1.10.0] - 2025-12-01

### Changed
- No changes

## [1.9.0] - 2025-11-26

### Changed
- No changes

## [1.8.0] - 2025-10-24

### Changed
- No changes

## [1.7.0] - 2025-10-21

### Changed
- No changes

## [1.6.3] - 2025-10-13

### Changed
- Converted tests from mock-based to real integration tests with multi-tenancy patterns
- Simplified test settings loading using `load_user_configs` from pydantic-settings-manager
- Updated `pydantic-settings-manager` dependency from `>=2.1.0` to `>=2.3.0`
- Refactored to use `settings_manager.get_settings` instead of deprecated `get_settings_by_key`

### Added
- Added `.env.sample` and `test_settings.sample.yaml` for easier test setup

## [1.6.2] - 2025-10-10

### Changed
- **Improved blob name handling**: Replaced `blob_name_prefix` and `blob_name` with `blob_name_pattern`
  - `blob_name_pattern` supports both fixed names and template patterns with placeholders
  - `get_blob()` now accepts `placeholders` parameter for pattern formatting
  - `blob_name` parameter in `get_blob()` now always represents the full blob path
  - Pattern examples: `"data.json"` (fixed), `"files/{basename}"` (single placeholder), `"my-service/{tenant_id}/users/{user_id}/files/{basename}"` (multiple placeholders)
  - Priority: explicit `blob_name` → `blob_name_pattern` with `placeholders` → `blob_name_pattern` without placeholders
  - Enhanced error messages for missing placeholders

## [1.6.1] - 2025-10-10

### Changed
- No changes

## [1.6.0] - 2025-10-10

### Changed
- **BREAKING**: Separated authentication configuration from storage configuration
  - Removed `google_auth_config_key` field from `GoogleCloudStorageSettings`
  - Added `auth_config_key` parameter to `get_storage_client()`, `get_bucket()`, and `get_blob()`
  - Authentication is now configured separately through kiarina-lib-google-auth
  - **Migration**: Replace `google_auth_config_key` in settings with `auth_config_key` parameter in function calls
  - **Rationale**: Clear separation of concerns - storage settings define "where", authentication defines "who"
  - **Benefits**: More flexible configuration, easier to reuse authentication across different storage configurations

## [1.5.0] - 2025-10-10

### Added
- Initial release of kiarina-lib-google-cloud-storage
- Google Cloud Storage client library with configuration management using pydantic-settings-manager
- `GoogleCloudStorageSettings`: Pydantic settings model for Google Cloud Storage configuration
  - `google_auth_config_key`: Configuration key for kiarina-lib-google-auth integration
  - `bucket_name`: Google Cloud Storage bucket name
  - `blob_name_prefix`: Optional prefix for blob names (e.g., "uploads/2024")
  - `blob_name`: Optional default blob name
- `get_storage_client()`: Get authenticated Google Cloud Storage client
- `get_bucket()`: Get Google Cloud Storage bucket
- `get_blob()`: Get Google Cloud Storage blob with optional name override
- `settings_manager`: Global settings manager instance with multi-configuration support
- Type safety with full type hints and Pydantic validation
- Environment variable configuration support with `KIARINA_LIB_GOOGLE_CLOUD_STORAGE_` prefix
- Runtime configuration overrides via `cli_args`
- Multiple named configurations support (e.g., production, staging)
- Seamless integration with kiarina-lib-google-auth for authentication
- Blob name prefix support for organizing blobs in hierarchical structures

### Dependencies
- google-cloud-storage>=2.19.0
- kiarina-lib-google-auth>=1.4.0
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
