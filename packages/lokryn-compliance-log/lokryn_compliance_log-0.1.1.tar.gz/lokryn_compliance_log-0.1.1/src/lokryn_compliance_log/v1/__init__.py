"""Version 1 of the compliance log schema."""

from lokryn_compliance_log.v1.logentry_pb2 import (
    LogEntry,
    EventType,
    Outcome,
    Severity,
    Sensitivity,
)

__all__ = ["LogEntry", "EventType", "Outcome", "Severity", "Sensitivity"]
