from dataclasses import dataclass
import os


@dataclass(frozen=True)
class CacheSettings:
    backend: str = "memory"      # memory | redis | layered
    redis_url: str | None = None
    redis_prefix: str | None = None
    default_ttl: int = 60
    l1_ttl: int = 2

    @classmethod
    def from_env(cls, prefix: str = "CACHE_"):
        return cls(
            backend=os.getenv(f"{prefix}BACKEND", "memory"),
            redis_url=os.getenv(f"{prefix}REDIS_URL"),
            redis_prefix=os.getenv(f"{prefix}REDIS_PREFIX"),
            default_ttl=int(os.getenv(f"{prefix}TTL", "60")),
            l1_ttl=int(os.getenv(f"{prefix}L1_TTL", "2")),
        )
