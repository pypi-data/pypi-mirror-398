from ..utils.singleton import singleton
from .exception.idp_exceptions import IDPExceptionHandler

@singleton
def get_exception_handler(provider="idp"):
    if provider == "idp":
        return IDPExceptionHandler()
    raise ValueError(f"Unknown Exception provider: {provider}")
