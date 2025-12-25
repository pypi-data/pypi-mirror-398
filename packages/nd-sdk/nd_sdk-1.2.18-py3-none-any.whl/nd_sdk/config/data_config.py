import os

class ServiceConfig:
    """Service configuration - set by application at startup"""
    service_name: str = os.getenv("service_name", "IDP Service")
    service_version: str = os.getenv("service_version", "1.0.0")
    environment: str = os.getenv("service_environment", "Dev")
    container_logs: bool = os.getenv("container_logs", True)
    export_logs: bool = os.getenv("export_logs", True)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class LogConfig:
    log_level: str = os.getenv("log_level", "INFO")
    log_exporter_format: str = os.getenv("log_exporter_format", "otlp")
    log_exporter_protocol: str = os.getenv("log_exporter_protocol", "http")
    log_provider: str = os.getenv("log_provider", "otel")


class ExporterConfig:
    exporter_mode: str = os.getenv("exporter_mode", "common")
    log_endpoint: str = os.getenv("log_endpoint", "http://localhost:4318/v1/logs")
    trace_endpoint: str = os.getenv("trace_endpoint", "http://localhost:4318/v1/traces")
    metrics_endpoint: str = os.getenv("metrics_endpoint", "http://localhost:4318/v1/metrics")

class TraceConfig:
    trace_provider: str = os.getenv("trace_provider", "otel")
    trace_exporter_format: str = os.getenv("trace_exporter_format", "otlp")
    trace_exporter_protocol: str = os.getenv("trace_exporter_protocol", "http")


class MetricsConfig:
    metrics_provider: str = os.getenv("metrics_provider", "otel")
    metrics_exporter_format: str = os.getenv("metrics_exporter_format", "otlp")
    metrics_exporter_protocol: str = os.getenv("metrics_exporter_protocol", "http")
    metrics_export_interval_millis: int = int(
        os.getenv("metrics_export_interval_millis", "60000")) # 60 seconds default
    environment: str = os.getenv("environment", "Dev")
    max_workers: int = int(os.getenv("max_metrics_worker", 4))