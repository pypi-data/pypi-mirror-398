from .logging.std_logger import StdLogger
from .logging.cloudwatch_logger import CloudWatchLogger
from .logging.otel_logger import OTELLogger
from ..utils.singleton import singleton

@singleton
def get_logger(provider):
    print(f"Provider: {provider}")
    if provider == "std":
        return StdLogger()
    if provider == "cloudwatch":
        return CloudWatchLogger()
    if provider == "otel":
        return OTELLogger()
    raise ValueError(f"Unknown logger provider: {provider}")

@singleton
def get_tracer(provider="otel"):
    from .tracing.otel_tracer import OTELTracer
    return OTELTracer.get_instance()

@singleton
def get_metrics(provider="otel"):
    from .metrics.otel_metrics import OTELMetrics
    return OTELMetrics.get_instance()
