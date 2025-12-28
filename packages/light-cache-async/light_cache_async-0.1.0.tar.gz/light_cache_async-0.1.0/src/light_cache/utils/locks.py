import asyncio
from collections import defaultdict


class KeyLock:
    """
    Lock assíncrono por chave.

    Evita múltiplas execuções concorrentes
    da mesma função quando o cache expira.
    """

    def __init__(self):
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire(self, key: str):
        lock = self._locks[key]
        await lock.acquire()

    def release(self, key: str):
        lock = self._locks.get(key)
        if lock and lock.locked():
            lock.release()
