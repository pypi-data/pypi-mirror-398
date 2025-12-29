import asyncio

import pytest

from marsel import RedisClient


@pytest.mark.asyncio
async def test_set_get_delete(redis_client_fixture):
    client = redis_client_fixture
    key = "test_key"
    value = "value123"

    result = await client.set(key, value, ex=5)
    assert result is True

    stored = await client.get(key)
    assert stored == value

    exists = await client.exists(key)
    assert exists == 1

    ttl = await client.ttl(key)
    assert ttl > 0

    deleted = await client.delete(key)
    assert deleted == 1

    exists = await client.exists(key)
    assert exists == 0


@pytest.mark.asyncio
async def test_incr_and_expire(redis_client_fixture):
    client = redis_client_fixture
    key = "counter"

    await client.delete(key)

    val1 = await client.incr(key)
    assert val1 == 1
    val2 = await client.incr(key)
    assert val2 == 2

    result = await client.expire(key, 2)
    assert result is True

    ttl = await client.ttl(key)
    assert 2 >= ttl > 0

    await asyncio.sleep(3)
    exists = await client.exists(key)
    assert exists == 0


@pytest.mark.asyncio
async def test_context_manager(redis_uri):
    await RedisClient.configure(url=redis_uri, decode_responses=True)

    async with RedisClient() as client:
        key = "ctx_key"
        value = "ctx_value"
        await client.set(key, value)
        stored = await client.get(key)
        assert stored == value

        await client.delete(key)
        exists = await client.exists(key)
        assert exists == 0
