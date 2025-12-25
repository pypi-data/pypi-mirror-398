from abc import ABC, abstractmethod

class CacheProvider(ABC):

    @abstractmethod
    def get(self, key: str): pass

    @abstractmethod
    def set(self, key: str, value, ttl=None): pass
