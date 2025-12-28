# Splunk Common Information Model (CIM) Mapping

## Overview

Maps Lokryn compliance log schema to Splunk CIM v6.1.

**Target Version:** 6.1
**Reference:** https://docs.splunk.com/Documentation/CIM

## Design Principles

- Lokryn fields are canonical
- Splunk CIM uses data models and tags for event classification
- Field names are flat (no dot notation)

## Key Mappings

### Data Model Assignment

| Lokryn EventType | CIM Data Model | Tags |
|------------------|----------------|------|
| EVENT_LOGIN | Authentication | authentication |
| EVENT_LOGOUT | Authentication | authentication |
| EVENT_FILE_ACCESS | Data Access | data, access |
| EVENT_POLICY_CHANGE | Change | change, audit |
| EVENT_CONFIG_CHANGE | Change | change, audit |
| EVENT_NETWORK_CONNECTION | Network Traffic | network, communicate |
| EVENT_PROCESS_START | Endpoint | process, report |
| EVENT_PROCESS_STOP | Endpoint | process, report |
| EVENT_USER_MANAGEMENT | Change | change, account |
| EVENT_TOOL_INVOCATION | Web | web |
| EVENT_MODEL_INFERENCE | Web | web |

### Field Mapping

| Lokryn Field | Splunk CIM Field |
|--------------|------------------|
| severity | severity |
| outcome | action |
| message | signature |
| actor_id | user |
| component | app |
| time | _time |

## Files

- `field_mapping.json` - Lokryn field → CIM field mappings
- `event_type_mapping.json` - EventType → data model/tags mappings
- `examples/` - Side-by-side JSON examples

## Usage with Splunk Enterprise

See `../platforms/splunk/` for props.conf and transforms.conf examples.
