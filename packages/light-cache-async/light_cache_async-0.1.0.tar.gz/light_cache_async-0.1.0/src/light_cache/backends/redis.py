from typing import Optional

from redis import asyncio as aioredis

from light_cache.core.interfaces import AsyncCacheBackend
from light_cache.core.exceptions import CacheBackendError


class RedisCacheBackend(AsyncCacheBackend):
    def __init__(
        self,
        redis_url: str,
        *,
        prefix: str | None = None,
        socket_timeout: float = 1.0,
    ):
        """
        redis_url: ex redis://localhost:6379/0
        prefix: namespace opcional no Redis
        """
        self._prefix = prefix
        self._redis = aioredis.from_url(
            redis_url,
            decode_responses=False,  # BYTES
            socket_timeout=socket_timeout,
        )

    def _key(self, key: str) -> str:
        if self._prefix:
            return f"{self._prefix}:{key}"
        return key

    async def get(self, key: str) -> Optional[bytes]:
        try:
            return await self._redis.get(self._key(key))
        except Exception as exc:
            raise CacheBackendError("Erro ao ler do Redis") from exc

    async def set(self, key: str, value: bytes, ttl: int) -> None:
        try:
            await self._redis.setex(self._key(key), ttl, value)
        except Exception as exc:
            raise CacheBackendError("Erro ao escrever no Redis") from exc

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(self._key(key))
        except Exception:
            pass

    async def close(self):
        await self._redis.close()
