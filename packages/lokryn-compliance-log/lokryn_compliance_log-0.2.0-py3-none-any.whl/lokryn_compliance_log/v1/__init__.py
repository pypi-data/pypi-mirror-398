"""Version 1 of the compliance log schema."""

from lokryn_compliance_log.v1.logentry_pb2 import (
    # Messages
    LogRequest,
    Metadata,
    GenAIPayload,
    MCPPayload,
    Message,
    ToolCall,
    # Enums
    EventType,
    Outcome,
    Severity,
    Sensitivity,
)

__all__ = [
    # Messages
    "LogRequest",
    "Metadata",
    "GenAIPayload",
    "MCPPayload",
    "Message",
    "ToolCall",
    # Enums
    "EventType",
    "Outcome",
    "Severity",
    "Sensitivity",
]
