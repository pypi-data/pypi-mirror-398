import asyncio

import pytest
import pytest_asyncio
from testcontainers.redis import RedisContainer

from marsel import RedisClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def redis_uri():
    container = RedisContainer("redis:7")
    container.start()

    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)
        yield f"redis://{host}:{port}"
    finally:
        container.stop()


@pytest_asyncio.fixture
async def redis_client_fixture(redis_uri):
    await RedisClient.configure(url=redis_uri, decode_responses=True)
    yield RedisClient()
    await RedisClient.close()
