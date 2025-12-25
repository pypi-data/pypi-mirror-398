from .base import CacheProvider

class InMemoryCache(CacheProvider):

    def __init__(self):
        self.store = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value, ttl=None):
        self.store[key] = value
