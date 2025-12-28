# Elasticsearch Integration

## Overview

Elasticsearch uses ECS (Elastic Common Schema) for log normalization.

**Standard Used:** ECS v8.17
**Reference:** https://www.elastic.co/guide/en/ecs/current/

## Integration

### Index Template

Use the provided index template to ensure proper field mappings:

```bash
curl -X PUT "localhost:9200/_index_template/lokryn-logs" \
  -H "Content-Type: application/json" \
  -d @index_template.json
```

### Ingest Pipeline

For transforming Lokryn logs to ECS format, create an ingest pipeline:

```json
{
  "processors": [
    {
      "rename": {
        "field": "time",
        "target_field": "@timestamp"
      }
    },
    {
      "rename": {
        "field": "trace_id",
        "target_field": "trace.id"
      }
    }
  ]
}
```

### Index Pattern

Recommended index pattern: `lokryn-logs-*`

## Files

- `index_template.json` - Elasticsearch index template with ECS mappings
- See `../standards/elastic-ecs/` for field mappings
