# Google Chronicle Integration

## Overview

Google Chronicle supports OCSF for log ingestion.

**Standard Used:** OCSF v1.3.0
**Reference:** https://cloud.google.com/chronicle/docs

## Integration

### Ingestion Method

Chronicle supports multiple ingestion methods:

1. **Forwarder** - Recommended for most deployments
2. **API** - Direct ingestion via Chronicle Ingestion API
3. **Cloud Storage** - Batch ingestion from GCS

### OCSF Ingestion

Chronicle natively supports OCSF. Use the OCSF mapping from `../standards/ocsf/`:

1. Transform Lokryn logs to OCSF format
2. Use pre-translated `ocsf_class_uid` and `ocsf_activity_id` fields
3. Ingest via Chronicle forwarder or API

### Parser Configuration

For custom parsing, create a Chronicle parser:

```yaml
filter {
  mutate {
    rename => {
      "ocsf_class_uid" => "class_uid"
      "ocsf_activity_id" => "activity_id"
    }
  }
}
```

## Files

- See `../standards/ocsf/` for OCSF field mappings
- `ingestion_example.py` - Example Python ingestion script
