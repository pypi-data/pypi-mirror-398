"""
Cloud Monitoring integration for custom metrics.

Provides methods to record SRE metrics to Google Cloud Monitoring.
"""

import logging
import time
from typing import Optional


class MonitoringClient:
    """
    Cloud Monitoring integration.

    Records custom metrics for:
    - Request latency
    - Retry counts
    - Success/failure rates
    - Validation failures
    - Circuit breaker states
    """

    def __init__(self, project_id: str, service_name: str = "gemini-sre"):
        """
        Initialize monitoring client.

        Args:
            project_id: GCP project ID
            service_name: Service name for metrics namespace
        """
        self.project_id = project_id
        self.service_name = service_name

        # Lazy initialization
        self._metrics_client = None
        self._project_name = None
        self._logger = logging.getLogger(__name__)

        self._initialize()

    def _initialize(self):
        """Initialize Cloud Monitoring client and create metric descriptors."""
        try:
            from google.cloud import monitoring_v3

            self._metrics_client = monitoring_v3.MetricServiceClient()
            self._project_name = f"projects/{self.project_id}"

            # Create metric descriptors
            self._create_metric_descriptors()

        except Exception as e:
            self._logger.warning(f"Cloud Monitoring setup failed: {e}")
            self._metrics_client = None

    def _create_metric_descriptors(self):
        """Create metric descriptors for Cloud Monitoring."""
        if not self._metrics_client:
            return

        from google.api import metric_pb2

        descriptors = [
            {
                "type": f"custom.googleapis.com/{self.service_name}/retry_count",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.GAUGE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
                "description": "Number of retries performed per request",
                "display_name": f"{self.service_name.title()} Retry Count",
            },
            {
                "type": f"custom.googleapis.com/{self.service_name}/retry_success",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.CUMULATIVE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
                "description": "Number of successful requests after retries",
                "display_name": f"{self.service_name.title()} Retry Success",
            },
            {
                "type": f"custom.googleapis.com/{self.service_name}/retry_failure",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.CUMULATIVE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
                "description": "Number of failed requests after all retries",
                "display_name": f"{self.service_name.title()} Retry Failure",
            },
            {
                "type": f"custom.googleapis.com/{self.service_name}/request_latency",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.GAUGE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.DOUBLE,
                "description": "Total request latency (including retries)",
                "display_name": f"{self.service_name.title()} Request Latency",
                "unit": "s",
            },
            {
                "type": f"custom.googleapis.com/{self.service_name}/validation_failure",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.CUMULATIVE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
                "description": "Number of validation failures",
                "display_name": f"{self.service_name.title()} Validation Failure",
            },
            {
                "type": f"custom.googleapis.com/{self.service_name}/circuit_breaker_open",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.GAUGE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
                "description": "Number of regions with open circuit breakers",
                "display_name": f"{self.service_name.title()} Circuit Breaker Open Count",
            },
            {
                "type": f"custom.googleapis.com/{self.service_name}/circuit_breaker_state_change",
                "metric_kind": metric_pb2.MetricDescriptor.MetricKind.CUMULATIVE,
                "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
                "description": "Circuit breaker state transitions",
                "display_name": f"{self.service_name.title()} Circuit State Changes",
            },
        ]

        for descriptor_config in descriptors:
            try:
                descriptor = metric_pb2.MetricDescriptor(
                    type=descriptor_config["type"],
                    metric_kind=descriptor_config["metric_kind"],
                    value_type=descriptor_config["value_type"],
                    description=descriptor_config["description"],
                    display_name=descriptor_config["display_name"],
                    unit=descriptor_config.get("unit", "1"),
                )
                self._metrics_client.create_metric_descriptor(
                    name=self._project_name, metric_descriptor=descriptor
                )
                self._logger.info(f"Metric descriptor created: {descriptor_config['display_name']}")
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    self._logger.debug(
                        f"Metric descriptor already exists: {descriptor_config['display_name']}"
                    )
                else:
                    self._logger.warning(f"Error creating metric descriptor: {e}")

    def record_success(
        self,
        latency: float,
        retry_count: int,
        location: str,
        model: Optional[str] = None,
    ):
        """
        Record successful request.

        Args:
            latency: Request latency in seconds
            retry_count: Number of retries performed
            location: GCP region
            model: Optional model name
        """
        labels = {"location": location}
        if model:
            labels["model"] = model

        self._write_metric("request_latency", latency, labels)
        self._write_metric("retry_count", retry_count, labels)
        self._write_metric("retry_success", 1, labels)

    def record_failure(
        self,
        error: str,
        retry_count: int,
        location: str,
        model: Optional[str] = None,
    ):
        """
        Record failed request.

        Args:
            error: Error message
            retry_count: Number of retries performed
            location: GCP region
            model: Optional model name
        """
        labels = {"location": location, "error": error[:100]}
        if model:
            labels["model"] = model

        self._write_metric("retry_count", retry_count, labels)
        self._write_metric("retry_failure", 1, labels)

    def _write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ):
        """
        Write metric to Cloud Monitoring.

        Args:
            metric_type: Metric type (latency, retry_count, etc.)
            value: Metric value
            labels: Optional metric labels
        """
        if not self._metrics_client:
            return

        try:
            from google.cloud import monitoring_v3

            series = monitoring_v3.types.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{self.service_name}/{metric_type}"

            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = str(val)

            series.resource.type = "global"
            series.resource.labels["project_id"] = self.project_id

            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10**9)

            # For CUMULATIVE metrics, start_time is required
            if metric_type in [
                "retry_success",
                "retry_failure",
                "validation_failure",
                "circuit_breaker_state_change",
            ]:
                interval = monitoring_v3.types.TimeInterval(
                    end_time={"seconds": seconds, "nanos": nanos},
                    start_time={"seconds": seconds - 60, "nanos": nanos},
                )
            else:
                interval = monitoring_v3.types.TimeInterval(
                    end_time={"seconds": seconds, "nanos": nanos}
                )

            # Create Point with the correct value type
            if metric_type == "request_latency":
                point = monitoring_v3.types.Point(
                    interval=interval,
                    value=monitoring_v3.types.TypedValue(double_value=value),
                )
            else:
                point = monitoring_v3.types.Point(
                    interval=interval,
                    value=monitoring_v3.types.TypedValue(int64_value=int(value)),
                )

            series.points = [point]

            self._metrics_client.create_time_series(name=self._project_name, time_series=[series])
        except Exception as e:
            self._logger.error(f"Error writing metric {metric_type}: {e}")
