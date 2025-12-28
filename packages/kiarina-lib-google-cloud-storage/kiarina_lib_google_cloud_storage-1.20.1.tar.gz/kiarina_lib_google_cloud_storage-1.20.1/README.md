# kiarina-lib-google-cloud-storage

A Python client library for Google Cloud Storage with configuration management using pydantic-settings-manager.

## Purpose

This library separates infrastructure configuration (bucket names, blob paths, credentials) from application code, enabling:

- Multi-environment deployment with the same codebase
- Multi-tenant applications with isolated storage
- Testable code without hard-coded infrastructure details
- Blob path structures aligned with GCS security rules

## Installation

```bash
pip install kiarina-lib-google-cloud-storage
```

## Quick Start

```python
from kiarina.lib.google.cloud_storage import get_blob, settings_manager

# Configure storage settings
settings_manager.user_config = {
    "default": {
        "bucket_name": "my-app-data",
        "blob_name_pattern": "users/{user_id}/files/{basename}"
    }
}

# Get blob with placeholders
blob = get_blob(placeholders={
    "user_id": "123",
    "basename": "profile.json"
})
# Actual path: gs://my-app-data/users/123/files/profile.json

# Use native google-cloud-storage API
blob.upload_from_string("Hello, World!")
content = blob.download_as_text()
```

## API Reference

### get_storage_client()

Get an authenticated Google Cloud Storage client.

```python
def get_storage_client(
    auth_settings_key: str | None = None,
    **kwargs: Any
) -> storage.Client
```

**Parameters:**
- `auth_settings_key`: Configuration key for kiarina-lib-google-auth (default: `None`)
- `**kwargs`: Additional arguments passed to `storage.Client()`

**Returns:** `storage.Client` - Authenticated Google Cloud Storage client

**Example:**
```python
from kiarina.lib.google.cloud_storage import get_storage_client

client = get_storage_client()
client = get_storage_client(auth_settings_key="production")
```

### get_bucket()

Get a Google Cloud Storage bucket.

```python
def get_bucket(
    settings_key: str | None = None,
    *,
    auth_settings_key: str | None = None,
    **kwargs: Any
) -> storage.Bucket
```

**Parameters:**
- `settings_key`: Configuration key for storage settings (default: `None`)
- `auth_settings_key`: Configuration key for authentication (default: `None`)
- `**kwargs`: Additional arguments passed to `get_storage_client()`

**Returns:** `storage.Bucket` - Google Cloud Storage bucket

**Example:**
```python
from kiarina.lib.google.cloud_storage import get_bucket

bucket = get_bucket()
bucket = get_bucket(settings_key="production", auth_settings_key="prod_auth")

# Use native google-cloud-storage API
for blob in bucket.list_blobs(prefix="users/"):
    print(blob.name)
```

### get_blob()

Get a Google Cloud Storage blob.

```python
def get_blob(
    blob_name: str | None = None,
    *,
    placeholders: dict[str, Any] | None = None,
    settings_key: str | None = None,
    auth_settings_key: str | None = None,
    **kwargs: Any
) -> storage.Blob
```

**Parameters:**
- `blob_name`: Full blob path (default: `None`)
- `placeholders`: Placeholders for `blob_name_pattern` formatting (default: `None`)
- `settings_key`: Configuration key for storage settings (default: `None`)
- `auth_settings_key`: Configuration key for authentication (default: `None`)
- `**kwargs`: Additional arguments passed to `get_bucket()`

**Returns:** `storage.Blob` - Google Cloud Storage blob

**Blob Name Resolution Priority:**
1. Explicit `blob_name` parameter
2. `blob_name_pattern` with `placeholders`
3. `blob_name_pattern` without placeholders (fixed name)

**Example:**
```python
from kiarina.lib.google.cloud_storage import get_blob

# Direct blob name
blob = get_blob(blob_name="users/123/profile.json")

# Using pattern with placeholders
blob = get_blob(placeholders={"user_id": "123", "basename": "profile.json"})

# Using fixed pattern from settings
blob = get_blob()

# Use native google-cloud-storage API
blob.upload_from_string("content")
content = blob.download_as_text()
blob.delete()
```

### GoogleCloudStorageSettings

Pydantic settings model for Google Cloud Storage configuration.

**Fields:**
- `bucket_name` (`str`, required): Google Cloud Storage bucket name
- `blob_name_pattern` (`str | None`, optional): Blob name pattern with placeholders (e.g., `"users/{user_id}/files/{basename}"`)

**Example:**
```python
from kiarina.lib.google.cloud_storage import GoogleCloudStorageSettings

settings = GoogleCloudStorageSettings(
    bucket_name="my-bucket",
    blob_name_pattern="users/{user_id}/files/{basename}"
)
```

### settings_manager

Global settings manager instance for managing multiple configurations.

**Type:** `SettingsManager[GoogleCloudStorageSettings]`

**Example:**
```python
from kiarina.lib.google.cloud_storage import settings_manager

# Single configuration
settings_manager.user_config = {
    "bucket_name": "my-bucket",
    "blob_name_pattern": "files/{basename}"
}

# Multiple configurations
settings_manager.user_config = {
    "production": {
        "bucket_name": "prod-bucket",
        "blob_name_pattern": "v2/prod/{basename}"
    },
    "staging": {
        "bucket_name": "staging-bucket",
        "blob_name_pattern": "v2/staging/{basename}"
    }
}
```

## Configuration

### YAML Configuration

```yaml
# config/production.yaml
kiarina.lib.google.auth:
  default:
    type: service_account
    service_account_file: /secrets/prod-sa-key.json

kiarina.lib.google.cloud_storage:
  default:
    bucket_name: prod-us-west1-app-data
    blob_name_pattern: "v2/production/{tenant_id}/users/{user_id}/files/{basename}"
```

**Loading Configuration:**
```python
import yaml
from pydantic_settings_manager import load_user_configs

with open("config/production.yaml") as f:
    config = yaml.safe_load(f)
load_user_configs(config)

# Now all modules are configured
from kiarina.lib.google.cloud_storage import get_blob
blob = get_blob(placeholders={
    "tenant_id": "acme",
    "user_id": "123",
    "basename": "data.json"
})
```

**Multiple Environments:**
```yaml
# config/production.yaml
kiarina.lib.google.cloud_storage:
  default:
    bucket_name: prod-us-west1-app-data
    blob_name_pattern: "v2/production/{basename}"

# config/staging.yaml
kiarina.lib.google.cloud_storage:
  default:
    bucket_name: staging-app-data
    blob_name_pattern: "v2/staging/{basename}"

# config/development.yaml
kiarina.lib.google.cloud_storage:
  default:
    bucket_name: dev-local-data
    blob_name_pattern: "v2/dev/{basename}"
```

**Multi-Tenant Configuration:**
```yaml
kiarina.lib.google.cloud_storage:
  tenant_acme:
    bucket_name: acme-corp-data
    blob_name_pattern: "app-data/{basename}"
  tenant_globex:
    bucket_name: globex-data
    blob_name_pattern: "app-data/{basename}"
```

**Blob Name Pattern Examples:**
```yaml
# Fixed name
blob_name_pattern: "data.json"

# Single placeholder
blob_name_pattern: "files/{basename}"

# Multiple placeholders
blob_name_pattern: "my-service/{tenant_id}/users/{user_id}/files/{basename}"

# Hierarchical structure
blob_name_pattern: "v2/{environment}/{service}/{tenant_id}/{resource_type}/{resource_id}/{basename}"
```

**Environment Variables:**

All settings can be configured via environment variables with the `KIARINA_LIB_GOOGLE_CLOUD_STORAGE_` prefix:

```bash
export KIARINA_LIB_GOOGLE_CLOUD_STORAGE_BUCKET_NAME="my-bucket"
export KIARINA_LIB_GOOGLE_CLOUD_STORAGE_BLOB_NAME_PATTERN="users/{user_id}/files/{basename}"
```

**Configuration Priority:**

1. CLI arguments (via `settings_manager.cli_args`)
2. Environment variables
3. User configuration (via `settings_manager.user_config`)
4. Default values

## Testing

### Running Tests

```bash
# Run tests (requires test configuration)
mise run package:test kiarina-lib-google-cloud-storage

# With coverage
mise run package:test kiarina-lib-google-cloud-storage --coverage
```

### Test Configuration

1. Copy sample files:
   ```bash
   cp .env.sample .env
   cp test_settings.sample.yaml test_settings.yaml
   ```

2. Edit `test_settings.yaml` with your GCS configuration:
   ```yaml
   kiarina.lib.google.auth:
     service_account:
       type: service_account
       service_account_file: ~/.gcp/service-account/your-project/key.json
   
   kiarina.lib.google.cloud_storage:
     default:
       bucket_name: your-test-bucket
       blob_name_pattern: "test/{tenant_id}/users/{user_id}/files/{basename}"
   ```

3. Set environment variable:
   ```bash
   export KIARINA_LIB_GOOGLE_CLOUD_STORAGE_TEST_SETTINGS_FILE=/path/to/test_settings.yaml
   ```

### Writing Tests

```python
# tests/conftest.py
import pytest
from kiarina.lib.google.cloud_storage import settings_manager

@pytest.fixture
def storage_config():
    settings_manager.user_config = {
        "test": {
            "bucket_name": "test-bucket",
            "blob_name_pattern": "test-run/{basename}"
        }
    }

# tests/test_user_service.py
def test_save_user_profile(storage_config):
    from myapp.services import save_user_profile
    save_user_profile("user123", {"name": "Alice"})
    
    from kiarina.lib.google.cloud_storage import get_blob
    blob = get_blob(placeholders={"basename": "users/user123/profile.json"})
    assert blob.exists()
```

## Dependencies

- **[google-cloud-storage](https://github.com/googleapis/python-storage)** (>=2.19.0) - Google Cloud Storage client library
- **[kiarina-lib-google-auth](../kiarina-lib-google-auth/)** (>=1.4.0) - Google Cloud authentication library
- **[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** (>=2.10.1) - Settings management
- **[pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager)** (>=2.3.0) - Advanced settings management

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- **[kiarina-python](https://github.com/kiarina/kiarina-python)** - The main monorepo containing this package
- **[kiarina-lib-google-auth](../kiarina-lib-google-auth/)** - Google Cloud authentication library
- **[pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager)** - Configuration management library
