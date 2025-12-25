"""
OpenTelemetry Exporters for Logs, Traces, and Metrics
"""
import asyncio
import json
import aiohttp
from typing import Any, Dict

from ..config.data_config import ExporterConfig
from ..config.factory import get_config


class OTELLogExporter:
    def __init__(self):
        self.endpoint = ExporterConfig.log_endpoint
        print("Exporter Endpoint for logs",self.endpoint)
        self._session: aiohttp.ClientSession = None
        self._timeout_seconds = 5
        self._connect_timeout = 2

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def export(self, data: Dict[str, Any]) -> None:
        if not self.endpoint:
            print(f"[LOCAL LOG] {json.dumps(data, default=str)}", flush=True)
            return

        try:
            payload = self._format_otlp(data)
            session = await self._get_session()

            timeout = aiohttp.ClientTimeout(
                total=self._timeout_seconds,
                connect=self._connect_timeout
            )

            async with session.post(
                self.endpoint,
                json=payload,
                timeout=timeout
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    print(f"[LOG EXPORT ERROR] HTTP {response.status}: {text}", flush=True)

        except asyncio.TimeoutError:
            print(f"[LOG EXPORTER ERROR] Request timed out", flush=True)
            print(f"[FALLBACK LOG] {json.dumps(data, default=str)}", flush=True)
        except aiohttp.ClientError as e:
            print(f"[LOG EXPORTER ERROR] Network error: {e}", flush=True)
            print(f"[FALLBACK LOG] {json.dumps(data, default=str)}", flush=True)
        except Exception as e:
            print(f"[LOG EXPORTER ERROR] Unexpected error: {e}", flush=True)
            print(f"[FALLBACK LOG] {json.dumps(data, default=str)}", flush=True)

    async def shutdown(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _format_otlp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        trace_id = data.get("trace_id", "")
        span_id = data.get("span_id", "")

        if trace_id and "-" in trace_id:
            trace_id = trace_id.replace("-", "")
        if span_id and "-" in span_id:
            span_id = span_id.replace("-", "")

        trace_id = trace_id.lower()[:32].ljust(32, '0') if trace_id else ""
        span_id = span_id.lower()[:16].ljust(16, '0') if span_id else ""

        timestamp = data.get("timestamp", 0)
        timestamp_ns = int(timestamp * 1_000_000_000) if timestamp else 0

        # Build attributes (exclude standard fields)
        excluded_keys = {
            "timestamp", "level", "message", "service_name",
            "trace_id", "span_id"
        }
        attributes = [
            {"key": k, "value": {"stringValue": str(v)}}
            for k, v in data.items()
            if k not in excluded_keys and v is not None
        ]

        return {
            "resourceLogs": [{
                "resource": {
                    "attributes": [{
                        "key": "service.name",
                        "value": {"stringValue": data.get("service_name", "unknown")}
                    }]
                },
                "scopeLogs": [{
                    "logRecords": [{
                        "timeUnixNano": str(timestamp_ns),
                        "severityText": data.get("level", "INFO"),
                        "body": {"stringValue": data.get("message", "")},
                        "attributes": attributes,
                        "traceId": trace_id,
                        "spanId": span_id
                    }]
                }]
            }]
        }


class OTELTraceExporter:
    """OpenTelemetry Trace Exporter"""

    async def export(self, data: Dict[str, Any]) -> None:
        """
        Export trace/span data to OTLP endpoint.

        Args:
            data: Span data to export
        """
        self.endpoint = ExporterConfig.trace_endpoint
        # Handle empty or error data
        if not data or "error" in data:
            print(f"[TRACE EXPORT SKIPPED] Invalid data: {data}")
            return

        if not self.endpoint:
            print(f"[LOCAL SPAN] {json.dumps(data, default=str)}")
            return

        try:
            payload = self._format_otlp(data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.endpoint}",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        print(f"[TRACE EXPORT ERROR] {response.status}: {text}")
                    # Success - no need to log

        except aiohttp.ClientError as e:
            print(f"[TRACE EXPORTER ERROR] Network error: {e}")
            print(f"[FALLBACK SPAN] {json.dumps(data, default=str)}")
        except Exception as e:
            print(f"[TRACE EXPORTER ERROR] Failed to send span: {e}")
            print(f"[FALLBACK SPAN] {json.dumps(data, default=str)}")

    async def shutdown(self) -> None:
        """Shutdown the exporter"""
        pass

    def _format_otlp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format span data to OTLP format.

        Args:
            data: Span data dictionary

        Returns:
            OTLP-formatted payload
        """
        trace_id = data.get("trace_id", "")
        span_id = data.get("span_id", "")

        # Normalize to OTLP format (no dashes)
        if "-" in trace_id:
            trace_id = trace_id.replace("-", "")
        if "-" in span_id:
            span_id = span_id.replace("-", "")

        # Ensure proper length (32 hex chars for trace_id, 16 for span_id)
        trace_id = trace_id.lower()[:32].zfill(32)
        span_id = span_id.lower()[:16].zfill(16)

        # Convert timestamps to nanoseconds
        start_time = data.get("start_time", 0)
        end_time = data.get("end_time", 0)

        # If timestamps are in seconds or milliseconds, convert to nanoseconds
        if start_time < 10 ** 15:  # Less than year 33658 in nanoseconds
            start_time = int(start_time * 10 ** 9) if start_time > 0 else int(start_time)
        if end_time < 10 ** 15:
            end_time = int(end_time * 10 ** 9) if end_time > 0 else int(end_time)

        # Build attributes
        attributes = []
        for key, value in data.get("attributes", {}).items():
            attributes.append({
                "key": key,
                "value": {"stringValue": str(value)}
            })

        # Map span kind
        span_kind = self._map_span_kind(data.get("kind", "INTERNAL"))

        return {
            "resourceSpans": [{
                "resource": {
                    "attributes": [{
                        "key": "service.name",
                        "value": {"stringValue": data.get("service_name", "unknown")}
                    }]
                },
                "scopeSpans": [{
                    "spans": [{
                        "traceId": trace_id,
                        "spanId": span_id,
                        "name": data.get("name", "unknown"),
                        "kind": span_kind,
                        "body":data.get("message",""),
                        "startTimeUnixNano": str(start_time),
                        "endTimeUnixNano": str(end_time),
                        "attributes": attributes,
                        "status": {
                            "code": self._map_status_code(data.get("status", "UNSET"))
                        }
                    }]
                }]
            }]
        }

    @staticmethod
    def _map_span_kind(kind: str) -> int:
        """Map span kind string to OTLP integer"""
        mapping = {
            "INTERNAL": 1,
            "SERVER": 2,
            "CLIENT": 3,
            "PRODUCER": 4,
            "CONSUMER": 5,
        }
        return mapping.get(str(kind).upper(), 1)

    @staticmethod
    def _map_status_code(status: str) -> int:
        """Map status string to OTLP integer"""
        mapping = {
            "UNSET": 0,
            "OK": 1,
            "ERROR": 2,
        }
        return mapping.get(str(status).upper(), 0)


class OTELMetricsExporter:
    def __init__(self):
        self.config = get_config.get()
        self.endpoint = ExporterConfig.metrics_endpoint

    async def export(self, data: Dict[str, Any]) -> None:
        if not self.endpoint:
            print(f"[LOCAL METRIC] {json.dumps(data, default=str)}")
            return

        try:
            payload = self._format_otlp(data)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.endpoint,
                        json=payload,
                        timeout=5
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        print(f"[EXPORT ERROR] {response.status}: {text}")

        except Exception as e:
            print(f"[EXPORTER ERROR] Failed to send metric: {e}")
            print(f"[FALLBACK METRIC] {json.dumps(data, default=str)}")

    async def shutdown(self) -> None:
        pass

    def _format_otlp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        metric_type = data.get("metric_type", "GAUGE").upper()
        name = data.get("name", "unknown_metric")
        value = data.get("value", 0)
        timestamp_ns = int(data.get("timestamp", 0) * 1000000000)

        attributes = []
        excluded_keys = {
            "metric_type", "name", "value", "timestamp",
            "service_name", "trace_id", "span_id", "correlation_id"
        }

        if "attributes" in data and isinstance(data["attributes"], dict):
            for k, v in data["attributes"].items():
                attributes.append({
                    "key": k,
                    "value": {"stringValue": str(v)}
                })

        for k, v in data.items():
            if k not in excluded_keys and k != "attributes":
                attributes.append({
                    "key": k,
                    "value": {"stringValue": str(v)}
                })

        metric_data_point = {
            "timeUnixNano": str(timestamp_ns),
            "attributes": attributes
        }

        if metric_type == "COUNTER":
            metric_data_point["asDouble"] = float(value)
            data_points_key = "dataPoints"
            metric_key = "sum"
            metric_specific = {
                "aggregationTemporality": 2,
                "isMonotonic": True
            }
        elif metric_type == "GAUGE":
            metric_data_point["asDouble"] = float(value)
            data_points_key = "dataPoints"
            metric_key = "gauge"
            metric_specific = {}
        elif metric_type == "HISTOGRAM":
            metric_data_point.update({
                "count": "1",
                "sum": float(value),
                "bucketCounts": ["1"],
                "explicitBounds": []
            })
            data_points_key = "dataPoints"
            metric_key = "histogram"
            metric_specific = {
                "aggregationTemporality": 2
            }
        else:
            metric_data_point["asDouble"] = float(value)
            data_points_key = "dataPoints"
            metric_key = "gauge"
            metric_specific = {}

        return {
            "resourceMetrics": [{
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {"stringValue": getattr(self.config, "service_name","unknown-service-name")}
                        },
                        {
                            "key": "service.version",
                            "value": {"stringValue": getattr(self.config, "service_version","1.0.0")}
                        },
                        {
                            "key": "deployment.environment",
                            "value": {"stringValue": getattr(self.config, "environment","Dev")}
                        }
                    ]
                },
                "scopeMetrics": [{
                    "metrics": [{
                        "name": name,
                        metric_key: {
                            **metric_specific,
                            data_points_key: [metric_data_point]
                        }
                    }]
                }]
            }]
        }



