from .loaders import load_config
from ..utils.singleton import singleton
from ..config.data_config import ServiceConfig

@singleton
def get_config(config_data, provider="service"):
    if provider == "service":
        return ServiceConfig(**config_data)
    if provider == "yaml":
        return load_config()
    return None