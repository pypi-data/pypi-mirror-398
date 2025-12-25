from .in_memory_cache import InMemoryCache
from .redis_cache import RedisCache
from ..utils.singleton import singleton

@singleton
def get_cache(provider="redis", environ="dev"):
    if provider == "memory":
        return InMemoryCache()
    if provider == "redis":
        return RedisCache(environment=environ)
    raise ValueError(f"Unknown cache provider: {provider}")
