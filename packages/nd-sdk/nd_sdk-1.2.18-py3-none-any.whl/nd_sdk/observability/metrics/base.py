from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MetricType:
    """Metric type constants"""
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"


class BaseMetricsProcessor(ABC):
    """
    Base class for metrics processors.
    Defines the interface all metrics processors must implement.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the metrics processor"""
        pass

    @abstractmethod
    def counter(self, name: str, value: float = 1.0, attributes: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Record a counter metric"""
        pass

    @abstractmethod
    def gauge(self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Record a gauge metric"""
        pass

    @abstractmethod
    def histogram(self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Record a histogram metric"""
        pass

    @abstractmethod
    async def process_metric(self, metric_type: str, name: str, value: float, **kwargs) -> None:
        """Process a metric asynchronously"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the metrics processor"""
        pass