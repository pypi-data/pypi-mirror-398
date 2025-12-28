from abc import ABC, abstractmethod
from typing import Optional, Any


class AsyncCacheBackend(ABC):
    """Contrato base para backends de cache async."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        ...

    async def delete(self, key: str) -> None:
        """Opcional: invalidação explícita."""
        return None
