# kiarina-lib-google-auth

A Python library for Google Cloud authentication with configuration management using pydantic-settings-manager.

## Features

- **Multiple Authentication Methods**: Default credentials (ADC), service accounts, and user accounts
- **Service Account Impersonation**: Delegated access with configurable scopes
- **Configuration Management**: Flexible configuration with pydantic-settings-manager
- **Credentials Caching**: Automatic caching and refresh for user accounts
- **Self-Signed JWT**: Generate JWTs for service account authentication
- **Type Safety**: Full type hints and Pydantic validation

## Installation

```bash
pip install kiarina-lib-google-auth
```

## Quick Start

### Default Credentials (ADC)

```python
from kiarina.lib.google.auth import get_credentials

# Uses Application Default Credentials
credentials = get_credentials()
```

### Service Account

```python
from kiarina.lib.google.auth import get_credentials, GoogleAuthSettings

# From key file
credentials = get_credentials(
    settings=GoogleAuthSettings(
        type="service_account",
        service_account_file="~/path/to/key.json"
    )
)

# From JSON data
credentials = get_credentials(
    settings=GoogleAuthSettings(
        type="service_account",
        service_account_data='{"type":"service_account",...}'
    )
)
```

### User Account (OAuth2)

```python
# From authorized user file
credentials = get_credentials(
    settings=GoogleAuthSettings(
        type="user_account",
        authorized_user_file="~/.config/gcloud/application_default_credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
)
```

### Service Account Impersonation

```python
# Impersonate a service account
credentials = get_credentials(
    settings=GoogleAuthSettings(
        type="service_account",
        service_account_file="~/source-key.json",
        impersonate_service_account="target@project.iam.gserviceaccount.com",
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
)
```

**Note**: Source principal requires `roles/iam.serviceAccountTokenCreator` role.

### Credentials Caching

```python
from kiarina.lib.google.auth import CredentialsCache

class InMemoryCache(CredentialsCache):
    def __init__(self):
        self._cache: str | None = None

    def get(self) -> str | None:
        return self._cache

    def set(self, value: str) -> None:
        self._cache = value

# Use cache for user account credentials
credentials = get_credentials(
    settings=GoogleAuthSettings(
        type="user_account",
        authorized_user_file="~/authorized-user.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    ),
    cache=InMemoryCache()
)
```

### Self-Signed JWT

```python
from kiarina.lib.google.auth import get_self_signed_jwt

jwt_token = get_self_signed_jwt(
    settings=GoogleAuthSettings(
        type="service_account",
        service_account_file="~/key.json"
    ),
    audience="https://your-service.example.com/"
)
```

## Configuration

### YAML Configuration (Recommended)

```yaml
kiarina.lib.google.auth:
  development:
    type: user_account
    authorized_user_file: ~/.config/gcloud/application_default_credentials.json
    scopes:
      - https://www.googleapis.com/auth/cloud-platform

  production:
    type: service_account
    service_account_file: /secrets/prod-sa-key.json
    project_id: your-project-id
    scopes:
      - https://www.googleapis.com/auth/cloud-platform

  impersonation:
    type: service_account
    service_account_file: ~/source-key.json
    impersonate_service_account: target@project.iam.gserviceaccount.com
    scopes:
      - https://www.googleapis.com/auth/cloud-platform
```

Load configuration:

```python
from pydantic_settings_manager import load_user_configs
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)
    load_user_configs(config)

# Use configured credentials
from kiarina.lib.google.auth import get_credentials
credentials = get_credentials("production")
```

### Environment Variables

```bash
export KIARINA_LIB_GOOGLE_AUTH_TYPE="service_account"
export KIARINA_LIB_GOOGLE_AUTH_SERVICE_ACCOUNT_FILE="~/key.json"
export KIARINA_LIB_GOOGLE_AUTH_PROJECT_ID="your-project-id"
export KIARINA_LIB_GOOGLE_AUTH_SCOPES="https://www.googleapis.com/auth/cloud-platform"
```

### Programmatic Configuration

```python
from kiarina.lib.google.auth import settings_manager

settings_manager.user_config = {
    "dev": {
        "type": "user_account",
        "authorized_user_file": "~/.config/gcloud/application_default_credentials.json"
    },
    "prod": {
        "type": "service_account",
        "service_account_file": "/secrets/key.json"
    }
}

settings_manager.active_key = "prod"
credentials = get_credentials()
```

## API Reference

### Main Functions

#### `get_credentials(settings_key=None, *, settings=None, scopes=None, cache=None)`

Get Google Cloud credentials based on configuration.

**Parameters:**
- `settings_key` (str | None): Configuration key for multi-config setup
- `settings` (GoogleAuthSettings | None): Settings object (overrides settings_key)
- `scopes` (list[str] | None): OAuth2 scopes (overrides settings.scopes)
- `cache` (CredentialsCache | None): Credentials cache for user accounts

**Returns:** `Credentials` - Google Cloud credentials

#### `get_self_signed_jwt(settings_key=None, *, settings=None, audience)`

Generate a self-signed JWT for service account authentication.

**Parameters:**
- `settings_key` (str | None): Configuration key
- `settings` (GoogleAuthSettings | None): Settings object
- `audience` (str): JWT audience (target service URL)

**Returns:** `str` - Self-signed JWT token

### Utility Functions

#### `get_default_credentials()`

Get default credentials using Application Default Credentials (ADC).

**Returns:** `Credentials`

#### `get_service_account_credentials(*, service_account_file=None, service_account_data=None)`

Get service account credentials from file or data.

**Returns:** `google.oauth2.service_account.Credentials`

#### `get_user_account_credentials(*, authorized_user_file=None, authorized_user_data=None, scopes, cache=None)`

Get user account credentials from file or data with optional caching.

**Returns:** `google.oauth2.credentials.Credentials`

### Configuration

#### `GoogleAuthSettings`

Pydantic settings model for authentication configuration.

**Key Fields:**
- `type`: Authentication type (`"default"`, `"service_account"`, `"user_account"`)
- `service_account_file`: Path to service account key file
- `service_account_data`: Service account key data (JSON string, SecretStr)
- `authorized_user_file`: Path to authorized user file
- `authorized_user_data`: Authorized user data (JSON string, SecretStr)
- `impersonate_service_account`: Target service account email for impersonation
- `scopes`: OAuth2 scopes (default: cloud-platform, drive, spreadsheets)
- `project_id`: GCP project ID

**Helper Methods:**
- `get_service_account_data()`: Parse service_account_data JSON
- `get_client_secret_data()`: Parse client_secret_data JSON
- `get_authorized_user_data()`: Parse authorized_user_data JSON

#### `CredentialsCache` (Protocol)

Protocol for implementing credentials cache.

**Methods:**
- `get() -> str | None`: Retrieve cached credentials (JSON string)
- `set(value: str) -> None`: Store credentials (JSON string)

## Authentication Priority

### Default Credentials

Uses Application Default Credentials (ADC) in this order:

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable (service account)
2. `gcloud auth application-default login` credentials (user account)
3. Compute Engine metadata server (compute engine)

### Default Scopes

- `https://www.googleapis.com/auth/cloud-platform` - All GCP resources
- `https://www.googleapis.com/auth/drive` - Google Drive
- `https://www.googleapis.com/auth/spreadsheets` - Google Sheets

Override by specifying custom scopes in configuration or function call.

## Testing

### Setup Test Configuration

```bash
# Copy sample configuration
cp packages/kiarina-lib-google-auth/test_settings.sample.yaml \
   packages/kiarina-lib-google-auth/test_settings.yaml

# Edit with your credentials
# Set environment variable
export KIARINA_LIB_GOOGLE_AUTH_TEST_SETTINGS_FILE="packages/kiarina-lib-google-auth/test_settings.yaml"
```

### Run Tests

```bash
# Run all checks
mise run package kiarina-lib-google-auth

# Run tests with coverage
mise run package:test kiarina-lib-google-auth --coverage
```

## Dependencies

- [google-api-python-client](https://github.com/googleapis/google-api-python-client) - Google API client
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## License

MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - Main monorepo
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library
