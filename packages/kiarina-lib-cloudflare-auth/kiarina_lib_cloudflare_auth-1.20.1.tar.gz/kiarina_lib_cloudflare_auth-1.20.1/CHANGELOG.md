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
- No changes

## [1.11.2] - 2025-12-02

### Changed
- No changes

## [1.11.1] - 2025-12-01

### Changed
- No changes

## [1.11.0] - 2025-12-01

### Changed
- Add environment variable prefix `KIARINA_LIB_CLOUDFLARE_AUTH_` to `CloudflareAuthSettings` for better configuration management

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

### Added
- Initial release of kiarina-lib-cloudflare-auth
- Cloudflare authentication library with configuration management using pydantic-settings-manager
- `CloudflareAuthSettings`: Pydantic settings model for Cloudflare authentication
  - `account_id`: Cloudflare account ID (required)
  - `api_token`: Cloudflare API token (required, protected with SecretStr)
- `settings_manager`: Global settings manager instance with multi-configuration support
- Type safety with full type hints and Pydantic validation
- Environment variable configuration support with `KIARINA_LIB_CLOUDFLARE_AUTH_` prefix
- Runtime configuration overrides via `cli_args`
- Multiple named configurations support (e.g., production, staging)

### Security
- **Enhanced credential protection**: API tokens use `SecretStr` for secure handling
  - Tokens are masked in string representations and logs (displayed as `**********`)
  - Prevents accidental exposure of sensitive data in debug output
  - Access token values explicitly via `.get_secret_value()` method
  - Follows the project-wide security policy for sensitive data

### Dependencies
- pydantic-settings>=2.10.1
- pydantic-settings-manager>=2.1.0
