"""Default handlers for HexSwitch framework.

Import this module to auto-register health and metrics endpoints.
"""

from hexswitch.handlers.health import health_handler, liveness_handler, readiness_handler
from hexswitch.handlers.metrics import metrics_handler

__all__ = [
    "health_handler",
    "readiness_handler",
    "liveness_handler",
    "metrics_handler",
]

