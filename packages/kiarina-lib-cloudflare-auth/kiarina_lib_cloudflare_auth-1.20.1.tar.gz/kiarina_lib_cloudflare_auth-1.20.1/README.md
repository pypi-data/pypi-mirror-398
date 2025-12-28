# kiarina-lib-cloudflare-auth

A Python library for Cloudflare authentication with configuration management using pydantic-settings-manager.

## Features

- **Configuration Management**: Use `pydantic-settings-manager` for flexible configuration
- **Type Safety**: Full type hints and Pydantic validation
- **Secure Credential Handling**: API tokens are protected using `SecretStr`
- **Multiple Configurations**: Support for multiple named configurations (e.g., different accounts)
- **Environment Variable Support**: Configure via environment variables with `KIARINA_LIB_CLOUDFLARE_AUTH_` prefix

## Installation

```bash
pip install kiarina-lib-cloudflare-auth
```

## Quick Start

### Basic Usage

```python
from kiarina.lib.cloudflare.auth import CloudflareAuthSettings, settings_manager

# Configure Cloudflare authentication
settings_manager.user_config = {
    "default": {
        "account_id": "your-account-id",
        "api_token": "your-api-token"
    }
}

# Get settings
settings = settings_manager.settings
print(f"Account ID: {settings.account_id}")
print(f"API Token: {settings.api_token.get_secret_value()}")  # Access secret value
```

### Environment Variable Configuration

Configure authentication using environment variables:

```bash
export KIARINA_LIB_CLOUDFLARE_AUTH_ACCOUNT_ID="your-account-id"
export KIARINA_LIB_CLOUDFLARE_AUTH_API_TOKEN="your-api-token"
```

```python
from kiarina.lib.cloudflare.auth import settings_manager

# Settings are automatically loaded from environment variables
settings = settings_manager.settings
print(f"Account ID: {settings.account_id}")
```

### Multiple Configurations

Manage multiple Cloudflare accounts:

```python
from kiarina.lib.cloudflare.auth import settings_manager

# Configure multiple accounts
settings_manager.user_config = {
    "production": {
        "account_id": "prod-account-id",
        "api_token": "prod-api-token"
    },
    "staging": {
        "account_id": "staging-account-id",
        "api_token": "staging-api-token"
    }
}

# Switch between configurations
settings_manager.active_key = "production"
prod_settings = settings_manager.settings
print(f"Production Account: {prod_settings.account_id}")

settings_manager.active_key = "staging"
staging_settings = settings_manager.settings
print(f"Staging Account: {staging_settings.account_id}")
```

## Configuration

This library uses [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) for flexible configuration management.

### CloudflareAuthSettings

The `CloudflareAuthSettings` class provides the following configuration fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `account_id` | `str` | Yes | Cloudflare account ID |
| `api_token` | `SecretStr` | Yes | Cloudflare API token (masked in logs) |

### Environment Variables

All settings can be configured via environment variables with the `KIARINA_LIB_CLOUDFLARE_AUTH_` prefix:

```bash
# Account ID
export KIARINA_LIB_CLOUDFLARE_AUTH_ACCOUNT_ID="your-account-id"

# API Token (will be automatically wrapped in SecretStr)
export KIARINA_LIB_CLOUDFLARE_AUTH_API_TOKEN="your-api-token"
```

### Programmatic Configuration

```python
from pydantic import SecretStr
from kiarina.lib.cloudflare.auth import CloudflareAuthSettings, settings_manager

# Direct settings object
settings = CloudflareAuthSettings(
    account_id="your-account-id",
    api_token=SecretStr("your-api-token")
)

# Via settings manager
settings_manager.user_config = {
    "default": {
        "account_id": "your-account-id",
        "api_token": "your-api-token"  # Automatically converted to SecretStr
    }
}
```

### Runtime Overrides

```python
from kiarina.lib.cloudflare.auth import settings_manager

# Override specific settings at runtime
settings_manager.cli_args = {
    "account_id": "override-account-id"
}

settings = settings_manager.settings
print(f"Account ID: {settings.account_id}")  # Uses overridden value
```

## Security

### API Token Protection

API tokens are stored using Pydantic's `SecretStr` type, which provides the following security benefits:

- **Masked in logs**: Tokens are displayed as `**********` in string representations
- **Prevents accidental exposure**: Tokens won't appear in debug output or error messages
- **Explicit access required**: Must use `.get_secret_value()` to access the actual token

```python
from kiarina.lib.cloudflare.auth import settings_manager

settings = settings_manager.settings

# Token is masked in string representation
print(settings)  # api_token=SecretStr('**********')

# Explicit access to get the actual token
token = settings.api_token.get_secret_value()
```

## API Reference

### CloudflareAuthSettings

```python
class CloudflareAuthSettings(BaseSettings):
    account_id: str
    api_token: SecretStr
```

Pydantic settings model for Cloudflare authentication.

**Fields:**
- `account_id` (str): Cloudflare account ID
- `api_token` (SecretStr): Cloudflare API token (protected)

### settings_manager

```python
settings_manager: SettingsManager[CloudflareAuthSettings]
```

Global settings manager instance for Cloudflare authentication.
See: [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager)

## Development

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone the repository
git clone https://github.com/kiarina/kiarina-python.git
cd kiarina-python

# Setup development environment
mise run setup
```

### Running Tests

```bash
# Run format, lint, type checks and tests
mise run package kiarina-lib-cloudflare-auth

# Coverage report
mise run package:test kiarina-lib-cloudflare-auth --coverage
```

## Dependencies

- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Contributing

This is a personal project, but contributions are welcome! Please feel free to submit issues or pull requests.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library used by this package
