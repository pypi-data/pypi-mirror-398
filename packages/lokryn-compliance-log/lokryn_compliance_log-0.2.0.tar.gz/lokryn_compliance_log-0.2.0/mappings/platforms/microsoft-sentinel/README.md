# Microsoft Sentinel Integration

## Overview

Microsoft Sentinel uses ASIM (Advanced SIEM Information Model) for log normalization.

**Standard Used:** ASIM
**Reference:** https://learn.microsoft.com/en-us/azure/sentinel/normalization

## Integration

### ASIM Schemas

ASIM provides normalized schemas similar to OCSF. Key schemas for Lokryn logs:

| Lokryn EventType | ASIM Schema |
|------------------|-------------|
| EVENT_LOGIN/LOGOUT | Authentication |
| EVENT_FILE_ACCESS | File Activity |
| EVENT_NETWORK_CONNECTION | Network Session |
| EVENT_PROCESS_START/STOP | Process |
| EVENT_USER_MANAGEMENT | User Management |

### Log Analytics Workspace

1. Configure Data Collection Rule (DCR) for custom logs
2. Use transformation rules to map to ASIM

### KQL Parser Example

```kql
lokryn_logs_CL
| extend
    EventType = toint(event_type_d),
    EventResult = case(
        outcome_d == 1, "Success",
        outcome_d >= 2 and outcome_d <= 4, "Failure",
        "NA"
    ),
    ActorUsername = actor_id_s,
    SrcDvcId = client_id_s,
    DstDvcId = server_id_s
```

## Files

- `field_mapping.json` - Lokryn → ASIM field mappings
- `examples/` - Example transformed events
