# kiarina-lib-cloudflare-d1

A Python client library for [Cloudflare D1](https://developers.cloudflare.com/d1/) with configuration management using [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager).

## Purpose

This library separates infrastructure configuration (database IDs, credentials) from application code, enabling:

- **Environment-agnostic code**: Same code works in dev, staging, and production
- **External configuration**: Manage settings via YAML files or environment variables
- **Multi-tenancy support**: Handle multiple D1 databases with different configurations
- **Easy testing**: Inject test configurations without modifying code

## Installation

```bash
pip install kiarina-lib-cloudflare-d1
```

## Quick Start

### Basic Usage (Sync)

```python
from kiarina.lib.cloudflare.d1 import create_d1_client

# Create client (configuration loaded from environment or settings)
client = create_d1_client()

# Execute query
result = client.query("SELECT * FROM users WHERE id = ?", [1])

# Access results
if result.success:
    for row in result.first.rows:
        print(row)
```

### Async Usage

```python
from kiarina.lib.cloudflare.d1.asyncio import create_d1_client

async def main():
    client = create_d1_client()
    result = await client.query("SELECT * FROM users WHERE id = ?", [1])

    if result.success:
        for row in result.first.rows:
            print(row)
```

### CRUD Operations

```python
from kiarina.lib.cloudflare.d1 import create_d1_client

client = create_d1_client()

# Create
result = client.query(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    ["Alice", "alice@example.com"]
)

# Read
result = client.query("SELECT * FROM users WHERE name = ?", ["Alice"])
users = result.first.rows

# Update
result = client.query(
    "UPDATE users SET email = ? WHERE name = ?",
    ["alice.new@example.com", "Alice"]
)

# Delete
result = client.query("DELETE FROM users WHERE name = ?", ["Alice"])
```

### Error Handling

```python
result = client.query("SELECT * FROM users")

if not result.success:
    # Check errors
    for error in result.errors:
        print(f"Error: {error}")

    # Or raise exception
    result.raise_for_status()
else:
    # Access results safely
    if result.result:
        for row in result.first.rows:
            print(row)
```

## API Reference

### Functions

#### `create_d1_client()`

Create a D1 client with configuration.

```python
def create_d1_client(
    settings_key: str | None = None,
    *,
    auth_settings_key: str | None = None,
) -> D1Client
```

**Parameters:**
- `settings_key`: Configuration key for D1 settings (default: uses active key)
- `auth_settings_key`: Configuration key for authentication (default: uses active key)

**Returns:** Configured `D1Client` instance

**Example:**
```python
# Use default configuration
client = create_d1_client()

# Use specific configuration
client = create_d1_client(
    settings_key="production",
    auth_settings_key="production"
)
```

### Classes

#### `D1Client`

Main client for interacting with Cloudflare D1.

**Methods:**

##### `query(sql: str, params: list[Any] | None = None) -> Result`

Execute a SQL query with optional parameters.

**Parameters:**
- `sql`: SQL query string
- `params`: Query parameters for parameterized statements (default: None)

**Returns:** `Result` object containing query results

**Example:**
```python
# Simple query
result = client.query("SELECT * FROM users")

# Parameterized query
result = client.query("SELECT * FROM users WHERE age > ?", [18])
```

#### `Result`

Query result container.

**Properties:**
- `success` (bool): Whether the query was successful
- `result` (list[QueryResult]): List of query results
- `errors` (list[ResponseInfo]): List of errors if query failed
- `messages` (list[ResponseInfo]): List of informational messages
- `first` (QueryResult): First query result (raises ValueError if empty)

**Methods:**
- `raise_for_status()`: Raise RuntimeError if query failed

**Example:**
```python
result = client.query("SELECT * FROM users")

# Check success
if result.success:
    # Access first result
    query_result = result.first

    # Access all results
    for qr in result.result:
        print(qr.rows)
```

#### `QueryResult`

Individual query result with metadata and rows.

**Properties:**
- `success` (bool): Whether this query was successful
- `meta` (dict[str, Any]): Query metadata (duration, rows read/written, etc.)
- `results` (list[dict[str, Any]]): Query result rows
- `rows` (list[dict[str, Any]]): Alias for `results`

**Example:**
```python
query_result = result.first

# Access metadata
print(f"Duration: {query_result.meta.get('duration')}ms")
print(f"Rows read: {query_result.meta.get('rows_read')}")

# Access rows
for row in query_result.rows:
    print(f"User: {row['name']}")
```

#### `ResponseInfo`

Error or message information.

**Properties:**
- `code` (int): Response code
- `message` (str): Response message

## Configuration

This library uses [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) for configuration management and requires [kiarina-lib-cloudflare-auth](../kiarina-lib-cloudflare-auth/) for authentication.

### YAML Configuration

```yaml
# config/production.yaml
kiarina.lib.cloudflare.d1:
  default:
    database_id: "prod-database-id"

kiarina.lib.cloudflare.auth:
  default:
    account_id: "prod-account-id"
    api_token: "${CLOUDFLARE_API_TOKEN}"  # From environment
```

```python
# Load configuration using pydantic-settings-manager
import yaml
from pydantic_settings_manager import load_user_configs

with open("config/production.yaml") as f:
    config = yaml.safe_load(f)

load_user_configs(config)

# Now create client with loaded configuration
client = create_d1_client()
```

### Settings Reference

#### `D1Settings`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database_id` | `str` | Yes | Cloudflare D1 database ID |

**Environment variable prefix:** `KIARINA_LIB_CLOUDFLARE_D1_`

#### Authentication Settings

See [kiarina-lib-cloudflare-auth](../kiarina-lib-cloudflare-auth/README.md) for authentication configuration details.

Required fields:
- `account_id`: Cloudflare account ID
- `api_token`: Cloudflare API token

**Environment variable prefix:** `KIARINA_LIB_CLOUDFLARE_AUTH_`

## Testing

Tests require actual Cloudflare D1 credentials. Create a `.env` file:

```bash
# .env
KIARINA_LIB_CLOUDFLARE_D1_TEST_SETTINGS_FILE=/path/to/test_settings.yaml
```

Create `test_settings.yaml`:

```yaml
kiarina.lib.cloudflare.auth:
  default:
    account_id: "your-test-account-id"
    api_token: "your-test-api-token"

kiarina.lib.cloudflare.d1:
  default:
    database_id: "your-test-database-id"
```

Run tests:

```bash
# Run all checks
mise run package kiarina-lib-cloudflare-d1

# Run tests with coverage
mise run package:test kiarina-lib-cloudflare-d1 --coverage
```

Tests will be skipped if credentials are not configured.

## Dependencies

- [httpx](https://www.python-httpx.org/) - HTTP client
- [kiarina-lib-cloudflare-auth](../kiarina-lib-cloudflare-auth/) - Cloudflare authentication
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## License

MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - Main monorepo
- [kiarina-lib-cloudflare-auth](../kiarina-lib-cloudflare-auth/) - Cloudflare authentication library
- [Cloudflare D1](https://developers.cloudflare.com/d1/) - Cloudflare's serverless SQL database
