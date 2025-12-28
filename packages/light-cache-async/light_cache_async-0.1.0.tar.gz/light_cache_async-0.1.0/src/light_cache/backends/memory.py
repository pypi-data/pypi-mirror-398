import asyncio
import time
from typing import Optional

from light_cache.core.interfaces import AsyncCacheBackend


class MemoryCacheBackend(AsyncCacheBackend):
    def __init__(self):
        self._cache: dict[str, tuple[bytes, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[bytes]:
        async with self._lock:
            item = self._cache.get(key)
            if not item:
                return None

            value, expires_at = item
            if time.time() >= expires_at:
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: bytes, ttl: int) -> None:
        async with self._lock:
            self._cache[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
