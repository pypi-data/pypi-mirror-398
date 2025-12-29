from typing import Any

from redis.asyncio import Redis, RedisError


class RedisClient:
    """
    Async Redis wrapper with simple interface and context manager support.

    Usage:

        # Configure once
        await RedisClient.configure(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )
        or
        await RedisClient.configure(url="redis://localhost:6379/0", decode_responses=True)

        # Basic usage
        await RedisClient.set("key", "value")
        value = await RedisClient.get("key")

        # Context manager usage
        async with RedisClient() as redis:
            await redis.set("key", "value")
    """

    _client: Redis | None = None
    _config: dict[str, Any] = {}

    @classmethod
    async def configure(cls, **kwargs: Any) -> None:
        """Store configuration and initialize Redis client."""
        cls._config = kwargs
        await cls._init_client()

    @classmethod
    async def _init_client(cls) -> Redis:
        """Initialize the Redis client if not already initialized."""
        if cls._client is None:
            if not cls._config:
                raise RuntimeError(
                    "RedisClient is not configured. Call `configure()` first."
                )
            try:
                if "url" in cls._config:
                    url = cls._config.pop("url")
                    cls._client = await Redis.from_url(url, **cls._config)
                else:
                    cls._client = Redis(**cls._config)
            except RedisError as e:
                raise RuntimeError(f"Failed to initialize Redis client: {e}") from e
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client:
            try:
                await cls._client.aclose()
            except RedisError:
                pass
            finally:
                cls._client = None

    async def __aenter__(self) -> "RedisClient":
        await self._init_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        client = await self._init_client()
        try:
            return await client.set(key, value, ex=ex)
        except RedisError as e:
            raise RuntimeError(f"Redis SET failed: {e}")

    async def get(self, key: str) -> Any:
        client = await self._init_client()
        try:
            return await client.get(key)
        except RedisError as e:
            raise RuntimeError(f"Redis GET failed: {e}")

    async def delete(self, key: str) -> int:
        client = await self._init_client()
        try:
            return await client.delete(key)
        except RedisError as e:
            raise RuntimeError(f"Redis DELETE failed: {e}")

    async def exists(self, key: str) -> int:
        client = await self._init_client()
        try:
            return await client.exists(key)
        except RedisError as e:
            raise RuntimeError(f"Redis EXISTS failed: {e}")

    async def expire(self, key: str, seconds: int) -> bool:
        client = await self._init_client()
        try:
            return await client.expire(key, seconds)
        except RedisError as e:
            raise RuntimeError(f"Redis EXPIRE failed: {e}")

    async def incr(self, key: str) -> int:
        client = await self._init_client()
        try:
            return await client.incr(key)
        except RedisError as e:
            raise RuntimeError(f"Redis INCR failed: {e}")

    async def ttl(self, key: str) -> int:
        client = await self._init_client()
        try:
            return await client.ttl(key)
        except RedisError as e:
            raise RuntimeError(f"Redis TTL failed: {e}")
