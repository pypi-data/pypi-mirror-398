from kiarina.lib.redis.asyncio import get_redis


async def test_get_redis():
    # Check if it is cached
    redis1 = get_redis(use_retry=True, decode_responses=True)
    redis2 = get_redis()
    assert redis1 is redis2

    # Verify that changing the cache key allows retrieval of a different instance
    redis3 = get_redis(cache_key="other")
    assert redis1 is not redis3

    # Test basic set and get operations
    await redis1.set("test_get_redis", "hello")
    value = await redis1.get("test_get_redis")
    assert value == "hello"
