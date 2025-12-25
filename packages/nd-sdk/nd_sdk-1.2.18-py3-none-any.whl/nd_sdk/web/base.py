from abc import ABC, abstractmethod

class WebFrameworkWrapper(ABC):

    @abstractmethod
    def register_error_handlers(self): pass

    @abstractmethod
    def register_middlewares(self): pass

    @abstractmethod
    def initialize(self): pass
