"""Metrics collection system for HexSwitch using OpenTelemetry."""

import logging
import os
import sys
from typing import Any

from opentelemetry import metrics
from opentelemetry.metrics import (
    MeterProvider,
)
from opentelemetry.sdk.metrics import MeterProvider as SDKMeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    InMemoryMetricReader,
    MetricExporter,
    MetricExportResult,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry MeterProvider
_meter_provider: MeterProvider | None = None


def _should_disable_console_exporter() -> bool:
    """Check if console exporter should be disabled.

    Disables console exporter in test environments to reduce noise.

    Returns:
        True if console exporter should be disabled, False otherwise.
    """
    # Check environment variable
    if os.getenv("HEXSWITCH_DISABLE_CONSOLE_METRICS", "").lower() in ("1", "true", "yes"):
        return True

    # Check if running in pytest
    try:
        import pytest  # noqa: F401
        # If pytest is importable, we're likely in a test environment
        # Check if pytest is actually running by checking sys.modules
        if "pytest" in sys.modules:
            return True
    except ImportError:
        pass

    # Check if PYTEST_CURRENT_TEST is set (pytest sets this)
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True

    return False


class SafeConsoleMetricExporter(MetricExporter):
    """Console metric exporter that handles closed file errors gracefully."""

    def __init__(self, out=None):
        """Initialize safe console exporter.

        Args:
            out: Output stream (default: sys.stdout).
        """
        self._exporter = ConsoleMetricExporter(out=out or sys.stdout)
        # Delegate required attributes from the internal exporter
        self._preferred_temporality = self._exporter._preferred_temporality
        self._preferred_aggregation = self._exporter._preferred_aggregation

    def export(self, metrics_data: Any, timeout_millis: float = 10_000, **kwargs) -> MetricExportResult:
        """Export metrics with error handling.

        Args:
            metrics_data: Metric data to export.
            timeout_millis: Export timeout in milliseconds.
            **kwargs: Additional keyword arguments.

        Returns:
            Export result.
        """
        try:
            return self._exporter.export(metrics_data, timeout_millis=timeout_millis, **kwargs)
        except (ValueError, OSError) as e:
            if "closed file" in str(e).lower() or "I/O operation on closed file" in str(e):
                return MetricExportResult.SUCCESS
            raise

    def force_flush(self, timeout_millis: float = 10_000, **kwargs) -> bool:
        """Force flush metrics with error handling.

        Args:
            timeout_millis: Flush timeout in milliseconds.
            **kwargs: Additional keyword arguments.

        Returns:
            True if flush was successful, False otherwise.
        """
        try:
            return self._exporter.force_flush(timeout_millis=timeout_millis, **kwargs)
        except (ValueError, OSError) as e:
            if "closed file" in str(e).lower() or "I/O operation on closed file" in str(e):
                return True
            return False
        except Exception:
            return False

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        """Shutdown exporter.

        Args:
            timeout_millis: Shutdown timeout in milliseconds.
            **kwargs: Additional keyword arguments.
        """
        try:
            self._exporter.shutdown(timeout_millis=timeout_millis, **kwargs)
        except Exception:
            pass


def _get_meter_provider() -> MeterProvider:
    """Get or create global meter provider.

    Returns:
        Global MeterProvider instance.
    """
    global _meter_provider
    if _meter_provider is None:
        # Only add console exporter if not disabled (e.g., in tests)
        # If disabled, use InMemoryMetricReader to avoid console output
        if _should_disable_console_exporter():
            metric_readers = [InMemoryMetricReader()]
        else:
            metric_readers = [
                PeriodicExportingMetricReader(
                    SafeConsoleMetricExporter(out=sys.stdout), export_interval_millis=5000
                )
            ]

        _meter_provider = SDKMeterProvider(
            resource=Resource.create({"service.name": "hexswitch"}),
            metric_readers=metric_readers,
        )
        metrics.set_meter_provider(_meter_provider)
    return _meter_provider


class Counter:
    """Wrapper around OpenTelemetry Counter for compatibility."""

    def __init__(self, name: str, labels: dict[str, str] | None = None):
        """Initialize counter.

        Args:
            name: Metric name.
            labels: Optional labels for the metric.
        """
        self.name = name
        self.labels = labels or {}
        meter = _get_meter_provider().get_meter("hexswitch")
        self._counter = meter.create_counter(name, description=f"Counter: {name}")

    def inc(self, value: float = 1.0) -> None:
        """Increment counter by value.

        Args:
            value: Value to increment by (default: 1.0).
        """
        self._counter.add(value, attributes=self.labels)

    def get(self) -> float:
        """Get current counter value (not directly available in OTel).

        Note:
            OpenTelemetry doesn't expose current value directly.
            This method returns 0 for compatibility.

        Returns:
            Always returns 0 (OpenTelemetry doesn't expose current value).
        """
        return 0.0  # OTel doesn't expose current value directly

    def reset(self) -> None:
        """Reset counter (not supported in OpenTelemetry)."""
        logger.warning("Counter reset not supported in OpenTelemetry")


class Gauge:
    """Wrapper around OpenTelemetry Gauge for compatibility."""

    def __init__(self, name: str, labels: dict[str, str] | None = None):
        """Initialize gauge.

        Args:
            name: Metric name.
            labels: Optional labels for the metric.
        """
        self.name = name
        self.labels = labels or {}
        meter = _get_meter_provider().get_meter("hexswitch")
        self._gauge = meter.create_up_down_counter(name, description=f"Gauge: {name}")
        self._value = 0.0

    def set(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: Value to set.
        """
        delta = value - self._value
        self._gauge.add(delta, attributes=self.labels)
        self._value = value

    def inc(self, value: float = 1.0) -> None:
        """Increment gauge by value.

        Args:
            value: Value to increment by (default: 1.0).
        """
        self._gauge.add(value, attributes=self.labels)
        self._value += value

    def dec(self, value: float = 1.0) -> None:
        """Decrement gauge by value.

        Args:
            value: Value to decrement by (default: 1.0).
        """
        self._gauge.add(-value, attributes=self.labels)
        self._value -= value

    def get(self) -> float:
        """Get current gauge value.

        Returns:
            Current gauge value (tracked locally).
        """
        return self._value


class Histogram:
    """Wrapper around OpenTelemetry Histogram for compatibility."""

    def __init__(self, name: str, labels: dict[str, str] | None = None):
        """Initialize histogram.

        Args:
            name: Metric name.
            labels: Optional labels for the metric.
        """
        self.name = name
        self.labels = labels or {}
        meter = _get_meter_provider().get_meter("hexswitch")
        self._histogram = meter.create_histogram(name, description=f"Histogram: {name}")
        self._values: list[float] = []

    def observe(self, value: float) -> None:
        """Record a value in the histogram.

        Args:
            value: Value to record.
        """
        self._histogram.record(value, attributes=self.labels)
        self._values.append(value)

    def get(self) -> dict[str, Any]:
        """Get histogram statistics.

        Returns:
            Dictionary with count, sum, min, max, avg.
        """
        if not self._values:
            return {
                "count": 0,
                "sum": 0.0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
            }

        return {
            "count": len(self._values),
            "sum": sum(self._values),
            "min": min(self._values),
            "max": max(self._values),
            "avg": sum(self._values) / len(self._values),
        }

    def reset(self) -> None:
        """Reset histogram."""
        self._values.clear()


class MetricsCollector:
    """Collector for managing metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(
        self, name: str, labels: dict[str, str] | None = None
    ) -> Counter:
        """Get or create a counter.

        Args:
            name: Metric name.
            labels: Optional labels.

        Returns:
            Counter instance.
        """
        key = self._metric_key(name, labels)
        if key not in self._counters:
            self._counters[key] = Counter(name, labels)
        return self._counters[key]

    def gauge(self, name: str, labels: dict[str, str] | None = None) -> Gauge:
        """Get or create a gauge.

        Args:
            name: Metric name.
            labels: Optional labels.

        Returns:
            Gauge instance.
        """
        key = self._metric_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = Gauge(name, labels)
        return self._gauges[key]

    def histogram(
        self, name: str, labels: dict[str, str] | None = None
    ) -> Histogram:
        """Get or create a histogram.

        Args:
            name: Metric name.
            labels: Optional labels.

        Returns:
            Histogram instance.
        """
        key = self._metric_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = Histogram(name, labels)
        return self._histograms[key]

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics as dictionary.

        Returns:
            Dictionary with counters, gauges, and histograms.
        """
        return {
            "counters": {
                key: counter.get() for key, counter in self._counters.items()
            },
            "gauges": {
                key: gauge.get() for key, gauge in self._gauges.items()
            },
            "histograms": {
                key: histogram.get() for key, histogram in self._histograms.items()
            },
        }

    def _metric_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create metric key from name and labels.

        Args:
            name: Metric name.
            labels: Optional labels.

        Returns:
            Metric key string.
        """
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


_global_metrics_collector: MetricsCollector | None = None


def create_metrics_collector() -> MetricsCollector:
    """Create a new metrics collector instance.

    Returns:
        New MetricsCollector instance.
    """
    return MetricsCollector()


def get_global_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector.

    Returns:
        Global MetricsCollector instance.
    """
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector
