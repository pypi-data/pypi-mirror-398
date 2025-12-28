"""
Pre-computed mappings for OCSF and OTel GenAI export.

These mappings allow zero-cost export by storing translated values at write time.
"""

from typing import NamedTuple, Optional


class EventTypeMapping(NamedTuple):
    """Mapping for a single EventType to OCSF and OTel values."""

    ocsf_class_uid: int
    ocsf_class_name: str
    ocsf_activity_id: int
    ocsf_activity_name: str
    otel_operation_name: Optional[str]


# EventType value -> mapping
EVENT_TYPE_MAPPINGS: dict[int, EventTypeMapping] = {
    # Traditional audit events (1-12)
    1: EventTypeMapping(3002, "Authentication", 1, "Logon", None),  # EVENT_LOGIN
    2: EventTypeMapping(3002, "Authentication", 2, "Logoff", None),  # EVENT_LOGOUT
    3: EventTypeMapping(4010, "File Activity", 1, "Read", None),  # EVENT_FILE_ACCESS
    4: EventTypeMapping(5001, "Security Finding", 2, "Update", None),  # EVENT_POLICY_CHANGE
    5: EventTypeMapping(3002, "Authentication", 3, "Privilege Escalation", None),  # EVENT_PRIVILEGE_USE
    6: EventTypeMapping(5002, "Configuration Change", 1, "Create", None),  # EVENT_CONFIG_CHANGE
    7: EventTypeMapping(3005, "Data Access", 5, "Export", None),  # EVENT_DATA_EXPORT
    8: EventTypeMapping(4001, "Network Activity", 1, "Open", None),  # EVENT_NETWORK_CONNECTION
    9: EventTypeMapping(1007, "Process Activity", 1, "Launch", None),  # EVENT_PROCESS_START
    10: EventTypeMapping(1007, "Process Activity", 2, "Terminate", None),  # EVENT_PROCESS_STOP
    11: EventTypeMapping(3001, "Account Change", 1, "Create", None),  # EVENT_USER_MANAGEMENT
    12: EventTypeMapping(6003, "API Activity", 3, "Read", None),  # EVENT_RESOURCE_ACCESS
    # AI/Agent events (20-26)
    20: EventTypeMapping(6003, "API Activity", 1, "Create", "execute_tool"),  # EVENT_TOOL_INVOCATION
    21: EventTypeMapping(6003, "API Activity", 1, "Create", "chat"),  # EVENT_MODEL_INFERENCE
    22: EventTypeMapping(6003, "API Activity", 1, "Create", "invoke_agent"),  # EVENT_AGENT_DECISION
    23: EventTypeMapping(6003, "API Activity", 1, "Create", "invoke_agent"),  # EVENT_DELEGATION
    24: EventTypeMapping(3005, "Data Access", 1, "Read", "embeddings"),  # EVENT_CONTEXT_ACCESS
    25: EventTypeMapping(6003, "API Activity", 1, "Create", "chat"),  # EVENT_PROMPT_EXECUTION
    26: EventTypeMapping(5001, "Security Finding", 1, "Create", None),  # EVENT_GUARDRAIL_CHECK
    # MCP events (30-42)
    30: EventTypeMapping(6003, "API Activity", 1, "Create", "create_agent"),  # EVENT_MCP_INITIALIZE
    31: EventTypeMapping(6003, "API Activity", 1, "Create", "create_agent"),  # EVENT_MCP_INITIALIZED
    32: EventTypeMapping(6003, "API Activity", 3, "Read", None),  # EVENT_MCP_PING
    33: EventTypeMapping(6003, "API Activity", 4, "Delete", None),  # EVENT_MCP_SHUTDOWN
    34: EventTypeMapping(6003, "API Activity", 3, "Read", None),  # EVENT_TOOL_LIST
    35: EventTypeMapping(6003, "API Activity", 3, "Read", None),  # EVENT_RESOURCE_LIST
    36: EventTypeMapping(6003, "API Activity", 3, "Read", None),  # EVENT_PROMPT_LIST
    37: EventTypeMapping(3005, "Data Access", 1, "Read", None),  # EVENT_RESOURCE_READ
    38: EventTypeMapping(6003, "API Activity", 1, "Create", "chat"),  # EVENT_SAMPLING_REQUEST
    39: EventTypeMapping(6003, "API Activity", 1, "Create", "chat"),  # EVENT_SAMPLING_RESPONSE
    40: EventTypeMapping(4001, "Network Activity", 1, "Open", None),  # EVENT_TRANSPORT_CONNECT
    41: EventTypeMapping(4001, "Network Activity", 2, "Close", None),  # EVENT_TRANSPORT_DISCONNECT
    42: EventTypeMapping(4001, "Network Activity", 5, "Fail", None),  # EVENT_TRANSPORT_ERROR
}

# Default mapping for unknown event types
_DEFAULT_MAPPING = EventTypeMapping(0, "Unknown", 0, "Unknown", None)


def get_mapping(event_type: int) -> EventTypeMapping:
    """
    Get OCSF/OTel mapping values for an EventType.

    Args:
        event_type: The EventType enum value (e.g., 1 for EVENT_LOGIN, 20 for EVENT_TOOL_INVOCATION)

    Returns:
        EventTypeMapping with ocsf_class_uid, ocsf_activity_id, and otel_operation_name

    Example:
        >>> mapping = get_mapping(20)  # EVENT_TOOL_INVOCATION
        >>> mapping.ocsf_class_uid
        6003
        >>> mapping.otel_operation_name
        'execute_tool'
    """
    return EVENT_TYPE_MAPPINGS.get(event_type, _DEFAULT_MAPPING)


def get_ocsf_values(event_type: int) -> tuple[int, int]:
    """
    Get OCSF class_uid and activity_id for an EventType.

    Args:
        event_type: The EventType enum value

    Returns:
        Tuple of (ocsf_class_uid, ocsf_activity_id)

    Example:
        >>> class_uid, activity_id = get_ocsf_values(1)  # EVENT_LOGIN
        >>> class_uid
        3002
        >>> activity_id
        1
    """
    mapping = get_mapping(event_type)
    return mapping.ocsf_class_uid, mapping.ocsf_activity_id


def get_otel_operation_name(event_type: int) -> Optional[str]:
    """
    Get OTel GenAI operation name for an EventType.

    Args:
        event_type: The EventType enum value

    Returns:
        OTel operation name string, or None if not applicable

    Example:
        >>> get_otel_operation_name(21)  # EVENT_MODEL_INFERENCE
        'chat'
        >>> get_otel_operation_name(1)  # EVENT_LOGIN
        None
    """
    return get_mapping(event_type).otel_operation_name


# Outcome prefix collapse rules for OCSF export
OUTCOME_TO_OCSF_STATUS = {
    0: 0,  # OUTCOME_UNKNOWN -> Unknown
    1: 1,  # OUTCOME_SUCCESS -> Success
    2: 2,  # OUTCOME_FAILURE_UNAUTHORIZED -> Failure
    3: 2,  # OUTCOME_FAILURE_DENIED -> Failure
    4: 2,  # OUTCOME_FAILURE_ERROR -> Failure
    99: 99,  # OUTCOME_OTHER -> Other
}


def get_ocsf_status_id(outcome: int) -> int:
    """
    Get OCSF status_id for a Lokryn Outcome.

    Applies prefix collapse rule: OUTCOME_FAILURE_* -> status_id 2

    Args:
        outcome: The Outcome enum value

    Returns:
        OCSF status_id (0=Unknown, 1=Success, 2=Failure, 99=Other)
    """
    return OUTCOME_TO_OCSF_STATUS.get(outcome, 0)


# Sensitivity to OCSF confidentiality_id (values align directly for 0-4)
SENSITIVITY_TO_OCSF_CONFIDENTIALITY = {
    0: 0,  # SENSITIVITY_UNKNOWN -> Unknown
    1: 1,  # SENSITIVITY_PUBLIC -> Not Confidential
    2: 2,  # SENSITIVITY_CONFIDENTIAL -> Confidential
    3: 3,  # SENSITIVITY_SECRET -> Secret
    4: 4,  # SENSITIVITY_TOP_SECRET -> Top Secret
    10: 1,  # SENSITIVITY_PUBLIC_INTERNAL -> Not Confidential (prefix rule)
}


def get_ocsf_confidentiality_id(sensitivity: int) -> int:
    """
    Get OCSF confidentiality_id for a Lokryn Sensitivity.

    Args:
        sensitivity: The Sensitivity enum value

    Returns:
        OCSF confidentiality_id (0-4)
    """
    return SENSITIVITY_TO_OCSF_CONFIDENTIALITY.get(sensitivity, 0)
