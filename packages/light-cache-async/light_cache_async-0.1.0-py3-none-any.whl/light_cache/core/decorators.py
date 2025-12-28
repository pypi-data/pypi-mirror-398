from functools import wraps
import logging
from typing import Callable

from .interfaces import AsyncCacheBackend
from .key_builder import make_cache_key
from .serializers import Serializer, AutoSerializer

from light_cache.utils.locks import KeyLock
from light_cache.utils.time import ttl_with_jitter
from light_cache.utils.metrics import CacheMetrics


_key_lock = KeyLock()
_metrics = CacheMetrics()


def cache_response(
    *,
    cache: AsyncCacheBackend,
    key_prefix: str,
    ttl: int,
    skip_args: int = 0,
    serializer: Serializer | None = None,
    key_version: str = "v1",
    use_lock: bool = True,
    use_jitter: bool = True,
) -> Callable:
    """
    Decorator async para cache de resposta.

    - AutoSerializer por padrão
    - Dogpile protection opcional
    - TTL com jitter opcional
    """
    serializer = serializer or AutoSerializer()

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_cache_key(
                prefix=key_prefix,
                args=args,
                kwargs=kwargs,
                skip_args=skip_args,
                version=key_version,
            )

            # 🔹 1. Fast path (sem lock)
            try:
                cached = await cache.get(key)
                if cached is not None:
                    _metrics.hit(key_prefix)
                    return serializer.loads(cached)
            except Exception as ex:
                logging.error(f"Cache get error for key {key}: {ex}")
                pass

            _metrics.miss(key_prefix)

            # 🔹 2. Dogpile protection
            if use_lock:
                await _key_lock.acquire(key)

            try:
                # 🔹 3. Double-check após lock
                try:
                    cached = await cache.get(key)
                    if cached is not None:
                        _metrics.hit(key_prefix)
                        return serializer.loads(cached)
                except Exception as ex:
                    logging.error(f"Cache get error for key {key}: {ex}")
                    pass

                # 🔹 4. Executa função real
                result = await func(*args, **kwargs)

                # 🔹 5. Escreve no cache
                try:
                    effective_ttl = (
                        ttl_with_jitter(ttl) if use_jitter else ttl
                    )
                    res = serializer.dumps(result)
                    await cache.set(
                        key,
                        res,
                        effective_ttl,
                    )
                except Exception as ex:
                    logging.error(f"Cache set error for key {key}: {ex}")
                    pass

                return serializer.loads(res)

            finally:
                if use_lock:
                    _key_lock.release(key)

        return wrapper

    return decorator
