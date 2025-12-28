# Datadog Integration

## Overview

Datadog supports both standard log ingestion and LLM Observability via OTel GenAI semantic conventions.

**Reference:** https://docs.datadoghq.com/logs/

## Integration Options

### 1. Standard Logs

Use Datadog reserved attributes for optimal indexing:

| Lokryn Field | Datadog Attribute |
|--------------|-------------------|
| severity | status |
| message | message |
| component | service |
| environment | env |
| actor_id | usr.id |
| trace_id | dd.trace_id |
| span_id | dd.span_id |

### 2. LLM Observability

For AI/Agent events, Datadog LLM Observability supports OTel GenAI SemConv natively.

Use the OTel GenAI mapping from `../standards/otel-genai/` and configure:

```yaml
# datadog.yaml
otlp_config:
  receiver:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
```

### Severity Mapping

Datadog uses string-based status levels:

| Lokryn Severity | Datadog Status |
|-----------------|----------------|
| 1-2 (DEBUG, INFO) | debug |
| 3-4 (NOTICE, WARNING) | info |
| 5 (ERROR) | warn |
| 6-8 (CRITICAL+) | error |

## Files

- `field_mapping.json` - Lokryn → Datadog reserved attributes
- `examples/` - Example log events
