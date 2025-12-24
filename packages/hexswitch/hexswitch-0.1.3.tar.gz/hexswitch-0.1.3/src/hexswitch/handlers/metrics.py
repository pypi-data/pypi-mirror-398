"""Default metrics handler."""

from hexswitch.ports import port
from hexswitch.shared.envelope import Envelope
from hexswitch.shared.observability import get_global_metrics_collector


def _format_prometheus(metrics: dict) -> str:
    """Format metrics dictionary as Prometheus text format.

    Args:
        metrics: Dictionary with counters, gauges, and histograms.

    Returns:
        Prometheus-formatted string.
    """
    lines = []

    # Format counters
    if "counters" in metrics:
        for key, value in metrics["counters"].items():
            # Extract name and labels from key
            if "{" in key:
                name, labels = key.split("{", 1)
                labels = labels.rstrip("}")
                lines.append(f"{name}{{{labels}}} {value}")
            else:
                lines.append(f"{key} {value}")

    # Format gauges
    if "gauges" in metrics:
        for key, value in metrics["gauges"].items():
            if "{" in key:
                name, labels = key.split("{", 1)
                labels = labels.rstrip("}")
                lines.append(f"{name}{{{labels}}} {value}")
            else:
                lines.append(f"{key} {value}")

    # Format histograms
    if "histograms" in metrics:
        for key, value in metrics["histograms"].items():
            if "{" in key:
                name, labels = key.split("{", 1)
                labels = labels.rstrip("}")
                lines.append(f"{name}{{{labels}}} {value}")
            else:
                lines.append(f"{key} {value}")

    return "\n".join(lines) if lines else "# No metrics available"


@port(name="__metrics__")
def metrics_handler(envelope: Envelope) -> Envelope:
    """Metrics endpoint (Prometheus format)."""
    metrics = get_global_metrics_collector()
    all_metrics = metrics.get_all_metrics()
    prometheus_output = _format_prometheus(all_metrics)

    return Envelope(
        path=envelope.path,
        status_code=200,
        headers={"Content-Type": "text/plain; version=0.0.4"},
        data={"metrics": prometheus_output}
    )

