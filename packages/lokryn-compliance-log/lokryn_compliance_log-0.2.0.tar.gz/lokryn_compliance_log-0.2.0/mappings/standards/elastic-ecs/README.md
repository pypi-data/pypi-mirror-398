# Elastic Common Schema (ECS) Mapping

## Overview

Maps Lokryn compliance log schema to Elastic Common Schema v8.17.

**Target Version:** 8.17
**Reference:** https://www.elastic.co/guide/en/ecs/current/

## Design Principles

- Lokryn fields are canonical
- ECS uses nested field structures with dot notation
- Event categorization uses `event.category` and `event.type` arrays

## Key Mappings

### Event Categorization

ECS categorizes events using `event.category` and `event.type` arrays:

| Lokryn EventType | event.category | event.type |
|------------------|----------------|------------|
| EVENT_LOGIN | authentication | start |
| EVENT_LOGOUT | authentication | end |
| EVENT_FILE_ACCESS | file | access |
| EVENT_POLICY_CHANGE | configuration | change |
| EVENT_CONFIG_CHANGE | configuration | change |
| EVENT_NETWORK_CONNECTION | network | connection |
| EVENT_PROCESS_START | process | start |
| EVENT_PROCESS_STOP | process | end |
| EVENT_USER_MANAGEMENT | iam | user |
| EVENT_TOOL_INVOCATION | api | access |
| EVENT_MODEL_INFERENCE | api | access |
| EVENT_GUARDRAIL_CHECK | intrusion_detection | info |

### Outcome Mapping

| Lokryn Outcome | ECS event.outcome |
|----------------|-------------------|
| OUTCOME_SUCCESS | success |
| OUTCOME_FAILURE_* | failure |
| OUTCOME_OTHER | unknown |

## Files

- `field_mapping.json` - Lokryn field → ECS field mappings
- `event_type_mapping.json` - EventType → event.category/event.type mappings
- `examples/` - Side-by-side JSON examples

## Usage with Elasticsearch

See `../platforms/elastic/` for Elasticsearch index template and integration details.
