from __future__ import annotations
"""
Minimal diagnostics bus.

Current behavior: publish FaultEvent to the standard Python logger as a single-line JSON.
This keeps the system self-contained and avoids external deps. You can later extend
this module (e.g., add subscribers, OTLP/Kafka/MQTT adapters) without touching guards.
"""
import json
import logging
from .faults import FaultEvent

log = logging.getLogger("spx.diagnostics")

_SEVERITY_TO_LOG = {
    "error": log.error,
    "warn": log.warning,
    "info": log.info,
}


def publish(event: FaultEvent) -> None:
    """
    Emit a diagnostics event to logs as JSON.

    The log line is prefixed with 'FAULT ' to make it easy to grep, and the JSON payload
    is `event.to_dict()` if available, otherwise the object itself (best-effort).
    The log level is derived from `event.severity` (error/warn/info).
    """
    try:
        payload = event.to_dict() if hasattr(event, "to_dict") else event  # best-effort
        sev = getattr(event, "severity", None)
        sev_val = getattr(sev, "value", None) if sev is not None else None
        sev_key = (sev_val or str(sev or "error")).lower()
        log_fn = _SEVERITY_TO_LOG.get(sev_key, log.error)
        log_fn("FAULT %s", json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        # Never raise from diagnostics path; log the failure for visibility.
        log.exception("Failed to publish diagnostics event")
