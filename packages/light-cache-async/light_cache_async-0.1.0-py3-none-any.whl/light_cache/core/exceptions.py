class CacheError(Exception):
    """Erro base da lib de cache."""


class CacheBackendError(CacheError):
    """Erro no backend (Redis, Memory, etc)."""


class CacheSerializationError(CacheError):
    """Erro ao serializar ou desserializar."""


class CacheKeyError(CacheError):
    """Erro ao gerar chave de cache."""
