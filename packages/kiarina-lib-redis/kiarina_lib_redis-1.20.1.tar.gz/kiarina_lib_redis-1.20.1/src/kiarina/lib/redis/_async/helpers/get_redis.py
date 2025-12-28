from typing import Any

import redis.asyncio as redis

from ..._core.helpers.get_redis import get_redis as _get_redis


def get_redis(
    settings_key: str | None = None,
    *,
    cache_key: str | None = None,
    use_retry: bool | None = None,
    url: str | None = None,
    **kwargs: Any,
) -> redis.Redis:
    """
    Get a Redis client.
    """
    return _get_redis(
        "async",
        settings_key,
        cache_key=cache_key,
        use_retry=use_retry,
        url=url,
        **kwargs,
    )
