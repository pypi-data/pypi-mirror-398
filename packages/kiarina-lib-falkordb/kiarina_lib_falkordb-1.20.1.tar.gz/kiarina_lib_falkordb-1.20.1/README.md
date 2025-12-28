# kiarina-lib-falkordb

A Python client library for [FalkorDB](https://falkordb.com/) with configuration management and connection pooling.

## Features

- **Configuration Management**: Flexible settings with `pydantic-settings-manager`
- **Connection Pooling**: Automatic caching and reuse
- **Retry Support**: Built-in retry mechanism for connection failures
- **Sync & Async**: Support for both synchronous and asynchronous operations
- **Type Safety**: Full type hints and Pydantic validation

## Installation

```bash
pip install kiarina-lib-falkordb
```

## Quick Start

### Basic Usage

```python
from kiarina.lib.falkordb import get_falkordb

# Get a FalkorDB client
db = get_falkordb()

# Run a query
graph = db.select_graph("social")
result = graph.query("CREATE (p:Person {name: 'Alice', age: 30}) RETURN p")
print(result.result_set)

# Connections are cached by default
db2 = get_falkordb()
assert db is db2

# Use different cache keys for separate connections
db3 = get_falkordb(cache_key="secondary")
assert db is not db3
```

### Async Usage

```python
from kiarina.lib.falkordb.asyncio import get_falkordb

async def main():
    db = get_falkordb()
    graph = db.select_graph("social")
    result = await graph.query("CREATE (p:Person {name: 'Bob', age: 25}) RETURN p")
    print(result.result_set)
```

### Runtime Overrides

```python
# Override settings at runtime
db = get_falkordb(
    url="falkor://custom-server:6379",
    use_retry=True
)
```

## API Reference

### `get_falkordb()`

Get a FalkorDB client with configuration management.

```python
def get_falkordb(
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> FalkorDB
```

**Parameters:**
- `settings_key`: Configuration key to use (for multi-config setups)
- `cache_key`: Cache key for connection pooling (defaults to URL)
- `use_retry`: Override retry setting
- `url`: Override connection URL
- `**kwargs`: Additional parameters for FalkorDB client

**Returns:** FalkorDB client instance (cached)

## Configuration

This library uses [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) for configuration management.

### YAML Configuration (Recommended)

```yaml
# config.yaml
kiarina.lib.falkordb:
  development:
    url: "falkor://localhost:6379"
    use_retry: true
    retry_attempts: 3

  production:
    url: "falkor://prod-server:6379"
    use_retry: true
    retry_attempts: 5
    socket_timeout: 10.0
```

```python
import yaml
from kiarina.lib.falkordb import settings_manager, get_falkordb

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

settings_manager.user_config = config["kiarina.lib.falkordb"]

# Use specific configuration
settings_manager.active_key = "production"
db = get_falkordb()
```

### Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `url` | `"falkor://localhost:6379"` | FalkorDB connection URL (supports `falkor://`, `falkors://` with optional auth) |
| `use_retry` | `false` | Enable automatic retries on connection errors |
| `socket_timeout` | `6.0` | Socket timeout in seconds |
| `socket_connect_timeout` | `3.0` | Connection timeout in seconds |
| `health_check_interval` | `60` | Health check interval in seconds |
| `retry_attempts` | `3` | Number of retry attempts |
| `retry_delay` | `1.0` | Delay between retries in seconds |

All settings can be configured via environment variables with the `KIARINA_LIB_FALKORDB_` prefix.

## Testing

```bash
# Start FalkorDB
docker compose up -d falkordb

# Run tests
mise run package:test kiarina-lib-falkordb

# With coverage
mise run package:test kiarina-lib-falkordb --coverage
```

## Dependencies

- [kiarina-falkordb](https://github.com/kiarina/falkordb-py) - FalkorDB Python client (fork with redis-py 6.x support)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management
- [redis](https://github.com/redis/redis-py) - Redis client

> **Note:** This library uses a fork of the official FalkorDB client that supports redis-py 6.x and includes async bug fixes. Once these improvements are merged upstream, we'll migrate back to the official client.

## License

MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - Main monorepo
- [FalkorDB](https://www.falkordb.com/) - Graph database
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management
