from datetime import date
from decimal import Decimal
from typing import Any, Protocol

import json
import msgspec
import orjson

from .exceptions import CacheSerializationError


class Serializer(Protocol):
    def dumps(self, obj: Any) -> str: ...
    def loads(self, raw: str) -> Any: ...

# Classe para realizar a serialização com json

class JSONSerializer:
    """Serializer padrão baseado em JSON."""

    def dumps(self, obj: Any) -> str:
        try:
            return json.dumps(obj, cls=_CustomJSONEncoder)
        except Exception as exc:
            raise CacheSerializationError("Erro ao serializar objeto") from exc

    def loads(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except Exception as exc:
            raise CacheSerializationError("Erro ao desserializar objeto") from exc

class _CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# Classe para realizar a serialização com orjson

class OrjsonSerializer:
    """Serializer rápido baseado em orjson."""

    def dumps(self, obj: Any) -> bytes:
        try:
            return orjson.dumps(
                obj,
                option=orjson.OPT_NON_STR_KEYS
                | orjson.OPT_NAIVE_UTC
                | orjson.OPT_SERIALIZE_NUMPY,
                default=_orjson_default,
            )
        except Exception as exc:
            raise CacheSerializationError("Erro ao serializar com orjson") from exc

    def loads(self, raw: bytes) -> Any:
        try:
            return orjson.loads(raw)
        except Exception as exc:
            raise CacheSerializationError("Erro ao desserializar com orjson") from exc

def _orjson_default(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Classe para realizar a serialização com msgspec

class MsgspecSerializer:
    """
    Serializer baseado em msgspec.

    Ideal quando o retorno da função é:
    - msgspec.Struct
    - list[msgspec.Struct]
    """

    def __init__(self):
        """
        type_hint: tipo esperado (ex: MyStruct ou list[MyStruct])
        """
        self._encoder = msgspec.json.Encoder()
        self._decoder = msgspec.json.Decoder()

    def dumps(self, obj: Any) -> bytes:
        try:
            return self._encoder.encode(obj)
        except Exception as exc:
            raise CacheSerializationError("Erro ao serializar com msgspec") from exc

    def loads(self, raw: bytes) -> Any:
        try:
            return self._decoder.decode(raw)
        except Exception as exc:
            raise CacheSerializationError("Erro ao desserializar com msgspec") from exc


class AutoSerializer:
    """
    Escolhe msgspec se detectar Struct,
    senão usa orjson.
    """

    def dumps(self, obj: Any) -> bytes:
        if _is_msgspec(obj):
            return msgspec.json.encode(obj)
        return OrjsonSerializer().dumps(obj)

    def loads(self, raw: bytes) -> Any:
        # fallback genérico
        return orjson.loads(raw)


def _is_msgspec(obj: Any) -> bool:
    return isinstance(obj, msgspec.Struct)
