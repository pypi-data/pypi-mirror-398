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

### Added
- **API key authentication**: Added support for API key authentication method
  - New `type: "api_key"` option in `GoogleAuthSettings`
  - New `api_key` field for storing API keys securely with `SecretStr`
  - Enables direct API key usage for Google APIs that support it

## [1.14.0] - 2025-12-13

### Fixed
- **Service account credentials**: Fixed scope application for service account credentials
  - `get_service_account_credentials()` now accepts `scopes` parameter
  - Scopes are properly applied via `with_scopes()` method
  - Resolves `invalid_scope` errors when using service account credentials with Google APIs

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
- No changes

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
- Simplified credentials retrieval and caching logic in user account credentials handling

## [1.6.3] - 2025-10-13

### Changed
- Updated `pydantic-settings-manager` dependency from `>=2.1.0` to `>=2.3.0`
- Improved test configuration approach using YAML-based settings file instead of individual environment variables
- Tests now use `pydantic-settings-manager` with multiple named configurations for different authentication scenarios
- Added `test_settings.sample.yaml` as a template for test configuration
- Added `.env.sample` to document required environment variables
- Reorganized `GoogleAuthSettings` field order for better readability (common fields first)
- Enhanced test coverage with more comprehensive authentication method tests
- Simplified test fixtures using session-scoped `load_settings` fixture

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

### Added
- Initial release of kiarina-lib-google-auth
- Google Cloud authentication library with configuration management using pydantic-settings-manager
- Multiple authentication methods:
  - Default credentials (Application Default Credentials)
  - Service account authentication (from file or JSON data)
  - User account authentication (OAuth2 authorized user credentials)
  - Service account impersonation with configurable scopes
- Credentials caching support with `CredentialsCache` protocol
- Self-signed JWT generation for service accounts
- Type safety with full type hints and Pydantic validation
- Environment variable configuration support with `KIARINA_LIB_GOOGLE_AUTH_` prefix
- Runtime configuration overrides
- Multiple named configurations support via pydantic-settings-manager
- Automatic credential refresh for user accounts
- Stable cache key generation for user account credentials
- Default scopes for GCP, Google Drive, and Google Sheets

### Features
- **`get_credentials()`**: Main function to obtain credentials based on configuration
- **`get_self_signed_jwt()`**: Generate self-signed JWTs for service account authentication
- **`get_default_credentials()`**: Utility to get default Google credentials (ADC)
- **`get_service_account_credentials()`**: Utility to get service account credentials
- **`get_user_account_credentials()`**: Utility to get user account credentials with caching
- **`GoogleAuthSettings`**: Pydantic settings model with comprehensive configuration options
- **`CredentialsCache`**: Protocol for implementing custom credentials caching strategies
- **`Credentials`**: Type alias for all supported credential types

### Security
- **Enhanced credential protection**: Changed `service_account_data`, `client_secret_data`, and `authorized_user_data` fields to use `SecretStr`
  - Credentials are now masked in string representations and logs (displayed as `**********`)
  - Prevents accidental exposure of sensitive data in debug output
  - Access secret values explicitly via `.get_secret_value()` method
  - Minimal breaking change: only affects direct field access (use `get_*_data()` methods instead)

### Configuration Options
- `type`: Authentication type (default, service_account, user_account)
- `service_account_file`: Path to service account key file
- `service_account_data`: Service account key data as JSON string
- `service_account_email`: Service account email address
- `authorized_user_file`: Path to authorized user credentials file
- `authorized_user_data`: Authorized user credentials as JSON string
- `user_account_email`: User account email address
- `client_secret_file`: Path to OAuth2 client secret file
- `client_secret_data`: OAuth2 client secret as JSON string
- `impersonate_service_account`: Target service account for impersonation
- `scopes`: List of OAuth2 scopes
- `project_id`: GCP project ID

### Dependencies
- google-api-python-client>=2.184.0
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
