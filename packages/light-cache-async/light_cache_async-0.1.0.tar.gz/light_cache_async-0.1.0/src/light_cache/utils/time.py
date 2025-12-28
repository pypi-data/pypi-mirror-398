import random


def ttl_with_jitter(base_ttl: int, jitter: float = 0.1) -> int:
    """
    Adiciona jitter ao TTL para evitar
    expiração simultânea (stampede).

    jitter=0.1 → ±10%
    """
    delta = int(base_ttl * jitter)
    return base_ttl + random.randint(-delta, delta)
