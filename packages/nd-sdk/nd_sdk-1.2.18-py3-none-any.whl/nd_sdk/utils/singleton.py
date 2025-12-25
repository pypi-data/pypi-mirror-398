class Singleton:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

class SingletonFactory:
    def __init__(self, factory_fn):
        self.factory_fn = factory_fn
        self.instance = None
        self._initialized = False

    def init(self, *args, **kwargs):
        """
        Must be called once from the application.
        """
        if self._initialized:
            return self.instance

        self.instance = self.factory_fn(*args, **kwargs)
        self._initialized = True
        return self.instance

    def get(self):
        """
        Library code calls this. Guaranteed to return the same instance.
        """
        if not self._initialized:
            raise RuntimeError(f"{self.factory_fn.__name__} not initialized. Call <{self.factory_fn.__name__}>_init(...) first.")
        return self.instance


def singleton(factory_fn):
    return SingletonFactory(factory_fn)
