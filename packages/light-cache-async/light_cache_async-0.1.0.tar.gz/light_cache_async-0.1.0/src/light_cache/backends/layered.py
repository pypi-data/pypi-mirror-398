from typing import Optional

from light_cache.core.interfaces import AsyncCacheBackend


class LayeredCacheBackend(AsyncCacheBackend):
    """
    Cache em camadas (L1 + L2).

    L1: rápido (Memory)
    L2: compartilhado (Redis)
    """

    def __init__(
        self,
        l1: AsyncCacheBackend,
        l2: AsyncCacheBackend,
        l1_ttl: int | None = None,
    ):
        self._l1 = l1
        self._l2 = l2
        self._l1_ttl = l1_ttl

    async def get(self, key: str) -> Optional[bytes]:
        value = await self._l1.get(key)
        if value is not None:
            return value

        value = await self._l2.get(key)
        if value is None:
            return None

        # reidrata L1
        ttl = self._l1_ttl or 1
        await self._l1.set(key, value, ttl)

        return value

    async def set(self, key: str, value: bytes, ttl: int) -> None:
        await self._l2.set(key, value, ttl)

        ttl_l1 = self._l1_ttl or ttl
        await self._l1.set(key, value, ttl_l1)

    async def delete(self, key: str) -> None:
        await self._l1.delete(key)
        await self._l2.delete(key)
