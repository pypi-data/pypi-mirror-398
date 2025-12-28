# Light Cache

**Light Cache** é uma biblioteca Python para caching assíncrono com suporte a **Redis, memória, L1/L2**, **decorators fáceis**, **orjson** e **msgspec**.  
Projetada para **FastAPI, Granian, ML/BRMS** e qualquer aplicação async Python.

---

## 🔹 Recursos principais

- Cache assíncrono com múltiplos backends:
  - Redis (com senha e TLS)
  - Memória local (L1)
  - Cache em camadas (LayeredCache: L1 + L2)
- Decorator `@cache_response` para funções async
- Serializadores rápidos:
  - `AutoSerializer` (orjson)
  - `MsgspecSerializer` (msgspec.Struct)
- Dogpile protection (evita múltiplas execuções pesadas)
- TTL com jitter (evita stampede)
- Métricas simples: hits / misses
- Suporta versionamento de chaves (`key_version`)
- Seguro: falhas no cache não quebram a aplicação

---

## 🔹 Instalação

```bash
pip install async_cache
```

## Exemplo
```python
import msgspec

from fastapi import FastAPI
import asyncio
import random

import uvicorn

class QuoteResult(msgspec.Struct):
    product_id: str
    price: float
    discount: float

from light_cache.backends import (
    MemoryCacheBackend,
    RedisCacheBackend,
    LayeredCacheBackend,
)
from light_cache.core.decorators import cache_response
from light_cache.core.serializers import MsgspecSerializer    

memory_cache = MemoryCacheBackend()
redis_cache = RedisCacheBackend(
    redis_url="redis://localhost:6379/0",
    prefix="fastapi-demo",
)

cache = LayeredCacheBackend(
    l1=memory_cache,
    l2=redis_cache,
    l1_ttl=2,
    )

    
app = FastAPI(title="Async Cache Demo")    

@app.get("/health")
@cache_response(
    cache=cache,
    key_prefix="health",
    ttl=60,
    use_lock=False,
)
async def health():
    return {
        "status": "ok",
        "value": random.random(),
    }
    
    
@app.get("/quote/{product_id}")
@cache_response(
    cache=cache,
    key_prefix="quote",
    ttl=60,
    serializer=MsgspecSerializer(),
)
async def calculate_quote(product_id: str):
    # simula cálculo pesado
    await asyncio.sleep(1)

    return QuoteResult(
        product_id=product_id,
        price=round(random.uniform(100, 500), 2),
        discount=round(random.uniform(0, 0.3), 2),
    )

    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
```