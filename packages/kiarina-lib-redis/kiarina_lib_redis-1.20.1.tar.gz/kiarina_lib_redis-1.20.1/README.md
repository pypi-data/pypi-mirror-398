# kiarina-lib-redis

A Python client library for [Redis](https://redis.io/) with configuration management and connection pooling.

## Purpose

This library provides a thin wrapper around the Redis Python client with:
- Configuration management using `pydantic-settings-manager`
- Automatic connection caching and pooling
- Built-in retry mechanism for connection failures
- Support for both synchronous and asynchronous operations

## Installation

```bash
pip install kiarina-lib-redis
```

## Quick Start

### Synchronous Usage

```python
from kiarina.lib.redis import get_redis

# Get a Redis client
redis = get_redis(decode_responses=True)

# Basic operations
redis.set("key", "value")
value = redis.get("key")
print(value)  # 'value'
```

### Asynchronous Usage

```python
from kiarina.lib.redis.asyncio import get_redis

async def main():
    redis = get_redis(decode_responses=True)

    await redis.set("key", "value")
    value = await redis.get("key")
    print(value)  # 'value'
```

## API Reference

### `get_redis()`

Get a Redis client with configuration management.

```python
def get_redis(
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> redis.Redis:
```

**Parameters:**
- `settings_key`: Configuration key to use (for multi-configuration setups)
- `cache_key`: Cache key for connection pooling (defaults to URL)
- `use_retry`: Enable automatic retry on connection errors
- `url`: Redis connection URL (overrides configuration)
- `**kwargs`: Additional parameters passed to `redis.Redis.from_url()`

**Returns:**
- `redis.Redis`: Redis client instance (cached)

### `RedisSettings`

Configuration model for Redis connection.

**Fields:**
- `url: SecretStr` - Redis connection URL (default: `"redis://localhost:6379"`)
- `use_retry: bool` - Enable automatic retries (default: `False`)
- `socket_timeout: float` - Socket timeout in seconds (default: `6.0`)
- `socket_connect_timeout: float` - Connection timeout in seconds (default: `3.0`)
- `health_check_interval: int` - Health check interval in seconds (default: `60`)
- `retry_attempts: int` - Number of retry attempts (default: `3`)
- `retry_delay: float` - Delay between retries in seconds (default: `1.0`)
- `initialize_params: dict[str, Any]` - Additional Redis client parameters

### `settings_manager`

Global settings manager instance for Redis configuration.

```python
from kiarina.lib.redis import settings_manager

# Configure multiple environments
settings_manager.user_config = {
    "development": {"url": "redis://localhost:6379"},
    "production": {"url": "redis://prod:6379", "use_retry": True}
}

# Switch configuration
settings_manager.active_key = "production"
```

## Configuration

Configuration can be provided via YAML files using `pydantic-settings-manager`.

### YAML Configuration

```yaml
# config.yaml
kiarina.lib.redis:
  development:
    url: "redis://localhost:6379"
    use_retry: false

  production:
    url: "redis://prod-server:6379"
    use_retry: true
    socket_timeout: 10.0
    retry_attempts: 5
    retry_delay: 2.0
```

Load configuration:

```python
import yaml
from kiarina.lib.redis import settings_manager

with open("config.yaml") as f:
    config = yaml.safe_load(f)
    settings_manager.user_config = config["kiarina.lib.redis"]

# For multi-config
settings_manager.active_key = "production"
```

### Environment Variables

All settings can be overridden using environment variables with the `KIARINA_LIB_REDIS_` prefix:

```bash
export KIARINA_LIB_REDIS_URL="redis://localhost:6379"
export KIARINA_LIB_REDIS_USE_RETRY="true"
export KIARINA_LIB_REDIS_SOCKET_TIMEOUT="10.0"
```

### URL Formats

- `redis://localhost:6379` - Basic connection
- `redis://username:password@localhost:6379` - With authentication
- `rediss://localhost:6379` - SSL/TLS connection
- `redis://localhost:6379/0` - Specify database number
- `unix:///path/to/socket.sock` - Unix socket connection

## Testing

```bash
# Start Redis for testing
docker compose up -d redis

# Run tests
mise run package:test kiarina-lib-redis

# With coverage
mise run package:test kiarina-lib-redis --coverage
```

## Dependencies

- [redis](https://github.com/redis/redis-py) - Redis client for Python
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [Redis](https://redis.io/) - The in-memory data structure store
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library
