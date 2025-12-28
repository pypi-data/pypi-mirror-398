import hashlib
from typing import Tuple, Dict, Any
import orjson

from .exceptions import CacheKeyError


def make_cache_key(
    prefix: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    skip_args: int = 0,
    version: str = "v1",
) -> str:
    """
    Gera chave determinística de cache baseada em hash usando orjson.

    - prefix: namespace do cache
    - skip_args: ignora args iniciais (ex: self, token)
    - version: versionamento de chave (invalidação fácil)
    """
    try:
        args = args[skip_args:]

        payload = {
            "args": args,
            "kwargs": kwargs,
        }

        # 🔹 orjson.dumps retorna bytes
        raw_bytes = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
        raw_str = raw_bytes.decode("utf-8")

        digest = hashlib.sha256(raw_str.encode()).hexdigest()
        return f"{prefix}:{version}:{digest}"

    except Exception as exc:
        raise CacheKeyError("Erro ao gerar chave de cache") from exc
