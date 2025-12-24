"""Default health check handlers."""

import os
import time

from hexswitch.ports import port
from hexswitch.shared.envelope import Envelope

_start_time = time.time()


@port(name="__health__")
def health_handler(envelope: Envelope) -> Envelope:
    """Health check endpoint."""
    uptime = time.time() - _start_time
    return Envelope.success({
        "status": "healthy",
        "version": os.getenv("VERSION", "unknown"),
        "uptime_seconds": round(uptime, 2),
        "service": os.getenv("SERVICE_NAME", "hexswitch")
    })


@port(name="__ready__")
def readiness_handler(envelope: Envelope) -> Envelope:
    """Readiness check endpoint."""
    return Envelope.success({"ready": True})


@port(name="__live__")
def liveness_handler(envelope: Envelope) -> Envelope:
    """Liveness check endpoint."""
    return Envelope.success({"alive": True})

