from abc import ABC, abstractmethod

class BaseLogger(ABC):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @abstractmethod
    def info(self, msg: str): pass

    @abstractmethod
    def error(self, msg: str): pass

    @abstractmethod
    def debug(self, msg: str): pass

    @abstractmethod
    def warning(self, msg: str): pass

    @abstractmethod
    def critical(self, msg: str): pass
